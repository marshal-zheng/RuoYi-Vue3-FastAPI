import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import { http } from '@/utils/http';
import { FileValidationOptions, FileValidationResult } from './types';

export function validateFile(file: File, options: FileValidationOptions): FileValidationResult {
  if (options.accept && options.accept.length) {
    const lower = file.name.toLowerCase();
    const matched = options.accept.some((ext) => lower.endsWith(ext.toLowerCase()));
    if (!matched) {
      return { valid: false, error: `文件类型不支持，仅允许: ${options.accept.join(', ')}` };
    }
  }

  if (typeof options.maxSize === 'number' && file.size > options.maxSize) {
    return {
      valid: false,
      error: `文件过大，最大支持 ${(options.maxSize / 1024 / 1024).toFixed(1)}MB`,
    };
  }

  if (typeof options.minSize === 'number' && file.size < options.minSize) {
    return { valid: false, error: '文件大小不足最小限制' };
  }

  return { valid: true };
}

export async function parseJsonFile<T>(file: File): Promise<T> {
  const text = await file.text();
  return JSON.parse(text) as T;
}

export async function uploadFormData(
  url: string,
  formData: FormData,
  options?: AxiosRequestConfig
): Promise<AxiosResponse> {
  return http.post(
    {
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(options?.headers || {}),
      },
      ...options,
    },
    { isReturnNativeResponse: true }
  );
}
