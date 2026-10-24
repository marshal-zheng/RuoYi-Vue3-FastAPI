import type { RequestHandler, WebSocketHandler } from 'msw';
import type { StartOptions } from 'msw/browser';

export type MockNetworkStrategy = 'fallback' | 'pure';
export type MockStrategy = MockNetworkStrategy;
export type MockMode = 'off' | MockStrategy;
export type MockErrorScenario = 'error-timeout' | 'error-5xx' | 'error-429';

/**
 * Legacy handler bundle selector.
 *
 * This no longer represents a business scenario or a multi-scenario runtime.
 * Use MockNetworkStrategy for new code.
 */
export type MockScenario = 'default' | 'pure' | MockErrorScenario;
export type MockRuntimeHandler = RequestHandler | WebSocketHandler;

export type OnUnhandledRequestOption = StartOptions['onUnhandledRequest'];

export interface StartMockOptions {
  strategy?: MockNetworkStrategy;
  scenario?: MockScenario;
  handlers?: MockRuntimeHandler[];
  onUnhandledRequest?: OnUnhandledRequestOption;
}
