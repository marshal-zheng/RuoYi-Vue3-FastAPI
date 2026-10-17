import { Blob as NodeBlob } from 'node:buffer';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { AbortError } from '@zxio/http';
import { parse } from '@vue/compiler-sfc';
import ts from 'typescript';
import { callWithAsyncErrorHandling } from 'vue';
import type { ComponentInternalInstance } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { post, get, close, service, errorMessage, saveAs } = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
  close: vi.fn(),
  service: vi.fn(),
  errorMessage: vi.fn(),
  saveAs: vi.fn(),
}));

vi.mock('./http', () => ({
  http: {
    post,
    get,
    request(config: { method: string }, options: unknown) {
      return config.method.toLowerCase() === 'post' ? post(config, options) : get(config, options);
    },
  },
  isRelogin: { show: false },
}));
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

  it('contains failed download feedback without changing the original rejection', async () => {
    const { download } = await import('./request');
    const original = new Error('original export failure');
    post.mockRejectedValueOnce(original);
    errorMessage.mockImplementationOnce(() => {
      throw new Error('feedback failed');
    });
    await expect(download('/export', {}, 'file.csv')).rejects.toBe(original);
    await new Promise((resolve) => setTimeout(resolve, 0));
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

  it('passes ZIP request cancellation through without failure feedback', async () => {
    const { default: files } = await import('@/plugins/download');
    const controller = new AbortController();
    const cancelled = new AbortError({ message: 'leave-generator' });
    get.mockRejectedValueOnce(cancelled);

    await expect(
      files.zip('/tool/gen/batchGenCode', 'code.zip', {
        signal: controller.signal,
      })
    ).rejects.toBe(cancelled);
    expect(get.mock.calls[0][0].signal).toBe(controller.signal);
    expect(errorMessage).not.toHaveBeenCalled();
    expect(saveAs).not.toHaveBeenCalled();
    expect(close).toHaveBeenCalledOnce();
  });

  it('passes the original ZIP error through and reports its actual message once', async () => {
    const { default: files } = await import('@/plugins/download');
    const original = new Error('没有代码生成权限');
    get.mockRejectedValueOnce(original);

    await expect(files.zip('/tool/gen/batchGenCode', 'code.zip')).rejects.toBe(original);
    expect(errorMessage).toHaveBeenCalledExactlyOnceWith('没有代码生成权限');
    expect(close).toHaveBeenCalledOnce();
  });

  it('rejects a ZIP problem response through existing binary decoding instead of saving it', async () => {
    const { default: files } = await import('@/plugins/download');
    const problem = {
      type: 'about:blank',
      title: '生成失败',
      status: 422,
      detail: '生成条件无效',
    };
    get.mockResolvedValueOnce({
      ...response(),
      headers: { 'content-type': 'application/problem+json' },
      data: new Blob([JSON.stringify(problem)], {
        type: 'application/problem+json',
      }),
    });

    await expect(files.zip('/tool/gen/batchGenCode', 'code.zip')).rejects.toMatchObject({
      message: '生成条件无效',
      data: problem,
    });
    expect(saveAs).not.toHaveBeenCalled();
    expect(errorMessage).toHaveBeenCalledExactlyOnceWith('生成条件无效');
    expect(close).toHaveBeenCalledOnce();
  });

  it('holds one fullscreen mask for concurrent ZIP and Excel downloads until both settle', async () => {
    const { download } = await import('./request');
    const { default: files } = await import('@/plugins/download');
    let release!: (value: unknown) => void;
    let fail!: (reason: unknown) => void;
    get.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)));
    post.mockImplementationOnce(() => new Promise((_, reject) => (fail = reject)));
    const zip = files.zip('/tool/gen/batchGenCode', 'code.zip');
    const excel = download('/system/user/export', {}, 'users.xlsx').catch((error) => error);
    const original = new Error('Excel failed');
    try {
      expect(service).toHaveBeenCalledOnce();
      release(response());
      await zip;
      expect(close).not.toHaveBeenCalled();
    } finally {
      release(response());
      fail(original);
      await Promise.allSettled([zip, excel]);
    }
    expect(await excel).toBe(original);
    expect(close).toHaveBeenCalledOnce();
    expect(errorMessage).toHaveBeenCalledExactlyOnceWith('Excel failed');
  });

  it('ends ZIP click failures at the page event boundary without changing operation rejection', async () => {
    const { default: files } = await import('@/plugins/download');
    const { useOperation } = await import('./operation');
    const source = readFileSync(resolve('src/views/tool/gen/index.vue'), 'utf8');
    const script = parse(source).descriptor.scriptSetup!.content;
    const ast = ts.createSourceFile('Gen.js', script, ts.ScriptTarget.Latest, true);
    const operation = ast.statements.find(
      (node) =>
        ts.isVariableStatement(node) &&
        node.declarationList.declarations.some(
          (declaration) =>
            ts.isObjectBindingPattern(declaration.name) &&
            declaration.name.elements.some((item) => item.name.getText(ast) === 'handleGenTable')
        )
    )!;
    const events = [...source.matchAll(/<(?:ZxButton|el-button)\b[^>]*>/g)]
      .map((match) => match[0])
      .filter((tag) => tag.includes('v-hasPermi="[\'tool:gen:code\']"'))
      .map((tag) => tag.match(/@click="(\w+)/)![1]);
    const declarations = ast.statements
      .filter(ts.isFunctionDeclaration)
      .map((node) => node.getText(ast));
    const page = new Function(
      'useOperation',
      'tableNames',
      'proxy',
      operation.getText(ast) +
        declarations.join('\n') +
        `\nreturn {run:handleGenTable,pending:handleGenTablePending,events:[${events.join(',')}]};`
    )(useOperation, { value: ['sys_post'] }, { $download: files });
    const vueError = vi.fn();
    const instance = {
      parent: null,
      appContext: { config: { errorHandler: vueError } },
    } as unknown as ComponentInternalInstance;
    expect(page.events).toHaveLength(2);
    for (const event of page.events) {
      get.mockRejectedValueOnce(new AbortError({ message: 'leave-generator' }));
      callWithAsyncErrorHandling(() => event({ tableName: 'sys_post', genType: '0' }), instance, 5);
      await vi.waitFor(() => expect(page.pending.value).toBe(false));
    }
    expect(vueError).not.toHaveBeenCalled();
    expect(errorMessage).not.toHaveBeenCalled();
    const original = new Error('generation failed');
    get.mockRejectedValueOnce(original);
    await expect(page.run({ tableName: 'sys_post', genType: '0' })).rejects.toBe(original);
  });
});
