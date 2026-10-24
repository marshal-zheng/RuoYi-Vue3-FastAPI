import { http, HttpResponse } from 'msw';

import { createApiPath } from '../constants';
import type {
  MockOpenApiPage,
  MockProjectResponse,
  MockProjectVersionResponse,
  MockTopologyResponse,
} from '../contracts';
import type { MockProject, MockProjectVersion, MockTopology } from '../data';
import { MockRepositoryError, type MockDataSource } from '../store';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import { getSearchParams, readJsonBody } from '../utils/request';
import { resultError, resultSuccess } from '../utils/response';
import { withBackendFallback } from '../utils/with-backend-fallback';

function toNumber(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

function toIdList(value: unknown): number[] {
  const values = Array.isArray(value) ? value : String(value ?? '').split(',');
  return Array.from(new Set(values.map(toNumber).filter((item): item is number => Boolean(item))));
}

function projectResponse(project: MockProject) {
  return {
    ...project,
    projectCode: `PRJ-${project.projectId}`,
    projectDesc: project.projectName,
    description: project.projectName,
    owner: 'mock',
    createBy: 'mock',
    updateBy: 'mock',
  } satisfies MockProjectResponse;
}

function versionResponse(version: MockProjectVersion) {
  return {
    ...version,
    versionNumber: version.versionNumber ?? `V${version.versionId}`,
    description: version.description ?? version.versionName,
    isLocked: version.isLocked ?? (version.locked ? '1' : '0'),
    createBy: 'mock',
    updateBy: 'mock',
  } satisfies MockProjectVersionResponse;
}

function topologyNumericId(
  topology: MockTopology | undefined,
  projectId: number,
  versionId?: number
) {
  const source = topology?.id ?? `topology-${projectId}-${versionId ?? 0}`;
  let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function topologyResponse(
  topology: MockTopology | undefined,
  projectId: number,
  versionId?: number
) {
  const response = {
    topologyId: topologyNumericId(topology, projectId, versionId),
    projectId,
    topologyData: topology?.graph ?? { nodes: [], edges: [] },
    graph: topology?.graph ?? { nodes: [], edges: [] },
    updateTime: topology?.updateTime ?? null,
  };
  return (versionId ? { ...response, versionId } : response) satisfies MockTopologyResponse;
}

function createdResourceLocation(request: Request, id: number): string {
  const location = new URL(request.url);
  location.pathname = `${location.pathname.replace(/\/clone\/?$/, '').replace(/\/$/, '')}/${id}`;
  location.search = '';
  location.hash = '';
  return location.href;
}

function fileResponse(filename: string, body: string, contentType = 'text/plain;charset=utf-8') {
  return new HttpResponse(body, {
    status: 200,
    headers: {
      'content-type': contentType,
      'content-disposition': `attachment; filename="${filename}"`,
      'X-Mock-Response': 'true',
      'X-Mock-Handler': 'project:file',
    },
  });
}

async function readBody<T extends Record<string, unknown>>(request: Request): Promise<T> {
  return ((await readJsonBody<T>(request)) ?? {}) as T;
}

function repositoryErrorResponse(error: unknown) {
  const status = error instanceof MockRepositoryError ? error.status : 500;
  const message = error instanceof Error ? error.message : 'Mock repository operation failed';
  return HttpResponse.json(resultError(message, { code: status }), { status });
}

export function createProjectHandlers(
  strategy: MockStrategy,
  dataSource: MockDataSource
): MockRuntimeHandler[] {
  return [
    http.get(createApiPath('/project/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const searchParams = getSearchParams(request);
          const page = await dataSource.project.list(Object.fromEntries(searchParams.entries()));
          return HttpResponse.json(
            resultSuccess({
              ...page,
              items: page.items.map(projectResponse),
            } satisfies MockOpenApiPage<MockProjectResponse>)
          );
        },
        { strategy, tag: 'project:list' }
      )
    ),
    http.get(createApiPath('/project/export/:projectId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const projectId = Number(params.projectId);
          const project = await dataSource.project.get(projectId);
          return fileResponse(
            `project-${projectId}.txt`,
            `mock project export: ${project?.projectName ?? projectId}`
          );
        },
        { strategy, tag: 'project:export' }
      )
    ),
    http.post(createApiPath('/project/export/batch'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const body = await readBody<{ projectIds?: Array<string | number> }>(request);
          return fileResponse(
            'projects.zip',
            `mock project batch export: ${(body.projectIds ?? []).join(',')}`
          );
        },
        { strategy, tag: 'project:export-batch' }
      )
    ),
    http.get(createApiPath('/project/topology/:projectId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const projectId = Number(params.projectId);
          const versionId =
            toNumber(getSearchParams(request).get('version_id')) ??
            toNumber(getSearchParams(request).get('versionId'));
          const topology = versionId
            ? await dataSource.topology.getByProjectVersion(projectId, versionId)
            : undefined;
          return HttpResponse.json(resultSuccess(topologyResponse(topology, projectId, versionId)));
        },
        { strategy, tag: 'project:topology:get' }
      )
    ),
    http.post(createApiPath('/project/topology/save'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<{
              projectId?: number | string;
              versionId?: number | string;
              topologyData?: unknown;
              graph?: unknown;
            }>(request);
            const projectId = toNumber(body.projectId);
            const versionId = toNumber(body.versionId);
            if (!projectId || !versionId) {
              return HttpResponse.json(
                resultError('projectId 和 versionId 不能为空', { code: 400 }),
                {
                  status: 400,
                }
              );
            }
            const topology = await dataSource.topology.save(
              projectId,
              versionId,
              body.topologyData ?? body.graph ?? { nodes: [], edges: [] }
            );
            return HttpResponse.json(
              resultSuccess(topologyResponse(topology, projectId, versionId))
            );
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:topology:save' }
      )
    ),
    http.get(createApiPath('/project/version/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const searchParams = getSearchParams(request);
          const projectId = toNumber(searchParams.get('projectId'));
          const page = await dataSource.version.list(
            projectId,
            Object.fromEntries(searchParams.entries())
          );
          return HttpResponse.json(
            resultSuccess({
              ...page,
              items: page.items.map(versionResponse),
            } satisfies MockOpenApiPage<MockProjectVersionResponse>)
          );
        },
        { strategy, tag: 'project:version:list' }
      )
    ),
    http.post(createApiPath('/project/version/clone'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<Record<string, unknown>>(request);
            const sourceVersionId = toNumber(body.sourceVersionId);
            if (
              !sourceVersionId ||
              !Number.isInteger(sourceVersionId) ||
              typeof body.versionNumber !== 'string' ||
              typeof body.versionName !== 'string'
            ) {
              return HttpResponse.json(
                resultError('sourceVersionId、versionNumber 和 versionName 为必填字段', {
                  code: 422,
                }),
                { status: 422, headers: { 'Content-Type': 'application/problem+json' } }
              );
            }
            const version = await dataSource.version.clone({
              sourceVersionId,
              versionNumber: body.versionNumber,
              versionName: body.versionName,
              ...(typeof body.description === 'string' ? { description: body.description } : {}),
            });
            return HttpResponse.json(resultSuccess(versionResponse(version)), {
              status: 201,
              headers: {
                Location: createdResourceLocation(request, version.versionId),
              },
            });
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:version:clone' }
      )
    ),
    http.put(createApiPath('/project/version/lock'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<{
              versionId?: number | string;
              isLocked?: string;
            }>(request);
            const versionId = toNumber(body.versionId);
            if (!versionId) {
              return HttpResponse.json(resultError('versionId 不能为空', { code: 400 }), {
                status: 400,
              });
            }
            const version =
              body.isLocked === '0'
                ? await dataSource.version.unlock(versionId)
                : await dataSource.version.lock(versionId);
            return HttpResponse.json(resultSuccess(versionResponse(version)));
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:version:lock' }
      )
    ),
    http.put(createApiPath('/project/version/unlock/project/:projectId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const projectId = Number(params.projectId);
          const count = await dataSource.version.unlockByProject(projectId);
          return HttpResponse.json(resultSuccess({ projectId, count }));
        },
        { strategy, tag: 'project:version:unlock-project' }
      )
    ),
    http.post(createApiPath('/project/version/export'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          const body = await readBody<{ versionId?: number | string }>(request);
          return fileResponse(
            `project-version-${body.versionId ?? 'unknown'}.doc`,
            'mock project version document',
            'application/msword'
          );
        },
        { strategy, tag: 'project:version:export-word' }
      )
    ),
    http.get(createApiPath('/project/version/export-excel/:versionId'), ({ request, params }) =>
      withBackendFallback(
        request,
        () =>
          fileResponse(
            `project-version-${params.versionId}.zip`,
            'mock project version excel appendices',
            'application/zip'
          ),
        { strategy, tag: 'project:version:export-excel' }
      )
    ),
    http.get(createApiPath('/project/version/export-xml/:versionId'), ({ request, params }) =>
      withBackendFallback(
        request,
        () =>
          fileResponse(
            `project-version-${params.versionId}.xml`,
            '<project-version />',
            'application/xml'
          ),
        { strategy, tag: 'project:version:export-xml' }
      )
    ),
    http.get(createApiPath('/project/version/:versionId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const version = await dataSource.version.get(Number(params.versionId));
          return version
            ? HttpResponse.json(resultSuccess(versionResponse(version)))
            : HttpResponse.json(resultError('版本不存在', { code: 404 }), {
                status: 404,
              });
        },
        { strategy, tag: 'project:version:get' }
      )
    ),
    http.post(createApiPath('/project/version'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<Partial<MockProjectVersion>>(request);
            const version = await dataSource.version.create(body);
            return HttpResponse.json(resultSuccess(versionResponse(version)), {
              status: 201,
              headers: {
                Location: createdResourceLocation(request, version.versionId),
              },
            });
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:version:create' }
      )
    ),
    http.put(createApiPath('/project/version'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<Partial<MockProjectVersion>>(request);
            const versionId = toNumber(body.versionId);
            if (!versionId) {
              return HttpResponse.json(resultError('versionId 不能为空', { code: 400 }), {
                status: 400,
              });
            }
            const version = await dataSource.version.update(versionId, body);
            return HttpResponse.json(resultSuccess(versionResponse(version)));
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:version:update' }
      )
    ),
    http.delete(createApiPath('/project/version/:versionIds'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            await Promise.all(
              toIdList(params.versionIds).map((id) => dataSource.version.delete(id))
            );
            return new HttpResponse(null, { status: 204 });
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:version:delete' }
      )
    ),
    http.get(createApiPath('/project/:projectId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const project = await dataSource.project.get(Number(params.projectId));
          return project
            ? HttpResponse.json(resultSuccess(projectResponse(project)))
            : HttpResponse.json(resultError('项目不存在', { code: 404 }), {
                status: 404,
              });
        },
        { strategy, tag: 'project:get' }
      )
    ),
    http.post(createApiPath('/project'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const project = await dataSource.project.create(
              await readBody<Partial<MockProject>>(request)
            );
            const version = await dataSource.version.create({
              projectId: project.projectId,
              versionNumber: 'v1.0.0',
              versionName: '初始版本',
              description: '项目初始版本',
              status: '1',
            });
            return HttpResponse.json(
              resultSuccess({ ...projectResponse(project), versionId: version.versionId }),
              {
                status: 201,
                headers: {
                  Location: createdResourceLocation(request, project.projectId),
                },
              }
            );
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:create' }
      )
    ),
    http.put(createApiPath('/project'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            const body = await readBody<Partial<MockProject>>(request);
            const projectId = toNumber(body.projectId);
            if (!projectId) {
              return HttpResponse.json(resultError('projectId 不能为空', { code: 400 }), {
                status: 400,
              });
            }
            const project = await dataSource.project.update(projectId, body);
            return HttpResponse.json(resultSuccess(projectResponse(project)));
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:update' }
      )
    ),
    http.delete(createApiPath('/project/:projectIds'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          try {
            await dataSource.init();
            await Promise.all(
              toIdList(params.projectIds).map((id) => dataSource.project.delete(id))
            );
            return new HttpResponse(null, { status: 204 });
          } catch (error) {
            return repositoryErrorResponse(error);
          }
        },
        { strategy, tag: 'project:delete' }
      )
    ),
  ];
}
