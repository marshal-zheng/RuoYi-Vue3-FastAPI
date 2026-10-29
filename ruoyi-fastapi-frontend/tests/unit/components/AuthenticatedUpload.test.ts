import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, ref, type Component, type App } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import ElementPlus, { ElUpload } from 'element-plus';
import modal from '@/plugins/modal';
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
            app.config.globalProperties.$modal = {
              ...modal,
              loading,
              closeLoading,
            };
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
const descriptor = (id: string, name = `${id}.txt`) => ({
  assetId: id,
  name,
  mediaType: 'text/plain',
  size: 2,
  contentUrl: `/file-assets/${id}/content`,
});
const ID = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
type Config = {
  url: string;
  method?: string;
  data?: unknown;
  signal?: AbortSignal;
};
/** Route the single request() mock by endpoint: upload, metadata batch and discard. */
const route =
  (
    upload: (config: Config) => Promise<unknown> = () =>
      Promise.resolve(descriptor(ID(1), 'qa.txt'))
  ) =>
  (config: Config) => {
    if (config.url === '/file-assets/metadata:batch') {
      const ids = (config.data as { assetIds: string[] }).assetIds;
      return Promise.resolve({
        items: ids
          .filter((id) => !id.endsWith('99'))
          .map((id) => descriptor(id, `name-${id.slice(-2)}.txt`)),
        unavailableIds: ids.filter((id) => id.endsWith('99')),
      });
    }
    if (config.method === 'delete') return Promise.resolve(null);
    return upload(config);
  };
const uploads = () =>
  requestMock.mock.calls.filter(([config]) => config.url === '/file-assets/uploads');
const select = async (w: ReturnType<typeof mount>, files: File[]) => {
  const input = w.find('input[type=file]');
  Object.defineProperty(input.element, 'files', {
    configurable: true,
    value: files,
  });
  await input.trigger('change');
  await flushPromises();
};

beforeEach(() => {
  vi.clearAllMocks();
  setQuerySession('qa', ['admin'], ['*:*:*']);
  requestMock.mockImplementation(route());
  vi.stubGlobal(
    'URL',
    Object.assign(URL, {
      createObjectURL: vi.fn(() => 'blob:qa'),
      revokeObjectURL: vi.fn(),
    })
  );
});
afterEach(() => {
  wrappers.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  vi.unstubAllGlobals();
});

describe('authenticated native upload wrappers', () => {
  const fileProps = { purpose: 'demo.files', typeIds: ['txt', 'pdf'] };
  const imageProps = { purpose: 'demo.images' };

  it.each([
    [FileUpload, fileProps, new File(['qa'], 'qa.txt', { type: 'text/plain' })],
    [ImageUpload, imageProps, new File(['qa'], 'qa.png', { type: 'image/png' })],
  ])('uploads once with purpose context and emits asset ids', async (component, props, file) => {
    const w = mountComponent(component, {
      modelValue: [],
      ownerId: 7,
      ...props,
    });
    await select(w, [file]);
    expect(uploads()).toHaveLength(1);
    const [config, options] = uploads()[0];
    expect(config.data.get('file')).toMatchObject({
      name: file.name,
      size: file.size,
    });
    expect(config.data.get('purpose')).toBe(props.purpose);
    expect(config.data.get('ownerId')).toBe('7');
    expect(config.timeout).toBe(0);
    expect(options.context).toBeDefined();
    expect(w.emitted('update:modelValue')).toEqual([[[ID(1)]]]);
    expect(closeLoading).toHaveBeenCalled();
  });

  it('derives accept and hints from the declared type ids', async () => {
    const w = mountComponent(FileUpload, { ...fileProps });
    expect(w.find('input[type=file]').attributes('accept')).toBe('.txt,.pdf');
    expect(w.text()).toContain('txt/pdf');
  });

  it('keeps a successful file when another request fails and settles the loading state', async () => {
    const good = deferred();
    const bad = deferred();
    requestMock.mockImplementation(
      route(vi.fn().mockReturnValueOnce(good.promise).mockReturnValueOnce(bad.promise))
    );
    const w = mountComponent(FileUpload, fileProps);
    await select(w, [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]);
    bad.reject(new Error('server failure'));
    good.resolve(descriptor(ID(2), 'a.txt'));
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([[[ID(2)]]]);
    expect(closeLoading).toHaveBeenCalled();
    expect(w.text()).toContain('a.txt');
    expect(w.text()).not.toContain('b.txt');
  });

  it('preserves queued files when the parent echoes one completed id', async () => {
    const first = deferred();
    const second = deferred();
    requestMock.mockImplementation(
      route(vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise))
    );
    const Host = defineComponent({
      setup() {
        const value = ref<string[]>([]);
        return () =>
          h(FileUpload, {
            ...fileProps,
            modelValue: value.value,
            'onUpdate:modelValue': (v: string[]) => {
              value.value = v;
            },
          });
      },
    });
    const w = mountComponent(Host);
    await select(w, [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]);
    first.resolve(descriptor(ID(3), 'a.txt'));
    await flushPromises();
    expect(w.findComponent(ElUpload).props('fileList')).toHaveLength(2);
    second.resolve(descriptor(ID(4), 'b.txt'));
    await flushPromises();
    expect(w.findComponent(FileUpload).emitted('update:modelValue')).toEqual([
      [[ID(3)]],
      [[ID(3), ID(4)]],
    ]);
  });

  it('aborts removal and ignores a late response', async () => {
    const task = deferred();
    requestMock.mockImplementation(route(() => task.promise));
    const w = mountComponent(FileUpload, fileProps);
    await select(w, [new File(['qa'], 'qa.txt')]);
    await w.find('.ele-upload-list__item-content-action .el-link').trigger('click');
    await flushPromises();
    expect(uploads()[0][0].signal.aborted).toBe(true);
    task.resolve(descriptor(ID(5)));
    await flushPromises();
    expect(w.emitted('update:modelValue')).toBeUndefined();
    expect(w.text()).not.toContain('qa.txt');
  });

  it('discards only drafts uploaded in this session, never saved ones', async () => {
    const w = mountComponent(FileUpload, {
      ...fileProps,
      modelValue: [ID(10)],
    });
    await flushPromises();
    await select(w, [new File(['qa'], 'qa.txt')]);
    await w.setProps({ modelValue: [ID(10), ID(1)] });
    const links = () => w.findAll('.ele-upload-list__item-content-action .el-link');
    await links()[1].trigger('click'); // the new draft
    await flushPromises();
    await links()[0].trigger('click'); // the saved asset: only the form value changes
    await flushPromises();
    const deletes = requestMock.mock.calls.filter(([config]) => config.method === 'delete');
    expect(deletes.map(([config]) => config.url)).toEqual([`/file-assets/${ID(1)}`]);
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual([[]]);
  });

  it('loads names for saved ids in one batch and marks unavailable ones', async () => {
    const w = mountComponent(FileUpload, {
      ...fileProps,
      modelValue: [ID(11), ID(99)],
    });
    await flushPromises();
    const batches = requestMock.mock.calls.filter(
      ([config]) => config.url === '/file-assets/metadata:batch'
    );
    expect(batches).toHaveLength(1);
    expect(batches[0][0].data).toEqual({ assetIds: [ID(11), ID(99)] });
    expect(w.text()).toContain('name-11.txt');
    expect(w.text()).toContain('文件不可用');
    expect(w.find('a').attributes('href')).toBe(`/file-assets/${ID(11)}/content?download=true`);
  });

  it('aborts scope termination and unmount without late model writes', async () => {
    const task = deferred();
    requestMock.mockImplementation(route(() => task.promise));
    const w = mountComponent(ImageUpload, imageProps);
    await select(w, [new File(['qa'], 'qa.png', { type: 'image/png' })]);
    endQuerySession();
    expect(uploads()[0][0].signal.aborted).toBe(true);
    w.unmount();
    wrappers.splice(wrappers.indexOf(w), 1);
    task.resolve(descriptor(ID(6), 'late.png'));
    await flushPromises();
    expect(w.emitted('update:modelValue')).toBeUndefined();
  });

  it('forwards progress only while the upload belongs to the current scope', async () => {
    const task = deferred();
    requestMock.mockImplementation(route(() => task.promise));
    const w = mountComponent(FileUpload, fileProps);
    await select(w, [new File(['qa'], 'qa.txt')]);
    const config = uploads()[0][0];
    config.onUploadProgress({ loaded: 5, total: 10 });
    await nextTick();
    expect(w.findComponent(ElUpload).props('fileList')?.[0]?.percentage).toBe(50);
    endQuerySession();
    config.onUploadProgress({ loaded: 10, total: 10 });
    await nextTick();
    expect(w.findComponent(ElUpload).props('fileList')?.[0]?.percentage).toBe(50);
    task.resolve(descriptor(ID(7)));
    await flushPromises();
  });

  it('rejects unsupported files before sending a request', async () => {
    const w = mountComponent(ImageUpload, imageProps);
    await select(w, [new File(['qa'], 'qa.txt', { type: 'text/plain' })]);
    expect(uploads()).toHaveLength(0);
    const f = mountComponent(FileUpload, fileProps);
    await select(f, [new File(['qa'], 'qa.docx')]);
    expect(uploads()).toHaveLength(0);
  });

  it('publishes removal of an existing file while preserving another queued upload', async () => {
    const task = deferred();
    requestMock.mockImplementation(route(() => task.promise));
    const w = mountComponent(FileUpload, {
      ...fileProps,
      modelValue: [ID(12)],
    });
    await flushPromises();
    await select(w, [new File(['qa'], 'new.txt')]);
    await w.findAll('.ele-upload-list__item-content-action .el-link')[0].trigger('click');
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([[[]]]);
    expect(uploads()[0][0].signal.aborted).toBe(false);
    task.resolve(descriptor(ID(8), 'new.txt'));
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([[[]], [[ID(8)]]]);
  });

  it('publishes image removal after the native file list has changed', async () => {
    const w = mountComponent(ImageUpload, {
      ...imageProps,
      modelValue: [ID(13)],
    });
    await flushPromises();
    await w.find('.el-upload-list__item-delete').trigger('click');
    await flushPromises();
    expect(w.emitted('update:modelValue')).toEqual([[[]]]);
  });
});
