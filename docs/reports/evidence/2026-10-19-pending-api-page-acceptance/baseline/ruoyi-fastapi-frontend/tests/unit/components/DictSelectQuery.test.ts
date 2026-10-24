import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, ref, watch } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import DictSelect from '@/components/business/DictSelect/index.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { getDicts } from '@/api/system/dict/data';

vi.mock('@/api/system/dict/data', () => ({ getDicts: vi.fn() }));
vi.mock('@/api/system/dict/type', () => ({}));

type Response = { items: { dictLabel: string; dictValue: string }[] };
const response = (label: string): Response => ({
  items: [{ dictLabel: label, dictValue: '0' }],
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((complete, fail) => {
    resolve = complete;
    reject = fail;
  });
  return { promise, resolve, reject };
}

let nextInstance = 0;
// Exercise the domain slots with native Query. The shell preserves selected
// metadata across missing options, as the public ZxSelect contract allows.
const SelectShell = defineComponent({
  name: 'ZxSelect',
  props: {
    modelValue: [String, Number, Array],
    entity: Object,
    options: { type: Array, default: () => [] },
    loading: Boolean,
    refreshing: Boolean,
    error: null,
    paused: Boolean,
  },
  emits: ['retry', 'search', 'visible-change'],
  setup(props, { slots, emit }) {
    const instance = ++nextInstance;
    const selectedLabel = ref(String(props.modelValue ?? ''));
    watch(
      () => props.options,
      () => {
        const selected = (props.options as { value: string; label: string }[]).find(
          (option) => option.value === props.modelValue
        );
        if (selected) selectedLabel.value = selected.label;
      },
      { immediate: true }
    );
    return () => {
      const state = {
        loading: props.loading,
        refreshing: props.refreshing,
        error: props.error,
        paused: props.paused,
        hasData: props.options.length > 0,
        retry: () => emit('retry'),
      };
      return h('section', { 'data-select-instance': instance }, [
        h('span', { class: 'selected-label' }, selectedLabel.value),
        h(
          'div',
          { class: 'options' },
          (props.options as { label: string }[]).map((option) => option.label).join(',')
        ),
        props.error != null
          ? slots.error?.(state)
          : props.loading || props.refreshing || props.paused
            ? slots.status?.(state)
            : props.options.length === 0
              ? slots.empty?.()
              : null,
      ]);
    };
  },
});
const Button = defineComponent({
  emits: ['click'],
  setup(_, { emit, slots }) {
    return () => h('button', { onClick: () => emit('click') }, slots.default?.());
  },
});
const wrappers: ReturnType<typeof mount>[] = [];
function selector() {
  const wrapper = mount(DictSelect, {
    props: { modelValue: '0', dictType: 'sys_a' },
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: { ZxSelect: SelectShell, ElButton: Button },
    },
  });
  wrappers.push(wrapper);
  return wrapper;
}
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  setQuerySession(1, [], []);
  vi.mocked(getDicts).mockReset();
  nextInstance = 0;
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

describe('dictionary Select query integration', () => {
  it('provides visible initial loading feedback instead of a blank or successful empty state', async () => {
    const pending = deferred<Response>();
    vi.mocked(getDicts).mockReturnValue(pending.promise);
    const wrapper = selector();
    await flushPromises();
    expect(wrapper.findComponent(SelectShell).props('loading')).toBe(true);
    expect(wrapper.text()).toContain('正在加载字典');
    expect(wrapper.text()).not.toContain('暂无选项');
    pending.resolve(response('正常'));
    await flushPromises();
    expect(wrapper.find('.options').text()).toBe('正常');
    expect(wrapper.findComponent(SelectShell).props('loading')).toBe(false);
  });

  it('retains options and selected labels during refresh failure and retries only the read', async () => {
    const refresh = deferred<Response>();
    vi.mocked(getDicts)
      .mockResolvedValueOnce(response('旧标签'))
      .mockReturnValueOnce(refresh.promise);
    const wrapper = selector();
    await flushPromises();
    const read = (wrapper.vm as unknown as { refresh: () => Promise<void> }).refresh();
    await nextTick();
    await flushPromises();
    expect(wrapper.findComponent(SelectShell).props('refreshing')).toBe(true);
    expect(wrapper.find('.options').text()).toBe('旧标签');
    expect(wrapper.find('.selected-label').text()).toBe('旧标签');
    expect(wrapper.text()).toContain('正在刷新字典');
    const error = new Error('refresh failed');
    refresh.reject(error);
    await expect(read).rejects.toBe(error);
    await flushPromises();
    expect(wrapper.text()).toContain('字典刷新失败');
    expect(wrapper.find('.options').text()).toBe('旧标签');
    expect(wrapper.find('.selected-label').text()).toBe('旧标签');
    vi.mocked(getDicts).mockResolvedValueOnce(response('新标签'));
    await wrapper.find('button').trigger('click');
    await flushPromises();
    expect(wrapper.find('.options').text()).toBe('新标签');
    expect(wrapper.text()).not.toContain('字典刷新失败');
    expect(getDicts).toHaveBeenCalledTimes(3);
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });

  it('remounts selected metadata for a different dictionary type and authorization scope', async () => {
    const oldScopeRead = deferred<Response>();
    const currentScopeRead = deferred<Response>();
    vi.mocked(getDicts)
      .mockResolvedValueOnce(response('旧类型标签'))
      .mockReturnValueOnce(oldScopeRead.promise)
      .mockReturnValueOnce(currentScopeRead.promise);
    const wrapper = selector();
    await flushPromises();
    const initial = wrapper.find('[data-select-instance]').attributes('data-select-instance');
    expect(wrapper.find('.selected-label').text()).toBe('旧类型标签');
    await wrapper.setProps({ dictType: 'sys_b' });
    await flushPromises();
    const changedType = wrapper.find('[data-select-instance]').attributes('data-select-instance');
    expect(changedType).not.toBe(initial);
    expect(wrapper.find('.selected-label').text()).toBe('0');
    setQuerySession(2, [], []);
    await flushPromises();
    expect(wrapper.find('[data-select-instance]').attributes('data-select-instance')).not.toBe(
      changedType
    );
    expect(wrapper.find('.selected-label').text()).toBe('0');
    oldScopeRead.resolve(response('旧账号晚到标签'));
    await flushPromises();
    expect(wrapper.text()).not.toContain('旧账号晚到标签');
    currentScopeRead.resolve(response('当前账号标签'));
    await flushPromises();
    expect(wrapper.find('.selected-label').text()).toBe('当前账号标签');
    expect(getDicts).toHaveBeenCalledTimes(3);
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
  });
});
