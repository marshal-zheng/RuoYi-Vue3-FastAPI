import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import ElementPlus from 'element-plus';
import { endQuerySession, setQuerySession } from '@/queries/context';
import Editor from '@/components/ui/Editor/index.vue';
import { recoverAsset, retryAssetImage } from '@/utils/file-assets/image-recovery';

const requestMock = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: requestMock }));

const ID = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
const descriptor = (id: string) => ({
  assetId: id,
  name: 'image.png',
  mediaType: 'image/png',
  size: 10,
  contentUrl: `/file-assets/${id}/content`,
});

const wrappers: ReturnType<typeof mount>[] = [];
const mountEditor = (props: Record<string, unknown> = {}) => {
  const w = mount(Editor, {
    props: {
      modelValue: '<p>hi</p>',
      purpose: 'notice.image',
      ownerId: 10,
      ...props,
    },
    global: { plugins: [ElementPlus] },
    attachTo: document.body,
  });
  wrappers.push(w);
  return w;
};
const quillOf = (w: ReturnType<typeof mount>) =>
  (
    w.findComponent({ name: 'QuillEditor' }).vm as unknown as {
      getQuill: () => any;
    }
  ).getQuill();
const uploadCalls = () =>
  requestMock.mock.calls.filter(([config]) => config.url === '/file-assets/uploads');

beforeEach(() => {
  vi.clearAllMocks();
  setQuerySession('qa', ['admin'], ['*:*:*']);
  let seq = 0;
  requestMock.mockImplementation(async (config: { url: string; data: { assetIds?: string[] } }) => {
    if (config.url === '/file-assets/metadata:batch') {
      return {
        items: (config.data.assetIds || []).map(descriptor),
        unavailableIds: [],
      };
    }
    return descriptor(ID(++seq));
  });
});
afterEach(() => {
  wrappers.splice(0).forEach((w) => w.unmount());
  endQuerySession();
});

describe('notice editor with file assets', () => {
  it('offers images but not the unsupported video embed', async () => {
    const w = mountEditor();
    await flushPromises();
    expect(w.find('.ql-image').exists()).toBe(true);
    expect(w.find('.ql-video').exists()).toBe(false);
  });

  it('uploads a pasted image file first and inserts its stable content URL', async () => {
    const w = mountEditor();
    await flushPromises();
    const quill = quillOf(w);
    const file = new File([new Uint8Array([137, 80, 78, 71])], 'shot.png', {
      type: 'image/png',
    });
    const event = new Event('paste', {
      bubbles: true,
      cancelable: true,
    }) as ClipboardEvent;
    Object.defineProperty(event, 'clipboardData', { value: { files: [file] } });
    quill.root.dispatchEvent(event);
    await flushPromises();
    expect(event.defaultPrevented).toBe(true);
    const [config] = uploadCalls()[0];
    expect(config.data.get('purpose')).toBe('notice.image');
    expect(config.data.get('ownerId')).toBe('10');
    expect(quill.root.innerHTML).toContain(`src="/file-assets/${ID(1)}/content"`);
    expect(quill.root.innerHTML).not.toContain('data:image');
  });

  it('uploads inline data: images from pasted HTML instead of saving the bytes', async () => {
    const w = mountEditor();
    await flushPromises();
    const quill = quillOf(w);
    quill.clipboard.dangerouslyPasteHTML(
      0,
      '<p><img src="data:image/png;base64,iVBORw0KGgo="></p>'
    );
    await flushPromises();
    expect(uploadCalls()).toHaveLength(1);
    expect(quill.root.innerHTML).not.toContain('data:image');
    expect(quill.root.innerHTML).toContain('/file-assets/');
  });

  it('names pasted JPEG/WebP data images by their real type so the server accepts them', async () => {
    const w = mountEditor();
    await flushPromises();
    const quill = quillOf(w);
    quill.clipboard.dangerouslyPasteHTML(
      0,
      '<p><img src="data:image/jpeg;base64,/9j/4AAQ"><img src="data:image/webp;base64,UklGRg=="></p>'
    );
    await flushPromises();
    const sent = uploadCalls().map(([config]) => config.data.get('file') as File);
    expect(sent.map((file) => [file.name, file.type])).toEqual([
      ['pasted-image.jpg', 'image/jpeg'],
      ['pasted-image.webp', 'image/webp'],
    ]);
  });

  it('keeps rich HTML from Office pastes instead of replacing it with the rendered picture', async () => {
    const w = mountEditor();
    await flushPromises();
    const quill = quillOf(w);
    const event = new Event('paste', { bubbles: true, cancelable: true }) as ClipboardEvent;
    Object.defineProperty(event, 'clipboardData', {
      value: {
        types: ['text/html', 'text/plain', 'Files'],
        files: [new File(['x'], 'image.png', { type: 'image/png' })],
        getData: () => '',
      },
    });
    quill.root.dispatchEvent(event);
    await flushPromises();
    expect(uploadCalls()).toHaveLength(0);
  });

  it('keeps the stable path when an asset image copied inside the editor comes back absolute', async () => {
    const w = mountEditor({ modelValue: '<p>x</p>' });
    await flushPromises();
    const quill = quillOf(w);
    quill.clipboard.dangerouslyPasteHTML(
      0,
      `<p><img src="${window.location.origin}/file-assets/${ID(7)}/content"></p>`
    );
    await flushPromises();
    expect(quill.root.innerHTML).toContain(`src="/file-assets/${ID(7)}/content"`);
    expect((w.vm as unknown as { validate: () => string }).validate()).toBe('');
    expect(uploadCalls()).toHaveLength(0);
  });

  it('inserts several pasted image files in their clipboard order', async () => {
    const w = mountEditor({ modelValue: '<p></p>' });
    await flushPromises();
    const quill = quillOf(w);
    const event = new Event('paste', { bubbles: true, cancelable: true }) as ClipboardEvent;
    Object.defineProperty(event, 'clipboardData', {
      value: {
        files: [
          new File(['a'], 'a.png', { type: 'image/png' }),
          new File(['b'], 'b.png', { type: 'image/png' }),
        ],
      },
    });
    quill.root.dispatchEvent(event);
    await flushPromises();
    const sources = Array.from(quill.root.querySelectorAll('img')).map((img) =>
      (img as HTMLImageElement).getAttribute('src')
    );
    expect(sources).toEqual([`/file-assets/${ID(1)}/content`, `/file-assets/${ID(2)}/content`]);
  });

  it('blocks saving with pending uploads or images the server cannot accept', async () => {
    let release!: (value: unknown) => void;
    requestMock.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)));
    const w = mountEditor({
      modelValue: '<p><img src="https://example.com/x.png"></p>',
    });
    await flushPromises();
    const editor = w.vm as unknown as { validate: () => string };
    expect(editor.validate()).toContain('外部或未上传');
    const quill = quillOf(w);
    quill.setContents([{ insert: 'text\n' }]);
    expect(editor.validate()).toBe('');
    const event = new Event('drop', {
      bubbles: true,
      cancelable: true,
    }) as DragEvent;
    Object.defineProperty(event, 'dataTransfer', {
      value: { files: [new File(['x'], 'a.png', { type: 'image/png' })] },
    });
    quill.root.dispatchEvent(event);
    await flushPromises();
    expect(editor.validate()).toContain('仍在上传');
    release(descriptor(ID(5)));
    await flushPromises();
    expect(editor.validate()).toBe('');
  });
});

describe('text-only editor (no registered image purpose, e.g. generated rich text)', () => {
  it('offers no image entry and refuses pasted image files without uploading', async () => {
    const w = mountEditor({ purpose: undefined });
    await flushPromises();
    expect(w.find('.ql-image').exists()).toBe(false);
    expect(w.find('.editor-img-uploader').exists()).toBe(false);
    const quill = quillOf(w);
    const event = new Event('paste', { bubbles: true, cancelable: true }) as ClipboardEvent;
    Object.defineProperty(event, 'clipboardData', {
      value: { files: [new File(['x'], 'shot.png', { type: 'image/png' })] },
    });
    quill.root.dispatchEvent(event);
    await flushPromises();
    expect(event.defaultPrevented).toBe(true);
    expect(uploadCalls()).toHaveLength(0);
    quill.clipboard.dangerouslyPasteHTML(
      0,
      '<p><img src="data:image/png;base64,iVBORw0KGgo="></p>'
    );
    await flushPromises();
    expect(uploadCalls()).toHaveLength(0);
    expect(quill.root.innerHTML).not.toContain('<img');
  });

  it('blocks saving any image the content still carries', async () => {
    const w = mountEditor({
      purpose: undefined,
      modelValue: '<p><img src="/file-assets/x/content"></p>',
    });
    await flushPromises();
    expect((w.vm as unknown as { validate: () => string }).validate()).toContain('不支持图片');
  });
});

describe('asset image recovery', () => {
  it('reloads a broken asset image once after a successful metadata check', async () => {
    const image = document.createElement('img');
    image.setAttribute('src', `/file-assets/${ID(7)}/content`);
    const spy = vi.spyOn(image, 'setAttribute');
    expect(await retryAssetImage(image)).toBe(true);
    expect(spy).toHaveBeenCalledWith('src', `/file-assets/${ID(7)}/content`);
    expect(await retryAssetImage(image)).toBe(false); // at most once
  });

  it('does not retry hidden, missing or foreign images and shares one flight', async () => {
    requestMock.mockImplementation(async () => ({
      items: [],
      unavailableIds: [ID(8)],
    }));
    expect(await recoverAsset(ID(8))).toBe(false);
    requestMock.mockRejectedValue(Object.assign(new Error('forbidden'), { status: 403 }));
    expect(await recoverAsset(ID(9))).toBe(false);
    const foreign = document.createElement('img');
    foreign.setAttribute('src', 'https://example.com/a.png');
    expect(await retryAssetImage(foreign)).toBe(false);
    requestMock.mockReset();
    requestMock.mockImplementation(async () => ({
      items: [descriptor(ID(10))],
      unavailableIds: [],
    }));
    const [a, b] = await Promise.all([recoverAsset(ID(10)), recoverAsset(ID(10))]);
    expect(a && b).toBe(true);
    expect(requestMock).toHaveBeenCalledTimes(1);
  });

  it('never recovers outside of a live session scope', async () => {
    endQuerySession();
    expect(await recoverAsset(ID(11))).toBe(false);
    expect(requestMock).not.toHaveBeenCalled();
  });
});
