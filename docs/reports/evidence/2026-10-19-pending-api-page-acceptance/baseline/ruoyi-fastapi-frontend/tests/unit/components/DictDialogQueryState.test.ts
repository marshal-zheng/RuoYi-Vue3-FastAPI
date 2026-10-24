import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, VueQueryPlugin } from '@tanstack/vue-query';
import { ElAlert, ElRadio, ElRadioGroup } from 'element-plus';
import DictDlg from '@/views/system/dict/components/DictDlg.vue';
import DictStatus from '@/components/business/DictStatus/index.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { getDicts } from '@/api/system/dict/data';
import { addType, updateType } from '@/api/system/dict/type';

vi.mock('@/api/system/dict/data', () => ({ getDicts: vi.fn() }));
vi.mock('@/api/system/dict/type', () => ({
  getType: vi.fn(),
  addType: vi.fn(),
  updateType: vi.fn(),
}));

const Dialog = defineComponent({
  name: 'DialogShell',
  inheritAttrs: false,
  props: { modelValue: Boolean },
  setup(props, { slots }) {
    return () => (props.modelValue ? h('section', slots.default?.()) : null);
  },
});
const Form = defineComponent({
  name: 'FormShell',
  inheritAttrs: false,
  setup(_, { slots }) {
    return () => h('div', slots.default?.());
  },
});
const Button = defineComponent({
  inheritAttrs: false,
  emits: ['click'],
  setup(_, { slots, emit }) {
    return () => h('button', { onClick: () => emit('click') }, slots.default?.());
  },
});
const wrappers: ReturnType<typeof mount>[] = [];
async function editor() {
  const wrapper = mount(DictDlg, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      components: { DictStatus, ElAlert, ElRadio, ElRadioGroup },
      stubs: { ZxDialog: Dialog, ElForm: Form, ElFormItem: Form, ElButton: Button, ZxInput: true },
    },
  });
  wrappers.push(wrapper);
  await (wrapper.vm as unknown as { open: () => Promise<void> }).open();
  await flushPromises();
  return wrapper;
}
const options = {
  items: [
    { dictLabel: '正常', dictValue: '0' },
    { dictLabel: '停用', dictValue: '1' },
  ],
};
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
  setQuerySession(1, ['admin'], ['system:dict:add']);
  vi.mocked(getDicts).mockReset();
  vi.mocked(addType).mockReset();
  vi.mocked(updateType).mockReset();
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

describe('dictionary dialog radio query state', () => {
  it('shows the initial radio read failure and restores the real radio choices after a read-only retry', async () => {
    vi.mocked(getDicts).mockRejectedValueOnce(new Error('dictionary unavailable'));
    const wrapper = await editor();
    expect(wrapper.text()).toContain('字典加载失败');
    expect(wrapper.find('[role="radiogroup"]').exists()).toBe(true);
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(0);
    expect(wrapper.text()).not.toContain('暂无选项');
    expect(getDicts).toHaveBeenCalledTimes(1);
    vi.mocked(getDicts).mockResolvedValueOnce(options);
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('.el-radio__label').map((label) => label.text())).toEqual([
      '正常',
      '停用',
    ]);
    expect(wrapper.text()).not.toContain('字典加载失败');
    expect(getDicts).toHaveBeenCalledTimes(2);
    expect(addType).not.toHaveBeenCalled();
    expect(updateType).not.toHaveBeenCalled();
  });

  it('presents offline pause beside the real radio group and resumes the shared read without a false empty result', async () => {
    onlineManager.setOnline(false);
    vi.mocked(getDicts).mockResolvedValue(options);
    const wrapper = await editor();
    expect(wrapper.text()).toContain('字典等待网络连接');
    expect(wrapper.find('[role="radiogroup"]').exists()).toBe(true);
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(0);
    expect(wrapper.text()).not.toContain('暂无选项');
    expect(wrapper.text()).not.toContain('字典加载失败');
    expect(getDicts).not.toHaveBeenCalled();
    onlineManager.setOnline(true);
    await flushPromises();
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(2);
    expect(wrapper.text()).not.toContain('字典等待网络连接');
    expect(getDicts).toHaveBeenCalledTimes(1);
  });
});
