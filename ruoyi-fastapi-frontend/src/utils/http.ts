/**
 * @zxio/http 全局 HTTP 客户端配置
 *
 * 使用方式：
 * 1. 直接导入使用：import { http } from '@/utils/http'
 * 2. 全局属性使用：this.$http (Options API) 或 inject('$http') (Composition API)
 */
import {
  createHttpClient,
  createGridListPlugin,
  type HttpNotifier,
  type HttpClientImpl,
  type SuccessResolver,
  type HttpTransformHook,
} from '@zxio/http';
import { ElNotification, ElMessage, ElMessageBox } from 'element-plus';
import { h } from 'vue';
import { getCsrfToken, getToken } from '@/utils/auth';
import errorCode from '@/utils/errorCode';
import cache from '@/plugins/cache';
import useUserStore from '@/store/modules/user';

// 重新登录状态
export let isRelogin = { show: false };

type ReloginMode = 'auto' | 'link';

// 401 重新登录交互方式：auto = 提示后自动跳转；link = 提示并提供跳转链接
const RELOGIN_MODE: ReloginMode = 'link';
const RELOGIN_DELAY = 1200;

const buildLoginRedirectUrl = (): string => {
  const current = `${location.pathname}${location.search}${location.hash}`;
  const redirect = encodeURIComponent(current || '/');
  return `/login?redirect=${redirect}`;
};

const readConfigFlag = (config: Record<string, unknown> | undefined, key: string): boolean => {
  if (!config) {
    return false;
  }
  if (config[key] === true) {
    return true;
  }
  const headers = config.headers as Record<string, unknown> | undefined;
  return headers?.[key] === true;
};

const shouldSkipRelogin = (config: Record<string, unknown> | undefined): boolean => {
  return readConfigFlag(config, 'skipRelogin');
};

const triggerRelogin = (message: string): void => {
  if (isRelogin.show) return;
  if (location.pathname === '/login') return;

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
  } else {
    ElMessage({
      message: `${message || '未认证，请先登录'}，即将跳转登录`,
      type: 'warning',
      duration: RELOGIN_DELAY,
    });
    window.setTimeout(doRedirect, RELOGIN_DELAY);
  }
};

// Element Plus 通知适配器
const notifier: HttpNotifier = {
  notify(event) {
    const { level, channel, payload } = event;
    if (channel === 'message') {
      ElMessage[level](payload.content);
    } else if (channel === 'modal') {
      ElMessageBox.alert(payload.content, payload.title || '提示', {
        type:
          level === 'success'
            ? 'success'
            : level === 'error'
              ? 'error'
              : level === 'warning'
                ? 'warning'
                : 'info',
      });
    }
  },
  message(type, content) {
    ElMessage[type](content);
  },
  modal(type, options) {
    ElMessageBox.alert(options.content, options.title || '提示', { type });
  },
};

// 自定义成功判定器（基于 HTTP 状态码）
const successResolver: SuccessResolver = ({ response }) => {
  const payload = (response.data || {}) as Record<string, unknown>;
  const status = response.status;

  // 基于 HTTP 2xx 判定成功
  const ok = status >= 200 && status < 300;

  if (ok) {
    // 成功响应
    const responseMsg =
      (payload.message as string | undefined) || (payload.msg as string | undefined) || '操作成功';

    // 响应数据解包策略：
    // - 如果后端返回 {"data": xxx, ...}，则解包返回 xxx
    // - 如果后端返回 {"rows": [...], "total": n, ...}，则返回完整 payload
    // 这样业务代码统一使用 res 访问数据（res 就是实际数据）
    return {
      ok: true,
      data: payload.data !== undefined ? payload.data : payload,
      message: responseMsg,
      code: status,
      raw: payload,
    };
  }

  // 错误响应（RFC 7807）
  const errorMsg =
    (payload.detail as string | undefined) ||
    (payload.title as string | undefined) ||
    (payload.message as string | undefined) ||
    (payload.msg as string | undefined) ||
    errorCode[status] ||
    errorCode['default'];

  return {
    ok: false,
    data: payload,
    message: errorMsg,
    code: (payload.errorCode as number) || status,
    raw: payload,
  };
};

// Grid List 插件配置（适配若依后端）
const gridListPlugin = createGridListPlugin({
  requestPagerKey: 'pager',
  responsePagerKey: 'pager',
  pageField: 'pageNum',
  sizeField: 'pageSize',
  totalField: 'total',
  listField: 'rows',
  resolveList(payload) {
    return (
      (payload.rows as unknown[]) || (payload.data as unknown[]) || (payload.list as unknown[])
    );
  },
  resolveTotal(payload) {
    return payload.total as number | undefined;
  },
});

// 请求前处理钩子
const beforeRequestTransform: HttpTransformHook = {
  async beforeRequest(config, options, context) {
    // FormData 交给浏览器自动设置 boundary
    if (config.data instanceof FormData) {
      const headers = config.headers as Record<string, unknown> | undefined;
      if (headers) {
        delete headers['Content-Type'];
        delete headers['content-type'];
      }
    }

    // 处理 GET 请求的 Grid List 参数转换
    if (config.method?.toLowerCase() === 'get' && config.params) {
      const params = config.params as Record<string, unknown>;
      if (params.pager || params.query) {
        config.params = normalizeGridParams(params);
      }
    }

    // 防重复提交检查
    const headers = (config.headers || {}) as Record<string, unknown>;
    const isRepeatSubmit = headers.repeatSubmit === false;

    if (
      !isRepeatSubmit &&
      (config.method?.toLowerCase() === 'post' || config.method?.toLowerCase() === 'put')
    ) {
      const requestObj = {
        url: config.url,
        data: typeof config.data === 'object' ? JSON.stringify(config.data) : config.data,
        time: new Date().getTime(),
      };
      const requestSize = Object.keys(JSON.stringify(requestObj)).length;
      const limitSize = 5 * 1024 * 1024; // 5M

      if (requestSize < limitSize) {
        const sessionObj = cache.session.getJSON('sessionObj');
        if (sessionObj) {
          const interval = 1000; // 间隔时间(ms)
          if (
            sessionObj.data === requestObj.data &&
            requestObj.time - sessionObj.time < interval &&
            sessionObj.url === requestObj.url
          ) {
            const message = '数据正在处理，请勿重复提交';
            console.warn(`[${sessionObj.url}]: ${message}`);
            return Promise.reject(new Error(message));
          }
        }
        cache.session.setJSON('sessionObj', requestObj);
      }
    }

    // 对写操作自动附加 CSRF Header（token 仅保存在内存中）
    const method = (config.method || 'get').toLowerCase();
    if (['post', 'put', 'patch', 'delete'].includes(method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        if (!config.headers) {
          config.headers = {};
        }
        (config.headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
      }
    }

    return config;
  },
};

// 需要显示成功提示的请求方法
const MUTATION_METHODS = ['post', 'put', 'delete', 'patch'];

// 响应后处理钩子（RFC 7807 标准）
const afterResponseTransform: HttpTransformHook = {
  async afterResponse(response, options, context) {
    const config = response.config as Record<string, unknown>;
    const silentError = readConfigFlag(config, 'silentError');
    const silentSuccess = readConfigFlag(config, 'silentSuccess');
    const skipRelogin = shouldSkipRelogin(config);

    // 二进制数据直接返回
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response;
    }

    const status = response.status;
    const payload = response.data as Record<string, unknown>;
    const method = (response.config.method || 'get').toLowerCase();

    // 2xx 成功响应
    if (status >= 200 && status < 300) {
      attachPager(response.data);

      // 只有写操作（POST/PUT/DELETE/PATCH）才显示成功提示
      if (!silentSuccess && MUTATION_METHODS.includes(method)) {
        const successMsg = (payload.message as string) || (payload.msg as string) || '操作成功';
        ElMessage.success(successMsg);
      }

      return response;
    }

    // RFC 7807 错误响应解析
    const bizErrorCode = (payload.errorCode as number) || status;
    const errorMsg =
      (payload.detail as string) ||
      (payload.title as string) ||
      (payload.message as string) ||
      (payload.msg as string) ||
      (errorCode as any)[status] ||
      (errorCode as any)['default'];

    // 401 未授权
    if (status === 401 || bizErrorCode === 20001 || bizErrorCode === 20002) {
      if (!skipRelogin) {
        triggerRelogin(errorMsg || '未认证，请先登录');
      }
      return Promise.reject(new Error('无效的会话，或者会话已过期，请重新登录。'));
    }

    // 403 权限不足
    if (status === 403 || bizErrorCode === 20004) {
      if (!silentError) {
        ElMessage({ message: errorMsg || '权限不足', type: 'error' });
      }
      return Promise.reject(new Error(errorMsg || '权限不足'));
    }

    // 422 校验错误（展示字段级错误）
    if (status === 422 || bizErrorCode === 10001) {
      if (!silentError) {
        const errors = (payload.errors as Array<{ field: string; message: string }>) || [];

        if (errors.length > 0) {
          // 展示字段级错误
          const errorDetails = errors.map((e) => `${e.field}: ${e.message}`).join('\n');
          ElNotification.error({
            title: '参数验证失败',
            message: errorDetails,
            duration: 5000,
          });
        } else {
          ElMessage({ message: errorMsg || '参数验证失败', type: 'error' });
        }
      }
      return Promise.reject(new Error(errorMsg || '参数验证失败'));
    }

    // 500+ 系统错误
    if (status >= 500) {
      if (!silentError) {
        ElMessage({ message: errorMsg || '系统错误', type: 'error' });
      }
      return Promise.reject(new Error(errorMsg || '系统错误'));
    }

    // 其他 4xx 错误
    if (status >= 400) {
      if (!silentError) {
        ElNotification.error({ title: errorMsg || '操作失败' });
      }
      return Promise.reject(new Error(errorMsg || '操作失败'));
    }

    return response;
  },

  async onError(error, options, context) {
    const axiosError = error as {
      config?: Record<string, unknown>;
      message?: string;
      response?: { data?: Record<string, unknown>; status?: number };
    };
    const silentError = readConfigFlag(axiosError.config, 'silentError');
    const skipRelogin = shouldSkipRelogin(axiosError.config);
    const data = axiosError.response?.data;
    const status = axiosError.response?.status;
    const code = (data?.code as number | undefined) || (data?.errorCode as number | undefined);

    // 优先从响应体获取错误信息（RFC 7807）
    let message = '';
    if (data) {
      message =
        (data.detail as string) ||
        (data.title as string) ||
        (data.message as string) ||
        (data.msg as string) ||
        (code ? (errorCode[code] as string | undefined) : '') ||
        '';
    }

    if (status === 401 || code === 20001 || code === 20002) {
      if (!skipRelogin) {
        triggerRelogin(message || '未认证，请先登录');
      }
      throw new Error('登录状态已过期，请重新登录');
    }

    if (!message) {
      message = axiosError.message || '';
      if (message === 'Network Error') {
        message = '后端接口连接异常';
      } else if (message.includes('timeout')) {
        message = '系统接口请求超时';
      } else if (message.includes('Request failed with status code')) {
        message = '系统接口' + message.substr(message.length - 3) + '异常';
      }
    }

    if (!silentError && message) {
      ElMessage({ message, type: 'error', duration: 5000 });
    }

    throw error;
  },
};

// 创建全局 HTTP 客户端
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
    applyToken(config, token, options) {
      // 检查是否需要携带 token
      const headers = (config.headers || {}) as Record<string, unknown>;
      const isToken = headers.isToken === false;

      if (!isToken && token.value) {
        (config.headers as Record<string, string>)[token.headerName] = token.headerValue;
      }
    },
    onAuthError(error) {
      // 401 错误在 afterResponse 中处理
    },
  },
  notifier,
  successResolver,
  successCodes: [200],
  plugins: [gridListPlugin],
  transforms: [beforeRequestTransform, afterResponseTransform],
  requestOptions: {
    withToken: true,
    isTransformResponse: true,
    showSuccessMessage: false,
    showErrorMessage: true,
    errorMessageMode: 'message',
    successMessageMode: 'none',
  },
});

// ==================== 辅助函数 ====================

const hasValue = (value: unknown): boolean => value !== null && value !== undefined;

interface PagerInfo {
  page?: number;
  size?: number;
  total?: number;
}

const resolvePager = (source?: Record<string, unknown>): PagerInfo | null => {
  if (!source) return null;
  const page = (source.pageNum ?? source.page) as number | undefined;
  const size = (source.pageSize ?? source.size) as number | undefined;
  const total = source.total as number | undefined;
  if ([page, size, total].some(hasValue)) {
    return { page, size, total };
  }
  return null;
};

const attachPager = (data: unknown): void => {
  if (!data || typeof data !== 'object') return;
  const payload = data as Record<string, unknown>;
  const candidates: Record<string, unknown>[] = [];
  if (payload && !candidates.includes(payload)) {
    candidates.push(payload);
  }
  if (
    payload.data &&
    typeof payload.data === 'object' &&
    !candidates.includes(payload.data as Record<string, unknown>)
  ) {
    candidates.push(payload.data as Record<string, unknown>);
  }
  const pager = resolvePager(payload) || resolvePager(payload.data as Record<string, unknown>);
  if (!pager) return;
  candidates.forEach((target) => {
    target.pager = { page: pager.page, size: pager.size, total: pager.total };
  });
};

const normalizeGridParams = (params: Record<string, unknown>): Record<string, unknown> => {
  const p: Record<string, unknown> = { ...(params || {}) };
  const pager = p.pager as Record<string, unknown> | undefined;
  if (pager && typeof pager === 'object') {
    if (hasValue(pager.page)) p.pageNum = pager.page;
    if (hasValue(pager.size)) p.pageSize = pager.size;
    delete p.pager;
  }
  const query = p.query as Record<string, unknown> | undefined;
  if (query && typeof query === 'object') {
    const q = { ...query };
    if (q.sortProp) {
      p.orderByColumn = q.sortProp;
      delete q.sortProp;
    }
    if (q.sortOrder) {
      const map: Record<string, string> = { ascending: 'asc', descending: 'desc' };
      p.isAsc = map[q.sortOrder as string] || q.sortOrder;
      delete q.sortOrder;
    }
    if (typeof q.isAsc === 'string') {
      const map2: Record<string, string> = { ascending: 'asc', descending: 'desc' };
      q.isAsc = map2[q.isAsc] || q.isAsc;
    }
    Object.keys(q).forEach((k) => {
      p[k] = q[k];
    });
    delete p.query;
  }
  return p;
};

// 导出类型
export type { HttpClientImpl };
