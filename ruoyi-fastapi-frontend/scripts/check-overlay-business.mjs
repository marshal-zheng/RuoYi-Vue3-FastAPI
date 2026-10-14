import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '@playwright/test';

const output =
  process.env.OVERLAY_BUSINESS_EVIDENCE_DIR ||
  '../docs/reports/evidence/2026-10-13-zxui-overlay-layout/business';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
const writes = [];
page.on('pageerror', (error) => errors.push(error.message));
page.on('request', (request) => {
  if (
    /\/system\/(role|user)(?:\/|$)/.test(request.url()) &&
    !['GET', 'HEAD'].includes(request.method())
  )
    writes.push({ method: request.method(), url: request.url() });
});
const evidence = { browser: browser.version(), cases: [] };
const measure = (panel) => {
  const body = panel.querySelector('.el-drawer__body, .el-dialog__body');
  const header = panel.querySelector('.el-drawer__header, .el-dialog__header');
  const footer = panel.querySelector('.el-drawer__footer, .el-dialog__footer');
  const content = panel.querySelector('[data-zx-overlay-content]');
  const form = content.querySelector('form');
  const rect = (node) => {
    const r = node.getBoundingClientRect();
    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, height: r.height };
  };
  const padding = (node) => {
    const css = getComputedStyle(node);
    return ['paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft'].map((key) =>
      Number.parseFloat(css[key])
    );
  };
  const viewport = rect(body),
    clientLeft = viewport.left + body.clientLeft;
  return {
    themeId: panel.closest('[data-zx-theme]')?.getAttribute('data-zx-theme'),
    variant: panel.closest('[data-zx-variant]')?.getAttribute('data-zx-variant'),
    title: header.innerText,
    panel: rect(panel),
    viewport,
    content: rect(content),
    form: rect(form),
    padding: padding(content),
    headerPadding: padding(header),
    footerPadding: padding(footer),
    clientLeft,
    clientRight: clientLeft + body.clientWidth,
    divider: getComputedStyle(header, '::after').borderBottomWidth,
    overflow: getComputedStyle(body).overflowY,
    footer: rect(footer),
  };
};
try {
  await mkdir(output, { recursive: true });
  await page.goto('http://127.0.0.1/');
  await page
    .getByRole('textbox', { name: '账号', exact: true })
    .fill(process.env.OVERLAY_TEST_USERNAME || 'admin');
  await page.locator('input[type=password]').fill(process.env.OVERLAY_TEST_PASSWORD || 'admin123');
  await page.getByTestId('demo-login-submit').click();
  await page.waitForURL((url) => !url.pathname.includes('login'));
  for (const [themeId, mode] of [
    ['default', 'light'],
    ['army-pine', 'dark'],
  ]) {
    for (const [route, kind, action] of [
      ['/system/role', 'drawer', '新增'],
      ['/system/user', 'dialog', '新增用户'],
    ]) {
      await page.goto(`http://127.0.0.1${route}`);
      await page.getByTestId('zx-theme-preset-switch').click();
      await page.locator(`[data-zx-theme-preset="${themeId}"]:visible`).click();
      const modeButton = page.getByTestId('zx-theme-mode-switch');
      if ((await modeButton.getAttribute('aria-pressed')) !== String(mode === 'dark'))
        await modeButton.click();
      await page.waitForFunction(
        (id) => !!document.querySelector(`[data-zx-theme="${id}"]`),
        themeId
      );

      await page.getByRole('button', { name: action, exact: true }).click();
      const panel = page.locator(`.zx-${kind}-container.el-${kind}:visible`);
      await panel.waitFor();
      await page.waitForTimeout(600);
      const g = await panel.evaluate(measure);
      assert.equal(g.themeId, themeId, 'business overlay belongs to selected theme');
      assert(g.variant.includes(mode), `business overlay uses selected mode: ${g.variant}`);
      assert(
        g.padding.every((value) => value > 0),
        'all four content insets have positive theme-derived padding'
      );
      assert(
        Math.abs(g.form.top - g.viewport.top - g.padding[0]) <= 1,
        'actual business form respects block-start inset'
      );
      assert(
        Math.abs(g.form.left - g.clientLeft - g.padding[3]) <= 1,
        'actual business form respects inline-start inset'
      );
      assert(
        Math.abs(g.clientRight - g.form.right - g.padding[1]) <= 1,
        'actual business form respects inline-end inset'
      );
      assert.equal(g.headerPadding[3], g.padding[3]);
      assert.equal(g.footerPadding[1], g.padding[1]);
      assert.equal(Number.parseFloat(g.divider), 1);
      evidence.cases.push({ themeId, mode, route, kind, geometry: g });
      await panel.screenshot({ path: `${output}/${themeId}-${kind}-desktop.png` });
      await page.setViewportSize({ width: 390, height: 844 });
      await page.waitForTimeout(300);
      const mobile = await panel.evaluate(measure);
      assert(mobile.padding.every((value) => value > 0));
      assert(Math.abs(mobile.form.left - mobile.clientLeft - mobile.padding[3]) <= 1);
      assert.equal(mobile.headerPadding[3], mobile.padding[3]);
      assert.equal(mobile.footerPadding[1], mobile.padding[1]);
      evidence.cases.push({ themeId, mode, route, kind, viewport: 'mobile', geometry: mobile });
      await panel.screenshot({ path: `${output}/${themeId}-${kind}-mobile.png` });
      await panel.locator('.el-drawer__close-btn, .el-dialog__headerbtn').click();
      await panel.waitFor({ state: 'hidden' });
      await page.setViewportSize({ width: 1440, height: 1000 });
    }
  }
  assert.deepEqual(writes, [], 'verification never submits business records');
  assert.deepEqual(errors, []);
  evidence.pageErrors = errors;
  evidence.businessWrites = writes;
  await writeFile(`${output}/browser.json`, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(
    JSON.stringify({
      cases: evidence.cases.length,
      pageErrors: errors.length,
      businessWrites: writes.length,
    })
  );
} finally {
  await browser.close();
}
