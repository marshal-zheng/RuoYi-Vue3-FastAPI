import type { MockDataSource } from "../store";
import { getMockDataSource } from "../store";
import type {
  MockNetworkStrategy,
  MockRuntimeHandler,
  MockStrategy,
} from "../types";
import { createUnhandledApiHandler } from "../runtime/unhandled";
import { createMockOverlayHandlers } from "../overlays/handlers";
import type { MockOverlayActivationInput } from "../overlays";

import { createSystemHandlers } from "./system";
import { createUserHandlers } from "./user";
import { createTestHandlers } from "./test";
import { createMonitorHandlers } from "./monitor";
import { createDeviceHandlers } from "./device";
import { createProjectHandlers } from "./project";
import { createSimulationHandlers } from "./simulation";

export interface CreateMockHandlersOptions {
  strategy: MockNetworkStrategy;
  dataSource?: MockDataSource;
  apiPrefix?: string;
  onMissingCapability?: "error" | "passthrough";
  overlays?: MockOverlayActivationInput;
}

export function createMockHandlers(
  options: CreateMockHandlersOptions,
): MockRuntimeHandler[] {
  const {
    strategy,
    apiPrefix = "/api",
    onMissingCapability = "passthrough",
  } = options;
  const dataSource = options.dataSource ?? getMockDataSource();
  void dataSource;

  const baseHandlers: MockRuntimeHandler[] = [
    ...createSystemHandlers(strategy, dataSource),
    ...createUserHandlers(strategy, dataSource),
    ...createDeviceHandlers(strategy),
    ...createProjectHandlers(strategy, dataSource),
    ...createSimulationHandlers(strategy, dataSource),
    ...createTestHandlers(strategy),
    ...createMonitorHandlers(strategy),
  ];

  const handlers: MockRuntimeHandler[] = [
    ...createMockOverlayHandlers({
      strategy,
      dataSource,
      apiPrefix,
      overlays: options.overlays,
    }),
    ...baseHandlers,
  ];

  if (onMissingCapability === "error") {
    handlers.push(createUnhandledApiHandler(apiPrefix));
  }

  return handlers;
}

export function createHandlers(strategy: MockStrategy): MockRuntimeHandler[] {
  return createMockHandlers({ strategy });
}
