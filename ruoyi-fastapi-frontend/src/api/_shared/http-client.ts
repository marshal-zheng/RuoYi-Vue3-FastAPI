/**
 * 类型安全的 HTTP 客户端
 * 封装 axios，提供统一的请求和响应处理
 */
import request from '@/utils/request';
import type { ApiResponse, PageResponse } from './types/common';
import type { AxiosRequestConfig } from 'axios';

/**
 * 类型安全的 HTTP 客户端
 */
export const http = {
  /**
   * GET 请求
   */
  get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return request.get(url, config);
  },

  /**
   * POST 请求
   */
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return request.post(url, data, config);
  },

  /**
   * PUT 请求
   */
  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return request.put(url, data, config);
  },

  /**
   * DELETE 请求
   */
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return request.delete(url, config);
  },

  /**
   * 分页查询
   */
  page<T>(url: string, params?: Record<string, unknown>): Promise<PageResponse<T> & { code: number; msg: string }> {
    return request.get(url, { params });
  },
} as const;

export default http;
