// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h, proxyRefs, ref } from 'vue';
import PostDlg from '@/views/system/post/components/PostDlg.vue';
import type { SchemaFormInstance } from '@zxio/schema-form/formily';
import type { PostValues } from '@/views/system/post/components/post-form';

const api = vi.hoisted(() => ({ read: vi.fn(), discard: vi.fn() }));
const dictionary = ref([
  { label: '正常', value: '0' },
  { label: '停用', value: '1' },
]);
vi.mock('@/api/system/post', () => ({
  getPost: api.read,
  listPost: vi.fn(),
  addPost: vi.fn(),
  updatePost: vi.fn(),
}));
vi.mock('@/utils/http', () => ({ presentRequestError: vi.fn() }));
vi.mock('@/utils/dict', () => ({
  useDict: () => ({ sys_normal_disable: dictionary }),
}));
vi.mock('element-plus', async (original) => ({
  ...(await original<typeof import('element-plus')>()),
  ElMessageBox: { confirm: api.discard },
}));
vi.mock('@/components/ui/Remark/RemarkEditor.vue', () => ({
  default: { inheritAttrs: false, render: () => null },
}));
const DialogShell = defineComponent({
  props: {
    modelValue: Boolean,
    handleBeforeCancel: { type: Function, required: true },
  },
  emits: ['update:modelValue'],
  setup(props, { slots, expose, emit }) {
    expose({
      async close() {
        if (await props.handleBeforeCancel()) emit('update:modelValue', false);
      },
    });
    return () => (props.modelValue ? h('section', slots.default?.()) : null);
  },
});
let wrapper: ReturnType<typeof mount>;
beforeEach(() => {
  vi.clearAllMocks();
  dictionary.value = [
    { label: '正常', value: '0' },
    { label: '停用', value: '1' },
  ];
  api.read.mockImplementation(async (postId: number) => ({
    postId,
    postName: '测试岗位',
    postCode: 'test-post',
    postSort: 0,
    status: '0',
    remark: null,
  }));
});
afterEach(() => wrapper?.unmount());

// The same public contract runs against source mode and the installed snapshot.
describe('post schema session', () => {
  it('protects unfinished numeric input on close and replacement, then releases after correction', async () => {
    wrapper = mount(PostDlg, {
      attachTo: document.body,
      global: {
        stubs: {
          ZxDialog: DialogShell,
          DictStatus: true,
          ElAlert: true,
          ElButton: true,
        },
      },
    });
    const dialog = wrapper.vm as unknown as {
      open(id: number): Promise<void>;
      close(): Promise<void>;
    };
    await dialog.open(31);
    await flushPromises();
    const component = wrapper.findComponent({ name: 'ZxSchemaForm' });
    const form = proxyRefs(
      (component.vm as unknown as { $: { exposed: Record<string, unknown> } }).$.exposed
    ) as unknown as SchemaFormInstance<PostValues>;
    expect(form.ready).toBe(true);
    dictionary.value = [
      { label: '当前可用', value: '0' },
      { label: '停用', value: '1' },
    ];
    await flushPromises();
    expect(wrapper.text()).toContain('当前可用');

    const input = wrapper.get<HTMLInputElement>('input[inputmode="decimal"]');
    await input.setValue('-');
    expect(form.read().postSort).toBe(0);
    expect(form.dirty).toBe(false);
    expect(form.fieldPending).toBe(false);
    expect(form.hasUncommittedInput).toBe(true);
    api.discard.mockRejectedValue(new Error('继续编辑'));
    await dialog.close();
    expect(component.exists()).toBe(true);
    await dialog.open(32);
    expect(api.discard).toHaveBeenCalledTimes(2);
    expect(api.read).toHaveBeenCalledTimes(1);
    expect(input.element.value).toBe('-');

    await input.setValue('0');
    expect(form.hasUncommittedInput).toBe(false);
    expect(form.dirty).toBe(false);
    await dialog.close();
    await flushPromises();
    expect(wrapper.findComponent({ name: 'ZxSchemaForm' }).exists()).toBe(false);
    expect(api.discard).toHaveBeenCalledTimes(2);
  });
});
