// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { h, markRaw } from 'vue';
import { ElForm } from 'element-plus';
import {
  ZxSchemaForm,
  type BusinessContext,
  type SchemaFormInstance,
} from '@zxio/schema-form/formily';
import { ZxTextEditor } from '@zxio/text-editor';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';

type Values = { remark: RemarkValue };
let host: ReturnType<typeof createRemarkFieldTestHost>;
let portal: HTMLDivElement;
beforeEach(() => {
  host = createRemarkFieldTestHost('remark-formily-probe');
  portal = host.portal;
  host.attach();
});
afterEach(() => host.dispose());

function mountedForm(initial: Values = { remark: null }) {
  let context!: BusinessContext<Values>;
  const save = vi.fn(async (values: Values) => ({ ok: true as const, values }));
  const wrapper = mount(ZxSchemaForm<Values>, {
    attachTo: document.body,
    props: {
      initial,
      save,
      bindings: {
        RemarkEditor: {
          component: markRaw(RemarkEditor),
          composite: true,
          group: false,
        },
      },
      createSchema(ctx) {
        context = ctx;
        return {
          type: 'object',
          properties: {
            remark: {
              type: 'object',
              title: '备注',
              'x-component': 'RemarkEditor',
            },
          },
        };
      },
    },
    global: host.global,
  });
  return {
    wrapper,
    save,
    form: wrapper.vm as unknown as SchemaFormInstance<Values>,
    context: () => context,
  };
}

describe('real Formily and RemarkEditor public integration', () => {
  it('inherits native ElForm disabled state through the public field adapter', async () => {
    const wrapper = mount(ElForm, {
      props: { disabled: true },
      slots: { default: () => h(RemarkEditor, { modelValue: null }) },
      global: host.global,
    });
    try {
      await flushPromises();
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      expect(editor.isEditable).toBe(false);
      expect(wrapper.find('button[aria-label="加粗"]').attributes('disabled')).toBeDefined();
      await wrapper.setProps({ disabled: false });
      await flushPromises();
      expect(editor.isEditable).toBe(true);
    } finally {
      wrapper.unmount();
    }
  });
  it('owns null/object values once, fills without dirty and submits canonical documents', async () => {
    const { wrapper, form, save } = mountedForm();
    try {
      await flushPromises();
      expect(form.ready).toBe(true);
      expect(form.read().remark).toBeNull();
      expect(form.dirty).toBe(false);
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor.commands.insertContent('中文 👩‍💻');
      await flushPromises();
      const document = readRemark(form.read().remark);
      expect(document).not.toBeNull();
      expect(typeof form.read().remark).toBe('object');
      expect(form.dirty).toBe(true);
      expect(await form.submit()).toBe(true);
      expect(save).toHaveBeenCalledTimes(1);
      expect(save.mock.calls[0][0].remark).toEqual(document);
      expect(form.dirty).toBe(false);
      await form.replaceValues({ remark: structuredClone(document) }, 'authority');
      await flushPromises();
      expect(form.dirty).toBe(false);
      const filledEditor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      filledEditor.commands.selectAll();
      filledEditor.commands.toggleBold();
      await flushPromises();
      expect(form.dirty).toBe(true);
      expect(JSON.stringify(form.read().remark)).toContain('bold');
      await form.replaceValues({ remark: null }, 'authority');
      await flushPromises();
      expect(form.read().remark).toBeNull();
      expect(form.dirty).toBe(false);
    } finally {
      wrapper.unmount();
    }
  });

  it('blocks submit during composition while retaining the single field document', async () => {
    const { wrapper, form, save } = mountedForm();
    try {
      await flushPromises();
      const field = wrapper.findComponent(RemarkEditor);
      await field.trigger('compositionstart');
      wrapper
        .findComponent(ZxTextEditor)
        .vm.$.exposed!.editor.value.commands.insertContent('输入法😀');
      await flushPromises();
      expect(form.fieldPending).toBe(true);
      expect(await form.submit()).toBe(false);
      expect(save).not.toHaveBeenCalled();
      await field.trigger('compositionend');
      await flushPromises();
      expect(form.fieldPending).toBe(false);
      expect(JSON.stringify(form.read().remark)).toContain('输入法😀');
      expect(await form.submit()).toBe(true);
    } finally {
      wrapper.unmount();
    }
  });

  it('commits the composition boundary before temporary hide without losing Chinese input', async () => {
    const { wrapper, form, save, context } = mountedForm();
    try {
      await flushPromises();
      const control = wrapper.findComponent(RemarkEditor);
      await control.trigger('compositionstart');
      wrapper
        .findComponent(ZxTextEditor)
        .vm.$.exposed!.editor.value.commands.insertContent('组合输入中文😀');
      await flushPromises();
      expect(form.fieldPending).toBe(true);
      const field = context().form.query('remark').take()!;
      field.visible = false;
      await flushPromises();
      field.visible = true;
      await flushPromises();
      expect(JSON.stringify(form.read().remark)).toContain('组合输入中文😀');
      expect(wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value.getText()).toContain(
        '组合输入中文😀'
      );
      expect(await form.submit()).toBe(true);
      expect(JSON.stringify(save.mock.calls[0][0].remark)).toContain('组合输入中文😀');
    } finally {
      wrapper.unmount();
    }
  });
  it('retains over-limit typing across temporary hide for correction while refusing submit', async () => {
    const { wrapper, form, save, context } = mountedForm();
    const text = '文'.repeat(5001);
    try {
      await flushPromises();
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      // A live editing transaction goes through the actual editor update event, not setDocument.
      editor.view.dispatch(editor.state.tr.insertText(text));
      await flushPromises();
      expect(editor.getText()).toBe(text);
      expect(JSON.stringify(form.read().remark)).toContain(text);
      expect(wrapper.findComponent(RemarkEditor).vm.$.exposed!.validate()).toBe(false);
      expect(await form.submit()).toBe(false);
      expect(save).not.toHaveBeenCalled();
      const field = context().form.query('remark').take()!;
      field.visible = false;
      await flushPromises();
      field.visible = true;
      await flushPromises();
      const restored = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      expect(restored.getText()).toBe(text);
      expect(restored.isEditable).toBe(true);
      expect(wrapper.findComponent(RemarkEditor).vm.$.exposed!.validate()).toBe(false);
      expect(await form.submit()).toBe(false);
      expect(save).not.toHaveBeenCalled();
    } finally {
      wrapper.unmount();
    }
  });
  it('captures and restores a pending link draft across Formily visibility and blocks save', async () => {
    const { wrapper, form, save, context } = mountedForm();
    try {
      await flushPromises();
      wrapper
        .findComponent(ZxTextEditor)
        .vm.$.exposed!.editor.value.commands.insertContent('链接文字');
      await flushPromises();
      const authoritative = structuredClone(form.read().remark);
      await wrapper.find('button[aria-label="链接"]').trigger('click');
      await flushPromises();
      const input = portal.querySelector('input')!;
      expect(input).not.toBeNull();
      input.value = 'https://example.com/draft';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await flushPromises();
      expect(form.fieldPending).toBe(true);
      const field = context().form.query('remark').take()!;
      field.visible = false;
      await flushPromises();
      expect(wrapper.findComponent(RemarkEditor).exists()).toBe(false);
      field.visible = true;
      await flushPromises();
      expect((portal.querySelector('input') as HTMLInputElement).value).toBe(
        'https://example.com/draft'
      );
      expect(form.read().remark).toEqual(authoritative);
      expect(await form.submit()).toBe(false);
      expect(save).not.toHaveBeenCalled();
      expect(form.fieldPending).toBe(true);
      expect((portal.querySelector('input') as HTMLInputElement).value).toBe(
        'https://example.com/draft'
      );
      const cancel = [...portal.querySelectorAll('button')].find(
        (button) => button.textContent?.trim() === '取消'
      )!;
      cancel.click();
      await flushPromises();
      expect(form.fieldPending).toBe(false);
      expect(await form.submit()).toBe(true);
    } finally {
      wrapper.unmount();
    }
  });
});
