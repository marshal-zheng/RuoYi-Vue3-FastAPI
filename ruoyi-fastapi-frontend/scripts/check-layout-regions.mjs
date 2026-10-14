import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from '@playwright/test';

const url = process.env.LAYOUT_TEST_URL || 'http://127.0.0.1:4196';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
await page.addInitScript(() => {
  const owner = (stack = '') =>
    /content-wrap\/src\/content-wrap|page-layout\/src\/page-layout/.test(stack);
  const resources = {
    observers: 0,
    observerCallbacks: 0,
    ownedObservers: 0,
    ownedReads: 0,
    ownedRaf: 0,
    ownedListeners: 0,
  };
  const all = [];
  const NativeObserver = window.ResizeObserver;
  window.ResizeObserver = class extends NativeObserver {
    constructor(callback) {
      super((...args) => {
        resources.observerCallbacks++;
        callback(...args);
      });
      this.targets = new Set();
      all.push(this);
      resources.observers++;
      if (owner(new Error().stack)) resources.ownedObservers++;
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
  const rect = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function (...args) {
    if (owner(new Error().stack)) resources.ownedReads++;
    return rect.apply(this, args);
  };
  const raf = window.requestAnimationFrame;
  window.requestAnimationFrame = function (callback) {
    if (owner(new Error().stack)) resources.ownedRaf++;
    return raf.call(this, callback);
  };
  const add = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function (...args) {
    if ((this === window || this === document) && owner(new Error().stack))
      resources.ownedListeners++;
    return add.apply(this, args);
  };
  window.layoutResources = () => ({
    ...resources,
    activeObservers: all.filter((o) =>
      [...o.targets].some((t) => t.isConnected),
    ).length,
    activeTargets: all.reduce(
      (n, o) => n + [...o.targets].filter((t) => t.isConnected).length,
      0,
    ),
    detachedTargets: all.reduce(
      (n, o) => n + [...o.targets].filter((t) => !t.isConnected).length,
      0,
    ),
  });
});
const evidence = { matrix: [], special: [], resources: {}, performance: {} };
const settle = async () => {
  await page.evaluate(
    () =>
      new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))),
  );
};
const configure = async (values) => {
  await page.evaluate((v) => window.layoutTest.configure(v), values);
  await settle();
};
const navigate = async (kind) => {
  await page.evaluate((v) => window.layoutTest.page(v), kind);
  await page.waitForTimeout(400);
  await settle();
};
const geometry = async () =>
  page.evaluate(() => {
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        top: r.top,
        bottom: r.bottom,
        left: r.left,
        width: r.width,
        height: r.height,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        scrollTop: el.scrollTop,
      };
    };
    const main = document.querySelector('.app-main');
    return {
      viewport: innerHeight,
      header: rect(document.querySelector('.app-header')),
      tags: rect(document.querySelector('.app-tabs')),
      main: rect(main),
      body: rect(main?.querySelector(':scope > .zx-page-layout__body')),
      breadcrumb: !!document.querySelector('.breadcrumb-container'),
      documentHeight: document.documentElement.scrollHeight,
      list: rect(document.querySelector('[data-testid="fixture-list"]')),
      listScroll: rect(
        document.querySelector('.zx-grid-list__table .el-scrollbar__wrap'),
      ),
      detail: rect(document.querySelector('[data-testid="fixture-detail"]')),
      mixed: rect(document.querySelector('.content-detail-wrap')),
      graph: rect(document.querySelector('.xflow-graph-container')),
      graphSvg: rect(document.querySelector('.xflow-graph-container > svg')),
      nested: rect(document.querySelector('[data-testid="nested-region"]')),
      nestedCanvas: rect(
        document.querySelector('[data-testid="nested-canvas"]'),
      ),
      iframe: rect(document.querySelector('.inner-link iframe')),
      recovery: !!document.querySelector('.layout-recovery'),
    };
  });
const near = (actual, expected, message) =>
  assert(
    Math.abs(actual - expected) <= 2,
    `${message}: ${actual} vs ${expected}`,
  );
try {
  await page.goto(`${url}/list`);
  await page.waitForFunction(() => !!window.layoutTest);
  await page.waitForTimeout(500);
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 1024, height: 768 },
    { width: 390, height: 800 },
  ]) {
    await page.setViewportSize(viewport);
    for (const kind of ['list', 'detail', 'mixed', 'editor']) {
      await navigate(kind);
      for (let mask = 0; mask < 8; mask++) {
        const config = {
          headerVisible: !!(mask & 1),
          tagsView: !!(mask & 2),
          breadcrumbVisible: !!(mask & 4),
          footerVisible: false,
        };
        await configure(config);
        // X6 and Element Plus retain their existing asynchronous resize mechanisms.
        await page.waitForTimeout(80);
        const g = await geometry();
        assert.equal(!!g.header, config.headerVisible);
        assert.equal(!!g.tags, config.tagsView);
        assert.equal(
          g.breadcrumb,
          config.headerVisible && config.breadcrumbVisible,
        );
        near(
          g.main.top,
          (g.header?.height || 0) + (g.tags?.height || 0),
          `${kind} chrome allocation`,
        );
        near(g.main.bottom, viewport.height, `${kind} main bottom`);
        near(
          g.documentHeight,
          viewport.height,
          `${kind} document does not own scrolling`,
        );
        assert.equal(g.recovery, !config.headerVisible);
        if (kind === 'list') {
          near(g.list.bottom, g.body.bottom, 'filled list bottom');
          assert(g.list.height > 200, 'list has usable remaining height');
          assert(
            g.body.scrollHeight <= g.body.clientHeight + 2,
            'list does not force outer scrolling',
          );
          const scrollable = await page.evaluate(() =>
            [
              ...document.querySelectorAll('.zx-grid-list .el-scrollbar__wrap'),
            ].some((el) => el.scrollHeight > el.clientHeight + 100),
          );
          assert(scrollable, 'long list scrolls inside its table');
        } else if (kind === 'detail') {
          assert(
            g.body.scrollHeight > g.body.clientHeight + 500,
            'natural detail scrolls in host',
          );
          assert(
            g.detail.height >= 1600,
            'natural detail retains content height',
          );
        } else if (kind === 'mixed') {
          near(g.mixed.bottom, g.body.bottom, 'mixed detail bottom');
          assert(
            g.body.scrollHeight <= g.body.clientHeight + 2,
            'bounded details delegate scrolling',
          );
        } else {
          assert(
            g.graph?.height > 200,
            'real X6 graph receives remaining space',
          );
          const svg = await page
            .locator('.xflow-graph-container svg')
            .first()
            .boundingBox();
          near(svg.height, g.graph.height, 'X6 resize follows region height');
          assert(
            g.body.scrollHeight <= g.body.clientHeight + 2,
            'editor does not force outer scrolling',
          );
        }
        evidence.matrix.push({
          viewport,
          kind,
          config,
          main: g.main,
          body: g.body,
        });
      }
    }
  }
  await page.setViewportSize({ width: 1280, height: 800 });
  await configure({
    headerVisible: true,
    tagsView: true,
    breadcrumbVisible: true,
  });
  await navigate('nested');
  let g = await geometry();
  near(
    g.nestedCanvas.height,
    g.body.height - 90,
    'nested region subtracts summary/tools once',
  );
  evidence.special.push({ kind: 'nested', geometry: g });
  await navigate('short-detail');
  g = await geometry();
  assert(
    g.detail.height < g.body.height / 2,
    'short detail stays content-sized',
  );
  assert(
    g.body.scrollHeight <= g.body.clientHeight + 2,
    'short detail has no unnecessary scroll',
  );
  await navigate('sticky');
  const sticky = async () =>
    page.evaluate(() => ({
      footer: document
        .querySelector('.zx-content-wrap__footer')
        .getBoundingClientRect().bottom,
      body: document
        .querySelector('.app-main > .zx-page-layout__body')
        .getBoundingClientRect().bottom,
    }));
  let fixed = await sticky();
  near(fixed.footer, fixed.body, 'sticky actions initial');
  await page.evaluate(() => {
    document.querySelector('.app-main > .zx-page-layout__body').scrollTop = 500;
  });
  await settle();
  fixed = await sticky();
  near(fixed.footer, fixed.body, 'sticky actions after scrolling');
  await navigate('sticky-detail');
  await page.evaluate(() => {
    document.querySelector('.app-main > .zx-page-layout__body').scrollTop = 500;
  });
  await settle();
  const summary = await page.evaluate(() => ({
    top: document
      .querySelector('.content-detail-wrap .zx-page-layout__header')
      .getBoundingClientRect().top,
    body: document
      .querySelector('.app-main > .zx-page-layout__body')
      .getBoundingClientRect().top,
  }));
  near(summary.top, summary.body, 'natural detail sticky summary');
  await navigate('iframe');
  g = await geometry();
  near(g.iframe.bottom, g.body.bottom, 'iframe fills remainder');
  await configure({ footerVisible: true });
  g = await geometry();
  assert(g.body.bottom < g.main.bottom, 'copyright reserves content space');
  near(g.iframe.bottom, g.body.bottom, 'iframe follows copyright');
  await configure({ footerVisible: false });
  await navigate('route-override');
  g = await geometry();
  assert(!g.header && !g.tags && !g.breadcrumb, 'route override applies');
  await navigate('short-detail');
  g = await geometry();
  assert(
    g.header && g.tags && g.breadcrumb,
    'saved preferences restored after override',
  );
  await page.setViewportSize({ width: 390, height: 800 });
  await page.evaluate(() => window.layoutTest.appStore.toggleSideBar());
  await page.waitForTimeout(350);
  const mobile = await page
    .locator('.sidebar-container')
    .evaluate((el) => ({
      position: getComputedStyle(el).position,
      top: el.getBoundingClientRect().top,
      height: el.getBoundingClientRect().height,
    }));
  assert.equal(mobile.position, 'fixed');
  near(mobile.top, 0, 'mobile drawer top');
  near(mobile.height, 800, 'mobile drawer height');
  await page.setViewportSize({ width: 1440, height: 900 });
  await navigate('form-builder');
  await page.waitForSelector('.right-board');
  const form = await page
    .locator('.right-board')
    .evaluate((el) => ({
      height: el.clientHeight,
      tabs: el.querySelector('.center-tabs').getBoundingClientRect().height,
      field: el.querySelector('.field-box').getBoundingClientRect().height,
    }));
  assert(
    form.tabs < 100 && form.field > form.height - 100,
    'form properties receive remaining space',
  );
  evidence.special.push(
    { kind: 'form-builder', geometry: form },
    { kind: 'mobile-drawer', geometry: mobile },
  );
  await navigate('short-detail');
  const before = await page.evaluate(() => window.layoutResources());
  for (let i = 0; i < 5; i++) {
    await navigate('list');
    await navigate('editor');
    await navigate('short-detail');
  }
  const after = await page.evaluate(() => window.layoutResources());
  assert.equal(
    after.activeObservers,
    before.activeObservers,
    'repeated page cycles release observers',
  );
  assert.equal(
    after.activeTargets,
    before.activeTargets,
    'repeated page cycles release observer targets',
  );
  assert.equal(after.ownedObservers, 0);
  assert.equal(after.ownedListeners, 0);
  assert.equal(after.ownedReads, 0);
  assert.equal(after.ownedRaf, 0);
  const controlBefore = await page.evaluate(() => window.layoutResources());
  for (let i = 0; i < 5; i++) {
    await navigate('native-table');
    await navigate('short-detail');
  }
  const controlAfter = await page.evaluate(() => window.layoutResources());
  const tableResidue =
    controlAfter.detachedTargets - controlBefore.detachedTargets;
  assert.equal(
    after.detachedTargets - before.detachedTargets,
    tableResidue,
    'page cycles add no detached targets beyond native Element Plus table control',
  );
  evidence.resources = {
    before,
    after,
    nativeTableControl: {
      before: controlBefore,
      after: controlAfter,
      detachedTargetsPerFiveMounts: tableResidue,
    },
  };
  await page.waitForTimeout(800); // Let the existing route transition finish before measuring idle.
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Performance.enable');
  const metrics = async () =>
    Object.fromEntries(
      (await cdp.send('Performance.getMetrics')).metrics.map(
        ({ name, value }) => [name, value],
      ),
    );
  const idleBefore = await metrics();
  await page.waitForTimeout(500);
  const idleAfter = await metrics();
  assert.equal(
    idleAfter.LayoutCount,
    idleBefore.LayoutCount,
    'no idle layout loop',
  );
  const durations = [];
  const busyBefore = await metrics();
  for (let i = 0; i < 40; i++) {
    const duration = await page.evaluate(async (i) => {
      const start = performance.now();
      await window.layoutTest.configure({
        headerVisible: !!(i & 1),
        tagsView: !!(i & 2),
        breadcrumbVisible: !!(i & 4),
      });
      await new Promise((r) =>
        requestAnimationFrame(() => requestAnimationFrame(r)),
      );
      return performance.now() - start;
    }, i);
    durations.push(duration);
  }
  const busyAfter = await metrics();
  durations.sort((a, b) => a - b);
  evidence.performance = {
    idleLayoutCount: idleAfter.LayoutCount - idleBefore.LayoutCount,
    toggles: 40,
    layoutCount: busyAfter.LayoutCount - busyBefore.LayoutCount,
    layoutDurationMs:
      (busyAfter.LayoutDuration - busyBefore.LayoutDuration) * 1000,
    toggleTwoFramesMedianMs: durations[20],
    toggleTwoFramesP95Ms: durations[38],
  };
  assert.deepEqual(errors, [], 'no page errors');
  const output = resolve(
    process.env.LAYOUT_EVIDENCE_DIR ||
      '../docs/reports/evidence/2026-10-13-zxui-layout-regions',
  );
  await mkdir(output, { recursive: true });
  await writeFile(
    resolve(output, 'browser.json'),
    `${JSON.stringify(evidence, null, 2)}\n`,
  );
  console.log(
    JSON.stringify(
      {
        passedCases: evidence.matrix.length,
        specialCases: evidence.special.length,
        resources: evidence.resources,
        performance: evidence.performance,
        output,
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
}
