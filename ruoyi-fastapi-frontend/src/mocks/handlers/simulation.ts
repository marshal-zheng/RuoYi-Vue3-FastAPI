import { http, HttpResponse } from 'msw';
import type {
  SimulationAlarm,
  SimulationBandwidth,
  SimulationEvent,
  SimulationFillStrategy,
  SimulationMessage,
} from '@/api/simulation/types';

import { createApiPath } from '../constants';
import type { MockDataSource } from '../store';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import { getSearchParams, readJsonBody } from '../utils/request';
import { resultSuccess } from '../utils/response';
import { withBackendFallback } from '../utils/with-backend-fallback';

function notSupported(request: Request, capability: 'simulation-control' | 'simulation-write') {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;
  return HttpResponse.json(
    {
      type: 'about:blank',
      title: 'MOCK_SIMULATION_NOT_SUPPORTED',
      status: 501,
      detail: `MOCK_SIMULATION_NOT_SUPPORTED: ${request.method} ${path} 首批只读 mock 不支持 ${capability}`,
      instance: path,
      errorCode: 'MOCK_SIMULATION_NOT_SUPPORTED',
    },
    {
      status: 501,
      headers: {
        'Content-Type': 'application/problem+json',
        'X-Mock-Response': 'true',
        'X-Mock-Handler': capability,
      },
    }
  );
}

function listSimulationStrategies(): SimulationFillStrategy[] {
  return [
    {
      value: 'random',
      label: '随机值',
      description: '在指定值域范围内随机生成数据',
      icon: 'Dice',
      params: ['valueRange'],
    },
    {
      value: 'increment',
      label: '序列递增',
      description: '计数器模式，数值按步长递增，到达上限后循环',
      icon: 'TrendCharts',
      params: ['startValue', 'step', 'valueRange'],
    },
    {
      value: 'fixed',
      label: '固定值',
      description: '使用预设的固定值填充',
      icon: 'Lock',
      params: ['fixedValue'],
    },
    {
      value: 'cycle',
      label: '循环模式',
      description: '按顺序循环使用预设数据集中的值',
      icon: 'Refresh',
      params: ['presetValues'],
    },
    {
      value: 'sine_wave',
      label: '正弦波',
      description: '模拟周期性数据变化，适合传感器数据仿真',
      icon: 'DataLine',
      params: ['amplitude', 'offset', 'frequency', 'phase'],
    },
  ];
}

function historyToEvents(
  events: Awaited<ReturnType<MockDataSource['simulation']['listEvents']>>
): SimulationEvent[] {
  return events.map((event) => ({
    eventId: event.eventId,
    sessionId: event.sessionId,
    name: event.eventType,
    status: 'triggered',
    triggerCount: 1,
    lastTriggerTime: Date.parse(event.triggerTime),
  }));
}

function historyToMessages(
  messages: Awaited<ReturnType<MockDataSource['simulation']['listMessages']>>
): SimulationMessage[] {
  return messages.map((message) => ({ ...message, timestamp: Date.parse(message.timestamp) }));
}

async function readSessionStatus(dataSource: MockDataSource, sessionId: string) {
  const session = await dataSource.simulation.getSession(sessionId);
  if (!session) return undefined;
  const [frames, messages, events] = await Promise.all([
    dataSource.simulation.listFrames(sessionId),
    dataSource.simulation.listMessages(sessionId),
    dataSource.simulation.listEvents(sessionId),
  ]);
  return {
    ...session,
    elapsedTime: frames.length * 60,
    speed: 1,
    messageCount: messages.length,
    eventCount: events.length,
    errorCount: frames.reduce((total, frame) => total + frame.alarmCount, 0),
  };
}

function framesToBandwidth(
  frames: Awaited<ReturnType<MockDataSource['simulation']['listFrames']>>
): SimulationBandwidth[] {
  return frames.map((frame) => ({
    id: frame.id,
    sessionId: frame.sessionId,
    timestamp: Date.parse(frame.timestamp),
    bandwidthMbps: frame.bandwidthMbps,
    bandwidth: frame.bandwidthMbps,
    latencyMs: frame.latencyMs,
    portId: 'mock-port',
  }));
}

function framesToAlarms(
  frames: Awaited<ReturnType<MockDataSource['simulation']['listFrames']>>
): SimulationAlarm[] {
  return frames
    .filter((frame) => frame.alarmCount > 0)
    .map((frame) => ({
      alarmId: `alarm-${frame.id}`,
      sessionId: frame.sessionId,
      timestamp: Date.parse(frame.timestamp),
      severity: 'warning',
      message: `检测到 ${frame.alarmCount} 条链路告警`,
    }));
}

export function createSimulationHandlers(
  strategy: MockStrategy,
  dataSource: MockDataSource
): MockRuntimeHandler[] {
  return [
    http.post(createApiPath('/simulation/sessions'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const body =
            (await readJsonBody<{ projectId?: number; versionId?: number }>(request)) ?? {};
          const sessions = await dataSource.simulation.listSessions();
          const session =
            sessions.find(
              (item) =>
                (!body.projectId || item.projectId === Number(body.projectId)) &&
                (!body.versionId || item.versionId === Number(body.versionId))
            ) ?? sessions[0];
          return HttpResponse.json(
            resultSuccess(session ? { ...session, message: '只读仿真会话' } : null)
          );
        },
        { strategy, tag: 'simulation:session:create-readonly' }
      )
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/status'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const status = await readSessionStatus(dataSource, String(params.sessionId));
          return HttpResponse.json(resultSuccess(status ?? null), {
            status: status ? 200 : 404,
          });
        },
        { strategy, tag: 'simulation:status' }
      )
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/messages'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const limit = Number(getSearchParams(request).get('limit') ?? 100);
          const messages = await dataSource.simulation.listMessages(String(params.sessionId));
          return HttpResponse.json(
            resultSuccess({ items: historyToMessages(messages.slice(0, limit)) })
          );
        },
        { strategy, tag: 'simulation:messages' }
      )
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/bandwidth'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const frames = await dataSource.simulation.listFrames(String(params.sessionId));
          const bandwidth = framesToBandwidth(frames);
          const portId = getSearchParams(request).get('port_id');
          return HttpResponse.json(
            resultSuccess({
              items: portId ? bandwidth.filter((point) => point.portId === portId) : bandwidth,
            })
          );
        },
        { strategy, tag: 'simulation:bandwidth' }
      )
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/alarms'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const frames = await dataSource.simulation.listFrames(String(params.sessionId));
          return HttpResponse.json(resultSuccess({ items: framesToAlarms(frames) }));
        },
        { strategy, tag: 'simulation:alarms' }
      )
    ),
    http.get(createApiPath('/simulation/faults'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json(resultSuccess({ items: [] })), {
        strategy,
        tag: 'simulation:faults',
      })
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/faults'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json(resultSuccess({ items: [] })), {
        strategy,
        tag: 'simulation:session-faults',
      })
    ),
    http.get(createApiPath('/simulation/sessions/:sessionId/events'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const events = await dataSource.simulation.listEvents(String(params.sessionId));
          return HttpResponse.json(resultSuccess({ items: historyToEvents(events) }));
        },
        { strategy, tag: 'simulation:events' }
      )
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/export'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          const body = await readJsonBody<{
            exportFormat?: string;
            dataType?: string;
          }>(request);
          return HttpResponse.json(
            resultSuccess({
              sessionId: String(params.sessionId),
              exportFormat: body?.exportFormat ?? 'json',
              dataType: body?.dataType ?? 'all',
              downloadUrl: `/api/simulation/${params.sessionId}/export?format=${body?.exportFormat ?? 'json'}`,
            })
          );
        },
        { strategy, tag: 'simulation:export' }
      )
    ),
    http.get(createApiPath('/simulation/strategies'), ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess({ items: listSimulationStrategies() })),
        {
          strategy,
          tag: 'simulation:strategies',
        }
      )
    ),
    http.get(createApiPath('/simulation/:sessionId/statistics'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const status = await readSessionStatus(dataSource, String(params.sessionId));
          return HttpResponse.json(resultSuccess(status ?? null), {
            status: status ? 200 : 404,
          });
        },
        { strategy, tag: 'simulation:statistics' }
      )
    ),
    http.get(createApiPath('/simulation/:sessionId/export'), ({ request, params }) =>
      withBackendFallback(
        request,
        () =>
          new HttpResponse(`mock simulation export ${params.sessionId}`, {
            status: 200,
            headers: {
              'content-type': 'text/plain;charset=utf-8',
              'content-disposition': `attachment; filename="simulation-${params.sessionId}.txt"`,
            },
          }),
        { strategy, tag: 'simulation:legacy-export' }
      )
    ),
    http.post(createApiPath('/simulation/start'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:legacy-start',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/start'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-start-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/pause'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-pause-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/resume'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-resume-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/stop'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-stop-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/step'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-step-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/speed'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-control'), {
        strategy,
        tag: 'simulation:session-speed-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/faults'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:fault-create-unsupported',
      })
    ),
    http.delete(createApiPath('/simulation/faults/:faultId'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:fault-delete-unsupported',
      })
    ),
    http.delete(createApiPath('/simulation/sessions/:sessionId/faults'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:fault-clear-unsupported',
      })
    ),
    http.post(createApiPath('/simulation/sessions/:sessionId/events'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:event-create-unsupported',
      })
    ),
    http.put(createApiPath('/simulation/sessions/:sessionId/events/:eventId'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:event-update-unsupported',
      })
    ),
    http.delete(createApiPath('/simulation/sessions/:sessionId/events/:eventId'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:event-delete-unsupported',
      })
    ),
    http.post(
      createApiPath('/simulation/sessions/:sessionId/events/:eventId/trigger'),
      ({ request }) =>
        withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
          strategy,
          tag: 'simulation:event-trigger-unsupported',
        })
    ),
    http.post(createApiPath('/simulation/:sessionId/event'), ({ request }) =>
      withBackendFallback(request, () => notSupported(request, 'simulation-write'), {
        strategy,
        tag: 'simulation:legacy-event-unsupported',
      })
    ),
  ];
}
