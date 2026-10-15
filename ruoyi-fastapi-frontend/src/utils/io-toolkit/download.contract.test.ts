import { Blob as NodeBlob } from 'node:buffer';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AxiosHeaders, type AxiosResponse } from 'axios';
import { downloadFromResponse, extractFilenameFromHeaders } from './download';

const saveAs = vi.hoisted(() => vi.fn<(data: Blob, filename: string) => void>());
vi.mock('file-saver', () => ({ saveAs }));

describe('binary download boundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('Blob', NodeBlob);
  });
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    ["attachment; filename*=UTF-8''%E6%8A%A5%E5%91%8A.csv", '报告.csv'],
    ["attachment; filename=report.csv; filename*=UTF-8''%E6%8A%A5%E5%91%8A.csv", '报告.csv'],
    ["attachment; filename=report.csv; filename*=UTF-8''%broken", 'report.csv'],
  ])('uses the actual server filename header: %s', (header, filename) => {
    expect(extractFilenameFromHeaders({ 'content-disposition': header })).toBe(filename);
  });

  it('rejects an Axios response without a binary body', async () => {
    const response: AxiosResponse<undefined> = {
      data: undefined,
      status: 204,
      statusText: '',
      headers: { 'content-type': 'application/octet-stream' },
      config: { headers: new AxiosHeaders() },
    };
    await expect(downloadFromResponse(response, 'empty.bin')).rejects.toThrow(
      'Unsupported response type'
    );
    expect(saveAs).not.toHaveBeenCalled();
  });

  it('preserves valid binary response contents and filename', async () => {
    const body = new Blob(['payload'], { type: 'application/octet-stream' });
    const response: AxiosResponse<Blob> = {
      data: body,
      status: 200,
      statusText: '',
      headers: {
        'content-type': 'application/octet-stream',
        'content-disposition': 'attachment; filename="file.bin"',
      },
      config: { headers: new AxiosHeaders() },
    };
    await downloadFromResponse(response, 'fallback.bin');
    expect(saveAs).toHaveBeenCalledOnce();
    const [saved, filename] = saveAs.mock.calls[0];
    expect(filename).toBe('file.bin');
    expect(await saved.text()).toBe('payload');
  });
});
