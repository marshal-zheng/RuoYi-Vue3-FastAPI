import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, ref, type Component, type App } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import ElementPlus, { ElUpload } from 'element-plus';
import { endQuerySession, setQuerySession } from '@/queries/context';
import FileUpload from '@/components/ui/FileUpload/index.vue';
import ImageUpload from '@/components/ui/ImageUpload/index.vue';

const requestMock = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: requestMock }));
const wrappers: ReturnType<typeof mount>[] = [];
const loading = vi.fn();
const closeLoading = vi.fn();
const mountComponent = (component: Component, props: Record<string, unknown> = {}) => {
  const w = mount(component, {
    props,
    global: {
      plugins: [
        ElementPlus,
        {
          install(app: App) {
            app.config.globalProperties.$modal = { loading, closeLoading };
          },
        },
      ],
    },
  });
  wrappers.push(w);
  return w;
};
const deferred = () => {
  let resolve!: (value: unknown) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
};
const select = async (w: ReturnType<typeof mount>, files: File[]) => {
  const input = w.find('input[type=file]');
  Object.defineProperty(input.element, 'files', { configurable: true, value: files });
  await input.trigger('change');
  await flushPromises();
};

beforeEach(() => {
  vi.clearAllMocks();
  setQuerySession('qa', ['admin'], ['*:*:*']);
  requestMock.mockResolvedValue({ fileName: '/profile/upload/qa.txt' });
  vi.stubGlobal(
    'URL',
    Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:qa'), revokeObjectURL: vi.fn() })
  );
});
afterEach(() => {
  wrappers.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  vi.unstubAllGlobals();
});

describe('authenticated native upload wrappers', () => {
  it.each([FileUpload, ImageUpload])(
    'uses the HTTP client once and emits one committed path',
    async (component) => {
      const file = new File(['qa'], 'qa.png', { type: 'image/png' });
      const w = mountComponent(component, { modelValue: '', fileType: ['png'] });
      await select(w, [file]);
      expect(requestMock).toHaveBeenCalledTimes(1);
      const [config, options] = requestMock.mock.calls[0];
      expect(config.url).toBe('/common/upload');
      expect(config.data.get('file')).toMatchObject({ name: file.name, size: file.size });
      expect(config.timeout).toBe(0);
      expect(config.headers).toBeUndefined();
      expect(options.context).toBeDefined();
      expect(w.emitted('update:modelValue')).toEqual([['/profile/upload/qa.txt']]);
      expect(closeLoading).toHaveBeenCalled();
    }
  );

  it('keeps a successful file when another request fails and settles the loading state', async () => {
    const good = deferred();
    const bad = deferred();
    requestMock.mockReturnValueOnce(good.promise).mockReturnValueOnce(bad.promise);
    const w = mountComponent(FileUpload);
    await select(w, [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]);
    bad.reject(new Error('server failure'));
    good.resolve({ fileName: '/profile/upload/good.txt' });
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([['/profile/upload/good.txt']]);
    expect(closeLoading).toHaveBeenCalled();
    expect(w.text()).toContain('a.txt');
    expect(w.text()).not.toContain('b.txt');
  });

  it('preserves queued files when the parent echoes one completed path', async () => {
    const first = deferred();
    const second = deferred();
    requestMock.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const Host = defineComponent({
      setup() {
        const value = ref('');
        return () =>
          h(FileUpload, {
            modelValue: value.value,
            'onUpdate:modelValue': (v: string) => {
              value.value = v;
            },
          });
      },
    });
    const w = mountComponent(Host);
    await select(w, [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]);
    first.resolve({ fileName: '/profile/first.txt' });
    await flushPromises();
    expect(w.findComponent(ElUpload).props('fileList')).toHaveLength(2);
    second.resolve({ fileName: '/profile/second.txt' });
    await flushPromises();
    expect(w.findComponent(FileUpload).emitted('update:modelValue')).toEqual([
      ['/profile/first.txt'],
      ['/profile/first.txt,/profile/second.txt'],
    ]);
  });

  it('aborts removal and ignores a late response', async () => {
    const task = deferred();
    requestMock.mockReturnValue(task.promise);
    const w = mountComponent(FileUpload);
    await select(w, [new File(['qa'], 'qa.txt')]);
    await w.find('.ele-upload-list__item-content-action .el-link').trigger('click');
    await flushPromises();
    expect(requestMock.mock.calls[0][0].signal.aborted).toBe(true);
    task.resolve({ fileName: '/profile/late.txt' });
    await flushPromises();
    expect(w.emitted('update:modelValue')).toBeUndefined();
    expect(w.text()).not.toContain('qa.txt');
  });

  it('aborts scope termination and unmount without late model writes', async () => {
    const task = deferred();
    requestMock.mockReturnValue(task.promise);
    const w = mountComponent(ImageUpload, { fileType: ['png'] });
    await select(w, [new File(['qa'], 'qa.png', { type: 'image/png' })]);
    endQuerySession();
    expect(requestMock.mock.calls[0][0].signal.aborted).toBe(true);
    w.unmount();
    wrappers.splice(wrappers.indexOf(w), 1);
    task.resolve({ fileName: '/profile/late.png' });
    await flushPromises();
    expect(w.emitted('update:modelValue')).toBeUndefined();
  });

  it('forwards progress only while the upload belongs to the current scope', async () => {
    const task = deferred();
    requestMock.mockReturnValue(task.promise);
    const w = mountComponent(FileUpload);
    await select(w, [new File(['qa'], 'qa.txt')]);
    const config = requestMock.mock.calls[0][0];
    config.onUploadProgress({ loaded: 5, total: 10 });
    await nextTick();
    expect(w.findComponent(ElUpload).props('fileList')?.[0]?.percentage).toBe(50);
    endQuerySession();
    config.onUploadProgress({ loaded: 10, total: 10 });
    await nextTick();
    expect(w.findComponent(ElUpload).props('fileList')?.[0]?.percentage).toBe(50);
    task.resolve({ fileName: '/profile/late.txt' });
    await flushPromises();
  });

  it('rejects unsupported files before sending a request', async () => {
    const w = mountComponent(ImageUpload);
    await select(w, [new File(['qa'], 'qa.txt', { type: 'text/plain' })]);
    expect(requestMock).not.toHaveBeenCalled();
  });

  it('publishes removal of an existing file while preserving another queued upload', async () => {
    const task = deferred();
    requestMock.mockReturnValue(task.promise);
    const w = mountComponent(FileUpload, { modelValue: '/profile/existing.txt' });
    await select(w, [new File(['qa'], 'new.txt')]);
    await w.findAll('.ele-upload-list__item-content-action .el-link')[0].trigger('click');
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([['']]);
    expect(requestMock.mock.calls[0][0].signal.aborted).toBe(false);
    task.resolve({ fileName: '/profile/new.txt' });
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([[''], ['/profile/new.txt']]);
  });

  it('publishes image removal after the native file list has changed', async () => {
    const w = mountComponent(ImageUpload, { modelValue: '/profile/existing.png' });
    await w.find('.el-upload-list__item-delete').trigger('click');
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([['']]);
  });
});
