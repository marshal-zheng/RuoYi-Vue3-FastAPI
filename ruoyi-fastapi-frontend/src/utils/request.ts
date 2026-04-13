/**
 * HTTP 请求工具 - 兼容层
 *
 * 此文件保持原有 API 接口不变，底层已迁移至 @zxio/http
 * 业务代码无需修改，可继续使用：
 *   import request from '@/utils/request'
 *   request({ url: '/api/xxx', method: 'get' })
 */
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ElLoading, ElMessage } from 'element-plus';
import { http, isRelogin } from './http';
import { blobValidate } from '@/utils/ruoyi';
import { saveAs } from 'file-saver';
import errorCode from '@/utils/errorCode';

interface LoadingInstance {
  close(): void;
}

interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  isToken?: boolean;
  silentSuccess?: boolean;
  silentError?: boolean;
  skipRelogin?: boolean;
}

interface RequestClient {
  <T = any>(config: ExtendedAxiosRequestConfig): Promise<T>;
  get<T = any>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T>;
  post<T = any>(url: string, data?: unknown, config?: ExtendedAxiosRequestConfig): Promise<T>;
  put<T = any>(url: string, data?: unknown, config?: ExtendedAxiosRequestConfig): Promise<T>;
  delete<T = any>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T>;
}

let downloadLoadingInstance: LoadingInstance;

// 重新导出 isRelogin
export { isRelogin };

/**
 * 兼容层请求函数
 * 保持与原有 request(config) 调用方式一致
 */
function request<T = any>(config: ExtendedAxiosRequestConfig): Promise<T> {
  const { method = 'get', ...restConfig } = config;
  const lowerMethod = method.toLowerCase();

  // 提取自定义 headers 配置
  const headers = (config.headers || {}) as Record<string, unknown>;
  const withToken = config.isToken !== false && headers.isToken !== false;
  const silentError = config.silentError === true || headers.silentError === true;

  // 构建请求配置
  const httpConfig = {
    ...restConfig,
    headers: config.headers,
  };

  // 请求选项
  const requestOptions = {
    withToken,
    showErrorMessage: !silentError,
  };

  // 根据方法类型调用对应的 http 方法
  switch (lowerMethod) {
    case 'get':
      return http.get<T>(httpConfig, requestOptions);
    case 'post':
      return http.post<T>(httpConfig, requestOptions);
    case 'put':
      return http.put<T>(httpConfig, requestOptions);
    case 'delete':
      return http.delete<T>(httpConfig, requestOptions);
    default:
      return http.request<T>({ ...httpConfig, method }, requestOptions);
  }
}

const requestClient = request as RequestClient;

requestClient.get = <T = any>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T> => {
  return request<T>({ ...config, url, method: 'get' });
};

requestClient.post = <T = any>(
  url: string,
  data?: unknown,
  config?: ExtendedAxiosRequestConfig
): Promise<T> => {
  return request<T>({ ...config, url, method: 'post', data });
};

requestClient.put = <T = any>(
  url: string,
  data?: unknown,
  config?: ExtendedAxiosRequestConfig
): Promise<T> => {
  return request<T>({ ...config, url, method: 'put', data });
};

requestClient.delete = <T = any>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T> => {
  return request<T>({ ...config, url, method: 'delete' });
};

// ==================== 下载方法 ====================

const resolveDownloadErrorMessage = async (data: unknown): Promise<string> => {
  const fallback = '下载文件出现错误，请联系管理员！';
  if (!data || typeof (data as Blob).text !== 'function') {
    return fallback;
  }
  const resText = await (data as Blob).text();
  const trimmed = (resText || '').trim();
  if (!trimmed) {
    return fallback;
  }
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    return Promise.resolve()
      .then(() => JSON.parse(trimmed))
      .then((rspObj: Record<string, unknown>) => {
        const code = rspObj?.code as number | undefined;
        const msg = rspObj?.msg as string | undefined;
        return (code ? errorCode[code] : undefined) || msg || errorCode['default'];
      })
      .catch(() => trimmed.slice(0, 200) || fallback);
  }
  return trimmed.slice(0, 200) || fallback;
};

/**
 * 通用下载方法
 */
export function download(
  url: string,
  params: unknown,
  filename: string,
  config?: AxiosRequestConfig
): Promise<void> {
  downloadLoadingInstance = ElLoading.service({
    text: '正在下载数据，请稍候',
    background: 'rgba(0, 0, 0, 0.7)',
  });

  return http
    .post<Blob>(
      {
        url,
        data: params,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        responseType: 'blob',
        ...config,
      },
      { isReturnNativeResponse: false, isTransformResponse: false }
    )
    .then(async (data: Blob) => {
      const isBlob = blobValidate(data);
      if (isBlob) {
        const blob = new Blob([data]);
        saveAs(blob, filename);
      } else {
        const errMsg = await resolveDownloadErrorMessage(data);
        ElMessage.error(errMsg);
      }
      downloadLoadingInstance.close();
    })
    .catch(async (r: { response?: { data?: unknown } } | unknown) => {
      const responseData = (r as { response?: { data?: unknown } })?.response?.data;
      const errMsg =
        (await resolveDownloadErrorMessage(responseData)) || '下载文件出现错误，请联系管理员！';
      ElMessage.error(errMsg);
      downloadLoadingInstance.close();
    });
}

export default requestClient;
