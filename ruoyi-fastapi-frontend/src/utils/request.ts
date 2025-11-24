import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ElNotification, ElMessageBox, ElMessage, ElLoading } from 'element-plus';
import { getToken } from '@/utils/auth';
import errorCode from '@/utils/errorCode';
import { tansParams, blobValidate } from '@/utils/ruoyi';
import cache from '@/plugins/cache';
import { saveAs } from 'file-saver';
import useUserStore from '@/store/modules/user';

interface LoadingInstance {
  close(): void;
}

interface ReloginState {
  show: boolean;
}

let downloadLoadingInstance: LoadingInstance;
// 是否显示重新登录
export let isRelogin: ReloginState = { show: false };

const FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded';

const hasValue = (value: unknown): boolean => value !== null && value !== undefined;

interface PagerInfo {
  page?: number;
  size?: number;
  total?: number;
}

const resolvePager = (source?: Record<string, any>): PagerInfo | null => {
  if (!source) return null;
  const page = source.pageNum ?? source.page;
  const size = source.pageSize ?? source.size;
  const total = source.total;
  if ([page, size, total].some(hasValue)) {
    return { page, size, total };
  }
  return null;
};

const attachPager = (data: unknown): void => {
  if (!data || typeof data !== 'object') return;
  const payload = data as Record<string, any>;
  const candidates: Record<string, any>[] = [];
  if (payload && !candidates.includes(payload)) {
    candidates.push(payload);
  }
  if (payload.data && typeof payload.data === 'object' && !candidates.includes(payload.data)) {
    candidates.push(payload.data as Record<string, any>);
  }
  const pager = resolvePager(payload) || resolvePager(payload.data as Record<string, any>);
  if (!pager) return;
  candidates.forEach((target) => {
    target.pager = { page: pager.page, size: pager.size, total: pager.total };
  });
};

const isPlainObject = (value: unknown): value is Record<string, any> => {
  return Object.prototype.toString.call(value) === '[object Object]';
};

const shouldFormEncode = (config: AxiosRequestConfig): boolean => {
  if (!config.data || !isPlainObject(config.data)) {
    return false;
  }
  const headers = (config.headers || {}) as Record<string, any>;
  const contentType = headers['Content-Type'] || headers['content-type'];
  return typeof contentType === 'string' && contentType.includes(FORM_CONTENT_TYPE);
};

const serializeAsForm = (payload: Record<string, any>): URLSearchParams => {
  const params = new URLSearchParams();
  Object.keys(payload).forEach((key) => {
    const value = payload[key];
    if (value === undefined || value === null) {
      return;
    }
    if (typeof value === 'object') {
      params.append(key, JSON.stringify(value));
    } else {
      params.append(key, String(value));
    }
  });
  return params;
};

const normalizeGridParams = (params: Record<string, any>): Record<string, any> => {
  console.log('params', params);
  const p: Record<string, any> = { ...(params || {}) };
  const pager = p.pager;
  if (pager && typeof pager === 'object') {
    if (pager.page !== undefined) p.pageNum = pager.page;
    if (pager.size !== undefined) p.pageSize = pager.size;
    delete p.pager;
  }
  const query = p.query;
  if (query && typeof query === 'object') {
    const q = { ...query };
    if (q.sortProp) {
      p.orderByColumn = q.sortProp;
      delete q.sortProp;
    }
    if (q.sortOrder) {
      const map: Record<string, string> = { ascending: 'asc', descending: 'desc' };
      p.isAsc = map[q.sortOrder] || q.sortOrder;
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

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8';
// 创建axios实例
const service = axios.create({
  // axios中请求配置有baseURL选项，表示请求URL公共部分
  baseURL: import.meta.env.VITE_APP_BASE_API,
  // 超时
  timeout: 10000,
});

// request拦截器
service.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    if (shouldFormEncode(config)) {
      config.data = serializeAsForm(config.data);
    }
    // 是否需要设置 token
    const isToken = (config.headers || {}).isToken === false;
    // 是否需要防止数据重复提交
    const isRepeatSubmit = (config.headers || {}).repeatSubmit === false;
    if (getToken() && !isToken) {
      config.headers!['Authorization'] = 'Bearer ' + getToken(); // 让每个请求携带自定义token 请根据实际情况自行修改
    }
    if (config.method === 'get' && config.params) {
      if ((config.params as any).pager || (config.params as any).query) {
        config.params = normalizeGridParams(config.params as Record<string, any>);
      }
      let url = config.url + '?' + tansParams(config.params);
      url = url.slice(0, -1);
      config.params = {};
      config.url = url;
    }
    if (!isRepeatSubmit && (config.method === 'post' || config.method === 'put')) {
      const requestObj = {
        url: config.url,
        data: typeof config.data === 'object' ? JSON.stringify(config.data) : config.data,
        time: new Date().getTime(),
      };
      const requestSize = Object.keys(JSON.stringify(requestObj)).length; // 请求数据大小
      const limitSize = 5 * 1024 * 1024; // 限制存放数据5M
      if (requestSize >= limitSize) {
        console.warn(
          `[${config.url}]: ` + '请求数据大小超出允许的5M限制，无法进行防重复提交验证。'
        );
        return config;
      }
      const sessionObj = cache.session.getJSON('sessionObj');
      if (sessionObj === undefined || sessionObj === null || sessionObj === '') {
        cache.session.setJSON('sessionObj', requestObj);
      } else {
        const s_url = sessionObj.url; // 请求地址
        const s_data = sessionObj.data; // 请求数据
        const s_time = sessionObj.time; // 请求时间
        const interval = 1000; // 间隔时间(ms)，小于此时间视为重复提交
        if (
          s_data === requestObj.data &&
          requestObj.time - s_time < interval &&
          s_url === requestObj.url
        ) {
          const message = '数据正在处理，请勿重复提交';
          console.warn(`[${s_url}]: ` + message);
          return Promise.reject(new Error(message));
        } else {
          cache.session.setJSON('sessionObj', requestObj);
        }
      }
    }
    return config;
  },
  (error: any) => {
    console.log(error);
    Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (res: AxiosResponse) => {
    // 未设置状态码则默认成功状态
    const code = res.data.code || 200;
    // 获取错误信息
    const msg = errorCode[code] || res.data.msg || errorCode['default'];
    // 二进制数据则直接返回
    if (res.request.responseType === 'blob' || res.request.responseType === 'arraybuffer') {
      return res.data;
    }
    if (code === 401) {
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
    } else if (code === 500) {
      ElMessage({ message: msg, type: 'error' });
      return Promise.reject(new Error(msg));
    } else if (code === 601) {
      ElMessage({ message: msg, type: 'warning' });
      return Promise.reject(new Error(msg));
    } else if (code !== 200) {
      ElNotification.error({ title: msg });
      return Promise.reject('error');
    } else {
      attachPager(res.data);
      return Promise.resolve(res.data);
    }
  },
  (error: any) => {
    console.log('err' + error);
    let { message } = error;
    if (message == 'Network Error') {
      message = '后端接口连接异常';
    } else if (message.includes('timeout')) {
      message = '系统接口请求超时';
    } else if (message.includes('Request failed with status code')) {
      message = '系统接口' + message.substr(message.length - 3) + '异常';
    }
    ElMessage({ message: message, type: 'error', duration: 5 * 1000 });
    return Promise.reject(error);
  }
);

// 通用下载方法
export function download(
  url: string,
  params: any,
  filename: string,
  config?: AxiosRequestConfig
): Promise<void> {
  downloadLoadingInstance = ElLoading.service({
    text: '正在下载数据，请稍候',
    background: 'rgba(0, 0, 0, 0.7)',
  });
  return service
    .post(url, params, {
      transformRequest: [
        (params) => {
          return tansParams(params);
        },
      ],
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      responseType: 'blob',
      ...config,
    })
    .then(async (data: any) => {
      const isBlob = blobValidate(data);
      if (isBlob) {
        const blob = new Blob([data]);
        saveAs(blob, filename);
      } else {
        const resText = await data.text();
        const rspObj = JSON.parse(resText);
        const errMsg = errorCode[rspObj.code] || rspObj.msg || errorCode['default'];
        ElMessage.error(errMsg);
      }
      downloadLoadingInstance.close();
    })
    .catch((r: any) => {
      console.error(r);
      ElMessage.error('下载文件出现错误，请联系管理员！');
      downloadLoadingInstance.close();
    });
}

export default service;
