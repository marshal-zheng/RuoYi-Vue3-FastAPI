import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
import { createThemeRuntimeDeployment, emitThemeDeployment } from '@zxio/theme-compiler/deployment';
import { ZX_THEME_PACKAGE_CHOICES } from '../../../src/theme/zx-theme-packages';
import { formConf } from '../../../src/utils/generator/config';
import { makeUpHtml, vueScript, vueTemplate } from '../../../src/utils/generator/html';
import { makeUpJs } from '../../../src/utils/generator/js';
const packages = ZX_THEME_PACKAGE_CHOICES.map(({ packageName }) => packageName);
const output = emitThemeDeployment({
  packages,
  resolveFrom: resolve('package.json'),
  outputDir: resolve('tests/fixtures/ui-convergence/public/zx-theme-assets'),
  assetBasePath: 'zx-theme-assets',
});
if (!output.ok) throw new Error(JSON.stringify(output.diagnostics));
const require = createRequire(resolve('package.json'));
const runtime = createThemeRuntimeDeployment({
  deployment: output.value.deployment,
  manifestSources: packages.map((name) => readFileSync(require.resolve(`${name}/manifest.json`))),
});
if (!runtime.ok) throw new Error(JSON.stringify(runtime.diagnostics));
writeFileSync('tests/fixtures/ui-convergence/theme-deployment.json', JSON.stringify(runtime.value));
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
writeFileSync(
  'tests/fixtures/ui-convergence/GeneratedForm.vue',
  vueTemplate(makeUpHtml(conf, 'dialog')) + vueScript(makeUpJs(conf, 'dialog'))
);

writeFileSync(
  'tests/fixtures/ui-convergence/public/fixture.svg',
  '<svg xmlns="http://www.w3.org/2000/svg" width="160" height="100"><rect width="160" height="100" fill="#d9e8f4"/><text x="20" y="55" font-size="18">Fixture image</text></svg>'
);

// Keep the actual source template/handlers; expose only otherwise unreachable branches for tests.
const versionSource = readFileSync('src/views/project/components/VersionList.vue', 'utf8');
const versionFixture = versionSource
  .replace(/from '\.\//g, "from '@/views/project/components/")
  .replace(
    '</script>',
    `
defineExpose({
  open: handleAddVersion,
  openEdit: (data) => versionDialog.open(data),
  close: () => { editVersionDialog.value = false; },
});
</script>`
  );
writeFileSync('tests/fixtures/ui-convergence/VersionListFixture.vue', versionFixture);
