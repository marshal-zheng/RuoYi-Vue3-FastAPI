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
      ])
    );
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
