import { beforeEach, describe, expect, it } from 'vitest';

import * as roleApi from '@/api/system/role';
import {
  createApiContractHandlers,
  createStatusHandler,
} from '../../mocks/api-contract-handlers';
import { mockServer } from '../../mocks/server';

describe('Role API contract', () => {
  beforeEach(() => {
    mockServer.use(...createApiContractHandlers());
  });

  it('loads role list and detail through the HTTP contract', async () => {
    const result = await roleApi.listRole({ page: 2, pageSize: 20, roleName: 'admin' });

    expect(result).toMatchObject({
      total: 1,
      page: 2,
      pageSize: 20,
      items: [
        expect.objectContaining({
          roleName: 'admin',
          roleKey: 'admin',
        }),
      ],
    });
    expect(result.pager).toMatchObject({ mode: 'offset', page: 2, size: 20, total: 1 });

    await expect(roleApi.getRole(1)).resolves.toMatchObject({
      roleId: 1,
      roleKey: 'admin',
    });
    await expect(roleApi.getRole('1')).resolves.toMatchObject({
      roleId: 1,
      roleName: '超级管理员',
    });
  });

  it('handles role mutations through real request serialization', async () => {
    await expect(
      roleApi.addRole({
        roleName: '测试角色',
        roleKey: 'test',
        roleSort: 1,
        status: '0',
        menuIds: [1, 2, 3],
      })
    ).resolves.toMatchObject({
      roleId: 1,
      roleKey: 'test',
      menuIds: [1, 2, 3],
    });

    await expect(
      roleApi.updateRole({
        roleId: 1,
        roleName: '更新角色',
        roleKey: 'updated',
      })
    ).resolves.toMatchObject({
      roleId: 1,
      roleKey: 'updated',
    });

    await expect(
      roleApi.dataScope({
        roleId: 1,
        dataScope: '2',
        deptIds: [1, 2, 3],
      })
    ).resolves.toMatchObject({
      roleId: 1,
      dataScope: '2',
      deptIds: [1, 2, 3],
    });

    await expect(roleApi.changeRoleStatus(1, '1')).resolves.toMatchObject({
      roleId: 1,
      status: '1',
    });

    await expect(roleApi.delRole('1,2,3')).resolves.toBeNull();
  });

  it('covers role authorization and dept tree endpoints via MSW', async () => {
    await expect(roleApi.allocatedUserList({ roleId: 1 })).resolves.toMatchObject({
      items: [expect.objectContaining({ userName: 'admin' })],
    });
    await expect(roleApi.unallocatedUserList({ roleId: 1 })).resolves.toMatchObject({
      items: [expect.objectContaining({ userName: 'guest' })],
    });
    await expect(roleApi.authUserCancel({ roleId: 1, userId: 2 })).resolves.toMatchObject({
      roleId: 1,
      userId: 2,
    });
    await expect(roleApi.authUserCancelAll({ roleId: 1, userIds: '2,3' })).resolves.toBeNull();
    await expect(roleApi.authUserSelectAll({ roleId: 1, userIds: '2,3' })).resolves.toBeNull();
    await expect(roleApi.deptTreeSelect(1)).resolves.toMatchObject({
      roleId: 1,
      checkedKeys: [100],
    });
  });

  it('surfaces role API failures from the request error mapping', async () => {
    mockServer.use(createStatusHandler('get', '/system/role/list', 503));
    await expect(roleApi.listRole({})).rejects.toMatchObject({ status: 503 });

    mockServer.use(createStatusHandler('get', '/system/role/list', 429));
    await expect(roleApi.listRole({})).rejects.toMatchObject({ status: 429 });
  });
});
