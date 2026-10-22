// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h, shallowRef } from 'vue';
import { ZxTextEditor, ZxTextEditorField } from '@zxio/text-editor';
import type { ZxTextEditorDocument } from '@zxio/text-editor/core';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';

describe('installed public remark link IME', () => {
  it('retains the composing URL through Enter, Escape and capture before applying its IDN', async () => {
    const host = createRemarkFieldTestHost('remark-link-ime');
    host.attach();
    const value = shallowRef<ZxTextEditorDocument | null>(null);
    const wrapper = mount(
      defineComponent(() => () =>
        h(ZxTextEditorField, {
          modelValue: value.value,
          'onUpdate:modelValue': (document) => {
            value.value = document;
          },
        })
      ),
      { attachTo: document.body, global: host.global }
    );
    try {
      await flushPromises();
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor.commands.insertContent('链接文字');
      editor.commands.selectAll();
      await flushPromises();
      const body = JSON.parse(JSON.stringify(value.value));
      await wrapper.find('button[aria-label="链接"]').trigger('click');
      await flushPromises();
      const input = host.portal.querySelector('input')!;
      expect(input).not.toBeNull();
      input.value = 'https://before.example';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await flushPromises();
      input.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
      input.value = 'https://例子.测试';
      input.dispatchEvent(
        new InputEvent('input', {
          bubbles: true,
          inputType: 'insertCompositionText',
          data: '例子.测试',
          isComposing: true,
        })
      );
      for (const key of ['Enter', 'Escape']) {
        input.dispatchEvent(
          new KeyboardEvent('keydown', {
            key,
            code: key,
            keyCode: 229,
            isComposing: true,
            bubbles: true,
          })
        );
        await flushPromises();
        expect(host.portal.querySelector('input')).toBe(input);
        expect(value.value).toEqual(body);
      }
      const field = wrapper.findComponent(ZxTextEditorField).vm.$.exposed!;
      expect(field.captureEdit()).toMatchObject({
        linkOpen: true,
        linkDraft: 'https://例子.测试',
      });
      input.dispatchEvent(
        new CompositionEvent('compositionend', { bubbles: true, data: '例子.测试' })
      );
      await flushPromises();
      input.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true })
      );
      await flushPromises();
      expect(host.portal.querySelector('input')).toBeNull();
      expect(field.validate()).toBe(true);
      expect(JSON.stringify(value.value)).toContain('https://例子.测试');
    } finally {
      wrapper.unmount();
      host.dispose();
    }
  });
});
