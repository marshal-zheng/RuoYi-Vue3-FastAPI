import { http, HttpResponse, type HttpHandler, type WebSocketHandler } from 'msw';

import type { RuntimeConfig } from '@/demo/runtime/mode';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import { createDemoAuthHandlers } from './auth';
import { createDemoProjectHandlers } from './project';
import { createDemoSimulationHandlers } from './simulation';
import { createDemoSystemHandlers } from './system';

export interface CreateDemoOfflineHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

export type DemoOfflineHandler = HttpHandler | WebSocketHandler;

export interface DemoApiNotImplementedPayload {
  code: 501;
  msg: string;
  type: 'error';
  data: {
    reason: 'DEMO_API_NOT_IMPLEMENTED';
    method: string;
    path: string;
    mode: 'demo-offline';
    scenarioId: string;
  };
}

export function isDemoApiRequest(request: Request, apiPrefix: string): boolean {
  const url = new URL(request.url);
  return url.pathname === apiPrefix || url.pathname.startsWith(`${apiPrefix}/`);
}

export function createDemoApiNotImplementedPayload(
  request: Request,
  config: RuntimeConfig
): DemoApiNotImplementedPayload {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;

  return {
    code: 501,
    msg: `DEMO_API_NOT_IMPLEMENTED: ${request.method} ${path} 尚未在 demo-offline 中实现`,
    type: 'error',
    data: {
      reason: 'DEMO_API_NOT_IMPLEMENTED',
      method: request.method,
      path,
      mode: 'demo-offline',
      scenarioId: config.scenarioId,
    },
  };
}

export function createDemoApiCatchAllHandler(
  config: RuntimeConfig,
  logger: DemoRuntimeLogger
): HttpHandler {
  return http.all(
    ({ request }) => isDemoApiRequest(request, config.apiPrefix),
    ({ request }) => {
      const payload = createDemoApiNotImplementedPayload(request, config);

      logger.warn('未覆盖 API 已被 demo-offline catch-all 拦截。', payload.data);

      return HttpResponse.json(payload, {
        status: 501,
        headers: {
          'X-Demo-Runtime': 'demo-offline',
          'X-Demo-Scenario': config.scenarioId,
          'X-Demo-Handler': 'catch-all',
        },
      });
    }
  );
}

export function createDemoOfflineHandlers({
  config,
  logger,
}: CreateDemoOfflineHandlersOptions): DemoOfflineHandler[] {
  logger.info('注册 demo-offline HTTP handlers。', {
    apiPrefix: config.apiPrefix,
    scenarioId: config.scenarioId,
  });

  return [
    ...createDemoAuthHandlers({ config, logger }),
    ...createDemoSystemHandlers({ config, logger }),
    ...createDemoProjectHandlers({ config, logger }),
    ...createDemoSimulationHandlers({ config, logger }),
    createDemoApiCatchAllHandler(config, logger),
  ];
}
