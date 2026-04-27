/**
 * @zxio/http 全局 HTTP 客户端配置
 */
import {
  createGridListPlugin,
  createHttpClient,
  type HttpClientImpl,
  type HttpNotifier,
  type HttpTransformHook,
  type SuccessResolver,
} from '@zxio/http';
import type { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { h } from 'vue';

import { getCsrfToken, getToken } from '@/utils/auth';
import errorCode from '@/utils/errorCode';
import cache from '@/plugins/cache';
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

// 重新登录状态
export let isRelogin = { show: false };

type ReloginMode = 'auto' | 'link';

type HttpConfigRecord = AxiosRequestConfig & {
  feedback?: FeedbackOptions;
  silentSuccess?: boolean;
  silentError?: boolean;
  skipRelogin?: boolean;
};

type RequestError = Error & {
  problem?: ProblemDetails;
  meta?: HttpContractMeta;
  status?: number;
};

const META_KEY = '__httpMeta';

// 401 重新登录交互方式：auto = 提示后自动跳转；link = 提示并提供跳转链接
const RELOGIN_MODE: ReloginMode = 'link';
const RELOGIN_DELAY = 1200;

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

const triggerRelogin = (message: string): void => {
  if (isRelogin.show || isLoginRoute()) {
    return;
  }

  isRelogin.show = true;
  const loginUrl = buildLoginRedirectUrl();

  const doRedirect = (): void => {
    useUserStore()
      .logOut({ silentSuccess: true, silentError: true })
      .then(() => {
        location.href = loginUrl;
      })
      .finally(() => {
        isRelogin.show = false;
      });
  };

  if (RELOGIN_MODE === 'link') {
    const content = h('span', null, [
      message || '未认证，请先登录',
      h(
        'a',
        {
          href: loginUrl,
          style: 'margin-left: 8px; color: var(--el-color-primary); text-decoration: underline;',
          onClick: (event: MouseEvent) => {
            event.preventDefault();
            doRedirect();
          },
        },
        '去登录'
      ),
    ]);
    ElMessage({
      message: content,
      type: 'warning',
      duration: 5000,
      showClose: true,
      onClose: () => {
        isRelogin.show = false;
      },
    });
    return;
  }

  ElMessage({
    message: `${message || '未认证，请先登录'}，即将跳转登录`,
    type: 'warning',
    duration: RELOGIN_DELAY,
  });
  window.setTimeout(doRedirect, RELOGIN_DELAY);
};

const notifier: HttpNotifier = {
  notify() {},
  message(type, content) {
    ElMessage[type](content);
  },
  modal(type, options) {
    ElMessageBox.alert(options.content, options.title || '提示', { type });
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
    detail: '请求失败，请稍后重试',
    instance: '',
  };
};

const createRequestError = (problem: ProblemDetails, meta: HttpContractMeta): RequestError => {
  const error = new Error(problem.detail || problem.title || '请求失败') as RequestError;
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
  async beforeRequest(config) {
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

    const headers = (requestConfig.headers || {}) as Record<string, unknown>;
    const isRepeatSubmit = headers.repeatSubmit === false;
    if (
      !isRepeatSubmit &&
      ['post', 'put', 'patch'].includes((requestConfig.method || 'get').toLowerCase())
    ) {
      const requestObj = {
        url: requestConfig.url,
        data:
          typeof requestConfig.data === 'object' && !(requestConfig.data instanceof FormData)
            ? JSON.stringify(requestConfig.data)
            : requestConfig.data,
        time: Date.now(),
      };
      const requestSize = Object.keys(JSON.stringify(requestObj)).length;
      const limitSize = 5 * 1024 * 1024;

      if (requestSize < limitSize) {
        const sessionObj = cache.session.getJSON('sessionObj');
        if (sessionObj) {
          const interval = 1000;
          if (
            sessionObj.data === requestObj.data &&
            requestObj.time - sessionObj.time < interval &&
            sessionObj.url === requestObj.url
          ) {
            return Promise.reject(new Error('数据正在处理，请勿重复提交'));
          }
        }
        cache.session.setJSON('sessionObj', requestObj);
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

const MUTATION_METHODS = new Set(['post', 'put', 'delete', 'patch']);

const afterResponseTransform: HttpTransformHook = {
  async afterResponse(response) {
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

    if (!readConfigFlag(config, 'silentSuccess')) {
      presentSuccessFeedback({
        status: response.status,
        payload,
        meta,
        feedback,
      });
    }

    return response;
  },

  async onError(error) {
    const axiosError = error as AxiosError & { config?: HttpConfigRecord };
    const config = (axiosError.config || {}) as HttpConfigRecord;
    const skipRelogin = shouldSkipRelogin(config);
    const status = axiosError.response?.status || 0;
    const meta = axiosError.response ? buildMeta(axiosError.response) : { status };
    const problem = normalizeProblemDetails(axiosError.response?.data, status);

    if (status === 401 || problem.errorCode === 20001 || problem.errorCode === 20002) {
      if (!skipRelogin) {
        triggerRelogin(problem.detail || problem.title || '未认证，请先登录');
      }
      throw createRequestError(problem, meta);
    }

    if (!readConfigFlag(config, 'silentError')) {
      presentProblemFeedback({
        problem,
        meta,
        feedback: resolveFeedback(config),
      });
    }

    throw createRequestError(problem, meta);
  },
};

export const http = createHttpClient({
  axiosConfig: {
    baseURL: import.meta.env.VITE_APP_BASE_API as string,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json;charset=utf-8',
    },
  },
  tokenProvider: {
    getToken: () => getToken() || '',
    applyToken(config, token) {
      const headers = (config.headers || {}) as Record<string, unknown>;
      const isToken = headers.isToken === false;
      if (!isToken && token.value) {
        (config.headers as Record<string, string>)[token.headerName] = token.headerValue;
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
