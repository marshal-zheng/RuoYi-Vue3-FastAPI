import { setupBrowserMocks } from '@/mocks';
import { createDemoOfflineHandlers } from '@/demo/handlers';
import type { StartOptions } from 'msw/browser';

import type { RuntimeConfig } from './mode';
import { createDemoRuntimeLogger } from './logger';
import { exposeDemoRuntimeDevtools } from './devtools';
import { initializeDemoRuntimeState, type DemoRuntimeSnapshot } from './state';

export interface DemoOfflineRuntime {
  config: RuntimeConfig;
  snapshot: DemoRuntimeSnapshot;
}

type UnhandledRequestCallback = Exclude<
  NonNullable<StartOptions['onUnhandledRequest']>,
  'bypass' | 'warn' | 'error'
>;

function createDemoUnhandledRequestHandler(config: RuntimeConfig): UnhandledRequestCallback {
  return (
    request: Request,
    print: {
      warning(): void;
      error(): void;
    }
  ) => {
    const url = new URL(request.url);
    const isApiRequest =
      url.pathname === config.apiPrefix || url.pathname.startsWith(`${config.apiPrefix}/`);

    if (isApiRequest) {
      console.error(
        `[DemoRuntime] ${request.method} ${url.pathname} 未被 demo-offline handler 覆盖。`
      );
      print.error();
      return;
    }

    console.info(`[DemoRuntime] 非 API 请求旁路：${request.method} ${url.pathname}`);
  };
}

export async function setupDemoOfflineRuntime(config: RuntimeConfig): Promise<DemoOfflineRuntime> {
  if (config.mode !== 'demo-offline') {
    throw new Error(
      `setupDemoOfflineRuntime can only run in demo-offline mode, got ${config.mode}.`
    );
  }

  const logger = createDemoRuntimeLogger(config);
  logger.info('开始启动 demo-offline 运行时。', {
    apiPrefix: config.apiPrefix,
    scenarioId: config.scenarioId,
    debug: config.debug,
  });

  const snapshot = await initializeDemoRuntimeState(config, logger);
  const handlers = createDemoOfflineHandlers({ config, logger });

  await setupBrowserMocks({
    strategy: 'pure',
    scenario: 'pure',
    handlers,
    onUnhandledRequest: createDemoUnhandledRequestHandler(config),
  });

  exposeDemoRuntimeDevtools(config, snapshot, logger);

  logger.info('demo-offline 运行时已就绪。', {
    scenarioId: snapshot.scenario.id,
    apiPrefix: snapshot.apiPrefix,
  });

  return {
    config,
    snapshot,
  };
}
