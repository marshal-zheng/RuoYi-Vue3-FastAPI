import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
await page.addInitScript(() => {
  if (
    location.protocol !== 'http:' ||
    sessionStorage.getItem('preferences-seeded')
  )
    return;
  localStorage.setItem(
    'layout-setting',
    JSON.stringify({
      tagsView: true,
      headerVisible: false,
      breadcrumbVisible: false,
      sidebarLogo: false,
      fixedHeader: true,
    }),
  );
  sessionStorage.setItem('preferences-seeded', '1');
});
const ready = async () => {
  await page.waitForFunction(() => !!window.layoutTest);
  await page.waitForTimeout(400);
};
try {
  await page.goto(
    `${process.env.LAYOUT_TEST_URL || 'http://127.0.0.1:4196'}/list`,
  );
  await ready();
  assert.equal(
    await page.locator('.app-tabs').count(),
    0,
    'old enabled cache must migrate to hidden tags',
  );
  assert.equal(
    await page.locator('.app-header').count(),
    0,
    'other saved preferences survive migration',
  );
  const migrated = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('layout-setting')),
  );
  assert.equal(migrated.tagsView, false);
  assert.equal(migrated.layoutVersion, 1);
  assert.equal(migrated.sidebarLogo, false);
  assert.equal(migrated.fixedHeader, true);
  const hidden = await page.locator('.app-main').boundingBox();
  assert.equal(hidden.height, 900, 'hidden tags release their entire height');

  await page.getByRole('button', { name: '打开布局设置' }).click();
  await page
    .locator('.drawer-item')
    .filter({ hasText: '开启 Tags-Views' })
    .locator('.el-switch')
    .click();
  await page.getByRole('button', { name: '保存配置', exact: true }).click();
  await page.waitForFunction(() => {
    const saved = JSON.parse(localStorage.getItem('layout-setting'));
    return saved.tagsView === true && saved.layoutVersion === 1;
  });
  await page.reload();
  await ready();
  assert.equal(
    await page.locator('.app-tabs').count(),
    1,
    'a deliberately saved choice survives reload',
  );
  assert.equal(await page.locator('.app-header').count(), 0);
  const enabled = await page.locator('.app-main').boundingBox();
  const tags = await page.locator('.app-tabs').boundingBox();
  assert(
    Math.abs(enabled.height + tags.height - hidden.height) <= 1,
    'enabled tags reserve their actual height',
  );

  await page.evaluate(() => localStorage.removeItem('layout-setting'));
  await page.reload();
  await ready();
  assert.equal(
    await page.locator('.app-tabs').count(),
    0,
    'fresh storage defaults to hidden tags',
  );
  assert.deepEqual(errors, []);
  const evidence = {
    browser: browser.version(),
    migrated,
    hiddenHeight: hidden.height,
    enabledHeight: enabled.height,
    tagsHeight: tags.height,
    cases: [
      'legacy migration',
      'preserved preferences',
      'explicit enable/save/reload',
      'fresh defaults',
      'height allocation',
    ],
  };
  const output = '../docs/reports/evidence/2026-10-13-zxui-layout-regions';
  await mkdir(output, { recursive: true });
  await writeFile(
    `${output}/preferences.json`,
    `${JSON.stringify(evidence, null, 2)}\n`,
  );
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await browser.close();
}
