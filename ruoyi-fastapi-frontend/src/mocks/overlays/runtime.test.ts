import { describe, expect, it } from "vitest";

import { createMockOverlayRuntime } from "./runtime";

describe("mock overlay runtime", () => {
  it("activates, lists, and resets overlays without touching dataset state", () => {
    const runtime = createMockOverlayRuntime();

    expect(runtime.listOverlays().map((entry) => entry.id)).toContain(
      "project-list-empty",
    );
    expect(runtime.getOverlayState()).toMatchObject({
      activeIds: [],
      source: "none",
    });

    const active = runtime.activateOverlays(["project-list-empty"], "vitest");
    expect(active).toMatchObject({
      activeIds: ["project-list-empty"],
      source: "vitest",
    });

    expect(runtime.resetOverlays()).toMatchObject({
      activeIds: [],
      source: "none",
    });
  });

  it("fails fast on unknown overlays and keeps the previous state", () => {
    const runtime = createMockOverlayRuntime({
      initialOverlays: ["project-list-empty"],
      source: "bootstrap",
    });

    expect(() => runtime.activateOverlays(["missing-overlay"])).toThrow(
      /Unknown mock overlay id: missing-overlay/,
    );
    expect(runtime.getOverlayState().activeIds).toEqual(["project-list-empty"]);
  });

  it("rejects conflicting overlays as one atomic activation request", () => {
    const runtime = createMockOverlayRuntime({
      initialOverlays: ["project-list-empty"],
      source: "bootstrap",
    });

    expect(() =>
      runtime.activateOverlays([
        "version-clone-forbidden",
        "version-clone-timeout",
      ]),
    ).toThrow(/conflicts with/);
    expect(runtime.getOverlayState().activeIds).toEqual(["project-list-empty"]);
  });

  it("keeps overlay state isolated per runtime instance", () => {
    const left = createMockOverlayRuntime();
    const right = createMockOverlayRuntime();

    left.activateOverlays(["project-list-empty"]);

    expect(left.getOverlayState().activeIds).toEqual(["project-list-empty"]);
    expect(right.getOverlayState().activeIds).toEqual([]);
  });

  it("rejects activation when the runtime mode does not allow overlays", () => {
    const runtime = createMockOverlayRuntime({ allowOverlays: false });

    expect(() => runtime.activateOverlays(["project-list-empty"])).toThrow(
      /not available in the current runtime mode/,
    );
    expect(runtime.getOverlayState().activeIds).toEqual([]);
  });
});
