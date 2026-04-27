import type { RequestHandler, WebSocketHandler } from 'msw';
import type { StartOptions } from 'msw/browser';

export type MockStrategy = 'fallback' | 'pure';
export type MockMode = 'off' | MockStrategy;

export type MockScenario = 'default' | 'pure';
export type MockRuntimeHandler = RequestHandler | WebSocketHandler;

export type OnUnhandledRequestOption = StartOptions['onUnhandledRequest'];

export interface StartMockOptions {
  strategy?: MockStrategy;
  scenario?: MockScenario;
  handlers?: MockRuntimeHandler[];
  onUnhandledRequest?: OnUnhandledRequestOption;
}
