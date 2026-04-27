import { beforeEach, describe, expect, it } from 'vitest';

import * as menuApi from '@/api/system/menu';
import {
  createApiContractHandlers,
  createStatusHandler,
} from '../../mocks/api-contract-handlers';
import { mockServer } from '../../mocks/server';

describe('Menu API contract', () => {
  beforeEach(() => {
    mockServer.use(...createApiContractHandlers());
  });

  it('loads menu list, details, and role tree through MSW', async () => {
    await expect(menuApi.listMenu({ menuName: '系统管理' })).resolves.toEqual([
      expect.objectContaining({ menuName: '系统管理' }),
    ]);
    await expect(menuApi.getMenu(1)).resolves.toMatchObject({
      menuId: 1,
      menuType: 'M',
    });
    await expect(menuApi.treeselect()).resolves.toEqual([
      expect.objectContaining({ label: '系统管理' }),
    ]);
    await expect(menuApi.roleMenuTreeselect(1)).resolves.toMatchObject({
      roleId: 1,
      checkedKeys: [1, 2],
    });
  });

  it('handles menu mutations via HTTP contract responses', async () => {
    await expect(
      menuApi.addMenu({
        menuName: '测试菜单',
        parentId: 0,
        menuType: 'C',
      })
    ).resolves.toMatchObject({ menuId: 9, menuName: '测试菜单' });

    await expect(
      menuApi.updateMenu({
        menuId: 9,
        menuName: '更新菜单',
      })
    ).resolves.toMatchObject({ menuId: 9, menuName: '更新菜单' });

    await expect(menuApi.delMenu(9)).resolves.toBeNull();
  });

  it('surfaces server-side menu failures through the request error mapping', async () => {
    mockServer.use(createStatusHandler('get', '/system/menu/list', 503));

    await expect(menuApi.listMenu({})).rejects.toMatchObject({ status: 503 });
  });
});
