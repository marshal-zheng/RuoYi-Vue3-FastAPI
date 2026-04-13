import { http, type HttpHandler } from 'msw';

import { getDemoOfflineDb } from '@/demo/db';
import { AuthRepository, SystemRepository } from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthService, DemoSystemService } from '@/demo/services';

import {
  createDemoApiPath,
  demoErrorResponse,
  demoJsonResponse,
  getDemoRequestToken,
} from './utils';

export interface CreateDemoSystemHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

function createAuthService(): DemoAuthService {
  return new DemoAuthService(new AuthRepository(getDemoOfflineDb()));
}

function createSystemService(): DemoSystemService {
  return new DemoSystemService(new SystemRepository(getDemoOfflineDb()));
}

async function resolveRoleKeys(request: Request): Promise<string[]> {
  const currentUser = await createAuthService().getInfo(getDemoRequestToken(request));
  return currentUser.roles;
}

export function createDemoSystemHandlers({
  config,
  logger,
}: CreateDemoSystemHandlersOptions): HttpHandler[] {
  const path = (value: string) => createDemoApiPath(config, value);

  return [
    http.get(path('/getRouters'), async ({ request }) => {
      try {
        const roleKeys = await resolveRoleKeys(request);
        const routers = await createSystemService().getRouters(roleKeys);

        logger.debug('demo-offline 返回菜单路由。', {
          handler: 'system:getRouters',
          count: routers.length,
        });

        return demoJsonResponse(
          config,
          'system:getRouters',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: routers,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system:getRouters');
      }
    }),
    http.get(path('/system/dict/data/type/:dictType'), async ({ request, params }) => {
      try {
        await resolveRoleKeys(request);
        const dictType = String(params.dictType ?? '');
        const dicts = await createSystemService().getDictsByType(dictType);

        return demoJsonResponse(
          config,
          `system:dict:${dictType}`,
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: dicts,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system:dict');
      }
    }),
    http.get(path('/system/user/deptTree'), async ({ request }) => {
      try {
        await resolveRoleKeys(request);
        const tree = await createSystemService().getDepartmentTree();

        return demoJsonResponse(
          config,
          'system:user:deptTree',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: tree,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system:user:deptTree');
      }
    }),
    http.get(path('/system/dept/treeselect'), async ({ request }) => {
      try {
        await resolveRoleKeys(request);
        const tree = await createSystemService().getDepartmentTree();

        return demoJsonResponse(
          config,
          'system:dept:treeselect',
          {
            code: 200,
            msg: '操作成功',
            type: 'success',
            data: tree,
          },
          200
        );
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system:dept:treeselect');
      }
    }),
  ];
}
