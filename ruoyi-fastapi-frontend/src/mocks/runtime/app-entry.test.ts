import { beforeEach, describe, expect, it, vi } from "vitest";

import { setupAppRuntimeMocks } from "./app-entry";
import type { RuntimeConfig } from "./mode";

function runtimeConfig(mode: RuntimeConfig["mode"]): RuntimeConfig {
  return {
    mode,
    apiPrefix: "/api",
    debug: mode === "demo-offline",
    source: "runtime-mode",
  };
}

describe("setupAppRuntimeMocks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.__MOCK_RUNTIME__ = {
      getMode: () => "demo-offline",
      getDatasetVersion: () => "old",
      resetDataset: vi.fn(),
      exportDatasetSnapshot: vi.fn(),
      listOverlays: vi.fn(() => []),
      getOverlayState: vi.fn(() => ({
        activeIds: [],
        activeEntries: [],
        source: "none" as const,
      })),
      activateOverlays: vi.fn(),
      resetOverlays: vi.fn(),
    };
    (window as unknown as { __DEMO_RUNTIME__?: unknown }).__DEMO_RUNTIME__ = {};
  });

  it("does not start mocks in real mode and clears legacy devtools", async () => {
    const setupRuntime = vi.fn();

    await setupAppRuntimeMocks(runtimeConfig("real"), setupRuntime);

    expect(setupRuntime).not.toHaveBeenCalled();
    expect(window.__MOCK_RUNTIME__).toBeUndefined();
    expect(
      (window as unknown as { __DEMO_RUNTIME__?: unknown }).__DEMO_RUNTIME__,
    ).toBeUndefined();
  });

  it("starts fallback and demo-offline through the unified mock runtime", async () => {
    const setupRuntime = vi.fn().mockResolvedValue(undefined);

    await setupAppRuntimeMocks(runtimeConfig("fallback"), setupRuntime);
    await setupAppRuntimeMocks(runtimeConfig("demo-offline"), setupRuntime);

    expect(setupRuntime).toHaveBeenNthCalledWith(1, {
      mode: "fallback",
      apiPrefix: "/api",
      debug: false,
    });
    expect(setupRuntime).toHaveBeenNthCalledWith(2, {
      mode: "demo-offline",
      apiPrefix: "/api",
      debug: true,
    });
  });
});
