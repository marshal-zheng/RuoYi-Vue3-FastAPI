import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import { ScenarioRepository, SystemRepository } from '@/demo/repositories';
import { defaultDemoScenario } from '@/demo/scenarios';

import { DemoSystemService } from './system';

let db: DemoOfflineDb;
let systemService: DemoSystemService;

describe('DemoSystemService', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-system-service-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    systemService = new DemoSystemService(new SystemRepository(db));
  });

  afterEach(async () => {
    await db.delete();
  });

  it('builds route trees from scenario menus', async () => {
    const routers = await systemService.getRouters(['admin']);
    const projectRoute = routers.find((route) => route.path === '/project');
    const systemRoute = routers.find((route) => route.path === '/system');

    expect(routers).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: '/',
          component: 'Layout',
          children: expect.arrayContaining([
            expect.objectContaining({
              path: 'index',
              component: 'dashboard/index',
            }),
          ]),
        }),
        expect.objectContaining({
          path: '/project',
          component: 'Layout',
        }),
        expect.objectContaining({
          path: '/system',
          component: 'Layout',
        }),
        expect.objectContaining({
          path: '/monitor',
          component: 'Layout',
        }),
        expect.objectContaining({
          path: '/tool',
          component: 'Layout',
        }),
        expect.objectContaining({
          path: '/protocol',
          component: 'Layout',
        }),
        expect.objectContaining({
          path: '/device',
          component: 'Layout',
        }),
      ])
    );

    expect(systemRoute?.children).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'user',
          component: 'system/user/index',
        }),
        expect.objectContaining({
          path: 'role',
          component: 'system/role/index',
        }),
        expect.objectContaining({
          path: 'menu',
          component: 'system/menu/index',
        }),
        expect.objectContaining({
          path: 'dept',
          component: 'system/dept/index',
        }),
        expect.objectContaining({
          path: 'dict',
          component: 'system/dict/index',
        }),
        expect.objectContaining({
          path: 'log',
          component: 'ParentView',
        }),
      ])
    );
    expect(projectRoute?.children).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'project',
          component: 'project/index',
        }),
        expect.objectContaining({
          path: 'detail-entry',
          component: 'project/entry',
          meta: expect.objectContaining({
            title: '工程详情',
            entryTarget: 'detail',
          }),
        }),
        expect.objectContaining({
          path: 'topology-entry',
          component: 'project/entry',
          meta: expect.objectContaining({
            title: '拓扑设计',
            entryTarget: 'topology',
          }),
        }),
        expect.objectContaining({
          path: 'simulation-entry',
          component: 'project/entry',
          meta: expect.objectContaining({
            title: '版本仿真',
            entryTarget: 'simulation',
          }),
        }),
      ])
    );
    expect(projectRoute?.alwaysShow).toBe(true);
  });

  it('returns dictionary data and department trees from scenario data', async () => {
    await expect(systemService.getDictsByType('sys_normal_disable')).resolves.toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          dictCode: 1,
          dictLabel: '正常',
          dictValue: '0',
        }),
      ])
    );

    await expect(systemService.getDepartmentTree()).resolves.toEqual([
      expect.objectContaining({
        id: 100,
        label: '离线演示组织',
        disabled: false,
      }),
    ]);
  });
});
