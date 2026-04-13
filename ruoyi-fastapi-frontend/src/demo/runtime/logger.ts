import type { RuntimeConfig } from './mode';

export type DemoRuntimeLogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface DemoRuntimeLogger {
  debug(message: string, context?: unknown): void;
  info(message: string, context?: unknown): void;
  warn(message: string, context?: unknown): void;
  error(message: string, context?: unknown): void;
}

function writeLog(
  level: DemoRuntimeLogLevel,
  config: RuntimeConfig,
  message: string,
  context?: unknown
) {
  if (level === 'debug' && !config.debug) {
    return;
  }

  const payload = context === undefined ? [] : [context];
  const prefix = `[DemoRuntime:${config.mode}]`;

  if (level === 'debug') {
    // eslint-disable-next-line no-console
    console.debug(prefix, message, ...payload);
    return;
  }

  if (level === 'warn') {
    // eslint-disable-next-line no-console
    console.warn(prefix, message, ...payload);
    return;
  }

  if (level === 'error') {
    // eslint-disable-next-line no-console
    console.error(prefix, message, ...payload);
    return;
  }

  // eslint-disable-next-line no-console
  console.info(prefix, message, ...payload);
}

export function createDemoRuntimeLogger(config: RuntimeConfig): DemoRuntimeLogger {
  return {
    debug: (message, context) => writeLog('debug', config, message, context),
    info: (message, context) => writeLog('info', config, message, context),
    warn: (message, context) => writeLog('warn', config, message, context),
    error: (message, context) => writeLog('error', config, message, context),
  };
}
