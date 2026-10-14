import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { flushPromises } from '@vue/test-utils';
import { CanceledError, type AxiosResponse, type AxiosRequestConfig } from 'axios';
import { getDicts } from './data';
import { useDict } from '@/utils/dict';

const { adapter } = vi.hoisted(() => ({ adapter: vi.fn() }));

vi.mock('@/utils/request', async () => {
  const { createHttpClient } = await import('@zxio/http');
  // Preserve the real client's duplicate-request cancellation behavior.
  const client = createHttpClient({
    axiosConfig: { adapter },
    successResolver: ({ response }) => ({ ok: true, data: response.data }),
    requestOptions: { withToken: false, showErrorMessage: false },
  });
  return { default: (config: AxiosRequestConfig) => client.request(config) };
});

const payload = {
  items: [
    { dictLabel: '是', dictValue: 'Y' },
    { dictLabel: '否', dictValue: 'N' },
  ],
};

function pendingResponse() {
  let finish!: () => void;
  adapter.mockImplementation(
    (config: AxiosRequestConfig) =>
      new Promise<AxiosResponse>((resolve, reject) => {
        config.signal?.addEventListener?.('abort', () => reject(new CanceledError()));
        finish = () =>
          resolve({ data: payload, status: 200, statusText: 'OK', headers: {}, config });
      })
  );
  return () => finish();
}

beforeEach(() => {
  setActivePinia(createPinia());
  adapter.mockReset();
});

describe('dictionary requests shared by hooks and selectors', () => {
  it('keeps hook options when a selector requests the same dictionary concurrently', async () => {
    const complete = pendingResponse();
    const { sys_yes_no } = useDict('sys_yes_no');
    await flushPromises();
    const selector = getDicts('sys_yes_no');
    await flushPromises();
    complete();
    await expect(selector).resolves.toEqual(payload);
    await flushPromises();
    expect(sys_yes_no.value.map(({ label, value }) => ({ label, value }))).toEqual([
      { label: '是', value: 'Y' },
      { label: '否', value: 'N' },
    ]);
    expect(adapter).toHaveBeenCalledTimes(1);
  });

  it('releases failed and completed requests so later loads can fetch fresh data', async () => {
    adapter.mockRejectedValueOnce(new Error('offline'));
    const first = getDicts('sys_reload');
    const second = getDicts('sys_reload');
    expect(await Promise.allSettled([first, second])).toEqual([
      expect.objectContaining({ status: 'rejected' }),
      expect.objectContaining({ status: 'rejected' }),
    ]);
    expect(adapter).toHaveBeenCalledTimes(1);

    const complete = pendingResponse();
    const retry = getDicts('sys_reload');
    await flushPromises();
    complete();
    await expect(retry).resolves.toEqual(payload);
    const reload = getDicts('sys_reload');
    await flushPromises();
    complete();
    await expect(reload).resolves.toEqual(payload);
    expect(adapter).toHaveBeenCalledTimes(3);
  });
});
