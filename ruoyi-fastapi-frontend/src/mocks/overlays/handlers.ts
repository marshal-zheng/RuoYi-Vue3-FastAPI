import { delay as mswDelay, http } from 'msw';

import type {
  MockProjectRepository,
  MockProjectVersionRepository,
  MockSimulationReadRepository,
  MockTopologyRepository,
} from '../store/repositories';
import type { MockDataSource } from '../store';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import {
  createOverlayPageResponse,
  createOverlayProblemResponse,
  createOverlaySuccessResponse,
} from './response';
import { resolveMockOverlayEntries } from './runtime';
import type {
  MockOverlayActivationInput,
  MockOverlayHttpMethod,
  MockOverlayRegistryEntry,
} from './types';

export interface ReadonlyOverlayDataSource {
  init(): Promise<void>;
  project: Pick<MockProjectRepository, 'list' | 'get'>;
  version: Pick<MockProjectVersionRepository, 'list' | 'get'>;
  topology: Pick<MockTopologyRepository, 'getByProjectVersion'>;
  simulation: MockSimulationReadRepository;
}

export interface CreateMockOverlayHandlersOptions {
  strategy: MockStrategy;
  dataSource: MockDataSource;
  apiPrefix?: string;
  overlays?: MockOverlayActivationInput;
}

function toNumber(value: unknown, fallback?: number): number | undefined {
  const parsed = Number(value);
  if (Number.isFinite(parsed) && parsed > 0) return parsed;
  return fallback;
}

function queryPage(request: Request) {
  const searchParams = new URL(request.url).searchParams;
  return {
    page: toNumber(searchParams.get('page'), 1) ?? 1,
    pageSize: toNumber(searchParams.get('pageSize') ?? searchParams.get('page_size'), 10) ?? 10,
  };
}

function normalizeApiPrefix(apiPrefix: string) {
  const normalized = apiPrefix.startsWith('/') ? apiPrefix : `/${apiPrefix}`;
  return normalized.replace(/\/+$/, '') || '/api';
}

function pathWithApiPrefix(mswPath: string, apiPrefix: string) {
  const prefix = normalizeApiPrefix(apiPrefix);
  const suffix = mswPath.replace(/^\/api(?=\/|$)/, '');
  if (/^https?:\/\//i.test(prefix)) {
    return `${prefix}${suffix}`;
  }
  return `*${prefix}${suffix}`;
}

function handlerForMethod(method: MockOverlayHttpMethod) {
  switch (method) {
    case 'GET':
      return http.get;
    case 'POST':
      return http.post;
    case 'PUT':
      return http.put;
    case 'DELETE':
      return http.delete;
    case 'PATCH':
      return http.patch;
    case 'OPTIONS':
      return http.options;
    case 'HEAD':
      return http.head;
    default:
      return http.all;
  }
}

export function createReadonlyOverlayDataSource(
  dataSource: MockDataSource
): ReadonlyOverlayDataSource {
  return {
    init: () => dataSource.init(),
    project: {
      list: (query) => dataSource.project.list(query),
      get: (projectId) => dataSource.project.get(projectId),
    },
    version: {
      list: (projectId, query) => dataSource.version.list(projectId, query),
      get: (versionId) => dataSource.version.get(versionId),
    },
    topology: {
      getByProjectVersion: (projectId, versionId) =>
        dataSource.topology.getByProjectVersion(projectId, versionId),
    },
    simulation: {
      listSessions: () => dataSource.simulation.listSessions(),
      getSession: (sessionId) => dataSource.simulation.getSession(sessionId),
      listFrames: (sessionId) => dataSource.simulation.listFrames(sessionId),
      listMessages: (sessionId) => dataSource.simulation.listMessages(sessionId),
      listEvents: (sessionId) => dataSource.simulation.listEvents(sessionId),
    },
  };
}

async function topologyProjection(
  request: Request,
  params: Record<string, unknown>,
  dataSource: ReadonlyOverlayDataSource
) {
  const projectId = toNumber(params.projectId);
  const searchParams = new URL(request.url).searchParams;
  const versionId =
    toNumber(searchParams.get('version_id')) ?? toNumber(searchParams.get('versionId'));
  const topology =
    projectId && versionId
      ? await dataSource.topology.getByProjectVersion(projectId, versionId)
      : undefined;
  const topologyId = topology?.id
    ? Math.abs(topology.id.split('').reduce((total, char) => total + char.charCodeAt(0), 0))
    : (projectId ?? 0);

  return {
    topologyId,
    projectId: projectId ?? 0,
    ...(versionId ? { versionId } : {}),
    topologyData: topology?.graph ?? { nodes: [], edges: [] },
    graph: topology?.graph ?? { nodes: [], edges: [] },
    updateTime: topology?.updateTime ?? null,
  };
}

async function readonlySimulationProjection(dataSource: ReadonlyOverlayDataSource) {
  const sessions = await dataSource.simulation.listSessions();
  const session = sessions[0] ?? null;
  return session
    ? {
        ...session,
        readonly: true,
        status: session.status ?? 'readonly',
      }
    : null;
}

async function createSuccessProjection(
  entry: MockOverlayRegistryEntry,
  request: Request,
  params: Record<string, unknown>,
  dataSource: ReadonlyOverlayDataSource
) {
  if (entry.response?.projection === 'empty-page') {
    return {
      kind: 'page' as const,
      items: [],
      total: 0,
      ...queryPage(request),
    };
  }

  if (entry.response?.projection === 'empty-list') {
    return {
      kind: 'data' as const,
      data: [],
    };
  }

  if (entry.response?.projection === 'readonly-view') {
    return {
      kind: 'data' as const,
      data: await readonlySimulationProjection(dataSource),
    };
  }

  if (entry.target.handlerTag === 'project:topology:get') {
    return {
      kind: 'data' as const,
      data: await topologyProjection(request, params, dataSource),
    };
  }

  return {
    kind: 'data' as const,
    data: null,
  };
}

function shouldReturnProblem(entry: MockOverlayRegistryEntry) {
  return ['problem', 'forbidden', 'timeout', 'unsupported'].includes(entry.stateType);
}

function createSingleOverlayHandler(
  entry: MockOverlayRegistryEntry,
  options: {
    strategy: MockStrategy;
    apiPrefix: string;
    dataSource: ReadonlyOverlayDataSource;
  }
): MockRuntimeHandler {
  const register = handlerForMethod(entry.target.method);
  const path = pathWithApiPrefix(entry.target.mswPath, options.apiPrefix);

  return register(path, async ({ request, params }) => {
    await options.dataSource.init();

    if (entry.response?.delayMs) {
      await mswDelay(entry.response.delayMs);
    }

    if (shouldReturnProblem(entry)) {
      return createOverlayProblemResponse({
        request,
        entry,
        strategy: options.strategy,
      });
    }

    const projection = await createSuccessProjection(
      entry,
      request,
      params as Record<string, unknown>,
      options.dataSource
    );

    if (projection.kind === 'page') {
      return createOverlayPageResponse({
        request,
        entry,
        strategy: options.strategy,
        items: projection.items,
        total: projection.total,
        page: projection.page,
        pageSize: projection.pageSize,
      });
    }

    return createOverlaySuccessResponse({
      request,
      entry,
      strategy: options.strategy,
      data: projection.data,
    });
  });
}

export function createMockOverlayHandlers(
  options: CreateMockOverlayHandlersOptions
): MockRuntimeHandler[] {
  const entries = resolveMockOverlayEntries(options.overlays);
  if (!entries.length) return [];

  const readOnlyDataSource = createReadonlyOverlayDataSource(options.dataSource);
  return entries.map((entry) =>
    createSingleOverlayHandler(entry, {
      strategy: options.strategy,
      apiPrefix: options.apiPrefix ?? '/api',
      dataSource: readOnlyDataSource,
    })
  );
}
