import { chromium, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

if (process.env.CODEX_DEPT_QUERY_WRITE !== '1')
  throw new Error('Explicit CODEX_DEPT_QUERY_WRITE=1 required');
const base = process.env.CODEX_DEPT_UI_BASE || 'http://127.0.0.1:3100';
if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(base).hostname))
  throw new Error('Loopback only');
if (!process.env.CODEX_DEPT_PASSWORD) throw new Error('CODEX_DEPT_PASSWORD required');
const mode = process.env.CODEX_DEPT_MODE || 'source';
if (!['source', 'installed'].includes(mode)) throw new Error('Invalid CODEX_DEPT_MODE');
const dir = resolve(
  process.env.CODEX_DEPT_EVIDENCE_DIR ||
    `../docs/reports/evidence/2026-11-02-department-resources/${mode === 'installed' ? 'installed' : 'source-browser'}`
);
await mkdir(dir, { recursive: true });
const marker = `codex_res_${Date.now().toString(36).slice(-7)}`;
const evidence = {
  timestamp: new Date().toISOString(),
  mode,
  marker,
  mocks: false,
  checks: {},
  cleanup: {},
};
const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const context = await browser.newContext({
  viewport: { width: 1600, height: 1100 },
  serviceWorkers: 'block',
});
const page = await context.newPage();
page.setDefaultTimeout(30000);
const requests = [];
const sourceImports = new Set();
const pageErrors = [];
page.on('request', (r) => {
  const u = new URL(r.url());
  if (decodeURIComponent(u.pathname).includes('/@fs/Users/hqz/Downloads/element-plus/'))
    sourceImports.add(u.pathname);
  if (u.pathname.startsWith('/api/system/'))
    requests.push({ method: r.method(), path: u.pathname.slice('/api'.length) });
});
page.on('pageerror', (e) => pageErrors.push(e.message));
const count = (method, path) =>
  requests.filter((r) => r.method === method && r.path === path).length;
let loggedIn = false;
let stage = 'login';
let failure;
try {
  await page.goto(`${base}/login`);
  await page
    .getByPlaceholder('账号', { exact: true })
    .fill(process.env.CODEX_DEPT_USERNAME || 'admin');
  await page.getByPlaceholder('密码', { exact: true }).fill(process.env.CODEX_DEPT_PASSWORD);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'));
  loggedIn = true;
  stage = 'production-route';
  await page.goto(`${base}/system/dept`);
  await expect(page.getByText('展开/折叠', { exact: true })).toBeVisible();
  const id = await page.evaluate(async (marker) => {
    // Test-data setup uses the real API; all edits under assertion use production UI commands.
    const api = await import('/src/api/system/dept.ts');
    const parent = await api.addDept(
      { parentId: 0, deptName: marker, orderNum: 0, status: '0' },
      { silentSuccess: true }
    );
    await api.addDept(
      { parentId: parent.deptId, deptName: `${marker}_child`, orderNum: 0, status: '0' },
      { silentSuccess: true }
    );
    return parent.deptId;
  }, marker);
  evidence.createdId = id;
  await page.reload();
  await page.getByText('展开/折叠', { exact: true }).waitFor();
  const row = page.locator('tr').filter({ hasText: marker }).first();
  await expect(row).toBeVisible();
  const childRow = page
    .locator('tr')
    .filter({ hasText: `${marker}_child` })
    .first();
  await expect(childRow).toBeVisible();
  const beforeToggle = count('GET', '/system/dept/list');
  const toggle = page.getByRole('button', { name: '展开/折叠', exact: true });
  await toggle.click();
  await expect(childRow).toBeHidden();
  await toggle.click();
  await expect(childRow).toBeVisible();
  expect(count('GET', '/system/dept/list')).toBe(beforeToggle);
  evidence.checks.treeExpandCollapse = { collapsed: true, expanded: true, extraReads: 0 };
  await row.getByRole('button', { name: '修改', exact: true }).click();
  const name = page.getByPlaceholder('请输入部门名称', { exact: true });
  await expect(name).toHaveValue(marker);
  const routeName = `${marker}_route`;
  await name.fill(routeName);
  await page
    .getByRole('button', { name: /确.*定/ })
    .last()
    .click();
  await expect(name).toBeHidden();
  await expect(page.locator('tr').filter({ hasText: routeName }).first()).toBeVisible();
  evidence.checks.productionRouteSaveRefresh = true;
  await page.screenshot({ path: `${dir}/production-route.png`, fullPage: true });
  stage = 'two-editor-sharing';
  const treesBefore = count('GET', '/system/user/deptTree');
  await page.goto(`${base}/tests/manual/department-resources/index.html?id=${id}`);
  await page.getByTestId('tree-left').waitFor();
  await expect(page.getByTestId('tree-left')).toContainText(routeName);
  await expect(page.getByTestId('tree-right')).toContainText(routeName);
  const treeRequests = count('GET', '/system/user/deptTree') - treesBefore;
  expect(treeRequests).toBe(1);
  const detailsBefore = count('GET', `/system/dept/${id}`);
  await page.getByTestId('open-both').click();
  await expect(page.getByTestId('opening')).toHaveText('loaded');
  const detailRequests = count('GET', `/system/dept/${id}`) - detailsBefore;
  expect(detailRequests).toBe(1);
  const inputs = page.getByPlaceholder('请输入部门名称', { exact: true });
  await expect(inputs).toHaveCount(2);
  const savedName = `${marker}_saved`;
  const otherDraft = `${marker}_draft`;
  await inputs.nth(0).fill(savedName, { force: true });
  await expect(inputs.nth(1)).toHaveValue(routeName);
  await inputs.nth(1).fill(otherDraft, { force: true });
  await expect(inputs.nth(0)).toHaveValue(savedName);
  await page.screenshot({ path: `${dir}/independent-drafts.png`, fullPage: true });
  evidence.checks.sharedReads = {
    treeSubscribers: 2,
    treeRequests,
    detailEditors: 2,
    detailRequests,
  };
  evidence.checks.independentDraftsBeforeSave = true;
  stage = 'save-with-other-draft';
  const writesBefore = count('PUT', '/system/dept');
  const listsBefore = count('GET', '/system/dept/list');
  const treeBeforeSave = count('GET', '/system/user/deptTree');
  await page
    .getByRole('button', { name: /确.*定/ })
    .nth(0)
    .evaluate((el) => el.click());
  await expect(inputs).toHaveCount(1);
  await expect(inputs).toHaveValue(otherDraft);
  await expect(page.getByTestId('tree-left')).toContainText(savedName);
  await expect(page.getByTestId('tree-right')).toContainText(savedName);
  await expect(page.locator('tr').filter({ hasText: savedName }).first()).toBeVisible();
  expect(count('PUT', '/system/dept') - writesBefore).toBe(1);
  expect(count('GET', '/system/dept/list')).toBeGreaterThan(listsBefore);
  expect(count('GET', '/system/user/deptTree')).toBeGreaterThan(treeBeforeSave);
  const persisted = await page.evaluate(
    async (id) => (await (await import('/src/api/system/dept.ts')).getDept(id)).deptName,
    id
  );
  expect(persisted).toBe(savedName);
  evidence.checks.saveRefresh = {
    writes: 1,
    listUpdated: true,
    bothTreesUpdated: true,
    otherDraftPreserved: true,
    realHttpPersisted: true,
  };
  await page.screenshot({ path: `${dir}/saved-with-other-draft.png`, fullPage: true });
  await page
    .getByRole('button', { name: /取.*消/ })
    .last()
    .evaluate((el) => el.click());
  await expect(inputs).toHaveCount(0);
  await page.getByTestId('open-right').click();
  await expect(inputs).toHaveValue(savedName);
  evidence.checks.reopenLoadsSavedSnapshot = true;
  expect(pageErrors).toEqual([]);
  if (mode === 'installed') expect(sourceImports.size).toBe(0);
  evidence.checks.runtimeMode = { mode, zxuiSourceImports: sourceImports.size };
  evidence.passed = true;
} catch (error) {
  failure = error;
  evidence.passed = false;
  evidence.failure = { stage, message: String(error.message).slice(0, 1500) };
  await page.screenshot({ path: `${dir}/failure.png`, fullPage: true }).catch(() => {});
} finally {
  if (loggedIn) {
    try {
      // A fresh route load also recovers from a fixture startup/navigation failure.
      await page.goto(`${base}/system/dept`);
      await page.getByText('展开/折叠', { exact: true }).waitFor();
      evidence.cleanup = await page.evaluate(async (marker) => {
        const api = await import('/src/api/system/dept.ts');
        const rows = (await api.listDept({ deptName: marker })).items.filter((r) =>
          r.deptName?.startsWith(marker)
        );
        for (const row of rows.sort(
          (a, b) => String(b.ancestors ?? '').length - String(a.ancestors ?? '').length
        )) {
          await api.delDept(row.deptId, { silentSuccess: true });
        }
        const absent = !(await api.listDept({ deptName: marker })).items.some((r) =>
          r.deptName?.startsWith(marker)
        );
        return { deleted: rows.length, verifiedAbsent: absent };
      }, marker);
      expect(evidence.cleanup.verifiedAbsent).toBe(true);
      await page.evaluate(async () => {
        await (
          await import('/src/api/login.ts')
        ).logout({ silentSuccess: true, silentError: true });
        (await import('/src/utils/auth.ts')).clearSecurityTokens();
      });
      evidence.ownSessionEnded = true;
    } catch (error) {
      evidence.cleanup.failure = String(error.message).slice(0, 500);
      failure ||= error;
      evidence.passed = false;
    }
  }
  evidence.pageErrors = pageErrors;
  evidence.requestCounts = requests.reduce((a, r) => {
    const key = `${r.method} ${r.path.replace(/\/\d+(?=\/|$)/g, '/:id')}`;
    a[key] = (a[key] || 0) + 1;
    return a;
  }, {});
  await writeFile(`${dir}/browser.json`, `${JSON.stringify(evidence, null, 2)}\n`, { mode: 0o600 });
  await browser.close();
}
if (failure) throw new Error(`${stage}: ${failure.message}`);
process.stdout.write(
  JSON.stringify({ passed: evidence.passed, checks: evidence.checks, cleanup: evidence.cleanup }) +
    '\n'
);
