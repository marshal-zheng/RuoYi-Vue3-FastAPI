// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h, nextTick, reactive, ref } from 'vue';
import { ElForm, ElFormItem, type FormInstance } from 'element-plus';
import { createForm } from '@formily/core';
import type { BusinessContext } from '@zxio/schema-form/formily';
import { ZxTextEditor, type ZxTextEditorDocument } from '@zxio/text-editor';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { captureRemarkAIContext } from '@/components/ui/Remark/ai';
import { readRemark } from '@/components/ui/Remark/contract';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import { createPostSchema, type PostValues } from '@/views/system/post/components/post-form';
import { generateRemarkAI } from '@/api/system/remarkAi';

vi.mock('@/api/system/remarkAi', () => ({ generateRemarkAI: vi.fn() }));

const generated: ZxTextEditorDocument = {
  version: 2,
  body: {
    format: 'json',
    content: {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          attrs: { blockId: 'blk_a1b2c3', textAlign: null },
          content: [{ type: 'text', text: '负责设备巡检，每周五汇总异常并完成交接。' }],
        },
      ],
    },
  },
  annotations: [],
  assets: [],
  meta: { schemaVersion: 'stable-block-identity/v2' },
};
let host: ReturnType<typeof createRemarkFieldTestHost>;

// The AI card is teleported into the editor portal, outside the component root.
const card = () => document.querySelector<HTMLElement>('.zx-field-ai');
const cardButton = (testId: string) => {
  const found = document.querySelector<HTMLButtonElement>(`[data-testid="${testId}"]`);
  if (!found) throw new Error(`Missing card control: ${testId}`);
  return found;
};
/** Open the field card from its hover glyph and send one instruction from the composer. */
async function askAI(wrapper: ReturnType<typeof mount>, instruction: string) {
  await wrapper.get('.zx-text-editor-field__ai').trigger('click');
  await flushPromises();
  const input = document.querySelector<HTMLTextAreaElement>(
    '.zx-field-ai [data-testid="inline-ai-surface-prompt"]'
  );
  if (!input) throw new Error('Missing AI composer');
  input.value = instruction;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  await nextTick();
  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  await flushPromises();
}

beforeEach(() => {
  vi.resetAllMocks();
  host = createRemarkFieldTestHost('remark-ai-business');
  host.attach();
});
afterEach(() => host.dispose());

describe('AI remark business boundary', () => {
  it('only captures allowed business context and never passwords, contacts or parameter values', () => {
    const roles = [' 运维 '];
    const context = captureRemarkAIContext('user', {
      deptName: ' 维护部 ',
      roleNames: roles,
      password: 'secret',
      phonenumber: 'private',
      email: 'private@example.com',
    });
    roles.push('later');
    expect(context).toEqual({ deptName: '维护部', roleNames: ['运维'] });
    expect(
      captureRemarkAIContext('config', {
        configName: '服务设置',
        configKey: 'service.key',
        configValue: 'secret',
      })
    ).toEqual({ configName: '服务设置', configKey: 'service.key' });
    expect(captureRemarkAIContext('post', { postName: {}, postCode: 0, status: '' })).toEqual({});
  });

  it('reads the current Formily values when generation starts without mirroring the form', () => {
    const form = createForm({ values: { postName: '旧岗位', postCode: 'old', status: '0' } });
    const schema = createPostSchema(() => []).createSchema({
      form,
      bindResource: vi.fn(),
    } as unknown as BusinessContext<PostValues>);
    const properties = schema.properties as Record<string, Record<string, unknown>>;
    const props = properties.remark['x-component-props'] as {
      scene: string;
      aiContext: () => Record<string, unknown>;
    };
    expect(props.scene).toBe('post');
    expect(props.aiContext().postName).toBe('旧岗位');
    form.setValues({ postName: '设备维护员', postCode: 'maintenance' });
    expect(props.aiContext()).toEqual({
      postName: '设备维护员',
      postCode: 'maintenance',
      status: '正常',
    });
  });

  it('previews a real shared-field candidate and updates the business value only on acceptance', async () => {
    vi.mocked(generateRemarkAI).mockImplementation(async (_body, { onDelta }) => {
      onDelta('负责设备巡检');
      return readRemark(generated);
    });
    let department = '维护部';
    const wrapper = mount(RemarkEditor, {
      attachTo: document.body,
      props: {
        modelValue: null,
        scene: 'user',
        aiContext: () => ({ deptName: department, password: 'never-send' }),
      },
      global: host.global,
    });
    try {
      await flushPromises();
      department = '设备保障部';
      await askAI(wrapper, '设备巡检，每周五汇总异常并交接');
      expect(generateRemarkAI).toHaveBeenCalledTimes(1);
      expect(vi.mocked(generateRemarkAI).mock.calls[0][0]).toMatchObject({
        scene: 'user',
        target: 'document',
        context: { deptName: '设备保障部' },
      });
      expect(vi.mocked(generateRemarkAI).mock.calls[0][0].context).not.toHaveProperty('password');
      expect(wrapper.emitted('update:modelValue')).toBeUndefined();
      const error = card()!.querySelector('[role="alert"]');
      expect(error ? error.textContent : '').toBe('');
      expect(card()!.querySelector('[aria-label="AI 候选内容"]')!.textContent).toContain(
        '负责设备巡检'
      );
      expect(wrapper.vm.validate()).toBe(false);
      cardButton('field-ai-accept').click();
      await flushPromises();
      expect(JSON.stringify(wrapper.emitted('update:modelValue'))).toContain('每周五汇总异常');
      expect(wrapper.vm.validate()).toBe(true);
      expect(card()).toBeNull();
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      expect(editor.getText()).toContain('完成交接');
      editor.commands.undo();
      await flushPromises();
      expect(editor.isEmpty).toBe(true);
    } finally {
      wrapper.unmount();
    }
  });

  it('aborts the business request when the field session is destroyed', async () => {
    let signal: AbortSignal | undefined;
    vi.mocked(generateRemarkAI).mockImplementation((_body, options) => {
      signal = options.signal;
      return new Promise(() => {});
    });
    const wrapper = mount(RemarkEditor, {
      props: { modelValue: null, scene: 'post' },
      global: host.global,
    });
    await flushPromises();
    await askAI(wrapper, '写一条岗位备注');
    expect(signal?.aborted).toBe(false);
    wrapper.unmount();
    expect(signal?.aborted).toBe(true);
  });

  it('keeps pending review out of change/blur errors, blocks submit and clears errors after discard', async () => {
    vi.mocked(generateRemarkAI).mockResolvedValue(readRemark(generated));
    const model = reactive({ remark: readRemark(generated) });
    const form = ref<FormInstance>();
    const nativeForm = defineComponent({
      setup() {
        const { remarkRef, remarkRule } = useRemarkField();
        return () =>
          h('div', [
            h(ElForm, { ref: form, model, rules: { remark: [remarkRule] } }, () =>
              h(ElFormItem, { prop: 'remark' }, () =>
                h(RemarkEditor, {
                  ref: remarkRef,
                  scene: 'user',
                  modelValue: model.remark,
                  'onUpdate:modelValue': (value) => {
                    model.remark = value;
                  },
                })
              )
            ),
            h('button', { class: 'outside-field', type: 'button' }, '外部操作'),
          ]);
      },
    });
    const wrapper = mount(nativeForm, { attachTo: document.body, global: host.global });
    try {
      await flushPromises();
      await askAI(wrapper, '整理成要点');
      const editor = wrapper.findComponent(ZxTextEditor).vm.$.exposed!.editor.value;
      editor.commands.insertContent('手动补充');
      editor.view.dom.focus();
      (wrapper.get('.outside-field').element as HTMLButtonElement).focus();
      await flushPromises();
      expect(card()!.querySelector('[role="alert"]')!.textContent).toContain('原文已变化');
      expect(wrapper.findComponent(ElFormItem).vm.validateState).not.toBe('error');
      expect(wrapper.find('.el-form-item__error').exists()).toBe(false);

      await expect(form.value!.validate()).rejects.toBeDefined();
      await vi.waitFor(() => expect(wrapper.find('.el-form-item__error').exists()).toBe(true));
      expect(wrapper.get('.el-form-item__error').text()).toContain('请完成备注编辑');

      cardButton('field-ai-discard').click();
      await flushPromises();
      expect(card()).toBeNull();
      await vi.waitFor(() => expect(wrapper.find('.el-form-item__error').exists()).toBe(false));
      expect(editor.getText()).toContain('手动补充');
      await expect(form.value!.validate()).resolves.toBe(true);
    } finally {
      wrapper.unmount();
    }
  });
});
