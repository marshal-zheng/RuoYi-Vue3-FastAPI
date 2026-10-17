import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import { VueQueryPlugin } from '@tanstack/vue-query';
import DictAutocomplete from '@/components/business/DictAutocomplete/index.vue';
import { queryClient } from '@/queries/client';
import { endQuerySession, setQuerySession } from '@/queries/context';
import { dictOptions } from '@/queries/system/dict';
import { getDicts } from '@/api/system/dict/data';

vi.mock('@/api/system/dict/data', () => ({ getDicts: vi.fn() }));
vi.mock('@/api/system/dict/type', () => ({}));
const Autocomplete = defineComponent({
  props: ['modelValue', 'fetchSuggestions'],
  emits: ['input', 'focus', 'blur', 'select', 'update:modelValue'],
  setup(props, { emit, expose }) {
    expose({ getData: (text: string) => props.fetchSuggestions(text, () => {}) });
    return () =>
      h('input', {
        value: props.modelValue,
        onFocus: () => emit('focus'),
        onBlur: () => emit('blur'),
        onInput: (event: Event) => {
          const value = (event.target as HTMLInputElement).value;
          emit('update:modelValue', value);
          emit('input', value);
        },
      });
  },
});
const wrappers: ReturnType<typeof mount>[] = [];
function editor() {
  const wrapper = mount(DictAutocomplete, {
    props: { dictType: 'sys_test', modelValue: '0' },
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: { ElAutocomplete: Autocomplete, ElButton: true },
    },
  });
  wrappers.push(wrapper);
  return wrapper;
}
const response = (label: string) => ({ items: [{ dictValue: '0', dictLabel: label }] });
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  vi.mocked(getDicts).mockReset();
  setQuerySession(1, [], []);
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
});

describe('dictionary autocomplete query integration', () => {
  it('filters locally and retains the editing draft while shared data refreshes', async () => {
    vi.mocked(getDicts).mockResolvedValue(response('旧标签'));
    const wrapper = editor();
    await flushPromises();
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('旧标签');
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').setValue('草稿');
    const suggestions = wrapper.findComponent(Autocomplete).props('fetchSuggestions');
    const callback = vi.fn();
    suggestions('草', callback);
    suggestions('草稿', callback);
    expect(callback).toHaveBeenCalledTimes(2);
    expect(getDicts).toHaveBeenCalledTimes(1);
    vi.mocked(getDicts).mockResolvedValue(response('新标签'));
    await queryClient.invalidateQueries({
      queryKey: dictOptions(setQuerySession(1, [], []), 'sys_test').queryKey,
    });
    await flushPromises();
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('草稿');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    await wrapper.find('input').trigger('blur');
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['草稿']);
  });

  it('invalidates an old suggestion callback as soon as debounced input changes', async () => {
    let finish!: (value: ReturnType<typeof response>) => void;
    vi.mocked(getDicts).mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        })
    );
    const wrapper = editor();
    await flushPromises();
    const suggestions = wrapper.findComponent(Autocomplete).props('fetchSuggestions');
    await wrapper.find('input').setValue('旧');
    const callback = vi.fn();
    suggestions('旧', callback);
    await wrapper.find('input').setValue('新');
    // The next fetch-suggestions is still in the control's debounce window.
    finish(response('旧标签'));
    await flushPromises();
    expect(callback).not.toHaveBeenCalled();
  });

  it('discards suggestions for old input and old scope after an initial read', async () => {
    let finish!: (value: ReturnType<typeof response>) => void;
    vi.mocked(getDicts).mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        })
    );
    const wrapper = editor();
    await flushPromises();
    const suggestions = wrapper.findComponent(Autocomplete).props('fetchSuggestions');
    const oldInput = vi.fn();
    const current = vi.fn();
    suggestions('旧', oldInput);
    suggestions('新', current);
    finish(response('新标签'));
    await flushPromises();
    expect(oldInput).not.toHaveBeenCalled();
    expect(current).toHaveBeenCalledWith([expect.objectContaining({ label: '新标签' })]);

    endQuerySession();
    setQuerySession(2, [], []);
    await flushPromises();
    const oldScope = vi.fn();
    suggestions('', oldScope);
    endQuerySession();
    await flushPromises();
    finish(response('另一个账号标签'));
    await flushPromises();
    expect(oldScope).not.toHaveBeenCalled();
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('0');
  });
  it('keeps a same-scope known selected label when refreshed options omit its value', async () => {
    vi.mocked(getDicts).mockResolvedValue(response('已有标签'));
    const wrapper = editor();
    await flushPromises();
    vi.mocked(getDicts).mockResolvedValue({ items: [] });
    await queryClient.invalidateQueries({
      queryKey: dictOptions(setQuerySession(1, [], []), 'sys_test').queryKey,
    });
    await flushPromises();
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('已有标签');
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').trigger('blur');
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['0']);
  });
});
