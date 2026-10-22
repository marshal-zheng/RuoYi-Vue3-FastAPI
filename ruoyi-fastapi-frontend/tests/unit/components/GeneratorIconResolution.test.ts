import { mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import * as icons from '@element-plus/icons-vue';
import { describe, expect, it, vi } from 'vitest';
import IconsDialog from '@/views/tool/build/IconsDialog.vue';
import elementIconNames from '@/icons/element-names.json';

vi.mock('@zxio/zxui/core', () => ({
  ZxDialog: defineComponent({
    setup:
      (_props, { slots }) =>
      () =>
        h('div', [slots.headerLeft?.(), slots.default?.()]),
  }),
}));

const Input = defineComponent({
  inheritAttrs: false,
  props: ['modelValue'],
  emits: ['update:modelValue'],
  setup:
    (props, { emit }) =>
    () =>
      h('input', {
        value: props.modelValue,
        onInput: (event: Event) =>
          emit('update:modelValue', (event.target as HTMLInputElement).value),
      }),
});

describe('generator icon selection without global icon registration', () => {
  it('renders every actual icon object and preserves search and selected names', async () => {
    expect(elementIconNames).toEqual(Object.keys(icons).sort());
    const wrapper = mount(IconsDialog, {
      props: { modelValue: true },
      global: {
        components: {
          ZxInput: Input,
          ElIcon: { template: '<span><slot /></span>' },
        },
      },
    });
    try {
      expect(wrapper.findAll('.icon-ul li')).toHaveLength(Object.keys(icons).length);
      expect(wrapper.findAll('.icon-ul svg')).toHaveLength(Object.keys(icons).length);
      await wrapper.get('input').setValue('Search');
      expect(wrapper.findAll('.icon-ul li')).toHaveLength(1);
      expect(wrapper.findAll('.icon-ul svg')).toHaveLength(1);
      await wrapper.get('.icon-ul li').trigger('click');
      expect(wrapper.emitted('select')).toEqual([['Search']]);
      expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    } finally {
      wrapper.unmount();
    }
  });
});
