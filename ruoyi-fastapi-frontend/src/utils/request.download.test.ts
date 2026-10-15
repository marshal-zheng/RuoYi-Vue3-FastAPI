import { Blob as NodeBlob } from 'node:buffer';
import { AbortError } from '@zxio/http';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { post, close, service, errorMessage, saveAs } = vi.hoisted(() => ({
  post: vi.fn(),
  close: vi.fn(),
  service: vi.fn(),
  errorMessage: vi.fn(),
  saveAs: vi.fn(),
}));

vi.mock('./http', () => ({ http: { post }, isRelogin: { show: false } }));
vi.mock('element-plus', () => ({
  ElLoading: { service },
  ElMessage: { error: errorMessage },
}));
vi.mock('file-saver', () => ({ saveAs }));

const response = () => ({
  status: 200,
  statusText: 'OK',
  headers: { 'content-disposition': 'attachment; filename="server.csv"' },
  config: { headers: {} },
  data: new Blob(['actual file'], { type: 'text/csv' }),
});

describe('download lifecycle', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.resetAllMocks();
    vi.stubGlobal('Blob', NodeBlob);
    service.mockReturnValue({ close });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('keeps cancellation rejected without notifying failure and releases loading', async () => {
    const { download } = await import('./request');
    const cancelled = new AbortError({ message: 'leave-page' });
    post.mockRejectedValueOnce(cancelled);

    await expect(download('/export', {}, 'file.csv')).rejects.toBe(cancelled);
    expect(errorMessage).not.toHaveBeenCalled();
    expect(saveAs).not.toHaveBeenCalled();
    expect(close).toHaveBeenCalledOnce();
  });

  it('preserves the original rejection and reports failure once', async () => {
    const { download } = await import('./request');
    const original = new Error('导出条件无效');
    post.mockRejectedValueOnce(original);

    await expect(download('/export', {}, 'file.csv')).rejects.toBe(original);
    expect(errorMessage).toHaveBeenCalledExactlyOnceWith('导出条件无效');
    expect(close).toHaveBeenCalledOnce();
  });

  it('keeps the shared fullscreen mask until all concurrent downloads settle', async () => {
    const { download } = await import('./request');
    let release!: (value: unknown) => void;
    let fail!: (reason: unknown) => void;
    post.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)));
    post.mockImplementationOnce(() => new Promise((_, reject) => (fail = reject)));
    const first = download('/first', {}, 'first.csv');
    const second = download('/second', {}, 'second.csv');
    const secondResult = second.catch((error) => error);

    expect(service).toHaveBeenCalledOnce();
    release(response());
    await first;
    expect(close).not.toHaveBeenCalled();
    const original = new Error('second failed');
    fail(original);
    expect(await secondResult).toBe(original);
    expect(close).toHaveBeenCalledOnce();
  });

  it('saves the server filename and releases loading when saving fails', async () => {
    const { download } = await import('./request');
    const original = new Error('保存失败');
    post.mockResolvedValueOnce(response());
    saveAs.mockImplementationOnce(() => {
      throw original;
    });

    await expect(download('/export', {}, 'fallback.csv')).rejects.toBe(original);
    expect(saveAs).toHaveBeenCalledWith(expect.any(Blob), 'server.csv');
    expect(errorMessage).toHaveBeenCalledExactlyOnceWith('保存失败');
    expect(close).toHaveBeenCalledOnce();
  });
});
