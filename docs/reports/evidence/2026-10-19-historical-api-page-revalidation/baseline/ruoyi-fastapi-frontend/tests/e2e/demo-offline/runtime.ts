import { expect, type BrowserContext, type Page } from "@playwright/test";

type E2EMockRuntime = {
  getMode?: () => string;
  resetDataset?: () => Promise<void>;
  exportDatasetSnapshot?: () => Promise<unknown>;
  listOverlays?: () => Array<{ id: string }>;
  getOverlayState?: () => { activeIds: string[]; source: string };
  activateOverlays?: (
    ids: string[],
  ) => Promise<{ activeIds: string[]; source: string }>;
  resetOverlays?: () => Promise<{ activeIds: string[]; source: string }>;
};

export async function expectDemoOfflineRuntime(page: Page) {
  await expect
    .poll(
      () =>
        page.evaluate(() => {
          return (
            window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime }
          ).__MOCK_RUNTIME__?.getMode?.();
        }),
      {
        message: "window.__MOCK_RUNTIME__.getMode() should be demo-offline",
      },
    )
    .toBe("demo-offline");

  const serviceWorkerReady = await page.evaluate(async () => {
    if (!("serviceWorker" in navigator)) {
      return false;
    }
    const registration = await navigator.serviceWorker.ready;
    return Boolean(registration.active);
  });

  expect(serviceWorkerReady, "MSW Service Worker should be registered").toBe(
    true,
  );
}

export async function resetDataset(page: Page) {
  await page.evaluate(async () => {
    const runtime = (window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime })
      .__MOCK_RUNTIME__;
    if (!runtime?.resetDataset) {
      throw new Error("demo-offline runtime does not expose resetDataset()");
    }
    await runtime.resetDataset();
  });
}

export async function exportDatasetSnapshot(page: Page) {
  return page.evaluate(async () => {
    const runtime = (window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime })
      .__MOCK_RUNTIME__;
    if (!runtime?.exportDatasetSnapshot) {
      throw new Error(
        "demo-offline runtime does not expose exportDatasetSnapshot()",
      );
    }
    return runtime.exportDatasetSnapshot();
  });
}

export async function bootstrapOverlays(
  context: BrowserContext,
  ids: string[],
) {
  await context.addInitScript((overlayIds) => {
    (
      window as Window & {
        __MOCK_RUNTIME_BOOTSTRAP__?: {
          source: "playwright";
          overlays: string[];
        };
      }
    ).__MOCK_RUNTIME_BOOTSTRAP__ = {
      source: "playwright",
      overlays: overlayIds,
    };
  }, ids);
}

export async function activateOverlays(page: Page, ids: string[]) {
  return page.evaluate(async (overlayIds) => {
    const runtime = (window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime })
      .__MOCK_RUNTIME__;
    if (!runtime?.activateOverlays) {
      throw new Error(
        "demo-offline runtime does not expose activateOverlays()",
      );
    }
    return runtime.activateOverlays(overlayIds);
  }, ids);
}

export async function resetOverlays(page: Page) {
  return page.evaluate(async () => {
    const runtime = (window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime })
      .__MOCK_RUNTIME__;
    if (!runtime?.resetOverlays) {
      throw new Error("demo-offline runtime does not expose resetOverlays()");
    }
    return runtime.resetOverlays();
  });
}

export async function expectOverlayState(page: Page, ids: string[]) {
  await expect
    .poll(
      () =>
        page.evaluate(() => {
          const runtime = (
            window as Window & { __MOCK_RUNTIME__?: E2EMockRuntime }
          ).__MOCK_RUNTIME__;
          return runtime?.getOverlayState?.().activeIds ?? [];
        }),
      {
        message: `window.__MOCK_RUNTIME__.getOverlayState() should be ${ids.join(",")}`,
      },
    )
    .toEqual(ids);
}

export async function clearBrowserStorage(page: Page, context: BrowserContext) {
  await context.clearCookies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
    document.cookie.split(";").forEach((cookie) => {
      const name = cookie.split("=")[0]?.trim();
      if (name) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
      }
    });
  });
}
