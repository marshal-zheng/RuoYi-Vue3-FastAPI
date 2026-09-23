import { describe, expect, it, vi } from 'vitest';
import { defineComponent, h, ref } from 'vue';
import { mount } from '@vue/test-utils';
import { compileScript, compileTemplate, parse } from '@vue/compiler-sfc';
import { formConf, inputComponents } from '@/utils/generator/config';
import { makeUpHtml, vueScript, vueTemplate } from '@/utils/generator/html';
import { makeUpJs } from '@/utils/generator/js';
import { normalizeGeneratorFields, resolveGeneratorTag } from '@/utils/generator/identity';
import { checkVueSource } from '../scripts/ui-standards-core.mjs';

vi.mock('@zxio/zxui/input', () => ({
  ZxInput: defineComponent({
    name: 'ZxInput',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    setup:
      (props, { emit, slots }) =>
      () =>
        h('div', { 'data-input': 'zx-input' }, [
          slots.prepend?.(),
          h('input', {
            value: props.modelValue,
            onInput: (event: Event) =>
              emit('update:modelValue', (event.target as HTMLInputElement).value),
          }),
          slots.append?.(),
        ]),
  }),
}));

import FormElementRender from '@/utils/generator/render';

const legacyFields = [
  {
    tag: 'el-input',
    layout: 'colFormItem',
    vModel: 'name',
    label: '名称',
    span: 12,
    required: true,
    defaultValue: 'initial',
    placeholder: '请输入名称',
    prepend: 'https://',
    append: '.com',
  },
  {
    tag: 'el-input',
    layout: 'colFormItem',
    vModel: 'quantityText',
    label: '原生数值',
    span: 12,
    type: 'number',
    defaultValue: '',
  },
  {
    tag: 'el-input',
    layout: 'colFormItem',
    vModel: 'notes',
    label: '说明',
    span: 24,
    type: 'textarea',
    defaultValue: '',
    autosize: { minRows: 2, maxRows: 4 },
  },
  {
    tag: 'el-input-number',
    layout: 'colFormItem',
    vModel: 'quantity',
    label: '步进数值',
    span: 12,
    defaultValue: 0,
    min: 0,
    max: 10,
  },
];

function generate(type = 'dialog') {
  const conf = { ...formConf, fields: structuredClone(legacyFields) };
  return vueTemplate(makeUpHtml(conf, type)) + vueScript(makeUpJs(conf, type));
}

describe('generator public form contract', () => {
  it('reads legacy identities without mutating saved fields or numeric semantics', () => {
    const fields = normalizeGeneratorFields(legacyFields);
    expect(fields.map((field) => field.tag)).toEqual([
      'zx-input',
      'zx-input',
      'zx-input',
      'el-input-number',
    ]);
    expect(legacyFields[0].tag).toBe('el-input');
    expect(fields[1].type).toBe('number');
    expect(fields[2].type).toBe('textarea');
    expect(resolveGeneratorTag('el-select')).toBe('el-select');
    expect(inputComponents.slice(0, 3).every((field) => field.tag === 'zx-input')).toBe(true);
  });

  it('generates a complete SFC accepted by the same source gate', () => {
    const source = generate();
    const { descriptor, errors } = parse(source, {
      filename: 'GeneratedForm.vue',
    });
    expect(errors).toEqual([]);
    const script = compileScript(descriptor, { id: 'generated-form' });
    const template = compileTemplate({
      source: descriptor.template!.content,
      filename: 'GeneratedForm.vue',
      id: 'generated-form',
      compilerOptions: { bindingMetadata: script.bindings },
    });
    expect(template.errors).toEqual([]);
    expect(
      checkVueSource(source, {
        filePath: 'GeneratedForm.vue',
        checkRawInput: true,
      })
    ).toEqual([]);
    for (const binding of [
      'ZxDialog',
      'ZxInput',
      'ElForm',
      'ElFormItem',
      'ElInputNumber',
      'FormGrid',
      'useFormDialog',
    ]) {
      expect(script.bindings?.[binding]).toBeDefined();
    }
    expect(source).toContain('columns: 2');
    expect(source).toContain('data-form-full');
    expect(source).toContain('<template #append>');
    expect(source).toContain('<template #prepend>');
    expect(source).not.toContain('slot="');
    expect(source).not.toMatch(/<el-input(?:\s|>)/);
    expect(source).not.toMatch(/<el-(?:row|col)(?:\s|>)/);
    expect(source).not.toContain('label-width');
    expect(source).toContain(":min='0'");
  });

  it('keeps page generation supported and escapes string defaults', () => {
    const conf = {
      ...formConf,
      fields: [{ ...legacyFields[0], defaultValue: "a'b\nsecond line" }],
    };
    const source = vueTemplate(makeUpHtml(conf, 'file')) + vueScript(makeUpJs(conf, 'file'));
    const { descriptor, errors } = parse(source);
    expect(errors).toEqual([]);
    expect(() => compileScript(descriptor, { id: 'generated-page' })).not.toThrow();
    expect(checkVueSource(source, { filePath: 'GeneratedPage.vue' })).toEqual([]);
  });

  it('normalizes nested saved rows into full-width semantic layout', () => {
    const conf = {
      ...formConf,
      columns: 3 as const,
      fields: [
        {
          ...legacyFields[0],
          layout: 'rowFormItem',
          tag: 'el-row',
          children: legacyFields,
        },
      ],
    };
    const source = vueTemplate(makeUpHtml(conf, 'dialog')) + vueScript(makeUpJs(conf, 'dialog'));
    expect(source).toContain('<div data-form-full><FormGrid');
    expect(source).not.toContain(':span=');
    expect(checkVueSource(source, { filePath: 'NestedGeneratedForm.vue' })).toEqual([]);
  });

  it('previews a legacy input using the same component and forwards slots/model once', async () => {
    const model = ref('old');
    const onUpdate = vi.fn((value: string) => {
      model.value = value;
    });
    const wrapper = mount(
      defineComponent({
        setup: () => () =>
          h(FormElementRender, {
            conf: legacyFields[0],
            modelValue: model.value,
            'onUpdate:modelValue': onUpdate,
          }),
      })
    );
    expect(wrapper.find('[data-input="zx-input"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('https://');
    expect(wrapper.text()).toContain('.com');
    await wrapper.find('input').setValue('edited');
    expect(model.value).toBe('edited');
    expect(onUpdate).toHaveBeenCalledTimes(1);
    expect(legacyFields[0].tag).toBe('el-input');
    wrapper.unmount();
  });
});
