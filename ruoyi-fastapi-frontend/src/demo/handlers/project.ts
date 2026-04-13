import { http, type HttpHandler } from 'msw';

import { getDemoOfflineDb } from '@/demo/db';
import {
  AuthRepository,
  ProjectRepository,
  ProjectVersionRepository,
  TopologyRepository,
} from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthService, DemoProjectService } from '@/demo/services';

import {
  createDemoApiPath,
  demoErrorResponse,
  demoFileResponse,
  demoJsonResponse,
  getDemoRequestToken,
  readDemoRequestBody,
} from './utils';

export interface CreateDemoProjectHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

function createAuthService(): DemoAuthService {
  return new DemoAuthService(new AuthRepository(getDemoOfflineDb()));
}

function createProjectService(): DemoProjectService {
  const db = getDemoOfflineDb();
  return new DemoProjectService(
    new ProjectRepository(db),
    new ProjectVersionRepository(db),
    new TopologyRepository(db)
  );
}

async function ensureCurrentOperator(request: Request): Promise<string> {
  const currentUser = await createAuthService().getInfo(getDemoRequestToken(request));
  const user = currentUser.user as Record<string, unknown>;
  const userName = user.userName;
  const nickName = user.nickName;

  return typeof userName === 'string'
    ? userName
    : typeof nickName === 'string'
      ? nickName
      : 'demo-offline';
}

function readSearchParam(
  request: Request,
  name: string,
  fallbackName?: string
): string | undefined {
  const searchParams = new URL(request.url).searchParams;
  return (
    searchParams.get(name) ?? (fallbackName ? searchParams.get(fallbackName) : null) ?? undefined
  );
}

export function createDemoProjectHandlers({
  config,
  logger,
}: CreateDemoProjectHandlersOptions): HttpHandler[] {
  const path = (value: string) => createDemoApiPath(config, value);

  return [
    http.get(path('/project/list'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const page = await createProjectService().listProjects({
          pageNum: readSearchParam(request, 'pageNum', 'page'),
          pageSize: readSearchParam(request, 'pageSize', 'size'),
          projectName: readSearchParam(request, 'projectName'),
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(
          config,
          'project:list',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: page,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:list');
      }
    }),
    http.post(path('/project/export/batch'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const body = await readDemoRequestBody<{ projectIds?: Array<string | number> }>(request);
        const file = await createProjectService().exportProjects(body.projectIds ?? []);

        logger.debug('demo-offline 返回工程批量导出占位文件。', {
          handler: 'project:export-batch',
          count: body.projectIds?.length ?? 0,
        });

        return demoFileResponse(config, 'project:export-batch', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:export-batch');
      }
    }),
    http.get(path('/project/export/:projectId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const file = await createProjectService().exportProject(Number(params.projectId));
        return demoFileResponse(config, 'project:export', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:export');
      }
    }),
    http.get(path('/project/topology/:projectId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const projectId = Number(params.projectId);
        const versionId = readSearchParam(request, 'version_id', 'versionId');
        const topology = await createProjectService().getProjectTopology(
          projectId,
          versionId ? Number(versionId) : undefined
        );

        return demoJsonResponse(
          config,
          'project:topology:get',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: topology,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:topology:get');
      }
    }),
    http.post(path('/project/topology/save'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          projectId?: number | string;
          versionId?: number | string;
          topologyData?: Record<string, unknown>;
        }>(request);
        const topology = await createProjectService().saveProjectTopology(body, operator);

        logger.info('demo-offline 已保存拓扑数据。', {
          handler: 'project:topology:save',
          projectId: topology.projectId,
          versionId: topology.versionId,
        });

        return demoJsonResponse(
          config,
          'project:topology:save',
          {
            code: 200,
            msg: '拓扑保存成功',
            type: 'success',
            data: topology,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:topology:save');
      }
    }),
    http.get(path('/project/version/list'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const page = await createProjectService().listProjectVersions({
          pageNum: readSearchParam(request, 'pageNum', 'page'),
          pageSize: readSearchParam(request, 'pageSize', 'size'),
          projectId: readSearchParam(request, 'projectId'),
          versionName: readSearchParam(request, 'versionName'),
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(
          config,
          'project:version:list',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: page,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:list');
      }
    }),
    http.post(path('/project/version/clone'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          sourceVersionId?: number | string;
          versionNumber?: string;
          versionName?: string;
          description?: string;
        }>(request);
        const version = await createProjectService().cloneProjectVersion(body, operator);

        return demoJsonResponse(
          config,
          'project:version:clone',
          {
            code: 200,
            msg: '版本克隆成功',
            type: 'success',
            data: version,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:clone');
      }
    }),
    http.put(path('/project/version/lock'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          versionId?: number | string;
          isLocked?: '0' | '1';
        }>(request);
        const version = await createProjectService().lockProjectVersion(
          Number(body.versionId),
          body.isLocked === '1' ? '1' : '0',
          operator
        );

        return demoJsonResponse(
          config,
          'project:version:lock',
          {
            code: 200,
            msg: body.isLocked === '1' ? '版本固化成功' : '解除固化成功',
            type: 'success',
            data: version,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:lock');
      }
    }),
    http.put(path('/project/version/unlock/project/:projectId'), async ({ request, params }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const count = await createProjectService().unlockProjectVersions(
          Number(params.projectId),
          operator
        );

        return demoJsonResponse(
          config,
          'project:version:unlock-project',
          {
            code: 200,
            msg: '批量解除固化成功',
            type: 'success',
            data: {
              projectId: Number(params.projectId),
              count,
            },
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:unlock-project');
      }
    }),
    http.post(path('/project/version/export'), async ({ request }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const body = await readDemoRequestBody<{
          versionId?: number | string;
          imageBase64?: string;
        }>(request);
        const file = await createProjectService().exportProjectVersion(
          Number(body.versionId),
          'word',
          body.imageBase64
        );

        return demoFileResponse(config, 'project:version:export-word', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:export-word');
      }
    }),
    http.get(path('/project/version/export-excel/:versionId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const file = await createProjectService().exportProjectVersion(
          Number(params.versionId),
          'excel'
        );

        return demoFileResponse(config, 'project:version:export-excel', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:export-excel');
      }
    }),
    http.get(path('/project/version/export-xml/:versionId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const file = await createProjectService().exportProjectVersion(
          Number(params.versionId),
          'xml'
        );

        return demoFileResponse(config, 'project:version:export-xml', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:export-xml');
      }
    }),
    http.get(path('/project/version/:versionId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const version = await createProjectService().getProjectVersion(Number(params.versionId));

        return demoJsonResponse(
          config,
          'project:version:get',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: version,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:get');
      }
    }),
    http.post(path('/project/version'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          projectId?: number | string;
          versionNumber?: string;
          versionName?: string;
          description?: string;
          status?: '0' | '1';
        }>(request);
        const version = await createProjectService().createProjectVersion(body, operator);

        return demoJsonResponse(
          config,
          'project:version:create',
          {
            code: 200,
            msg: '版本新增成功',
            type: 'success',
            data: version,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:create');
      }
    }),
    http.put(path('/project/version'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          versionId?: number | string;
          versionNumber?: string;
          versionName?: string;
          description?: string;
        }>(request);
        const version = await createProjectService().updateProjectVersion(body, operator);

        return demoJsonResponse(
          config,
          'project:version:update',
          {
            code: 200,
            msg: '版本编辑成功',
            type: 'success',
            data: version,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:update');
      }
    }),
    http.delete(path('/project/version/:versionIds'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        await createProjectService().deleteProjectVersions(String(params.versionIds ?? ''));

        return demoJsonResponse(
          config,
          'project:version:delete',
          {
            code: 200,
            msg: '删除成功',
            type: 'success',
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:version:delete');
      }
    }),
    http.get(path('/project/:projectId'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        const project = await createProjectService().getProject(Number(params.projectId));

        return demoJsonResponse(
          config,
          'project:get',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: project,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:get');
      }
    }),
    http.post(path('/project'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          projectName?: string;
          projectCode?: string;
          projectDesc?: string;
          description?: string;
          status?: '0' | '1';
        }>(request);
        const project = await createProjectService().createProject(body, operator);

        return demoJsonResponse(
          config,
          'project:create',
          {
            code: 200,
            msg: '新增成功',
            type: 'success',
            data: project,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:create');
      }
    }),
    http.put(path('/project'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{
          projectId?: number | string;
          projectName?: string;
          projectCode?: string;
          projectDesc?: string;
          description?: string;
          status?: '0' | '1';
        }>(request);
        const project = await createProjectService().updateProject(body, operator);

        return demoJsonResponse(
          config,
          'project:update',
          {
            code: 200,
            msg: '修改成功',
            type: 'success',
            data: project,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:update');
      }
    }),
    http.delete(path('/project/:projectIds'), async ({ request, params }) => {
      try {
        await createAuthService().getInfo(getDemoRequestToken(request));
        await createProjectService().deleteProjects(String(params.projectIds ?? ''));

        return demoJsonResponse(
          config,
          'project:delete',
          {
            code: 200,
            msg: '删除成功',
            type: 'success',
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'project:delete');
      }
    }),
  ];
}
