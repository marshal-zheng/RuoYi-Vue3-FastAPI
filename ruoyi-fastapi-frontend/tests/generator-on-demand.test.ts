import { mount, shallowMount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import * as ElementPlus from 'element-plus';
import type { Component } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import Render from '@/utils/generator/render';
import { inputComponents, selectComponents } from '@/utils/generator/config';
import { elementIcons } from '@/icons/element';

const palette = [...inputComponents, ...selectComponents];

describe('generator without a global component installer', () => {
  it('restores an uncommon saved icon without registering the complete catalog', async () => {
    expect(Object.hasOwn(elementIcons, 'Watermelon')).toBe(false);
    const wrapper = mount(Render, {
      props: { conf: { tag: 'el-button', icon: 'Watermelon' } },
    });
    try {
      await vi.waitFor(() => expect(wrapper.find('button svg').exists()).toBe(true));
      expect(Object.hasOwn(elementIcons, 'Watermelon')).toBe(false);
    } finally {
      wrapper.unmount();
    }
  });
  it.each(palette.filter(({ tag }) => tag.startsWith('el-')))(
    'renders $tag from its component object',
    (conf) => {
      const wrapper = shallowMount(Render, { props: { conf: { ...conf } } });
      try {
        const expected = Object.entries(ElementPlus).find(
          ([name]) =>
            name ===
            conf.tag.replace(/(^|-)(\w)/g, (_, _dash, letter: string) => letter.toUpperCase())
        )?.[1];
        expect(expected).toBeDefined();
        expect(wrapper.findComponent(expected as Component).exists()).toBe(true);
      } finally {
        wrapper.unmount();
      }
    }
  );

  it('renders picture upload icons without global icon registration', () => {
    const conf = {
      ...selectComponents.find(({ tag }) => tag === 'el-upload')!,
      'list-type': 'picture-card',
    };
    const wrapper = shallowMount(Render, {
      props: { conf: { ...conf } },
      global: { renderStubDefaultSlot: true },
    });
    try {
      expect(wrapper.findComponent(Plus).exists()).toBe(true);
    } finally {
      wrapper.unmount();
    }
  });
});
