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
  const schemaForm = `<script setup>
    import { schemaFormDialog as schemaDialog } from '@/components/ui/FormDialog';
    const { dialogProps, schemaFormProps } = schemaDialog({ columns: 1 });
  </script><template><ZxDialog v-bind="dialogProps">
    <ZxSchemaForm v-bind="schemaFormProps" />
  </ZxDialog></template>`;

  it('accepts SchemaForm presentation without a native form or a second form model', () => {
    expect(checkVueSource(schemaForm)).toEqual([]);
  });

  it('requires SchemaForm presentation from the same entry and rejects native form-ref casts', () => {
    expect(rules(schemaForm.replace('v-bind="schemaFormProps"', ':label-width="80"'))).toEqual(
      expect.arrayContaining(['schema-form-source', 'form-label-width'])
    );
    expect(
      rules(schemaForm.replace('v-bind="dialogProps"', 'v-bind="dialogProps" :form-ref="formRef"'))
    ).toContain('schema-form-ref');
    expect(
      rules(
        schemaForm
          .replace('v-bind="schemaFormProps"', 'v-bind="other.schemaFormProps"')
          .replace(
            'const { dialogProps',
            'const other = schemaDialog({ columns: 1 }); const { dialogProps'
          )
      )
    ).toContain('schema-form-source');
  });

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

describe('query definition source checker', () => {
  const checkQuery = (source: string, filePath = 'src/views/example.vue') =>
    checkSource(source, { filePath });
  const queryRules = (source: string, filePath = 'src/views/example.ts') =>
    checkQuery(source, filePath).map((item: { rule: string }) => item.rule);

  it('accepts public factory aliases through locals, ref, computed and getters', () => {
    expect(
      checkQuery(`<script setup lang="ts">
        import { useQuery as query } from '@tanstack/vue-query';
        import { computed as derive, ref } from 'vue';
        import { dictOptions as factory } from '@/queries/system/dict';
        const current = ref(factory(scope, { type }));
        const options = derive(() => factory(scope, { type: type.value }));
        const getter = () => options.value;
        query(current); query(options); query(getter);
        query(derive(() => factory(scope, { type: () => props.type })));
        query({ ...factory(scope, { type }), select: items => items.slice(0, 3) });
      </script><template><div /></template>`)
    ).toEqual([]);
  });

  it('accepts relative and namespace factories and reactive useQueries arrays or maps', () => {
    expect(
      checkQuery(
        `
        import * as query from '@tanstack/vue-query';
        import { computed } from 'vue';
        import * as shared from '../../queries/system/dict';
        import { dictOptions as factory } from '@/queries/system/dict';
        const queries = computed(() => types.value.map(type => shared.dictOptions(scope, { type })));
        query.useQuery(computed(() => shared.dictQueries.options(scope, type)));
        query.useQueries({ queries });
        query.useQueries(computed(() => ({ queries: [factory(scope, first), factory(scope, second)] })));
        query.useQueries({ queries: types.map(factory) });
      `,
        'src/components/business/Example.ts'
      )
    ).toEqual([]);
  });

  it('ignores same-named ordinary functions, objects and shadowed TanStack bindings', () => {
    expect(
      checkQuery(
        `
        import { useQuery } from '@tanstack/vue-query';
        import { useQueries } from './ordinary';
        const client = { invalidateQueries() {}, setQueryData() {} };
        const record = { queryKey: ['ordinary'] };
        function run(useQuery: Function) { useQuery({ queryKey: ['ordinary'] }); }
        useQueries({ queries: [{ queryKey: ['ordinary'] }] });
        client.invalidateQueries(); client.setQueryData(['ordinary'], 1);
      `,
        'src/components/ordinary.ts'
      )
    ).toEqual([]);
  });

  it('allows query definitions and native cache operations inside src/queries', () => {
    expect(
      checkQuery(
        `
        import { queryOptions, QueryClient } from '@tanstack/vue-query';
        const client = new QueryClient();
        const options = queryOptions({ queryKey: ['dict'], queryFn: fetchDict, staleTime: 10 });
        client.invalidateQueries({ queryKey: ['dict'] }); client.setQueryData(['dict'], []);
      `,
        '/workspace/src/queries/system/dict.ts'
      )
    ).toEqual([]);
  });

  it('rejects literal keys resolved through local variables and reactive wrappers outside queries', () => {
    const violations = checkQuery(
      `
      import { useQuery as nativeQuery, queryOptions as options } from '@tanstack/vue-query';
      import { computed } from 'vue';
      const key = ['dict'] as const;
      const inline = computed(() => ({ queryKey: key, queryFn: fetchDict }));
      nativeQuery(inline);
      options({ queryKey: ['other'], queryFn: fetchOther });
    `,
      'src/utils/inline-query.ts'
    );
    expect(
      violations.filter((item: { rule: string }) => item.rule === 'query-key-definition')
    ).toHaveLength(2);
    expect(
      violations.every((item: { line: number; column: number }) => item.line > 0 && item.column > 0)
    ).toBe(true);
  });

  it('rejects inline requests, resource overrides and unresolved option sources in views/components', () => {
    expect(
      queryRules(`
        import { useQuery as query } from '@tanstack/vue-query';
        import { dictOptions } from '@/queries/system/dict';
        query({ queryKey: ['dict'], queryFn: fetchDict });
        query({ ...dictOptions(scope, type), enabled: true });
        query({ ...dictOptions(scope, type), staleTime: 10, refetchOnWindowFocus: false });
        query(externalOptions);
      `).filter((rule: string) => rule === 'query-options-source')
    ).toHaveLength(4);
  });

  it('rejects public key helpers used to rebuild options and mixed useQueries maps', () => {
    expect(
      queryRules(`
        import { useQuery, useQueries } from '@tanstack/vue-query';
        import { dictKeys, dictOptions } from '@/queries/system/dict';
        useQuery({ queryKey: dictKeys.all(scope), queryFn: fetchDict });
        useQueries({ queries: types.map(type => ({ ...dictOptions(scope, type), retry: 3 })) });
        useQueries({ queries: [dictOptions(scope, type), unknownFactory()] });
      `).filter((rule: string) => rule === 'query-options-source')
    ).toHaveLength(3);
  });

  it('recognizes QueryClient aliases, local aliases, destructured methods and typed parameters', () => {
    const result = queryRules(
      `
      import { QueryClient as Client, useQueryClient as currentClient } from '@tanstack/vue-query';
      import { queryClient as sharedClient } from '@/queries/client';
      import * as appQueries from '@/queries/client';
      const client = currentClient(); const alias = client;
      const constructed = new Client();
      const { removeQueries: remove } = client;
      alias.invalidateQueries(filters); constructed.cancelQueries(filters); remove(filters);
      sharedClient.setQueryData(key, []);
      const namespacedClient = appQueries.queryClient; namespacedClient.removeQueries(filters);
      function write(client: Client) { client.setQueriesData(filters, []); }
    `,
      'src/utils/cache-write.ts'
    );
    expect(result.filter((rule: string) => rule === 'query-cache-command')).toHaveLength(6);
  });

  it('rejects literal keys on known QueryClient reads and useQuerySelect inline policies', () => {
    expect(
      queryRules(`
        import * as Query from '@tanstack/vue-query';
        import { useQuerySelect as select } from '@zxio/vue-query/ui';
        const client = new Query.QueryClient();
        client.getQueryData(['dict']);
        select(() => ({ queryKey: ['dict'], queryFn: fetchDict }));
      `)
    ).toEqual(expect.arrayContaining(['query-key-definition', 'query-options-source']));
  });
});
