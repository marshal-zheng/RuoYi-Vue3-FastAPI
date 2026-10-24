import { observeFeedback } from '@/utils/feedback/channel';
/**
 * @zxio/http 全局 HTTP 客户端配置
 */
import {
  createGridListPlugin,
  createHttpClient,
  isAbortError,
  isQueryRequest,
  resolveHttpError,
  type HttpError,
  type HttpClientImpl,
  type HttpNotifier,
  type HttpTransformHook,
  type SuccessResolver,
} from '@zxio/http';
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ElMessageBox } from 'element-plus';

import { getCsrfToken, getToken } from '@/utils/auth';
import { createSessionTransport } from '@/utils/session';
import errorCode from '@/utils/errorCode';
import { isHashRouteMode } from '@/router/history';
import useUserStore from '@/store/modules/user';
import {
  isCursorPage,
  isOffsetPage,
  isProblemDetails,
  isRecord,
  type HttpContractMeta,
  type HttpPager,
  type ProblemDetails,
} from '@/types/http-contract';
import {
  presentProblemFeedback,
  presentSuccessFeedback,
  resolveFeedbackOptions,
} from '@/utils/feedback/presenter';
import type { FeedbackOptions, ResolvedFeedbackOptions } from '@/utils/feedback/types';
import { showMessage } from '@/utils/feedback/message';
import { assertRequestScope, isRequestScopeCurrent } from '@/queries/context';

// 重新登录状态
export let isRelogin = { show: false };

type HttpConfigRecord = AxiosRequestConfig & {
  feedback?: FeedbackOptions;
  silentSuccess?: boolean;
  silentError?: boolean;
  skipRelogin?: boolean;
};

type RequestError = HttpError & {
  problem?: ProblemDetails;
  meta?: HttpContractMeta;
  status?: number;
};

const META_KEY = '__httpMeta';

// 401 反馈契约：
// 1. 登录/注册页本身就是恢复入口，不弹「去登录」，进入时清掉残留提示
// 2. silentError / skipRelogin 表示预期内的鉴权失败（会话探测、退出、登录表单），不走重新登录提示
// 3. 只有业务页上用户可感知的 401 才提示，并留在当前页

const readCurrentSpaPath = (): string => {
  if (typeof window === 'undefined') {
    return '/';
  }
  if (isHashRouteMode()) {
    const hashPath = window.location.hash.replace(/^#/, '');
    return hashPath || '/';
  }
  return `${location.pathname}${location.search}${location.hash}` || '/';
};

const isLoginRoute = (): boolean => {
  const currentPath = readCurrentSpaPath();
  return currentPath === '/login' || currentPath.startsWith('/login?');
};

const buildLoginRedirectUrl = (): string => {
  const redirect = encodeURIComponent(readCurrentSpaPath());
  return `/login?redirect=${redirect}`;
};

const readConfigFlag = (config: unknown, key: string): boolean => {
  const source = config as
    | { [key: string]: unknown; headers?: Record<string, unknown> }
    | undefined;
  if (!source) {
    return false;
  }
  if (source[key] === true) {
    return true;
  }
  const headers = source.headers;
  return headers?.[key] === true;
};

const shouldSkipRelogin = (config: unknown): boolean => {
  return readConfigFlag(config, 'skipRelogin');
};

type ReloginMessageHandle = { close: () => void };

let reloginMessage: ReloginMessageHandle | null = null;
let reloginPromptVersion = 0;

export const dismissReloginPrompt = (): void => {
  reloginPromptVersion++;
  const message = reloginMessage;
  reloginMessage = null;
  isRelogin.show = false;
  observeFeedback(() => message?.close());
};

const triggerRelogin = (): void =>
  observeFeedback(async () => {
    if (isRelogin.show || isLoginRoute()) {
      return;
    }

    isRelogin.show = true;
    const version = ++reloginPromptVersion;
    const loginUrl = buildLoginRedirectUrl();

    const doRedirect = (): void => {
      dismissReloginPrompt();
      useUserStore()
        .logOut({ silentSuccess: true, silentError: true })
        .then(() => {
          location.href = loginUrl;
        });
    };

    try {
      const result = await showMessage({
        message: '登录状态已失效',
        type: 'warning',
        action: { label: '重新登录', href: loginUrl, onClick: doRedirect },
        duration: 0,
        showClose: true,
        onClose: () => {
          if (version === reloginPromptVersion) {
            isRelogin.show = false;
            reloginMessage = null;
          }
        },
      });
      if (!result.ok) {
        if (version === reloginPromptVersion) isRelogin.show = false;
        return;
      }
      if (version !== reloginPromptVersion || isLoginRoute()) {
        await result.value.close();
        return;
      }
      reloginMessage = result.value;
    } catch {
      if (version === reloginPromptVersion) {
        isRelogin.show = false;
        reloginMessage = null;
      }
    }
  });

const notifier: HttpNotifier = {
  notify() {},
  message(type, content) {
    return showMessage({ type, message: content });
  },
  modal(type, options) {
    return ElMessageBox.alert(options.content, options.title || '提示', { type });
  },
};

const toNumber = (value: unknown): number | undefined => {
  if (value === null || value === undefined || value === '') {
    return undefined;
  }
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : undefined;
};

const readHeader = (headers: AxiosResponse['headers'], key: string): string | undefined => {
  const value = headers?.[key] ?? headers?.[key.toLowerCase()] ?? headers?.[key.toUpperCase()];
  if (Array.isArray(value)) {
    return value[0];
  }
  return typeof value === 'string' ? value : undefined;
};

const buildMeta = (response: AxiosResponse): HttpContractMeta => ({
  status: response.status,
  requestId: readHeader(response.headers, 'x-request-id'),
  traceId: readHeader(response.headers, 'x-trace-id'),
  location: readHeader(response.headers, 'location'),
  retryAfter: toNumber(readHeader(response.headers, 'retry-after')),
  rateLimitLimit: toNumber(readHeader(response.headers, 'ratelimit-limit')),
  rateLimitRemaining: toNumber(readHeader(response.headers, 'ratelimit-remaining')),
  rateLimitReset: toNumber(readHeader(response.headers, 'ratelimit-reset')),
});

const attachMeta = (payload: unknown, meta: HttpContractMeta): void => {
  if (!payload || (typeof payload !== 'object' && !Array.isArray(payload))) {
    return;
  }
  Object.defineProperty(payload, META_KEY, {
    value: meta,
    configurable: true,
    enumerable: false,
    writable: true,
  });
};

const resolvePager = (payload: unknown): HttpPager | null => {
  if (isOffsetPage(payload)) {
    return {
      mode: 'offset',
      page: payload.page,
      size: payload.pageSize,
      total: payload.total,
    };
  }

  if (isCursorPage(payload)) {
    return {
      mode: 'cursor',
      size: payload.pageSize,
      nextCursor: payload.nextCursor ?? null,
    };
  }

  if (isRecord(payload) && Array.isArray(payload.items)) {
    return {
      mode: 'collection',
      total: payload.items.length,
    };
  }

  return null;
};

const attachPager = (payload: unknown): void => {
  if (!payload || typeof payload !== 'object') {
    return;
  }
  const pager = resolvePager(payload);
  if (!pager) {
    return;
  }
  (payload as Record<string, unknown>).pager = pager;
};

const normalizeProblemDetails = (payload: unknown, status: number): ProblemDetails => {
  if (isProblemDetails(payload)) {
    return payload;
  }

  if (isRecord(payload)) {
    return {
      type: typeof payload.type === 'string' ? payload.type : 'about:blank',
      title:
        (payload.title as string | undefined) ||
        (status ? (errorCode as Record<number, string | undefined>)[status] : undefined) ||
        '请求失败',
      status: typeof payload.status === 'number' ? payload.status : status,
      detail:
        (payload.detail as string | undefined) ||
        (typeof payload.message === 'string' ? payload.message : undefined) ||
        (typeof payload.msg === 'string' ? payload.msg : undefined) ||
        (payload.title as string | undefined) ||
        '请求失败，请稍后重试',
      instance: typeof payload.instance === 'string' ? payload.instance : '',
      errorCode: payload.errorCode as string | number | undefined,
      requestId: payload.requestId as string | undefined,
      traceId: payload.traceId as string | undefined,
      errors: Array.isArray(payload.errors)
        ? (payload.errors as ProblemDetails['errors'])
        : undefined,
    };
  }

  return {
    type: 'about:blank',
    title: status
      ? (errorCode as Record<number, string | undefined>)[status] || '请求失败'
      : '请求失败',
    status,
    detail: typeof payload === 'string' && payload.trim() ? payload : '请求失败，请稍后重试',
    instance: '',
  };
};

const createRequestError = (
  original: HttpError,
  problem: ProblemDetails,
  meta: HttpContractMeta
): RequestError => {
  const error = original as RequestError;
  error.message = problem.detail || problem.title || '请求失败';
  error.problem = problem;
  error.meta = meta;
  error.status = problem.status || meta.status;
  return error;
};

const resolveFeedback = (config: HttpConfigRecord | undefined): ResolvedFeedbackOptions => {
  return resolveFeedbackOptions(config?.feedback);
};

const successResolver: SuccessResolver = ({ response }) => {
  const status = response.status;
  return {
    ok: status >= 200 && status < 300,
    data: status === 204 ? null : response.data,
    code: status,
    raw: response.data,
  };
};

const gridListPlugin = createGridListPlugin({
  requestPagerKey: 'pager',
  responsePagerKey: 'pager',
  pageField: 'page',
  sizeField: 'pageSize',
  totalField: 'total',
  listField: 'items',
  resolveList(payload) {
    return Array.isArray(payload.items) ? (payload.items as unknown[]) : undefined;
  },
  resolveTotal(payload) {
    return typeof payload.total === 'number' ? payload.total : undefined;
  },
});

const hasValue = (value: unknown): boolean => value !== null && value !== undefined && value !== '';

const normalizeGridParams = (params: Record<string, unknown>): Record<string, unknown> => {
  const normalizedParams: Record<string, unknown> = { ...(params || {}) };
  const pager = normalizedParams.pager as Record<string, unknown> | undefined;
  if (pager && typeof pager === 'object') {
    if (hasValue(pager.page)) normalizedParams.page = pager.page;
    if (hasValue(pager.size)) normalizedParams.pageSize = pager.size;
    delete normalizedParams.pager;
  }

  const query = normalizedParams.query as Record<string, unknown> | undefined;
  if (query && typeof query === 'object') {
    const queryPayload = { ...query };

    if (queryPayload.sortProp) {
      normalizedParams.orderByColumn = queryPayload.sortProp;
      delete queryPayload.sortProp;
    }
    if (queryPayload.sortOrder) {
      const orderMap: Record<string, string> = {
        ascending: 'asc',
        descending: 'desc',
      };
      normalizedParams.isAsc = orderMap[queryPayload.sortOrder as string] || queryPayload.sortOrder;
      delete queryPayload.sortOrder;
    }
    if (typeof queryPayload.isAsc === 'string') {
      const orderMap: Record<string, string> = {
        ascending: 'asc',
        descending: 'desc',
      };
      queryPayload.isAsc = orderMap[queryPayload.isAsc] || queryPayload.isAsc;
    }
    Object.assign(normalizedParams, queryPayload);
    delete normalizedParams.query;
  }

  return normalizedParams;
};

const beforeRequestTransform: HttpTransformHook = {
  async beforeRequest(config, options) {
    assertRequestScope(options);
    const requestConfig = config as HttpConfigRecord;

    if (requestConfig.data instanceof FormData) {
      const headers = requestConfig.headers as Record<string, unknown> | undefined;
      if (headers) {
        delete headers['Content-Type'];
        delete headers['content-type'];
      }
    }

    if (requestConfig.method?.toLowerCase() === 'get' && isRecord(requestConfig.params)) {
      const params = requestConfig.params as Record<string, unknown>;
      if (params.pager || params.query || hasValue(params.page)) {
        requestConfig.params = normalizeGridParams(params);
      }
    }

    const method = (requestConfig.method || 'get').toLowerCase();
    if (['post', 'put', 'patch', 'delete'].includes(method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        requestConfig.headers = requestConfig.headers || {};
        (requestConfig.headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
      }
    }

    return requestConfig;
  },
};

/** Present an already normalized business failure for the interaction that still owns it. */
export function presentRequestError(
  original: HttpError,
  config: HttpConfigRecord = original.config || {}
): void {
  const error = original as RequestError;
  const { problem, meta } = error;
  if (!problem || !meta || isAbortError(error)) return;
  const status = meta.status;
  const skipRelogin = shouldSkipRelogin(config);
  if (status === 401 || problem.errorCode === 20001 || problem.errorCode === 20002) {
    const onLoginPage = isLoginRoute();
    const silentError = readConfigFlag(config, 'silentError');
    const shouldPromptRelogin = !skipRelogin && !silentError && !onLoginPage;
    if (shouldPromptRelogin) {
      triggerRelogin();
    } else if (skipRelogin && !silentError) {
      presentProblemFeedback({
        problem,
        meta,
        feedback: resolveFeedback(config),
      });
    }
    return;
  }

  if (!readConfigFlag(config, 'silentError')) {
    presentProblemFeedback({
      problem,
      meta,
      feedback: resolveFeedback(config),
    });
  }
}

const MUTATION_METHODS = new Set(['post', 'put', 'delete', 'patch']);

const afterResponseTransform: HttpTransformHook = {
  async afterResponse(response, options) {
    const config = response.config as HttpConfigRecord;
    const method = (config.method || 'get').toLowerCase();
    const feedback = resolveFeedback(config);

    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response;
    }

    const payload = response.status === 204 ? null : response.data;
    const meta = buildMeta(response);
    attachMeta(payload, meta);
    attachPager(payload);

    if (!MUTATION_METHODS.has(method) && !(feedback.mode === 'auto' && feedback.key)) {
      return response;
    }

    if (isRequestScopeCurrent(options) && !readConfigFlag(config, 'silentSuccess')) {
      presentSuccessFeedback({
        status: response.status,
        payload,
        meta,
        feedback,
      });
    }

    return response;
  },

  async onError(error, options) {
    const axiosError = await resolveHttpError(error);
    if (isAbortError(axiosError)) {
      throw axiosError;
    }
    const config = (axiosError.config || {}) as HttpConfigRecord;
    const status = axiosError.response?.status || 0;
    const meta = axiosError.response ? buildMeta(axiosError.response) : { status };
    const localFailureMessage =
      !axiosError.response &&
      (axiosError.name === 'RequestPreparationError' || axiosError.name === 'HttpError')
        ? axiosError.message
        : undefined;
    const problem = normalizeProblemDetails(axiosError.data ?? localFailureMessage, status);

    const requestError = createRequestError(axiosError, problem, meta);
    if (isRequestScopeCurrent(options)) {
      const authFailure =
        status === 401 || problem.errorCode === 20001 || problem.errorCode === 20002;
      if (authFailure || !isQueryRequest(options)) presentRequestError(requestError, config);
    }
    throw requestError;
  },
};

const sessionTransport = createSessionTransport((token) => {
  useUserStore().token = token;
});
export const refreshHttpSession = sessionTransport.refresh;

export const http = createHttpClient({
  axiosConfig: {
    baseURL: import.meta.env.VITE_APP_BASE_API as string,
    timeout: 10000,
    adapter: sessionTransport.adapter,
  },
  tokenProvider: {
    getToken: () => getToken() || '',
    applyToken(config, token, options) {
      assertRequestScope(options);
      const headers = (config.headers ??= {}) as Record<string, unknown>;
      const isToken = headers.isToken === false;
      if (!isToken && token.value) {
        headers[token.headerName] = token.headerValue;
      }
    },
  },
  notifier,
  successResolver,
  successCodes: [200, 201, 202, 204],
  plugins: [gridListPlugin],
  transforms: [beforeRequestTransform, afterResponseTransform],
  requestOptions: {
    withToken: true,
    isTransformResponse: true,
    showSuccessMessage: false,
    showErrorMessage: false,
    errorMessageMode: 'none',
    successMessageMode: 'none',
  },
});

export type { HttpClientImpl };
