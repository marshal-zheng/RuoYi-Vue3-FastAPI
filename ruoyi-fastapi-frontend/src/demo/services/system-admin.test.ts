import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import { ScenarioRepository, SystemAdminRepository } from '@/demo/repositories';
import { defaultDemoScenario } from '@/demo/scenarios';

import { DemoSystemAdminService } from './system-admin';

let db: DemoOfflineDb;
let systemAdminService: DemoSystemAdminService;

describe('DemoSystemAdminService', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-system-admin-service-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    systemAdminService = new DemoSystemAdminService(new SystemAdminRepository(db), db);
  });

  afterEach(async () => {
    await db.delete();
  });

  it('lists offline users with department and role context', async () => {
    const page = await systemAdminService.listUsers({
      page: 1,
      pageSize: 20,
    });

    expect(page.total).toBe(4);
    expect(page.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          userName: 'admin',
          dept: expect.objectContaining({
            deptName: '离线演示组织',
          }),
        }),
        expect.objectContaining({
          userName: 'demo_user',
          role: expect.arrayContaining([
            expect.objectContaining({
              roleKey: 'ops',
            }),
          ]),
        }),
      ])
    );

    const scoped = await systemAdminService.listUsers({
      deptId: 102,
      page: 1,
      pageSize: 20,
    });

    expect(scoped.items.map((row) => row.userName)).toEqual(
      expect.arrayContaining(['demo_user', 'data_viewer', 'qa_case'])
    );
  });

  it('keeps user/account authorization data in sync across CRUD flows', async () => {
    const created = await systemAdminService.createUser(
      {
        deptId: 103,
        userName: 'new_ops',
        nickName: '新运维',
        password: 'ops12345',
        roleIds: [2],
        postIds: [2],
        status: '0',
      },
      'admin'
    );

    const createdUserId = Number(created.userId);
    expect(createdUserId).toBeGreaterThan(4);

    const detail = await systemAdminService.getUserDetail(createdUserId);
    expect(detail).toEqual(
      expect.objectContaining({
        userName: 'new_ops',
        roleIds: [2],
        postIds: [2],
        roles: expect.arrayContaining([
          expect.objectContaining({
            roleKey: 'ops',
          }),
        ]),
      })
    );

    await systemAdminService.changeUserStatus(createdUserId, '1', 'admin');
    await systemAdminService.updateUserAuthRole(
      {
        userId: createdUserId,
        roleIds: '3',
      },
      'admin'
    );

    const authRole = await systemAdminService.getUserAuthRole(createdUserId);
    expect(authRole).toEqual(
      expect.objectContaining({
        user: expect.objectContaining({
          status: '1',
        }),
        roles: expect.arrayContaining([
          expect.objectContaining({
            roleKey: 'viewer',
            flag: true,
          }),
        ]),
      })
    );

    await expect(db.accounts.get('new_ops')).resolves.toEqual(
      expect.objectContaining({
        roleIds: [3],
        roles: ['viewer'],
        user: expect.objectContaining({
          status: '1',
        }),
      })
    );
  });

  it('supports role, menu, department and dict management data flows', async () => {
    const roleTree = await systemAdminService.getRoleDeptTree(2);
    expect(roleTree).toEqual(
      expect.objectContaining({
        checkedKeys: expect.arrayContaining([102, 103]),
        depts: expect.any(Array),
      })
    );

    const roleMenuTree = await systemAdminService.getRoleMenuTree(2);
    expect(roleMenuTree).toEqual(
      expect.objectContaining({
        checkedKeys: expect.arrayContaining([21, 22, 23, 24, 26]),
        menus: expect.any(Array),
      })
    );

    const menuList = await systemAdminService.listMenus({ menuName: '用户' });
    expect(menuList).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          menuId: 21,
          component: 'system/user/index',
        }),
      ])
    );

    const dictType = await systemAdminService.createDictType({
      dictName: '测试字典',
      dictType: 'sys_demo_case',
      status: '0',
      remark: '用于离线测试',
    });

    await systemAdminService.createDictData({
      dictType: 'sys_demo_case',
      dictLabel: '启用',
      dictValue: 'enabled',
      dictSort: 1,
      status: '0',
    });

    const dictTypes = await systemAdminService.listDictTypes({
      dictType: 'sys_demo_case',
      page: 1,
      pageSize: 10,
    });
    expect(dictTypes.total).toBe(1);
    expect(Number(dictType.dictId)).toBeGreaterThan(3);

    const dictData = await systemAdminService.listDictData({
      dictType: 'sys_demo_case',
      page: 1,
      pageSize: 10,
    });
    expect(dictData.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          dictLabel: '启用',
          dictValue: 'enabled',
        }),
      ])
    );

    const deptList = await systemAdminService.listDepartmentsExcludeChildren(102);
    expect(deptList.map((item) => item.deptId)).not.toEqual(
      expect.arrayContaining([102, 103, 104])
    );
  });
});
