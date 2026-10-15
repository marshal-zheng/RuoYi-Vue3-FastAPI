import { describe, expect, it } from 'vitest';
import type { AxiosRequestConfig } from 'axios';

import { uploadFormData } from './upload';

describe('multipart upload contract', () => {
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
