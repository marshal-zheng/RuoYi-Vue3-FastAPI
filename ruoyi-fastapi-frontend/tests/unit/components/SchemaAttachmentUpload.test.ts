import { effectScope, nextTick } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { FieldUploadError } from '@zxio/schema-form/fields';
import { useSchemaAttachmentUpload } from '@/composables/useSchemaAttachmentUpload';
import { setQuerySession } from '@/queries/context';

const { uploadFileAsset, presentRequestError } = vi.hoisted(() => ({
  uploadFileAsset: vi.fn(),
  presentRequestError: vi.fn(),
}));
vi.mock('@/api/fileAssets', () => ({ uploadFileAsset }));
vi.mock('@/utils/http', () => ({ presentRequestError }));

const asset = {
  assetId: 'asset-1',
  name: 'picture.png',
  contentUrl: '/file-assets/asset-1/content',
  mediaType: 'image/png',
  size: 12,
};

const failure = (status: number, errorCode?: number) =>
  Object.assign(new Error('请求失败'), {
    problem: {
      type: 'about:blank',
      title: '请求失败',
      status,
      detail: '文件类型不支持：仅允许 PDF 与图片',
      instance: '',
      errorCode,
    },
  });

beforeEach(() => {
  uploadFileAsset.mockReset();
  presentRequestError.mockReset();
  setQuerySession('actor:1', [], ['system:notice:edit']);
});

function setup() {
  const scope = effectScope();
  const upload = scope.run(() =>
    useSchemaAttachmentUpload({
      purpose: () => 'notice.image',
      ownerId: () => 10,
    })
  )!;
  return {
    scope,
    upload,
    file: new File(['image'], 'picture.png', { type: 'image/png' }),
  };
}

describe('schema attachment service adapter', () => {
  it('uses the authenticated registered-purpose transport and emits only durable JSON', async () => {
    uploadFileAsset.mockResolvedValue(asset);
    const { scope, upload, file } = setup();
    try {
      expect(await upload(file, { signal: new AbortController().signal })).toEqual({
        id: asset.assetId,
        name: asset.name,
        url: asset.contentUrl,
        metadata: { mediaType: asset.mediaType, size: asset.size },
      });
      const [form, config, options] = uploadFileAsset.mock.calls[0];
      expect(form.get('purpose')).toBe('notice.image');
      expect(form.get('ownerId')).toBe('10');
      expect(form.get('file').name).toBe('picture.png');
      expect(config.signal).toBeInstanceOf(AbortSignal);
      expect(options).toBeDefined();
    } finally {
      scope.stop();
    }
  });

  it.each(['field', 'session', 'unmount'] as const)(
    'retires a late response after %s cancellation',
    async (reason) => {
      let resolve!: (value: typeof asset) => void;
      uploadFileAsset.mockImplementation(
        () =>
          new Promise((done) => {
            resolve = done;
          })
      );
      const { scope, upload, file } = setup();
      const controller = new AbortController();
      const pending = upload(file, { signal: controller.signal });
      const rejection = expect(pending).rejects.toThrow('Upload cancelled');
      if (reason === 'field') controller.abort();
      if (reason === 'session') {
        setQuerySession('actor:2', [], ['system:notice:edit']);
        await nextTick();
      }
      if (reason === 'unmount') scope.stop();
      expect(uploadFileAsset.mock.calls[0][1].signal.aborted).toBe(true);
      resolve(asset);
      await rejection;
      scope.stop();
    }
  );

  it('shows a business rejection as the field reason without a global message', async () => {
    const error = failure(415, 48004);
    uploadFileAsset.mockRejectedValue(error);
    const { scope, upload, file } = setup();
    try {
      const rejection = upload(file, { signal: new AbortController().signal });
      await expect(rejection).rejects.toBeInstanceOf(FieldUploadError);
      await expect(rejection).rejects.toMatchObject({
        message: '文件类型不支持：仅允许 PDF 与图片',
        cause: error,
      });
      expect(uploadFileAsset.mock.calls[0][1].feedback).toEqual({ mode: 'silent' });
      expect(presentRequestError).not.toHaveBeenCalled();
    } finally {
      scope.stop();
    }
  });

  it.each([
    ['a server failure', failure(503, 50006)],
    ['a rejection without a business code', failure(422)],
    ['a transport failure', new TypeError('Failed to fetch')],
  ])('keeps %s generic in the field and presents it globally', async (_, error) => {
    uploadFileAsset.mockRejectedValue(error);
    const { scope, upload, file } = setup();
    try {
      await expect(upload(file, { signal: new AbortController().signal })).rejects.toBe(error);
      expect(presentRequestError).toHaveBeenCalledWith(error, {
        silentError: false,
        feedback: { mode: 'auto' },
      });
    } finally {
      scope.stop();
    }
  });

  it('does not dispatch an already cancelled selection', async () => {
    const { scope, upload, file } = setup();
    const controller = new AbortController();
    controller.abort();
    await expect(upload(file, { signal: controller.signal })).rejects.toThrow('Upload cancelled');
    expect(uploadFileAsset).not.toHaveBeenCalled();
    scope.stop();
  });
});
