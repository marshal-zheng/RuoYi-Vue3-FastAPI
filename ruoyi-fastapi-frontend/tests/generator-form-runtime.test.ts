import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { webcrypto } from 'node:crypto';
import { compileScript, parse } from '@vue/compiler-sfc';
import { mount, flushPromises } from '@vue/test-utils';
import * as Vue from 'vue';
import * as ElementPlus from 'element-plus';
import * as ZxUi from '@zxio/zxui/core';
import { ZxThemeProvider } from '@zxio/zxui/theme-provider';
import { createDefaultBrowserThemeHost } from '@zxio/zxui/theme-host';
import defaultManifest from '@zxio/theme-default/manifest.json';
import ts from 'typescript';
import { describe, expect, it, vi } from 'vitest';
import * as FormDialog from '@/components/ui/FormDialog';
import { formConf } from '@/utils/generator/config';
import { makeUpHtml, vueScript, vueTemplate } from '@/utils/generator/html';
import { makeUpJs } from '@/utils/generator/js';
import { checkVueSource } from '../scripts/ui-standards-core.mjs';

const require = createRequire(import.meta.url);

/** Compile the actual exported SFC; imports resolve to the installed public APIs. */
function executableGeneratedForm() {
  const conf = {
    ...formConf,
    fields: [
      {
        tag: 'el-input',
        layout: 'colFormItem',
        vModel: 'name',
        label: '名称',
        span: 12,
        required: true,
        defaultValue: '',
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
        defaultValue: 'initial notes',
        autosize: { minRows: 2, maxRows: 4 },
      },
    ],
  };
  const source = vueTemplate(makeUpHtml(conf, 'dialog')) + vueScript(makeUpJs(conf, 'dialog'));
  expect(checkVueSource(source, { filePath: 'GeneratedRuntimeForm.vue' })).toEqual([]);
  const { descriptor, errors } = parse(source, {
    filename: 'GeneratedRuntimeForm.vue',
  });
  expect(errors).toEqual([]);
  const compiled = compileScript(descriptor, {
    id: 'generated-runtime',
    inlineTemplate: true,
  });
  const javascript = ts.transpileModule(compiled.content, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const modules: Record<string, unknown> = {
    vue: Vue,
    'element-plus': ElementPlus,
    '@zxio/zxui/core': ZxUi,
    '@/components/ui/FormDialog': FormDialog,
  };
  const exports: { default?: Vue.Component } = {};
  new Function('require', 'exports', javascript)((id: string) => {
    if (!(id in modules)) throw new Error(`Unexpected generated import: ${id}`);
    return modules[id];
  }, exports);
  return exports.default!;
}

describe('complete generated form runtime', () => {
  it('opens the generated dialog, validates real fields, resets and emits submitted values', async () => {
    const GeneratedForm = executableGeneratedForm();
    vi.stubGlobal('crypto', webcrypto);
    vi.spyOn(window.navigator, 'userAgent', 'get').mockReturnValue(
      'Mozilla/5.0 (X11; Linux x86_64)'
    );
    const host = createDefaultBrowserThemeHost({
      appKey: 'generated-form-test',
      defaultThemeId: 'default',
      themes: [
        {
          manifest: defaultManifest,
          assets: {
            './theme.css': readFileSync(require.resolve('@zxio/theme-default/theme.css'), 'utf8'),
            './element-plus.css': readFileSync(
              require.resolve('@zxio/theme-default/element-plus.css'),
              'utf8'
            ),
            './element-plus/mode-light__density-default__contrast-normal__motion-full__radius-default':
              readFileSync(
                require.resolve(
                  '@zxio/theme-default/element-plus/mode-light__density-default__contrast-normal__motion-full__radius-default'
                ),
                'utf8'
              ),
          },
        },
      ],
      portalTarget: () => document.body,
      rootRequest: { mode: 'light' },
      systemPreference: {
        currentMode: () => 'light',
        subscribe: () => () => {},
      },
    });
    if (!host.ok) throw new Error(JSON.stringify(host.diagnostics));
    const visible = Vue.ref(false);
    const onConfirm = vi.fn();
    const wrapper = mount(
      Vue.defineComponent({
        setup: () => () =>
          Vue.h(ZxThemeProvider, { portalTarget: () => document.body }, () =>
            Vue.h(GeneratedForm, {
              modelValue: visible.value,
              'onUpdate:modelValue': (value: boolean) => {
                visible.value = value;
              },
              onConfirm,
            })
          ),
      }),
      {
        attachTo: document.body,
        global: {
          plugins: [
            {
              install(app) {
                const bound = host.value.bind(app);
                if (!bound.ok) throw new Error(JSON.stringify(bound.diagnostics));
              },
            },
          ],
        },
      }
    );
    try {
      visible.value = true;
      await vi.waitFor(() => expect(document.querySelector('[role="dialog"]')).not.toBeNull());
      await flushPromises();
      const form = wrapper.findComponent(ElementPlus.ElForm);
      const formApi = form.vm.$.exposed as ElementPlus.FormInstance;
      const inputs = wrapper.findAllComponents(ZxUi.ZxInput);
      expect(inputs).toHaveLength(3);
      expect(document.querySelector('.el-input-group__prepend')?.textContent).toContain('https://');
      expect(document.querySelector('.el-input-group__append')?.textContent).toContain('.com');
      expect(document.querySelector('input[type="number"]')).not.toBeNull();
      expect(document.querySelector('textarea')?.value).toBe('initial notes');
      expect(await formApi.validate().catch(() => false)).toBe(false);
      await vi.waitFor(() =>
        expect(document.querySelector('.el-form-item__error')?.textContent).toContain('请输入名称')
      );
      await inputs[0].find('input').setValue('Ada');
      await inputs[1].find('input').setValue('12');
      await inputs[2].find('textarea').setValue('edited notes');
      expect(await formApi.validate()).toBe(true);
      formApi.resetFields();
      await Vue.nextTick();
      expect(inputs[0].find('input').element.value).toBe('');
      expect(inputs[1].find('input').element.value).toBe('');
      expect(inputs[2].find('textarea').element.value).toBe('initial notes');
      await inputs[0].find('input').setValue('Submitted');
      const confirm = document.querySelector<HTMLButtonElement>(
        '[data-dialog-action="save"], [data-dialog-action="submit"]'
      );
      expect(confirm).not.toBeNull();
      confirm!.click();
      await vi.waitFor(() => expect(onConfirm).toHaveBeenCalledOnce());
      expect(onConfirm.mock.calls[0][0]).toMatchObject({
        name: 'Submitted',
        quantityText: '',
        notes: 'initial notes',
      });
      await vi.waitFor(() => expect(visible.value).toBe(false));
    } finally {
      wrapper.unmount();
      await host.value.dispose();
      vi.unstubAllGlobals();
    }
  });
});
