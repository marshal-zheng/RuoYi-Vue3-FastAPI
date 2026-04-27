import { http, ws, type HttpHandler, type WebSocketHandler } from 'msw';

import { getDemoOfflineDb } from '@/demo/db';
import {
  AuthRepository,
  ProjectRepository,
  ProjectVersionRepository,
  SimulationRepository,
} from '@/demo/repositories';
import { DemoRealtimeStream } from '@/demo/realtime/stream';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthService, DemoSimulationError, DemoSimulationService } from '@/demo/services';

import {
  createDemoApiPath,
  demoErrorResponse,
  demoJsonResponse,
  getDemoRequestToken,
  readDemoRequestBody,
} from './utils';

export interface CreateDemoSimulationHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

interface DemoNotSupportedProblem {
  type: 'about:blank';
  title: string;
  status: 501;
  detail: string;
  instance: string;
  errorCode: 'DEMO_NOT_SUPPORTED';
}

function createAuthService(): DemoAuthService {
  return new DemoAuthService(new AuthRepository(getDemoOfflineDb()));
}

function createSimulationService(): DemoSimulationService {
  const db = getDemoOfflineDb();
  return new DemoSimulationService(
    new ProjectRepository(db),
    new ProjectVersionRepository(db),
    new SimulationRepository(db)
  );
}

function readSearchParam(request: Request, name: string): string | undefined {
  return new URL(request.url).searchParams.get(name) ?? undefined;
}

function createNotSupportedPayload(
  request: Request,
  config: RuntimeConfig,
  capability: 'simulation-control' | 'simulation-write'
): DemoNotSupportedProblem {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;

  return {
    type: 'about:blank',
    title: 'Demo Capability Not Supported',
    status: 501,
    detail: `DEMO_NOT_SUPPORTED: ${request.method} ${path} 在 demo-offline(${config.scenarioId}) 中暂不支持 ${capability}`,
    instance: path,
    errorCode: 'DEMO_NOT_SUPPORTED',
  };
}

function demoNotSupportedResponse(
  request: Request,
  config: RuntimeConfig,
  logger: DemoRuntimeLogger,
  handlerName: string,
  capability: 'simulation-control' | 'simulation-write'
): Response {
  const payload = createNotSupportedPayload(request, config, capability);

  logger.info('demo-offline 拒绝仿真写操作。', {
    handler: handlerName,
    capability,
    method: request.method,
    path: new URL(request.url).pathname,
  });

  return demoJsonResponse(config, handlerName, payload, 501);
}

function requireSessionId(sessionId: string | undefined): string {
  if (!sessionId) {
    throw new DemoSimulationError('仿真会话不存在', 404);
  }

  return sessionId;
}

function listSimulationStrategies() {
  return [
    {
      value: 'preset',
      label: '预置样本',
      description: '按场景包预置内容回放离线演示数据',
    },
    {
      value: 'repeat',
      label: '循环填充',
      description: '重复已有报文片段形成稳定展示窗口',
    },
    {
      value: 'increment',
      label: '递增填充',
      description: '基于序号和时间戳生成可预测占位内容',
    },
    {
      value: 'random',
      label: '随机扰动',
      description: '对预置内容做确定性伪随机扰动',
    },
  ];
}

export function createDemoSimulationHandlers({
  config,
  logger,
}: CreateDemoSimulationHandlersOptions): Array<HttpHandler | WebSocketHandler> {
  const path = (value: string) => createDemoApiPath(config, value);
  const simulationWs = ws.link(`*${path('/simulation/sessions/:sessionId/ws')}`);

  return [
    simulationWs.addEventListener('connection', async ({ client, params }) => {
      const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
      const ticket = client.url.searchParams.get('ticket') ?? undefined;

      try {
        await createAuthService().consumeWsTicket(ticket, sessionId);
        await new DemoRealtimeStream(createSimulationService(), logger).start(client, sessionId);
      } catch (error) {
        logger.warn('demo-offline 仿真 WebSocket 连接被拒绝。', {
          sessionId,
          message: error instanceof Error ? error.message : String(error),
        });
        client.send(
          JSON.stringify({
            type: 'status',
            data: {
              sessionId,
              status: 'error',
              errorCount: 1,
              message: error instanceof Error ? error.message : 'WebSocket ticket 校验失败',
            },
          })
        );
        client.close(1008, 'DEMO_WS_UNAUTHORIZED');
      }
    }),
    http.post(path('/simulation/sessions'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const body = await readDemoRequestBody<{
          projectId?: number | string | null;
          versionId?: number | string | null;
        }>(request);
        const session = await createSimulationService().createSession(body);

        return demoJsonResponse(
          config,
          'simulation:session:create',
          {
            code: 200,
            msg: '仿真会话创建成功',
            type: 'success',
            data: session,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:session:create');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/status'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const status = await createSimulationService().getStatus(sessionId);

        return demoJsonResponse(
          config,
          'simulation:status',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: status,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:status');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/messages'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const limit = readSearchParam(request, 'limit');
        const messages = await createSimulationService().listMessages(
          sessionId,
          limit ? Number(limit) : undefined
        );

        return demoJsonResponse(
          config,
          'simulation:messages',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: messages,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:messages');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/bandwidth'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const bandwidth = await createSimulationService().listBandwidth(sessionId, {
          portId: readSearchParam(request, 'portId'),
        });

        return demoJsonResponse(
          config,
          'simulation:bandwidth',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: bandwidth,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:bandwidth');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/alarms'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const alarms = await createSimulationService().listAlarms(sessionId);

        return demoJsonResponse(
          config,
          'simulation:alarms',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: alarms,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:alarms');
      }
    }),
    http.get(path('/simulation/faults'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(readSearchParam(request, 'sessionId'));
        const faults = await createSimulationService().listFaults(sessionId);

        return demoJsonResponse(
          config,
          'simulation:faults',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: faults,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:faults');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/faults'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const faults = await createSimulationService().listFaults(sessionId);

        return demoJsonResponse(
          config,
          'simulation:session:faults',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: faults,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:session:faults');
      }
    }),
    http.get(path('/simulation/sessions/:sessionId/events'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const events = await createSimulationService().listEvents(sessionId);

        return demoJsonResponse(
          config,
          'simulation:events',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: events,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:events');
      }
    }),
    http.post(path('/simulation/sessions/:sessionId/export'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const sessionId = requireSessionId(params.sessionId ? String(params.sessionId) : undefined);
        const body = await readDemoRequestBody<{
          exportFormat?: string;
          dataType?: string;
        }>(request);
        const result = await createSimulationService().exportSession(sessionId, body);

        return demoJsonResponse(
          config,
          'simulation:export',
          {
            code: 200,
            msg: '导出数据已生成',
            type: 'success',
            data: result,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:export');
      }
    }),
    http.get(path('/simulation/strategies'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));

        return demoJsonResponse(
          config,
          'simulation:strategies',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: listSimulationStrategies(),
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'simulation:strategies');
      }
    }),
    http.post(path('/simulation/sessions/:sessionId/start'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:start', 'simulation-control')
    ),
    http.post(path('/simulation/sessions/:sessionId/pause'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:pause', 'simulation-control')
    ),
    http.post(path('/simulation/sessions/:sessionId/resume'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:resume', 'simulation-control')
    ),
    http.post(path('/simulation/sessions/:sessionId/stop'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:stop', 'simulation-control')
    ),
    http.post(path('/simulation/sessions/:sessionId/step'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:step', 'simulation-control')
    ),
    http.post(path('/simulation/sessions/:sessionId/speed'), ({ request }) =>
      demoNotSupportedResponse(request, config, logger, 'simulation:speed', 'simulation-control')
    ),
    http.post(path('/simulation/faults'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:faults:create',
        'simulation-write'
      )
    ),
    http.delete(path('/simulation/faults/:faultId'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:faults:delete',
        'simulation-write'
      )
    ),
    http.delete(path('/simulation/sessions/:sessionId/faults'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:faults:clear-all',
        'simulation-write'
      )
    ),
    http.post(path('/simulation/sessions/:sessionId/events'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:events:create',
        'simulation-write'
      )
    ),
    http.put(path('/simulation/sessions/:sessionId/events/:eventId'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:events:update',
        'simulation-write'
      )
    ),
    http.delete(path('/simulation/sessions/:sessionId/events/:eventId'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:events:delete',
        'simulation-write'
      )
    ),
    http.post(path('/simulation/sessions/:sessionId/events/:eventId/trigger'), ({ request }) =>
      demoNotSupportedResponse(
        request,
        config,
        logger,
        'simulation:events:trigger',
        'simulation-write'
      )
    ),
  ];
}
