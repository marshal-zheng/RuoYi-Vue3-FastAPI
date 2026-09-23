import { describe, expect, it } from 'vitest';
import { checkSource, checkVueSource } from '../scripts/ui-standards-core.mjs';

const formScript = `<script setup lang="ts">
import { useFormDialog as useBusinessForm, FormGrid } from '@/components/ui/FormDialog';
const columns = 2;
const dialog = useBusinessForm({ columns, title: 'Example', formRef });
const { dialogProps, formProps, layoutProps } = dialog;
</script>`;
const validForm = `<template><ZxDialog v-bind="dialogProps"><el-form v-bind="formProps"><FormGrid v-bind="layoutProps"><el-form-item data-form-full><zx-input /><el-input-number /></el-form-item></FormGrid></el-form></ZxDialog></template>${formScript}`;
const rules = (source: string) => checkVueSource(source).map((item: { rule: string }) => item.rule);

describe('UI standards shared SFC checker', () => {
  it('accepts generated and handwritten thin forms with aliases and local destructuring', () => {
    expect(checkVueSource(validForm)).toEqual([]);
  });

  it('matches exact executable inputs/dialogs, excluding comments and input-number', () => {
    const source = `<template><div><!-- <el-input /> --><el-input-number /><el-input /><el-dialog width="500px" /></div></template>`;
    expect(rules(source).filter((rule: string) => rule === 'no-raw-el-input')).toHaveLength(1);
    expect(rules(source)).toContain('no-raw-el-dialog');
    expect(rules(source)).toContain('dialog-dimensions');
    expect(
      checkVueSource(source, { checkRawInput: false }).map((item: { rule: string }) => item.rule)
    ).not.toContain('no-raw-el-input');
  });

  it('reports missing presets, dynamic spreads, local constant widths and style bypasses', () => {
    const source = `<template><ZxDialog v-bind="unknown" :dialog-style="sizing" /></template><script setup>
      const sizing = { width: '720px', height: '60vh' };
      const { dialogProps } = useDialog({ ...external, title: 'unresolved' });
      const width = '800px'; useDialog({ width, dialogSize: 'lg' });
    </script>`;
    expect(rules(source)).toContain('dialog-options-unresolved');
    expect(rules(source)).toContain('dialog-preset');
    expect(rules(source)).toContain('dialog-dimensions');
  });

  it('rejects independent layout columns and field geometry only inside modal forms', () => {
    expect(rules(validForm.replace('v-bind="layoutProps"', ':columns="3"'))).toContain(
      'form-layout-source'
    );
    expect(
      rules(
        validForm.replace(
          '<el-form-item data-form-full>',
          '<el-form-item label-width="80px"><el-row :gutter="12"><el-col :span="12" /></el-row>'
        )
      )
    ).toContain('form-label-width');
    expect(
      checkVueSource(
        '<template><el-form label-width="100px"><el-row :gutter="16"><el-col :span="8" /></el-row></el-form><div style="width: 880px" /></template>'
      )
    ).toEqual([]);
    expect(
      checkVueSource(
        '<template><ZxDialog dialog-size="lg"><el-form :inline="true"><el-form-item><zx-input /></el-form-item></el-form></ZxDialog></template>'
      )
    ).toEqual([]);
  });

  it('requires form/layout props to originate in the same controller', () => {
    const source =
      validForm.replace('v-bind="layoutProps"', 'v-bind="other.layoutProps"') +
      '<script>const other = useFormDialog({ columns: 1 })</script>';
    expect(rules(source)).toContain('form-layout-source');
  });

  it('requires dialog/form/layout props to originate in the same local controller', () => {
    const source = `<script setup>
      const a = useFormDialog({ columns: 1 });
      const b = useFormDialog({ columns: 3 });
    </script><template><ZxDialog v-bind="a.dialogProps.value">
      <el-form v-bind="b.formProps.value"><FormGrid v-bind="b.layoutProps.value" /></el-form>
    </ZxDialog></template>`;
    expect(rules(source)).toContain('form-dialog-source');
    expect(
      checkVueSource(
        source.replaceAll('b.formProps', 'a.formProps').replaceAll('b.layoutProps', 'a.layoutProps')
      )
    ).toEqual([]);
    expect(rules(source.replace('v-bind="a.dialogProps.value"', 'dialog-size="lg"'))).toContain(
      'form-dialog-source'
    );
  });

  it('rejects missing columns, invalid size and raw useDialog form ownership', () => {
    expect(
      rules(
        '<script setup>useFormDialog({ title: "Missing columns" }); useDialog({ formRef, dialogSize: "880px" });</script><template><div /></template>'
      )
    ).toEqual(expect.arrayContaining(['form-columns', 'form-dialog-entry', 'dialog-preset']));
  });

  it('diagnoses competing theme declarations/writes, not ordinary domain colors', () => {
    expect(
      checkVueSource(
        '<template><div /></template><style>.domain { color: #f00; --domain-status: green; } /* --el-color-primary: red */</style>'
      )
    ).toEqual([]);
    expect(
      rules(
        '<template><div :style="{ \'--el-color-primary\': \'red\' }" /></template><script setup>const shade = "red"; document.documentElement.style.setProperty("--el-color-primary", shade)</script><style>:root { --zx-semantic-color-primary: red }</style>'
      ).filter((rule: string) => rule === 'competing-theme-write')
    ).toHaveLength(3);
    expect(
      checkSource('declare module "@zxio/zxui" { interface PublicPatch {} }', {
        filePath: 'src/theme-patch.d.ts',
      }).map((item: { rule: string }) => item.rule)
    ).toContain('public-type-patch');
  });

  it('rejects private theme loading while allowing public deployment imports', () => {
    expect(
      checkSource('import data from "@zxio/theme-default/generated/theme.manifest.json";', {
        filePath: 'src/theme.ts',
      })
    ).toHaveLength(1);
    expect(
      checkSource('import { createThemeDeploymentResolver } from "@zxio/zxui/theme-host";', {
        filePath: 'src/theme.ts',
      })
    ).toEqual([]);
  });
});
