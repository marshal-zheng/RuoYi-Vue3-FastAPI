// @ts-nocheck
import type { RequestHandler, WebSocketHandler } from 'msw';

export type MockStrategy = 'fallback' | 'pure';
export type MockMode = 'off' | MockStrategy;

export type MockScenario = 'default' | 'pure';
export type MockRuntimeHandler = RequestHandler | WebSocketHandler;

export type OnUnhandledRequestHandler = (
  request: Request,
  print: {
    info(...args: any[]): void;
    warning(...args: any[]): void;
    error(...args: any[]): void;
  }
) => void;

export type OnUnhandledRequestOption = 'bypass' | 'warn' | 'error' | OnUnhandledRequestHandler;

export interface StartMockOptions {
  strategy?: MockStrategy;
  scenario?: MockScenario;
  handlers?: MockRuntimeHandler[];
  onUnhandledRequest?: OnUnhandledRequestOption;
}
