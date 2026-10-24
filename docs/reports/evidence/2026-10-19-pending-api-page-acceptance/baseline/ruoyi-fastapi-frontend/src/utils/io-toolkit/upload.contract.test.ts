import { describe, expect, it } from 'vitest';
import type { AxiosRequestConfig } from 'axios';

import { uploadFormData } from './upload';
import { importUserExcel } from '@/api/system/user';
import { http } from '@/utils/http';

describe('multipart upload contract', () => {
  it('routes user Excel import through HTTP while preserving the upload wait and cancellation contract', async () => {
    let transmitted: AxiosRequestConfig | undefined;
    const file = new File(['workbook'], 'users.xlsx');
    const controller = new AbortController();
    const progress = () => {};
    const interceptor = http.axiosInstance.interceptors.request.use((config) => {
      config.adapter = async (prepared) => {
        transmitted = prepared;
        return {
          data: { results: [], summary: { total: 0, succeeded: 0, failed: 0 } },
          status: 200,
          statusText: 'OK',
          headers: {},
          config: prepared,
        };
      };
      return config;
    });
    try {
      const result = await importUserExcel(file, true, {
        signal: controller.signal,
        onUploadProgress: progress,
      });
      expect(result.summary.total).toBe(0);
      expect(transmitted?.url).toBe('/system/user/importData');
      expect(transmitted?.params).toEqual({ updateSupport: true });
      expect(transmitted?.data).toBeInstanceOf(FormData);
      expect((transmitted?.data as FormData).get('file')).toBe(file);
      expect(transmitted?.signal).toBe(controller.signal);
      expect(transmitted?.onUploadProgress).toBe(progress);
      expect(transmitted?.timeout).toBe(0);
    } finally {
      http.axiosInstance.interceptors.request.eject(interceptor);
    }
  });

  it('preserves FormData through the real Axios request serialization', async () => {
    let transmittedData: unknown;
    const form = new FormData();
    form.append('file', new File(['上传内容'], 'axios-upgrade.txt', { type: 'text/plain' }));

    const options: AxiosRequestConfig = {
      adapter: async (config) => {
        transmittedData = config.data;
        return {
          data: { fileName: '/profile/axios-upgrade.txt' },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        };
      },
    };
    await uploadFormData('/common/upload', form, options);

    expect(transmittedData).toBe(form);
  });
});
