/**
 * HTTP 请求工具 - 兼容层
 *
 * 此文件保持原有 API 接口不变，底层已迁移至 @zxio/http
 * 业务代码无需修改，可继续使用：
 *   import request from '@/utils/request'
 *   request({ url: '/api/xxx', method: 'get' })
 */
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { isAbortError, type RequestOptions } from '@zxio/http';
import { ElLoading, ElMessage } from 'element-plus';
import { http, isRelogin } from './http';
import { downloadFromResponse } from '@/utils/io-toolkit/download';
import { observeFeedback } from '@/utils/feedback/channel';
import type { FeedbackOptions } from '@/utils/feedback/types';

interface LoadingInstance {
  close(): void;
}

export interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  requestOptions?: RequestOptions;
  isToken?: boolean;
  silentSuccess?: boolean;
  silentError?: boolean;
  skipRelogin?: boolean;
  feedback?: FeedbackOptions;
}

interface RequestClient {
  <T = unknown>(config: ExtendedAxiosRequestConfig, options?: RequestOptions): Promise<T>;
  get<T = unknown>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T>;
  post<T = unknown>(url: string, data?: unknown, config?: ExtendedAxiosRequestConfig): Promise<T>;
  put<T = unknown>(url: string, data?: unknown, config?: ExtendedAxiosRequestConfig): Promise<T>;
  delete<T = unknown>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T>;
}

let downloadLoadingInstance: LoadingInstance | undefined;
let activeDownloads = 0;

export { isRelogin };

/**
 * 兼容层请求函数
 * 保持与原有 request(config) 调用方式一致
 */
function request<T = unknown>(
  config: ExtendedAxiosRequestConfig,
  options?: RequestOptions
): Promise<T> {
  const { method = 'get', ...restConfig } = config;
  const lowerMethod = method.toLowerCase();

  // 提取自定义 headers 配置
  const headers = (config.headers || {}) as Record<string, unknown>;
  const withToken = config.isToken !== false && headers.isToken !== false;

  // 构建请求配置
  const httpConfig = {
    ...restConfig,
    headers: config.headers,
  };

  // 请求选项
  const requestOptions = {
    withToken,
    showErrorMessage: false,
    showSuccessMessage: false,
    ...options,
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

requestClient.get = <T = unknown>(url: string, config?: ExtendedAxiosRequestConfig): Promise<T> => {
  return request<T>({ ...config, url, method: 'get' });
};

requestClient.post = <T = unknown>(
  url: string,
  data?: unknown,
  config?: ExtendedAxiosRequestConfig
): Promise<T> => {
  return request<T>({ ...config, url, method: 'post', data });
};

requestClient.put = <T = unknown>(
  url: string,
  data?: unknown,
  config?: ExtendedAxiosRequestConfig
): Promise<T> => {
  return request<T>({ ...config, url, method: 'put', data });
};

requestClient.delete = <T = unknown>(
  url: string,
  config?: ExtendedAxiosRequestConfig
): Promise<T> => {
  return request<T>({ ...config, url, method: 'delete' });
};

// ==================== 下载方法 ====================

/**
 * 通用下载方法
 */
export function download(
  url: string,
  params: unknown,
  filename: string,
  config?: AxiosRequestConfig
): Promise<void> {
  return downloadFile(
    {
      url,
      data: params,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      ...config,
      method: 'post',
    },
    filename
  );
}

/** HTTP 文件下载共用执行入口，负责反馈和并行任务的 loading 生命周期。 */
export function downloadFile(config: ExtendedAxiosRequestConfig, filename: string): Promise<void> {
  if (activeDownloads === 0) {
    downloadLoadingInstance = ElLoading.service({ text: '正在下载数据，请稍候' });
  }
  activeDownloads++;

  const task = (async () => {
    try {
      const response = await http.request<AxiosResponse<Blob>>(
        {
          method: 'get',
          responseType: 'blob',
          ...config,
          // 下载入口负责失败反馈，避免与全局错误反馈重复。
          feedback: { mode: 'silent' },
          silentError: true,
        } as ExtendedAxiosRequestConfig,
        { isReturnNativeResponse: true, isTransformResponse: false }
      );
      await downloadFromResponse(response, filename);
    } finally {
      activeDownloads--;
      if (activeDownloads === 0) {
        downloadLoadingInstance?.close();
        downloadLoadingInstance = undefined;
      }
    }
  })();

  // 反馈观察者不改变 task 的拒绝结果，也兼容页面不等待的事件调用。
  observeFeedback(() =>
    task.catch((error: unknown) => {
      if (!isAbortError(error)) {
        return ElMessage.error(
          error instanceof Error ? error.message : '下载文件出现错误，请联系管理员！'
        );
      }
      return undefined;
    })
  );
  return task;
}

export default requestClient;
