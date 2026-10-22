import { h, nextTick, reactive } from 'vue';
import { mount } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import { ZxInputNumber } from '@zxio/zxui/input-number';

it('keeps the installed SchemaForm dependency raw text without a second numeric write', async () => {
  const state = reactive({ text: '3', value: 3, readonly: false });
  const numeric = vi.fn();
  const wrapper = mount(() =>
    h(ZxInputNumber, {
      text: state.text,
      modelValue: state.value,
      min: 0,
      max: 5,
      precision: 1,
      readonly: state.readonly,
      'onUpdate:modelValue': numeric,
      'onUpdate:text': (text: string) => {
        state.text = text;
        if (text.trim() && Number.isFinite(Number(text))) state.value = Number(text);
      },
    })
  );
  try {
    const input = wrapper.get('input');
    expect(input.attributes('type')).toBe('text');
    expect(input.attributes('inputmode')).toBe('decimal');
    await input.setValue('-');
    await input.trigger('change');
    await input.trigger('blur');
    expect(input.element.value).toBe('-');
    expect(state.value).toBe(3);
    await input.trigger('keydown', { key: 'ArrowUp', code: 'ArrowUp' });
    expect(state.text).toBe('4.0');
    expect(state.value).toBe(4);
    expect(numeric).not.toHaveBeenCalled();
    state.readonly = true;
    await nextTick();
    await input.trigger('keydown', { key: 'ArrowUp', code: 'ArrowUp' });
    expect(state.text).toBe('4.0');
  } finally {
    wrapper.unmount();
  }
});
