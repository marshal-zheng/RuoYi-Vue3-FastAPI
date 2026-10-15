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

  it('rejects a 200 Problem response instead of saving it as a file', async () => {
    const problem = {
      type: 'about:blank',
      title: '导出失败',
      status: 422,
      detail: '导出条件无效',
      instance: '/export',
    };
    const body = new Blob([JSON.stringify(problem)], { type: 'application/problem+json' });
    await expect(downloadFromResponse(body, 'report.zip')).rejects.toMatchObject({
      message: '导出条件无效',
      data: problem,
      raw: body,
    });
    expect(saveAs).not.toHaveBeenCalled();
  });

  it('saves a valid JSON attachment without classifying it as a failure', async () => {
    const body = new Blob(['{"status":422,"title":"domain data"}'], { type: 'application/json' });
    await downloadFromResponse(
      {
        data: body,
        status: 200,
        statusText: 'OK',
        headers: { 'content-disposition': 'attachment; filename="data.json"' },
        config: { headers: new AxiosHeaders() },
      },
      'fallback.json'
    );
    expect(saveAs).toHaveBeenCalledOnce();
    expect(saveAs.mock.calls[0][1]).toBe('data.json');
  });

  it('rejects a non-success response even when transport validation allowed it', async () => {
    await expect(
      downloadFromResponse(
        {
          data: new Blob(['redirect body']),
          status: 302,
          statusText: 'Found',
          headers: {},
          config: { headers: new AxiosHeaders() },
        },
        'redirect.bin'
      )
    ).rejects.toMatchObject({ status: 302 });
    expect(saveAs).not.toHaveBeenCalled();
  });
});
