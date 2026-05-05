import { beforeEach } from "vitest";

import { createMockHandlers } from "@/mocks/handlers";
import type { MockOverlayActivationInput } from "@/mocks/overlays";
import type { MockDataSource } from "@/mocks/store";

import {
  type MainlineMockContext,
  setupMainlineMockHandlers,
} from "./mainline";
import { mockServer } from "./server";

export interface OverlayMockContext extends MainlineMockContext {
  activateOverlayHandlers(overlays: string[]): void;
  resetOverlayHandlers(): void;
}

function useOverlayHandlers(
  overlays: MockOverlayActivationInput,
  dataSource: MockDataSource,
) {
  mockServer.resetHandlers(
    ...createMockHandlers({
      strategy: "pure",
      dataSource,
      overlays,
    }),
  );
}

export function activateOverlayHandlers(
  overlays: string[],
  context: MainlineMockContext,
): void {
  useOverlayHandlers(overlays, context.dataSource());
}

export function resetOverlayHandlers(context: MainlineMockContext): void {
  useOverlayHandlers([], context.dataSource());
}

export function setupOverlayMockHandlers(
  overlays: string[] = [],
): OverlayMockContext {
  const context = setupMainlineMockHandlers();

  beforeEach(() => {
    if (overlays.length) {
      activateOverlayHandlers(overlays, context);
    }
  });

  return {
    dataSource: context.dataSource,
    activateOverlayHandlers(nextOverlays: string[]) {
      activateOverlayHandlers(nextOverlays, context);
    },
    resetOverlayHandlers() {
      resetOverlayHandlers(context);
    },
  };
}
