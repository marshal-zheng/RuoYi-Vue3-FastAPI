import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { onlineManager, VueQueryPlugin } from '@tanstack/vue-query';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { dictTypeOptions } from '@/queries/system/dict';
import { optionselect } from '@/api/system/dict/type';
import DictTypeSelect from '@/components/business/DictTypeSelect/index.vue';

vi.mock('@/api/system/dict/type', () => ({ optionselect: vi.fn() }));
vi.mock('@/api/system/dict/data', () => ({}));

const Select = defineComponent({
  name: 'TypeChoiceSelect',
  props: ['modelValue', 'options', 'loading', 'refreshing', 'error', 'paused'],
  emits: ['update:modelValue', 'change', 'search', 'visible-change', 'retry'],
  setup(props, { emit, slots }) {
    return () => {
      const state = {
        ...props,
        hasData: props.options.length > 0,
        retry: () => emit('retry'),
      };
      return h('section', [
        ...(props.error ? (slots.error?.(state) ?? []) : (slots.status?.(state) ?? [])),
        ...props.options.map((option: unknown) => slots.option?.({ option })),
        ...(!props.options.length && !props.error && !props.loading && !props.paused
          ? (slots.empty?.() ?? [])
          : []),
      ]);
    };
  },
});
const wrappers: ReturnType<typeof mount>[] = [];
function selector(props: Record<string, unknown> = {}) {
  const wrapper = mount(DictTypeSelect, {
    props,
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: { ZxSelect: Select, ElButton: { template: '<button><slot /></button>' } },
    },
  });
  wrappers.push(wrapper);
  return wrapper;
}
const response = (name = '状态类型') => ({
  items: [{ dictId: 1, dictName: name, dictType: 'sys_status', status: '0' as const }],
});
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  vi.mocked(optionselect).mockReset();
  onlineManager.setOnline(true);
  setQuerySession(1, [], []);
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
  onlineManager.setOnline(true);
});

describe('shared dictionary type selector', () => {
  it('shares fresh type choices, displays both fields and keeps selection/search local', async () => {
    vi.mocked(optionselect).mockResolvedValue(response());
    const first = await selector({ modelValue: 'sys_status' });
    const second = await selector({ modelValue: 'another_type' });
    await flushPromises();
    expect(optionselect).toHaveBeenCalledTimes(1);
    expect(first.text()).toContain('状态类型');
    expect(first.text()).toContain('sys_status');
    const select = first.findComponent(Select);
    select.vm.$emit('search', 'missing');
    await flushPromises();
    expect(first.text()).toContain('无匹配结果');
    expect(second.text()).toContain('状态类型');
    expect(optionselect).toHaveBeenCalledTimes(1);
    first.findComponent(Select).vm.$emit('update:modelValue', undefined);
    first.findComponent(Select).vm.$emit('change', undefined);
    expect(first.emitted('update:modelValue')).toEqual([[undefined]]);
    expect(first.emitted('change')).toEqual([[undefined]]);
    expect(second.emitted('update:modelValue')).toBeUndefined();

    await selector();
    await flushPromises();
    expect(optionselect).toHaveBeenCalledTimes(1);
    const scope = setQuerySession(1, [], []);
    queryClient.setQueryData(
      dictTypeOptions(scope).queryKey,
      queryClient.getQueryData(dictTypeOptions(scope).queryKey),
      { updatedAt: 1 }
    );
    vi.mocked(optionselect).mockResolvedValue(response('新名称'));
    second.findComponent(Select).vm.$emit('visible-change', true);
    await flushPromises();
    expect(optionselect).toHaveBeenCalledTimes(2);
    expect(second.text()).toContain('新名称');
  });

  it('shows paused and initial failure states and retries only the shared read', async () => {
    onlineManager.setOnline(false);
    vi.mocked(optionselect).mockRejectedValue(new Error('network failure'));
    const wrapper = await selector();
    await flushPromises();
    expect(wrapper.text()).toContain('等待网络连接');
    expect(wrapper.text()).not.toContain('暂无选项');
    onlineManager.setOnline(true);
    await flushPromises();
    expect(wrapper.text()).toContain('字典类型加载失败');
    expect(wrapper.text()).not.toContain('暂无选项');
    vi.mocked(optionselect).mockResolvedValue(response());
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('状态类型');
    expect(optionselect).toHaveBeenCalledTimes(2);
  });

  it('honors active and clears the control identity on a scope change', async () => {
    vi.mocked(optionselect).mockResolvedValue(response('旧账号类型'));
    const wrapper = await selector({ active: false });
    wrapper.findComponent(Select).vm.$emit('visible-change', true);
    await flushPromises();
    expect(optionselect).not.toHaveBeenCalled();
    await wrapper.setProps({ active: true });
    await flushPromises();
    const oldControl = wrapper.findComponent(Select).vm;
    vi.mocked(optionselect).mockImplementation(() => new Promise(() => {}));
    setQuerySession(2, [], []);
    await flushPromises();
    expect(wrapper.findComponent(Select).vm).not.toBe(oldControl);
    expect(wrapper.text()).not.toContain('旧账号类型');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });
});
