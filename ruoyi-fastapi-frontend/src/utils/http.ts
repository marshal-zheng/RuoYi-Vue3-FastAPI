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
import { ElNotification, ElMessageBox, ElMessage } from 'element-plus';
import { getToken } from '@/utils/auth';
import errorCode from '@/utils/errorCode';
import cache from '@/plugins/cache';
import useUserStore from '@/store/modules/user';

// 重新登录状态
export let isRelogin = { show: false };

// Element Plus 通知适配器
const notifier: HttpNotifier = {
  notify(event) {
    const { level, channel, payload } = event;
    if (channel === 'message') {
      ElMessage[level](payload.content);
    } else if (channel === 'modal') {
      ElMessageBox.alert(payload.content, payload.title || '提示', {
        type: level === 'success' ? 'success' : level === 'error' ? 'error' : level === 'warning' ? 'warning' : 'info',
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

// 自定义成功判定器
const successResolver: SuccessResolver = ({ response }) => {
  const payload = (response.data || {}) as Record<string, unknown>;
  const responseCode = (payload.code as number | undefined) ?? 200;
  const responseMsg =
    (payload.msg as string | undefined) ||
    (payload.message as string | undefined) ||
    errorCode[responseCode] ||
    errorCode['default'];

  return {
    ok: responseCode === 200,
    data: payload,
    message: responseMsg,
    code: responseCode,
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
    return (payload.rows as unknown[]) || (payload.data as unknown[]) || (payload.list as unknown[]);
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

    return config;
  },
};

// 响应后处理钩子
const afterResponseTransform: HttpTransformHook = {
  async afterResponse(response, options, context) {
    const { code, msg, message } = response.data as Record<string, unknown>;
    const responseCode = (code as number) ?? 200;
    const responseMsg =
      (msg as string) || (message as string) || errorCode[responseCode] || errorCode['default'];

    // 检查是否为静默模式
    const silentError = ((response.config as Record<string, unknown>)?.silentError as boolean) === true;

    // 二进制数据直接返回
    if (
      response.config.responseType === 'blob' ||
      response.config.responseType === 'arraybuffer'
    ) {
      return response;
    }

    // 401 未授权
    if (responseCode === 401) {
      if (!isRelogin.show) {
        isRelogin.show = true;
        ElMessageBox.confirm('登录状态已过期，您可以继续留在该页面，或者重新登录', '系统提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning',
        })
          .then(() => {
            isRelogin.show = false;
            useUserStore()
              .logOut()
              .then(() => {
                location.href = '/index';
              });
          })
          .catch(() => {
            isRelogin.show = false;
          });
      }
      return Promise.reject('无效的会话，或者会话已过期，请重新登录。');
    }

    // 500 服务器错误
    if (responseCode === 500) {
      if (!silentError) {
        ElMessage({ message: responseMsg, type: 'error' });
      }
      return Promise.reject(new Error(responseMsg));
    }

    // 601 警告
    if (responseCode === 601) {
      if (!silentError) {
        ElMessage({ message: responseMsg, type: 'warning' });
      }
      return Promise.reject(new Error(responseMsg));
    }

    // 其他非 200 错误
    if (responseCode !== 200) {
      if (!silentError) {
        ElNotification.error({ title: responseMsg });
      }
      return Promise.reject('error');
    }

    // 成功响应，附加 pager 信息（兼容旧逻辑）
    attachPager(response.data);
    return response;
  },

  async onError(error, options, context) {
    const axiosError = error as { config?: Record<string, unknown>; message?: string };
    const silentError = (axiosError.config?.silentError as boolean) === true;
    let message = axiosError.message || '';

    if (message === 'Network Error') {
      message = '后端接口连接异常';
    } else if (message.includes('timeout')) {
      message = '系统接口请求超时';
    } else if (message.includes('Request failed with status code')) {
      message = '系统接口' + message.substr(message.length - 3) + '异常';
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
