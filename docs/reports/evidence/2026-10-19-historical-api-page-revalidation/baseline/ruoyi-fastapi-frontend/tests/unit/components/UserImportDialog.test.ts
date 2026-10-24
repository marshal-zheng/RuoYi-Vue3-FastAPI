import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, type App } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { importUserExcel } from '@/api/system/user';
import UserImportDialog from '@/views/system/user/components/UserImportDialog.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';

const feedback = vi.hoisted(() => ({
  error: vi.fn(),
  problem: vi.fn(),
  alert: vi.fn(),
}));
vi.mock('@/api/system/user', () => ({ importUserExcel: vi.fn() }));
vi.mock('element-plus', () => ({ ElMessage: { error: feedback.error } }));
vi.mock('@/utils/feedback/presenter', () => ({
  presentProblemFeedback: feedback.problem,
  resolveFeedbackOptions: (options: unknown) => options,
}));

const Dialog = defineComponent({
  name: 'ZxDialog',
  props: ['modelValue'],
  emits: ['update:modelValue', 'close'],
  setup(_, { slots, emit, expose }) {
    expose({
      close: () => {
        emit('update:modelValue', false);
        emit('close');
      },
    });
    return () => h('div', [slots.default?.(), slots.footer?.()]);
  },
});
const Upload = defineComponent({
  name: 'ZxUpload',
  props: ['modelValue', 'disabled', 'autoUpload'],
  emits: ['update:modelValue'],
  setup(_, { expose }) {
    expose({ submit: vi.fn() });
    return () => h('div');
  },
});
const Button = defineComponent({
  name: 'ElButton',
  props: ['loading'],
  setup(props, { slots }) {
    return () => h('button', { 'data-loading': String(!!props.loading) }, slots.default?.());
  },
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}
const result = {
  summary: { total: 1, succeeded: 1, failed: 0 },
  results: [{ success: true, userName: '<probe>', action: 'created' }],
};
const mounted: ReturnType<typeof mount>[] = [];
function mountDialog() {
  const wrapper = mount(UserImportDialog, {
    global: {
      plugins: [
        (app: App) => {
          app.config.globalProperties.$alert = feedback.alert;
        },
      ],
      stubs: {
        ZxDialog: Dialog,
        ZxUpload: Upload,
        ElButton: Button,
        ElCheckbox: true,
        ElLink: true,
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}
type DialogApi = { open: () => void; close: () => void };
function selectFile(wrapper: ReturnType<typeof mount>, name = 'users.xlsx') {
  const raw = new File(['excel'], name);
  const file = { name, raw, uid: 1, status: 'ready', percentage: 0 };
  wrapper.findComponent(Upload).vm.$emit('update:modelValue', [file]);
  return file;
}
beforeEach(() => {
  queryClient.clear();
  setQuerySession(1, [], []);
});
afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount());
  endQuerySession();
  queryClient.clear();
  vi.clearAllMocks();
});

describe('UserImportDialog lifecycle', () => {
  it('closes on a scope change and ignores the old upload result', async () => {
    const response = deferred<typeof result>();
    vi.mocked(importUserExcel).mockReturnValueOnce(response.promise);
    const wrapper = mountDialog();
    (wrapper.vm as unknown as DialogApi).open();
    selectFile(wrapper);
    await wrapper.find('button').trigger('click');
    await flushPromises();
    setQuerySession(2, [], []);
    await nextTick();
    expect(wrapper.findComponent(Dialog).props('modelValue')).toBe(false);
    expect(vi.mocked(importUserExcel).mock.calls[0][2]?.signal?.aborted).toBe(true);
    response.resolve(result);
    await flushPromises();
    expect(wrapper.emitted('success')).toBeUndefined();
    expect(feedback.alert).not.toHaveBeenCalled();
  });

  it('releases loading after failure and retries the same selected Excel once', async () => {
    const failed = deferred<typeof result>();
    vi.mocked(importUserExcel).mockReturnValueOnce(failed.promise).mockResolvedValueOnce(result);
    const wrapper = mountDialog();
    (wrapper.vm as unknown as DialogApi).open();
    const file = selectFile(wrapper);
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(importUserExcel).toHaveBeenCalledTimes(1);
    expect(wrapper.find('button').attributes('data-loading')).toBe('true');
    const error = new Error('Excel validation failed');
    failed.reject(error);
    await flushPromises();
    expect(feedback.error).toHaveBeenCalledExactlyOnceWith(error.message);
    expect(wrapper.find('button').attributes('data-loading')).toBe('false');
    expect(wrapper.findComponent(Upload).props('modelValue')[0].raw).toBe(file.raw);
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(importUserExcel).toHaveBeenCalledTimes(2);
    expect(wrapper.emitted('success')).toHaveLength(1);
    expect(feedback.alert).toHaveBeenCalledTimes(1);
    expect(feedback.alert.mock.calls[0][0]).toContain('&lt;probe&gt;');
    expect(wrapper.find('button').attributes('data-loading')).toBe('false');
  });

  it('acquires loading before progress and sends only one import for repeated clicks', async () => {
    const response = deferred<typeof result>();
    vi.mocked(importUserExcel).mockReturnValue(response.promise);
    const wrapper = mountDialog();
    (wrapper.vm as unknown as DialogApi).open();
    selectFile(wrapper);
    const button = wrapper.find('button');
    void button.trigger('click');
    void button.trigger('click');
    await flushPromises();
    expect(importUserExcel).toHaveBeenCalledTimes(1);
    expect(wrapper.find('button').attributes('data-loading')).toBe('true');
    expect(wrapper.findComponent(Upload).props('disabled')).toBe(true);
    response.resolve(result);
    await flushPromises();
    expect(feedback.error.mock.calls).toEqual([]);
    expect(wrapper.emitted('success')).toHaveLength(1);
  });

  it.each(['success', 'failure'] as const)(
    'ignores late %s and progress after close/reopen while a new import runs',
    async (outcome) => {
      const old = deferred<typeof result>(),
        current = deferred<typeof result>();
      vi.mocked(importUserExcel)
        .mockReturnValueOnce(old.promise)
        .mockReturnValueOnce(current.promise);
      const wrapper = mountDialog();
      const api = wrapper.vm as unknown as DialogApi;
      api.open();
      selectFile(wrapper);
      await wrapper.find('button').trigger('click');
      await flushPromises();
      expect(importUserExcel).toHaveBeenCalledTimes(1);
      const oldConfig = vi.mocked(importUserExcel).mock.calls[0][2]!;
      await api.close();
      await nextTick();
      expect(oldConfig.signal?.aborted).toBe(true);
      expect(wrapper.find('button').attributes('data-loading')).toBe('false');
      api.open();
      const selected = selectFile(wrapper, 'new.xlsx');
      await wrapper.find('button').trigger('click');
      await flushPromises();
      expect(importUserExcel).toHaveBeenCalledTimes(2);
      oldConfig.onUploadProgress?.({
        loaded: 5,
        total: 5,
        progress: 1,
        bytes: 5,
        lengthComputable: true,
      });
      if (outcome === 'success') old.resolve(result);
      else old.reject(new Error('late failure'));
      await flushPromises();
      expect(wrapper.find('button').attributes('data-loading')).toBe('true');
      expect(wrapper.findComponent(Upload).props('modelValue')[0].raw).toBe(selected.raw);
      expect(wrapper.findComponent(Upload).props('modelValue')[0].percentage).toBe(0);
      expect(wrapper.emitted('success')).toBeUndefined();
      expect(feedback.alert).not.toHaveBeenCalled();
      expect(feedback.error).not.toHaveBeenCalled();
      expect(feedback.problem).not.toHaveBeenCalled();
      current.resolve(result);
      await flushPromises();
      expect(wrapper.emitted('success')).toHaveLength(1);
      expect(wrapper.find('button').attributes('data-loading')).toBe('false');
    }
  );

  it.each(['dialog-close', 'unmount'] as const)(
    'aborts on %s without reporting a late error',
    async (path) => {
      const response = deferred<typeof result>();
      vi.mocked(importUserExcel).mockReturnValue(response.promise);
      const wrapper = mountDialog();
      (wrapper.vm as unknown as DialogApi).open();
      selectFile(wrapper);
      await wrapper.find('button').trigger('click');
      await flushPromises();
      const config = vi.mocked(importUserExcel).mock.calls[0][2]!;
      if (path === 'dialog-close')
        wrapper.findComponent(Dialog).vm.$emit('update:modelValue', false);
      else wrapper.unmount();
      await nextTick();
      expect(config.signal?.aborted).toBe(true);
      response.reject(new Error('request completed after cancellation'));
      await flushPromises();
      expect(feedback.error).not.toHaveBeenCalled();
      expect(feedback.problem).not.toHaveBeenCalled();
      expect(wrapper.emitted('success')).toBeUndefined();
    }
  );

  it('validates the selection before acquiring an import', async () => {
    const wrapper = mountDialog();
    (wrapper.vm as unknown as DialogApi).open();
    await wrapper.find('button').trigger('click');
    await flushPromises();
    selectFile(wrapper, 'not-excel.txt');
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(importUserExcel).not.toHaveBeenCalled();
    expect(feedback.error).toHaveBeenCalledTimes(2);
    expect(wrapper.find('button').attributes('data-loading')).toBe('false');
  });
});
