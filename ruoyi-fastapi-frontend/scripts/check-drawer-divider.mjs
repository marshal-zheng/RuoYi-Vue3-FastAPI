import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
await page.addInitScript(() => {
  const all = [];
  const counts = {
    resizeCreated: 0,
    intersectionCreated: 0,
    globalListeners: 0,
    totalBounds: 0,
    ownedBounds: 0,
    ownedRaf: 0,
  };
  for (const kind of ['ResizeObserver', 'IntersectionObserver']) {
    const Native = window[kind];
    window[kind] = class extends Native {
      constructor(callback, options) {
        super(callback, options);
        this.targets = new Set();
        all.push(this);
        counts[kind === 'ResizeObserver' ? 'resizeCreated' : 'intersectionCreated']++;
      }
      observe(target, options) {
        this.targets.add(target);
        return super.observe(target, options);
      }
      unobserve(target) {
        this.targets.delete(target);
        return super.unobserve(target);
      }
      disconnect() {
        this.targets.clear();
        return super.disconnect();
      }
    };
  }
  const owned = () => /drawer\/src|_shared\/use-modal/.test(new Error().stack || '');
  const rect = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function (...args) {
    counts.totalBounds++;
    if (owned()) counts.ownedBounds++;
    return rect.apply(this, args);
  };
  const raf = window.requestAnimationFrame;
  window.requestAnimationFrame = function (fn) {
    if (owned()) counts.ownedRaf++;
    return raf.call(this, fn);
  };
  const registrations = new Map([
    [window, new Map()],
    [document, new Map()],
  ]);
  const eventKey = (type, options) =>
    `${type}:${typeof options === 'boolean' ? options : !!options?.capture}`;
  const add = EventTarget.prototype.addEventListener;
  const remove = EventTarget.prototype.removeEventListener;
  EventTarget.prototype.addEventListener = function (...args) {
    if (this === window || this === document) {
      counts.globalListeners++;
      const events = registrations.get(this);
      const key = eventKey(args[0], args[2]);
      if (!events.has(key)) events.set(key, new Set());
      events.get(key).add(args[1]);
    }
    return add.apply(this, args);
  };
  EventTarget.prototype.removeEventListener = function (...args) {
    registrations.get(this)?.get(eventKey(args[0], args[2]))?.delete(args[1]);
    return remove.apply(this, args);
  };
  window.dividerResources = () => ({
    ...counts,
    activeGlobalListeners: [...registrations.values()].reduce(
      (n, events) => n + [...events.values()].reduce((sum, listeners) => sum + listeners.size, 0),
      0
    ),
    activeTargets: all.reduce((n, o) => n + [...o.targets].filter((t) => t.isConnected).length, 0),
  });
});
const evidence = {
  browser: browser.version(),
  cases: [],
  resources: {},
  performance: {},
};
const settle = async () => {
  await page.evaluate(
    () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
  );
};
const configure = async (values) => {
  await page.evaluate((v) => window.dividerTest.configure(v), values);
  await settle();
};
const open = async () => {
  await page.evaluate(() => window.dividerTest.open());
  await page.waitForSelector('.zx-drawer-container.el-drawer');
  await page.waitForTimeout(400);
};
const close = async () => {
  await page.evaluate(() => window.dividerTest.close());
  await page.waitForSelector('.zx-drawer-container.el-drawer', {
    state: 'hidden',
  });
  await page.waitForTimeout(150);
};
const snapshot = async () =>
  page.locator('.zx-drawer-container.el-drawer').evaluate((el) => {
    const region = (node, edge) => {
      if (!node) return null;
      const r = node.getBoundingClientRect();
      const s = getComputedStyle(node);
      const paint = node.classList.contains('el-drawer__header')
        ? getComputedStyle(node, '::after')
        : node.classList.contains('el-drawer__footer')
          ? getComputedStyle(node, '::before')
          : s;
      return {
        top: r.top,
        bottom: r.bottom,
        width: r.width,
        height: r.height,
        display: s.display,
        padding: s.padding,
        border: Number.parseFloat(paint.borderBottomWidth),
        color: paint.borderBottomColor,
        scrollHeight: node.scrollHeight,
        clientHeight: node.clientHeight,
        scrollTop: node.scrollTop,
      };
    };
    return {
      root: region(el, 'borderTopWidth'),
      header: region(el.querySelector('.el-drawer__header'), 'borderBottomWidth'),
      footer: region(el.querySelector('.el-drawer__footer'), 'borderTopWidth'),
      body: region(el.querySelector('.el-drawer__body'), 'borderTopWidth'),
      enabled: el.classList.contains('zx-overlay-layout--divider'),
      leaked: el.hasAttribute('divider'),
    };
  });
const near = (a, b, message) => assert(Math.abs(a - b) <= 2, `${message}: ${a} / ${b}`);
const regionGeometry = (g) => {
  assert(g.body.height > 100, 'body receives usable remaining height');
  near(
    g.body.top,
    !g.header || g.header.display === 'none' ? g.root.top : g.header.bottom,
    'body starts after header'
  );
  near(g.body.bottom, g.footer ? g.footer.top : g.root.bottom, 'body ends before footer');
  assert(g.root.scrollHeight <= g.root.clientHeight + 2, 'outer drawer does not own scrolling');
};
try {
  await page.goto(process.env.DRAWER_TEST_URL || 'http://127.0.0.1:4199');
  await page.waitForFunction(() => !!window.dividerTest);
  const policies = [
    {
      name: 'default',
      values: { upper: {}, near: {}, local: undefined },
      enabled: false,
    },
    {
      name: 'upper',
      values: { upper: { divider: true }, near: {}, local: undefined },
      enabled: true,
    },
    {
      name: 'nearest off',
      values: {
        upper: { divider: true },
        near: { divider: false },
        local: undefined,
      },
      enabled: false,
    },
    {
      name: 'explicit on',
      values: {
        upper: { divider: false },
        near: { divider: false },
        local: true,
      },
      enabled: true,
    },
    {
      name: 'explicit off',
      values: {
        upper: { divider: true },
        near: { divider: true },
        local: false,
      },
      enabled: false,
    },
    {
      name: 'restore inheritance',
      values: { upper: {}, near: { divider: true }, local: undefined },
      enabled: true,
    },
  ];
  for (const mode of ['modal', 'inline', 'push']) {
    await configure({
      mode,
      footer: true,
      noTitle: false,
      customFooter: false,
      long: true,
      style: {},
    });
    await open();
    let padding;
    for (const policy of policies) {
      await configure(policy.values);
      const g = await snapshot();
      assert.equal(g.enabled, policy.enabled);
      assert.equal(g.header.border, policy.enabled ? 1 : 0);
      assert.equal(g.footer.border, policy.enabled ? 1 : 0);
      assert.equal(g.leaked, false);
      regionGeometry(g);
      assert(g.body.scrollHeight > g.body.clientHeight + 500);
      const currentPadding = {
        header: g.header.padding,
        body: g.body.padding,
        footer: g.footer.padding,
      };
      if (padding)
        assert.deepEqual(currentPadding, padding, 'divider does not change section padding');
      padding = currentPadding;
      evidence.cases.push({ mode, policy: policy.name, geometry: g });
    }
    await close();
  }
  for (const placement of ['left', 'top', 'bottom']) {
    await configure({ mode: 'modal', placement, local: false });
    await open();
    for (const enabled of [false, true]) {
      await configure({ local: enabled });
      const geometry = await snapshot();
      regionGeometry(geometry);
      assert.equal(geometry.header.border, enabled ? 1 : 0);
      evidence.cases.push({ placement, enabled, geometry });
    }
    await close();
  }
  await configure({ placement: 'right' });
  await configure({ mode: 'modal', local: true, customFooter: true });
  await open();
  assert.equal(await page.getByRole('button', { name: 'Custom actions' }).count(), 1);
  regionGeometry(await snapshot());
  await configure({ footer: false });
  let g = await snapshot();
  assert.equal(g.footer, null);
  regionGeometry(g);
  await configure({ footer: true, noTitle: true });
  g = await snapshot();
  assert.equal(
    await page
      .locator('.zx-drawer-container__header-container')
      .evaluate((el) => getComputedStyle(el).display),
    'none'
  );
  regionGeometry(g);
  await configure({ noTitle: false, withHeader: false });
  g = await snapshot();
  assert.equal(g.header, null);
  regionGeometry(g);
  await configure({ withHeader: true });
  await configure({ noTitle: false, long: false });
  g = await snapshot();
  assert(g.body.scrollHeight <= g.body.clientHeight + 1, 'short body has no spurious scrolling');
  await configure({ long: true });
  await page.locator('.el-drawer__body').evaluate((el) => {
    el.scrollTop = 300;
  });
  await configure({ local: false });
  g = await snapshot();
  assert.equal(g.body.scrollTop, 300, 'divider toggle preserves scroll position');
  await page.locator('.zx-drawer-container__fullscreen-btn').click();
  await page.waitForTimeout(400);
  g = await snapshot();
  near(g.root.width, 1440, 'fullscreen width');
  regionGeometry(g);
  await page.locator('.zx-drawer-container__fullscreen-btn').click();
  await page.waitForTimeout(400);
  const handle = await page.locator('.zx-drawer-container__handle').boundingBox();
  const widthBeforeResize = (await snapshot()).root.width;
  await page.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2);
  await page.mouse.down();
  await page.mouse.move(handle.x + handle.width / 2 - 100, handle.y + handle.height / 2, {
    steps: 5,
  });
  await page.mouse.up();
  await page.waitForTimeout(200);
  g = await snapshot();
  near(g.root.width, widthBeforeResize + 100, 'resize handle retains its original behavior');
  regionGeometry(g);
  await page.locator('.zx-drawer-container__handle').dblclick();
  await page.waitForTimeout(300);
  near((await snapshot()).root.width, widthBeforeResize, 'resize reset');
  await page.setViewportSize({ width: 390, height: 800 });
  await page.waitForTimeout(400);
  g = await snapshot();
  near(g.root.width, 390, 'mobile fallback width');
  regionGeometry(g);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(400);
  await page.evaluate(() => window.dividerTest.updateDivider(true));
  await settle();
  assert((await snapshot()).enabled);
  await page.evaluate(() => window.dividerTest.updateDivider(false));
  await settle();
  assert(!(await snapshot()).enabled);
  await page.evaluate(() => window.dividerTest.updateDivider(undefined));
  await settle();
  assert((await snapshot()).enabled, 'Hook undefined restores enabled nearest Provider');

  for (const [themeId, themeMode] of [
    ['default', 'light'],
    ['army-pine', 'dark'],
  ]) {
    await page.evaluate(([id, mode]) => window.dividerTest.theme(id, mode), [themeId, themeMode]);
    await page.waitForTimeout(500);
    await configure({ local: true, style: {} });
    const drawerColor = (await snapshot()).header.color;
    await close();
    await page.evaluate(() => window.dividerTest.dialog(true));
    await page.waitForSelector('.zx-dialog-container.el-dialog');
    await page.waitForTimeout(400);
    const dialogColor = await page
      .locator('.zx-dialog-container .el-dialog__header')
      .evaluate((el) => getComputedStyle(el, '::after').borderBottomColor);
    assert.equal(drawerColor, dialogColor, 'Dialog and Drawer use the same themed fallback');
    evidence.cases.push({ themeId, themeMode, drawerColor, dialogColor });
    await page.evaluate(() => window.dividerTest.dialog(false));
    await page.waitForSelector('.zx-dialog-container.el-dialog', {
      state: 'hidden',
    });
    await open();
  }
  await configure({
    local: true,
    style: { '--zx-overlay-divider': '2px solid rgb(22, 50, 70)' },
  });
  g = await snapshot();
  assert.equal(g.header.border, 2);
  assert.equal(g.footer.border, 2);
  regionGeometry(g);
  await configure({
    style: {
      '--zx-overlay-divider': '2px solid rgb(22, 50, 70)',
      '--zx-overlay-header-divider': '3px solid rgb(80, 100, 120)',
      '--zx-overlay-footer-divider': '4px solid rgb(100, 120, 140)',
    },
  });
  g = await snapshot();
  assert.equal(g.header.border, 3);
  assert.equal(g.footer.border, 4);
  regionGeometry(g);
  await configure({ local: false });
  g = await snapshot();
  assert.equal(g.header.border, 0);
  assert.equal(g.footer.border, 0);
  await configure({ style: {}, local: false, customFooter: false });
  await page.waitForTimeout(800);
  const before = await page.evaluate(() => window.dividerResources());
  for (let i = 0; i < 40; i++) await configure({ local: !!(i & 1) });
  await page.waitForTimeout(200);
  const after = await page.evaluate(() => window.dividerResources());
  assert.equal(after.resizeCreated, before.resizeCreated);
  assert.equal(after.intersectionCreated, before.intersectionCreated);
  assert.equal(after.globalListeners, before.globalListeners);
  assert.equal(after.activeGlobalListeners, before.activeGlobalListeners);
  assert.equal(after.activeTargets, before.activeTargets);
  assert.equal(after.totalBounds, before.totalBounds);
  assert.equal(after.ownedBounds, before.ownedBounds);
  assert.equal(after.ownedRaf, before.ownedRaf);
  evidence.resources = { before, after };
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Performance.enable');
  const metrics = async () =>
    Object.fromEntries(
      (await cdp.send('Performance.getMetrics')).metrics.map(({ name, value }) => [name, value])
    );
  const idleBefore = await metrics();
  await page.waitForTimeout(500);
  const idleAfter = await metrics();
  assert.equal(idleAfter.LayoutCount, idleBefore.LayoutCount, 'no idle layout loop');
  const busyBefore = await metrics();
  for (let i = 0; i < 40; i++) await configure({ local: !!(i & 1) });
  const busyAfter = await metrics();
  evidence.performance = {
    idleLayoutCount: idleAfter.LayoutCount - idleBefore.LayoutCount,
    toggles: 40,
    layoutCount: busyAfter.LayoutCount - busyBefore.LayoutCount,
    layoutDurationMs: (busyAfter.LayoutDuration - busyBefore.LayoutDuration) * 1000,
  };
  assert.deepEqual(errors, []);
  await close();
  const closedBefore = await page.evaluate(() => window.dividerResources());
  for (let i = 0; i < 5; i++) {
    await open();
    await close();
  }
  const closedAfter = await page.evaluate(() => window.dividerResources());
  assert.equal(
    closedAfter.activeTargets,
    closedBefore.activeTargets,
    'repeated open/close releases observer targets'
  );
  assert.equal(
    closedAfter.activeGlobalListeners,
    closedBefore.activeGlobalListeners,
    'repeated open/close releases global listeners'
  );
  evidence.resources.closedCycles = {
    before: closedBefore,
    after: closedAfter,
    cycles: 5,
  };
  await open();
  await page.locator('.el-drawer__body').evaluate((el) => {
    el.scrollTop = 0;
  });
  const output =
    process.env.DRAWER_EVIDENCE_DIR || '../docs/reports/evidence/2026-10-13-zxui-drawer-divider';
  await mkdir(output, { recursive: true });
  await page.screenshot({ path: `${output}/enabled.png` });
  await configure({ local: false });
  await page.screenshot({ path: `${output}/disabled.png` });
  assert.deepEqual(errors, []);
  await writeFile(`${output}/browser.json`, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(
    JSON.stringify(
      {
        matrixCases: evidence.cases.length,
        resources: evidence.resources,
        performance: evidence.performance,
      },
      null,
      2
    )
  );
} finally {
  await browser.close();
}
