import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '@playwright/test';

const output =
  process.env.OVERLAY_EVIDENCE_DIR ||
  '../docs/reports/evidence/2026-10-13-zxui-overlay-layout/source';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
const evidence = { browser: browser.version(), cases: [], resources: {} };
await page.addInitScript(() => {
  const counts = {
    resizeCreated: 0,
    intersectionCreated: 0,
    globalListeners: 0,
    bounds: 0,
  };
  for (const name of ['ResizeObserver', 'IntersectionObserver']) {
    const Native = window[name];
    window[name] = class extends Native {
      constructor(...args) {
        super(...args);
        counts[name === 'ResizeObserver' ? 'resizeCreated' : 'intersectionCreated']++;
      }
    };
  }
  const add = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function (...args) {
    if (this === window || this === document) counts.globalListeners++;
    return add.apply(this, args);
  };
  const bounds = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function (...args) {
    counts.bounds++;
    return bounds.apply(this, args);
  };
  window.overlayResources = () => ({ ...counts });
});
const settle = async () =>
  page.evaluate(
    () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  );
const configure = async (values) => {
  await page.evaluate((v) => window.dividerTest.configure(v), values);
  await settle();
};
const selector = (kind) => `.zx-${kind}-container.el-${kind}`;
const close = async (kind) => {
  await page.evaluate(
    (k) => (k === 'drawer' ? window.dividerTest.close() : window.dividerTest.dialog(false)),
    kind
  );
  await page.locator(selector(kind)).waitFor({ state: 'hidden' });
};
const open = async (kind) => {
  await page.evaluate(
    (k) => (k === 'drawer' ? window.dividerTest.open() : window.dividerTest.dialog(true)),
    kind
  );
  await page.locator(selector(kind)).waitFor({ state: 'visible' });
  await page.waitForTimeout(400);
};
const snapshot = async (kind) =>
  page.locator(selector(kind)).evaluate((panel) => {
    const body = panel.querySelector('.el-drawer__body, .el-dialog__body');
    const header = panel.querySelector('.el-drawer__header, .el-dialog__header');
    const footer = panel.querySelector('.el-drawer__footer, .el-dialog__footer');
    const content = panel.querySelector('[data-zx-overlay-content]');
    const probe = panel.querySelector('[data-layout-probe]');
    const rect = (element) => {
      const r = element.getBoundingClientRect();
      return {
        left: r.left,
        right: r.right,
        top: r.top,
        bottom: r.bottom,
        width: r.width,
        height: r.height,
      };
    };
    const padding = (element) => {
      const css = getComputedStyle(element);
      return ['paddingBlockStart', 'paddingInlineEnd', 'paddingBlockEnd', 'paddingInlineStart'].map(
        (key) => Number.parseFloat(css[key])
      );
    };
    body.scrollTop = 0;
    const viewport = rect(body),
      start = rect(probe);
    const rhythmProbe = document.createElement('div');
    rhythmProbe.style.cssText =
      'position:absolute;visibility:hidden;width:var(--zx-overlay-rhythm);height:0';
    panel.append(rhythmProbe);
    const rhythm = rect(rhythmProbe).width;
    rhythmProbe.remove();
    body.scrollTop = body.scrollHeight;
    const end = rect(probe);
    const clientLeft = viewport.left + body.clientLeft;
    const scroll = panel.querySelector('[data-owned-scroll]');
    const action = panel.querySelector('.el-drawer__close-btn, .el-dialog__headerbtn');
    return {
      root: rect(panel),
      viewport,
      header: header && rect(header),
      footer: footer && rect(footer),
      padding: padding(content),
      headerPadding: header && padding(header),
      footerPadding: footer && padding(footer),
      actual: {
        top: start.top - viewport.top,
        bottom: viewport.bottom - end.bottom,
        left: start.left - clientLeft,
        right: clientLeft + body.clientWidth - start.right,
      },
      rhythm,
      direction: getComputedStyle(panel).direction,
      gutter: body.offsetWidth - body.clientWidth,
      clientLeft,
      clientRight: clientLeft + body.clientWidth,
      overflow: getComputedStyle(body).overflowY,
      scrollHeight: body.scrollHeight,
      clientHeight: body.clientHeight,
      headerOverflow: header && getComputedStyle(header).overflowY,
      footerOverflow: footer && getComputedStyle(footer).overflowY,
      owned: scroll && {
        height: scroll.clientHeight,
        scrollHeight: scroll.scrollHeight,
        overflow: getComputedStyle(scroll).overflowY,
      },
      action: action && {
        width: rect(action).width,
        expected: Number.parseFloat(
          getComputedStyle(panel).getPropertyValue('--zx-overlay-action-size')
        ),
      },
      divider: header && {
        width: Number.parseFloat(getComputedStyle(header, '::after').borderBottomWidth),
        content: getComputedStyle(header, '::after').content,
      },
    };
  });
const near = (actual, expected, message, tolerance = 0.15) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${message}: ${actual} / ${expected}`);
try {
  await mkdir(output, { recursive: true });
  await page.goto(process.env.OVERLAY_TEST_URL || 'http://127.0.0.1:4299/');
  await page.waitForFunction(() => !!window.dividerTest);
  for (const width of process.env.OVERLAY_SKIP_MATRIX === '1' ? [] : [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [themeId, mode] of [
      ['default', 'light'],
      ['army-pine', 'dark'],
    ]) {
      await page.evaluate(([id, m]) => window.dividerTest.theme(id, m), [themeId, mode]);
      await page.waitForTimeout(150);
      for (const kind of ['drawer', 'dialog']) {
        await configure({
          axes: {},
          commonLayout: {},
          drawerLayout: {},
          dialogLayout: {},
          near: {},
          local: true,
          dialogDivider: true,
          long: true,
          footer: true,
          style: {},
          withHeader: true,
        });
        await open(kind);
        for (const density of ['compact', 'default', 'comfortable'])
          for (const scale of [90, 100, 125])
            for (const direction of ['ltr', 'rtl']) {
              await configure({
                axes: { density, display: { profile: 'office', scale } },
                direction,
              });
              await page.waitForTimeout(200);
              const g = await snapshot(kind);
              const inline = g.rhythm * (width < 768 ? 2 : 3);
              near(g.padding[0], g.rhythm * 2, 'density-aware block start');
              near(g.padding[2], g.rhythm * 2, 'density-aware block end');
              near(g.padding[1], inline, 'theme-aware inline end');
              near(g.padding[3], inline, 'theme-aware inline start');
              for (const edge of ['top', 'bottom'])
                near(g.actual[edge], g.rhythm * 2, `actual ${edge} content inset`, 1);
              for (const edge of ['left', 'right'])
                near(g.actual[edge], inline, `actual ${edge} content inset`, 1);
              assert.equal(g.direction, direction);
              assert.equal(g.headerOverflow, 'visible');
              assert.equal(g.footerOverflow, 'visible');
              near(g.headerPadding[1], inline, 'header gutter');
              near(g.footerPadding[1], inline, 'footer gutter');
              const expectedAction = await page.locator(selector(kind)).evaluate((el) => {
                const test = document.createElement('div');
                test.style.cssText = 'position:absolute;width:var(--zx-overlay-action-size)';
                el.append(test);
                const width = test.getBoundingClientRect().width;
                test.remove();
                return width;
              });
              near(g.action.width, expectedAction, 'action hit area uses shared recipe');
              if (width < 768) assert(g.action.width >= 44);
              const before = {
                root: g.root.height,
                body: g.viewport.height,
                top: g.viewport.top,
              };
              await configure(kind === 'drawer' ? { local: false } : { dialogDivider: false });
              const off = await snapshot(kind);
              assert.deepEqual(
                {
                  root: off.root.height,
                  body: off.viewport.height,
                  top: off.viewport.top,
                },
                before,
                'divider preserves geometry'
              );
              await configure(kind === 'drawer' ? { local: true } : { dialogDivider: true });
              evidence.cases.push({
                type: 'matrix',
                width,
                themeId,
                mode,
                kind,
                density,
                scale,
                direction,
                geometry: g,
              });
            }
        await close(kind);
      }
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await configure({
    axes: { density: 'default', display: { profile: 'office', scale: 100 } },
    direction: 'ltr',
    style: {},
    commonLayout: {},
    near: {},
    drawerLayout: {},
    dialogLayout: {},
    long: true,
    footer: true,
  });
  for (const kind of ['drawer', 'dialog']) {
    const localKey = kind === 'drawer' ? 'drawerLayout' : 'dialogLayout';
    await open(kind);
    await configure({
      commonLayout: { bodyPadding: 'var(--case-padding)' },
      near: { bodyPadding: { blockStart: 0 } },
      [localKey]: { bodyPadding: { inlineEnd: 0 } },
      style: { '--case-padding': '7px 11px 13px 17px' },
    });
    let g = await snapshot(kind);
    assert.deepEqual(g.padding, [0, 0, 13, 17]);
    await configure({ [localKey]: { bodyPadding: undefined } });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [0, 11, 13, 17]);
    await configure({
      commonLayout: {},
      near: {},
      [localKey]: { bodyPadding: 'calc(1rem + 2px) 9px' },
    });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [18, 9, 18, 9]);
    await configure({ [localKey]: { bodyPadding: 0 } });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [0, 0, 0, 0]);
    assert.equal(g.overflow, 'auto');
    await configure({
      [localKey]: { bodyPadding: 0, bodyScroll: 'none' },
      dialogHeight: kind === 'dialog' ? 'min(80dvh, 48rem)' : undefined,
    });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [0, 0, 0, 0]);
    assert.equal(g.overflow, 'hidden');
    assert(g.owned.height > 100, JSON.stringify({ kind, geometry: g }));
    assert(g.owned.scrollHeight > g.owned.height + 500);
    assert.equal(g.owned.overflow, 'auto');
    assert(
      g.scrollHeight <= g.clientHeight + 1,
      'outer viewport does not scroll delegated content'
    );
    evidence.cases.push({ type: 'delegated', kind, geometry: g });
    await configure({ [localKey]: {}, footer: false });
    g = await snapshot(kind);
    assert.equal(g.footer, null);
    near(g.actual.top, g.padding[0], 'no footer top');
    near(g.actual.bottom, g.padding[2], 'no footer bottom', 1);
    await configure({
      footer: true,
      style: {
        '--zx-overlay-body-padding-block': '1.375rem',
        '--zx-overlay-padding-inline': '2.125rem',
      },
    });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [22, 34, 22, 34]);
    evidence.cases.push({ type: 'theme-role-override', kind, geometry: g });
    await configure({
      style: {},
      axes: { display: { profile: 'distance', scale: 100 } },
      [localKey]: { bodyPadding: 10 },
    });
    g = await snapshot(kind);
    assert.deepEqual(g.padding, [10, 10, 10, 10], 'explicit lengths are not scaled twice');
    await close(kind);
  }
  await configure({
    axes: {},
    drawerLayout: {},
    dialogLayout: {},
    commonLayout: {},
    near: {},
    style: {},
    footer: true,
    long: true,
    direction: 'ltr',
  });
  for (const kind of ['drawer', 'dialog']) {
    const localKey = kind === 'drawer' ? 'drawerLayout' : 'dialogLayout';
    await configure({
      [localKey]: { paddingInline: 10, headerPadding: 0, bodyPadding: 0, footerPadding: 0 },
    });
    await open(kind);
    const nested = await page.locator(selector(kind)).evaluate((panel) => {
      const child = document.createElement('div');
      child.className =
        'app-dialog-container el-dialog zx-overlay-layout zx-overlay-layout--divider';
      const header = document.createElement('header');
      header.className = 'el-dialog__header';
      header.textContent = 'Nested';
      const body = document.createElement('div');
      body.className = 'el-dialog__body';
      const content = document.createElement('div');
      content.setAttribute('data-zx-overlay-content', '');
      content.textContent = 'Child';
      body.append(content);
      const footer = document.createElement('footer');
      footer.className = 'el-dialog__footer';
      footer.textContent = 'Actions';
      child.append(header, body, footer);
      panel.querySelector('[data-zx-overlay-content]').append(child);
      const read = (el) => {
        const css = getComputedStyle(el);
        return [css.paddingTop, css.paddingRight].map(Number.parseFloat);
      };
      const metric = document.createElement('div');
      metric.style.cssText = 'position:absolute;width:var(--zx-overlay-rhythm)';
      child.append(metric);
      const rhythm = metric.getBoundingClientRect().width;
      metric.remove();
      const result = {
        rhythm,
        divider: Number.parseFloat(getComputedStyle(header, '::after').borderBottomWidth),
        header: read(child.firstElementChild),
        body: read(child.querySelector('[data-zx-overlay-content]')),
        footer: read(child.lastElementChild),
      };
      child.remove();
      return result;
    });
    near(nested.body[0], nested.rhythm * 2, 'nested default block inset');
    near(nested.body[1], nested.rhythm * 3, 'parent instance inline inset does not leak');
    near(nested.header[0], nested.rhythm * 1.5, 'nested header inset');
    near(nested.header[1], nested.rhythm * 3, 'nested header inline');
    near(nested.footer[0], nested.rhythm * 1.5, 'nested footer inset');
    near(nested.footer[1], nested.rhythm * 3, 'nested footer inline');
    assert.equal(nested.divider, 1, 'custom namespace retains divider recipe');
    evidence.cases.push({ type: 'nested-css-isolation', kind, nested });
    await close(kind);
    await configure({ [localKey]: {} });
  }
  for (const kind of ['drawer', 'dialog']) {
    await open(kind);
    const inline = await page.locator(selector(kind)).evaluate((panel) => {
      const wrapper = document.createElement('div');
      const first = document.createElement('span');
      const second = document.createElement('span');
      first.textContent = 'First';
      second.textContent = 'Second';
      wrapper.append(first, second);
      panel.querySelector('[data-zx-overlay-content]').append(wrapper);
      const result = {
        first: first.getBoundingClientRect().top,
        second: second.getBoundingClientRect().top,
        display: getComputedStyle(wrapper).display,
      };
      wrapper.remove();
      return result;
    });
    assert.equal(inline.first, inline.second, 'default overlay slot uses inline flow');
    evidence.cases.push({ type: 'slot-inline-flow', kind, inline });
    await close(kind);
  }
  const classic = await page.addStyleTag({
    content:
      '.zx-overlay-layout :is(.el-drawer__body,.el-dialog__body){scrollbar-width:auto!important}.zx-overlay-layout :is(.el-drawer__body,.el-dialog__body)::-webkit-scrollbar{width:12px!important}',
  });
  for (const kind of ['drawer', 'dialog']) {
    await open(kind);
    for (const direction of ['ltr', 'rtl']) {
      await configure({ direction });
      await page.waitForTimeout(80);
      const g = await snapshot(kind);
      assert.equal(g.gutter, 12);
      near(g.header.left, g.clientLeft, 'classic header left');
      near(g.header.right, g.clientRight, 'classic header right');
      near(g.footer.left, g.clientLeft, 'classic footer left');
      near(g.footer.right, g.clientRight, 'classic footer right');
      evidence.cases.push({
        type: 'classic-scrollbar',
        kind,
        direction,
        geometry: g,
      });
    }
    await close(kind);
  }
  await classic.evaluate((el) => el.remove());
  await configure({
    direction: 'ltr',
    commonLayout: {},
    near: {},
    drawerLayout: {},
    dialogLayout: {},
    style: {},
    axes: {},
    long: false,
    dialogHeight: undefined,
  });
  await open('dialog');
  const short = await snapshot('dialog');
  assert(short.root.height < 400, 'short Dialog retains natural height');
  assert(short.scrollHeight <= short.clientHeight + 1);
  await close('dialog');
  await configure({ long: true });
  await open('drawer');
  await page.waitForTimeout(200);
  const before = await page.evaluate(() => window.overlayResources());
  for (let i = 0; i < 40; i++)
    await configure({
      local: !!(i & 1),
      drawerLayout: { bodyPadding: { blockStart: `${(i % 3) + 1}rem` } },
    });
  await page.waitForTimeout(100);
  const after = await page.evaluate(() => window.overlayResources());
  assert.deepEqual(
    after,
    before,
    'spacing/divider updates add no observers, listeners or geometry reads'
  );
  evidence.resources = { before, after };
  await configure({ drawerLayout: {}, local: true });
  await page.locator('.el-drawer__body').evaluate((el) => {
    el.scrollTop = 0;
  });
  await page.screenshot({ path: `${output}/drawer.png` });
  await close('drawer');
  await open('dialog');
  await page.screenshot({ path: `${output}/dialog.png` });
  await close('dialog');
  assert.deepEqual(errors, []);
  await writeFile(`${output}/browser.json`, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(
    JSON.stringify({
      cases: evidence.cases.length,
      resources: evidence.resources,
      pageErrors: errors.length,
    })
  );
} finally {
  await browser.close();
}
