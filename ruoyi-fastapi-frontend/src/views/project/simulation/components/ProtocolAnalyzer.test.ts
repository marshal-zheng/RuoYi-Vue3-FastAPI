import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { shallowMount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';
import ProtocolAnalyzer from './ProtocolAnalyzer.vue';

const Checkbox = defineComponent({
  name: 'ElCheckbox',
  props: ['modelValue'],
  emits: ['change', 'update:modelValue'],
  template: '<button><slot /></button>',
});
const Table = defineComponent({
  name: 'ElTableV2',
  template: '<div><div class="el-table-v2__body"></div></div>',
});

describe('protocol analyzer automatic scrolling', () => {
  const frames: FrameRequestCallback[] = [];
  const errors: unknown[] = [];
  let wrapper: VueWrapper;
  let body: HTMLElement;
  let checkbox: VueWrapper;

  beforeEach(async () => {
    frames.length = 0;
    errors.length = 0;
    vi.spyOn(performance, 'now').mockReturnValue(0);
    vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) =>
      frames.push(callback)
    );
    wrapper = shallowMount(ProtocolAnalyzer, {
      props: { autoScroll: false, messages: [{ messageId: 'message-1', sendTimestamp: 1 }] },
      global: {
        config: { errorHandler: (error: unknown) => errors.push(error) },
        stubs: {
          ElCheckbox: Checkbox,
          ElTableV2: Table,
          ElSelect: true,
          ElOption: true,
          ElInput: true,
          ElPopover: true,
          ElButton: true,
          ElIcon: true,
          ElDropdown: true,
          ElDropdownMenu: true,
          ElDropdownItem: true,
          ElTag: true,
        },
      },
    });
    await nextTick();
    const target = wrapper.find('.el-table-v2__body').element;
    if (!(target instanceof HTMLElement)) throw new Error('The scroll body is missing');
    body = target;
    Object.defineProperty(body, 'scrollHeight', { configurable: true, value: 500 });
    const control = wrapper.findAllComponents(Checkbox).find((item) => item.text() === '自动滚动');
    if (!control) throw new Error('The automatic scroll control is missing');
    checkbox = control;
  });
  afterEach(() => {
    wrapper.unmount();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('enables actual scrolling and emits the new preference without undefined callbacks', async () => {
    checkbox.vm.$emit('change', true);
    await nextTick();
    expect(errors).toEqual([]);
    expect(wrapper.emitted('auto-scroll-change')).toEqual([[true]]);
    expect(frames.length).toBe(1);
    frames.shift()?.(100);
    expect(body.scrollTop).toBeGreaterThan(0);
  });

  it('turning off stops an already scheduled animation', async () => {
    checkbox.vm.$emit('change', true);
    await nextTick();
    frames.shift()?.(100);
    const position = body.scrollTop;
    checkbox.vm.$emit('change', false);
    await nextTick();
    expect(errors).toEqual([]);
    frames.shift()?.(200);
    expect(body.scrollTop).toBe(position);
    expect(frames).toHaveLength(0);
    expect(wrapper.emitted('auto-scroll-change')).toEqual([[true], [false]]);
  });

  it('a rapid on/off change does not start scrolling in the next tick', async () => {
    checkbox.vm.$emit('change', true);
    checkbox.vm.$emit('change', false);
    await nextTick();
    expect(errors).toEqual([]);
    expect(frames).toHaveLength(0);
    expect(body.scrollTop).toBe(0);
  });
});
