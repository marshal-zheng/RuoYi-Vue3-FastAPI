import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises } from '@vue/test-utils';
import { isQueryRequest } from '@zxio/http';
import * as api from '@/api/system/role';
import * as menuApi from '@/api/system/menu';
import { queryClient } from '../client';
import { endQuerySession, setQuerySession } from '../context';
import { userKeys } from './user';
import * as role from './role';

vi.mock('@/api/system/role', () => ({
  listRole: vi.fn(),
  getRole: vi.fn(),
  deptTreeSelect: vi.fn(),
  addRole: vi.fn(),
  updateRole: vi.fn(),
  delRole: vi.fn(),
  changeRoleStatus: vi.fn(),
  dataScope: vi.fn(),
}));
vi.mock('@/api/system/menu', () => ({
  treeselect: vi.fn(),
  roleMenuTreeselect: vi.fn(),
}));
const detail = {
  remarkText: '',
  roleId: 2,
  roleName: 'Operator',
  roleKey: 'operator',
  roleSort: 1,
  status: '0' as const,
};
beforeEach(() => {
  endQuerySession();
  queryClient.clear();
  vi.resetAllMocks();
  setQuerySession(1, [], []);
});
afterEach(() => {
  endQuerySession();
  queryClient.clear();
});

describe('role resource coordination', () => {
  it('shares equivalent submitted filters and snapshots page parameters', async () => {
    expect(role).toHaveProperty('roleListOptions');
    const scope = setQuerySession(1, [], []);
    const draft = {
      roleName: ' Operator ',
      roleKey: ' operator ',
      status: '0',
      page: '2',
      pageSize: '20',
      dateRange: ['2026-10-01', '2026-10-17'],
    };
    const first = role.roleListOptions(scope, draft);
    const same = role.roleListOptions(scope, {
      ...draft,
      roleName: 'Operator',
    });
    draft.roleName = 'later';
    draft.dateRange[0] = 'later';
    let resolve!: (value: Awaited<ReturnType<typeof api.listRole>>) => void;
    vi.mocked(api.listRole).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    const a = queryClient.fetchQuery(first),
      b = queryClient.fetchQuery(same);
    expect(api.listRole).toHaveBeenCalledTimes(1);
    expect(api.listRole).toHaveBeenCalledWith(
      {
        roleName: 'Operator',
        roleKey: 'operator',
        status: '0',
        page: 2,
        pageSize: 20,
        beginTime: '2026-10-01',
        endTime: '2026-10-17',
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(isQueryRequest(vi.mocked(api.listRole).mock.calls[0][1]?.options)).toBe(true);
    resolve({ items: [detail], total: 1, page: 2, pageSize: 20 });
    expect(await a).toEqual(await b);
    expect(role.normalizeRoleFilters({ dateRange: null, status: '', roleName: ' ' })).toEqual({});
  });

  it('separates permission tree identities and reads current editor snapshots', async () => {
    expect(role).toHaveProperty('readRoleEditor');
    const scope = setQuerySession(1, [], []);
    vi.mocked(api.getRole).mockResolvedValue(detail);
    vi.mocked(menuApi.treeselect).mockResolvedValue({
      items: [{ id: 1, label: 'Create menu' }],
    });
    vi.mocked(menuApi.roleMenuTreeselect).mockResolvedValue({
      menus: [{ id: 2, label: 'Menu' }],
      checkedKeys: [2],
    });
    vi.mocked(api.deptTreeSelect).mockResolvedValue({
      depts: [{ id: 3, label: 'Dept' }],
      checkedKeys: [3],
    });
    const [editor, dataScope] = await Promise.all([
      role.readRoleEditor(scope, 2),
      role.readRoleDataScopeEditor(scope, 2),
    ]);
    expect(api.getRole).toHaveBeenCalledTimes(1);
    expect(editor.menus.checkedKeys).toEqual([2]);
    expect(dataScope.depts.checkedKeys).toEqual([3]);
    editor.menus.menus[0].label = 'Draft tree';
    dataScope.depts.checkedKeys.push(99);
    expect(queryClient.getQueryData(role.roleMenuOptions(scope, 2).queryKey)?.menus[0].label).toBe(
      'Menu'
    );
    expect(queryClient.getQueryData(role.roleDeptOptions(scope, 2).queryKey)?.checkedKeys).toEqual([
      3,
    ]);
    expect(role.roleMenuOptions(scope, 2).queryKey).not.toEqual(
      role.roleDeptOptions(scope, 2).queryKey
    );
    expect((await role.readRoleEditor(scope)).menus.menus[0].label).toBe('Create menu');
    vi.mocked(api.getRole).mockResolvedValue({ ...detail, roleName: 'Latest' });
    expect((await role.readRoleEditor(scope, 2)).data?.roleName).toBe('Latest');
    expect(isQueryRequest(vi.mocked(api.getRole).mock.calls[0][1]?.requestOptions)).toBe(true);
  });

  it('ends one opening without cancelling a shared snapshot and rejects ended scopes', async () => {
    expect(role).toHaveProperty('readRoleEditor');
    const scope = setQuerySession(1, [], []);
    let resolve!: (value: typeof detail) => void;
    vi.mocked(api.getRole).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    vi.mocked(menuApi.roleMenuTreeselect).mockResolvedValue({
      menus: [],
      checkedKeys: [],
    });
    const ended = new AbortController();
    const first = role.readRoleEditor(scope, 2, ended.signal).catch((error) => error);
    const second = role.readRoleEditor(scope, 2);
    ended.abort();
    expect(await first).toMatchObject({ name: 'AbortError' });
    resolve(detail);
    expect((await second).data).toEqual(detail);
    expect(api.getRole).toHaveBeenCalledTimes(1);
    setQuerySession(2, [], []);
    await expect(role.readRoleEditor(scope, 2)).rejects.toBeDefined();
    expect(api.getRole).toHaveBeenCalledTimes(1);
  });

  it('captures array DTOs and rejects commands from a previous authorization scope', async () => {
    expect(role).toHaveProperty('captureRoleCommand');
    const scope = setQuerySession(1, [], []);
    const draft = { roleId: 2, menuIds: [3] };
    const command = role.captureRoleCommand(draft, scope);
    draft.menuIds.push(9);
    expect(command.input.menuIds).toEqual([3]);
    setQuerySession(2, [], []);
    await expect(role.roleCommands.updateRole(command)).rejects.toBeDefined();
    expect(api.updateRole).not.toHaveBeenCalled();
  });

  it.each(['createRole', 'updateRole', 'deleteRoles', 'changeStatus', 'updateDataScope'] as const)(
    '%s invalidates roles and embedded user catalogs',
    async (name) => {
      expect(role).toHaveProperty('roleCommands');
      const scope = setQuerySession(1, [], []);
      const keys = [
        [...role.roleKeys.all(scope), 'probe'],
        [...userKeys.all(scope), 'probe'],
      ];
      keys.forEach((key) => queryClient.setQueryData(key, []));
      const inputs = {
        createRole: { roleName: 'Operator', roleKey: 'operator', roleSort: 1 },
        updateRole: { roleId: 2, menuIds: [] },
        deleteRoles: [2, 3],
        changeStatus: { roleId: 2, status: '1' },
        updateDataScope: { roleId: 2, dataScope: '2', deptIds: [] },
      };
      await (
        role.roleCommands[name] as (
          command: ReturnType<typeof role.captureRoleCommand>
        ) => Promise<unknown>
      )(role.captureRoleCommand(inputs[name]));
      await flushPromises();
      keys.forEach((key) =>
        expect(queryClient.getQueryCache().find({ queryKey: key })?.state.isInvalidated).toBe(true)
      );
    }
  );
});
