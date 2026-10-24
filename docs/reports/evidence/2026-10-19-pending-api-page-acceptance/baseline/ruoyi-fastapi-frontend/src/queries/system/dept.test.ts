import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { skipToken, useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { defineComponent, unref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { isAbortError, isQueryRequest } from '@zxio/http';
import * as api from '@/api/system/dept';
import * as userApi from '@/api/system/user';
import type { MenuTreeNode } from '@/api/system/menu';
import type { HttpCollection } from '@/types/http-contract';
import request from '@/utils/request';
import { queryClient } from '../client';
import { endQuerySession, setQuerySession } from '../context';
import { userKeys } from './user';
import * as deptDomain from './dept';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));

function domain() {
  return deptDomain;
}
const wrappers: ReturnType<typeof mount>[] = [];
const collection = (deptName = '研发'): HttpCollection<api.DeptRecord> => ({
  items: [{ deptId: 7, parentId: 1, deptName, orderNum: 0, status: '0' }],
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((ok, fail) => {
    resolve = ok;
    reject = fail;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  vi.resetAllMocks();
  endQuerySession();
  queryClient.clear();
  setQuerySession(1, [], []);
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  endQuerySession();
  queryClient.clear();
});

describe('department API request scope', () => {
  it.each([
    ['addDept', { parentId: 1, deptName: '研发', orderNum: 0 }],
    ['updateDept', { deptId: 7, deptName: '研发' }],
    ['delDept', 7],
  ] as const)('forwards captured write scope through %s', async (name, input) => {
    vi.mocked(request).mockResolvedValue({ deptId: 7 });
    const options = { context: { 'ruoyi.query-scope': '1:1' } };
    await Reflect.apply(api[name], undefined, [input, options]);
    expect(request).toHaveBeenCalledWith(expect.any(Object), options);
  });
});

describe('public department resource', () => {
  it('copies native tree nodes recursively without mutating the shared cached tree', async () => {
    const dept = domain();
    expect(dept).toHaveProperty('copyUserDeptTree', expect.any(Function));
    const cached: MenuTreeNode[] = [{ id: 1, label: '总部', children: [{ id: 7, label: '研发' }] }];
    Object.freeze(cached[0].children![0]);
    Object.freeze(cached[0].children);
    Object.freeze(cached[0]);
    Object.freeze(cached);
    const projection = dept.copyUserDeptTree(cached);
    expect(projection).toEqual(cached);
    expect(projection[0]).not.toBe(cached[0]);
    expect(projection[0].children![0]).not.toBe(cached[0].children![0]);
    projection[0].children![0].label = '选择器本地状态';
    expect(cached[0].children![0].label).toBe('研发');
    expect(dept.copyUserDeptTree([])).toEqual([]);
  });

  it('uses a submitted filter snapshot for the key and scoped flat request', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const draft = { deptName: ' 研发 ', status: '0', page: 2, parentId: 999 };
    const options = dept.deptListOptions(scope, draft);
    draft.deptName = 'later';
    const rows = collection();
    const list = vi.spyOn(api, 'listDept').mockResolvedValue(rows);
    expect(dept.normalizeDeptFilters(draft)).toEqual({
      deptName: 'later',
      status: '0',
    });
    expect(dept.normalizeDeptFilters({ deptName: ' ', status: '' })).toEqual({});
    expect(await queryClient.fetchQuery(options)).toBe(rows);
    expect(list).toHaveBeenCalledWith(
      { deptName: '研发', status: '0' },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(isQueryRequest(list.mock.calls[0][1]?.requestOptions)).toBe(true);
    expect(options.queryKey).toEqual(
      dept.deptListOptions(scope, { deptName: '研发', status: '0' }).queryKey
    );
    expect(rows.items[0]).not.toHaveProperty('children');
  });

  it('keeps endpoint and authorization variants separate and disables invalid conditions', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const list = vi.spyOn(api, 'listDept').mockResolvedValue(collection());
    const exclude = vi.spyOn(api, 'listDeptExcludeChild').mockResolvedValue(collection());
    const detail = vi.spyOn(api, 'getDept').mockResolvedValue(collection().items[0]);
    const tree = vi.spyOn(userApi, 'deptTreeSelect').mockResolvedValue({
      items: [{ id: 7, label: '研发' }],
    });
    const options = [
      dept.deptListOptions(scope),
      dept.deptExcludeChildOptions(scope, 7),
      dept.deptDetailOptions(scope, 7),
      dept.userDeptTreeOptions(scope),
    ];
    expect(new Set(options.map((item) => JSON.stringify(item.queryKey))).size).toBe(4);
    await queryClient.fetchQuery(dept.deptParentOptions(scope));
    await queryClient.fetchQuery(dept.deptParentOptions(scope, 7));
    await queryClient.fetchQuery(dept.deptDetailOptions(scope, '7'));
    expect(await queryClient.fetchQuery(dept.userDeptTreeOptions(scope))).toEqual([
      { id: 7, label: '研发' },
    ]);
    expect(list).toHaveBeenCalledOnce();
    expect(exclude).toHaveBeenCalledWith(7, expect.any(Object));
    expect(detail).toHaveBeenCalledWith(7, expect.any(Object));
    expect(isQueryRequest(tree.mock.calls[0][0]?.options)).toBe(true);
    for (const disabled of [
      unref(dept.deptListOptions(null)),
      unref(dept.deptDetailOptions(scope, 0)),
      unref(dept.deptExcludeChildOptions(scope, 'invalid')),
      unref(dept.userDeptTreeOptions(null)),
    ]) {
      expect(disabled.queryFn).toBe(skipToken);
      expect(disabled.enabled).toBe(false);
    }
  });

  it('shares the user department endpoint between concurrent native readers', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const response = deferred<Awaited<ReturnType<typeof userApi.deptTreeSelect>>>();
    const tree = vi.spyOn(userApi, 'deptTreeSelect').mockReturnValue(response.promise);
    const first = queryClient.fetchQuery(dept.userDeptTreeOptions(scope));
    const second = queryClient.fetchQuery(dept.userDeptTreeOptions(scope));
    expect(tree).toHaveBeenCalledOnce();
    response.resolve({ items: [{ id: 7, label: '研发' }] });
    expect(await first).toEqual(await second);
  });

  it.each(['createDept', 'updateDept', 'deleteDept'] as const)(
    '%s invalidates every department variant and user lists from the public command',
    async (name) => {
      const dept = domain();
      const scope = setQuerySession(1, [], []);
      vi.spyOn(api, 'addDept').mockResolvedValue(collection().items[0]);
      vi.spyOn(api, 'updateDept').mockResolvedValue(collection().items[0]);
      vi.spyOn(api, 'delDept').mockResolvedValue(null);
      const affected = [
        dept.deptListOptions(scope).queryKey,
        dept.deptDetailOptions(scope, 7).queryKey,
        dept.deptExcludeChildOptions(scope, 7).queryKey,
        dept.userDeptTreeOptions(scope).queryKey,
        [...userKeys.lists(scope), 'probe'],
      ];
      affected.forEach((key) => queryClient.setQueryData(key, []));
      const userDetailKey = userKeys.detail(scope, 7);
      queryClient.setQueryData(userDetailKey, {});
      const command = dept.captureDeptCommand({
        parentId: 1,
        deptName: '研发',
        orderNum: 0,
        deptId: 7,
      });
      if (name === 'deleteDept') await dept.deptCommands.deleteDept(dept.captureDeptCommand(7));
      else await dept.deptCommands[name](command);
      await flushPromises();
      for (const key of affected) expect(queryClient.getQueryState(key)?.isInvalidated).toBe(true);
      expect(queryClient.getQueryState(userDetailKey)?.isInvalidated).toBe(false);
    }
  );

  it('keeps the successful write independent from failed list and tree refreshes', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const listRead = vi.spyOn(api, 'listDept').mockResolvedValue(collection());
    const treeRead = vi.spyOn(userApi, 'deptTreeSelect').mockResolvedValue({
      items: [{ id: 7, label: '研发' }],
    });
    let list!: ReturnType<typeof useQuery<HttpCollection<api.DeptRecord>>>;
    let tree!: ReturnType<typeof useQuery<readonly { id: number; label: string }[]>>;
    wrappers.push(
      mount(
        defineComponent({
          setup() {
            list = useQuery(dept.deptListOptions(scope));
            tree = useQuery(dept.userDeptTreeOptions(scope));
            return () => null;
          },
        }),
        { global: { plugins: [[VueQueryPlugin, { queryClient }]] } }
      )
    );
    await flushPromises();
    const pendingList = deferred<HttpCollection<api.DeptRecord>>();
    const pendingTree = deferred<Awaited<ReturnType<typeof userApi.deptTreeSelect>>>();
    listRead.mockReturnValue(pendingList.promise);
    treeRead.mockReturnValue(pendingTree.promise);
    const saved = { ...collection().items[0], deptName: '已保存' };
    vi.spyOn(api, 'updateDept').mockResolvedValue(saved);
    expect(
      await dept.deptCommands.updateDept(dept.captureDeptCommand({ deptId: 7, deptName: '已保存' }))
    ).toBe(saved);
    await flushPromises();
    expect(list.isFetching.value).toBe(true);
    expect(tree.isFetching.value).toBe(true);
    pendingList.reject(new Error('列表刷新失败'));
    pendingTree.reject(new Error('部门树刷新失败'));
    await flushPromises();
    expect(list.error.value?.message).toBe('列表刷新失败');
    expect(tree.error.value?.message).toBe('部门树刷新失败');
    expect(list.data.value?.items[0].deptName).toBe('研发');
    expect(tree.data.value?.[0].label).toBe('研发');
  });

  it('copies a captured DTO and rejects an expired scope before sending', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const write = vi.spyOn(api, 'updateDept').mockResolvedValue(collection().items[0]);
    const input = { deptId: 7, deptName: '提交时名称' };
    const command = dept.captureDeptCommand(input, scope);
    input.deptName = '之后编辑';
    expect(command.input.deptName).toBe('提交时名称');
    setQuerySession(2, [], []);
    await expect(dept.deptCommands.updateDept(command)).rejects.toSatisfy(isAbortError);
    expect(write).not.toHaveBeenCalled();
  });

  it('does not invalidate successful reads when the write itself fails', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const key = dept.userDeptTreeOptions(scope).queryKey;
    queryClient.setQueryData(key, [{ id: 7, label: '研发' }]);
    vi.spyOn(api, 'updateDept').mockRejectedValue(new Error('写入失败'));
    await expect(
      dept.deptCommands.updateDept(dept.captureDeptCommand({ deptId: 7, deptName: '已保存' }))
    ).rejects.toThrow('写入失败');
    expect(queryClient.getQueryState(key)?.isInvalidated).toBe(false);
  });

  it('reads current editor detail without repeating a completed sibling after parent cancellation', async () => {
    const dept = domain();
    const scope = setQuerySession(1, [], []);
    const oldDetail = { ...collection().items[0], deptName: '旧快照' };
    queryClient.setQueryData(dept.deptDetailOptions(scope, 7).queryKey, oldDetail);
    const detail = vi.spyOn(api, 'getDept').mockResolvedValue(collection().items[0]);
    const firstParent = deferred<HttpCollection<api.DeptRecord>>();
    const parent = vi
      .spyOn(api, 'listDeptExcludeChild')
      .mockReturnValueOnce(firstParent.promise)
      .mockResolvedValueOnce(collection('替代读取'));
    const opening = dept.readDeptEditor(scope, 7);
    await flushPromises();
    await queryClient.cancelQueries({
      queryKey: dept.deptExcludeChildOptions(scope, 7).queryKey,
    });
    const result = await opening;
    expect(result.data?.deptName).toBe('研发');
    expect(result.options.items[0].deptName).toBe('替代读取');
    expect(detail).toHaveBeenCalledOnce();
    expect(parent).toHaveBeenCalledTimes(2);
    firstParent.resolve(collection('旧读取'));
    const creation = vi.spyOn(api, 'listDept').mockResolvedValue(collection());
    expect((await dept.readDeptEditor(scope)).data).toBeUndefined();
    expect(creation).toHaveBeenCalledOnce();
    await expect(dept.readDeptEditor(scope, 0)).rejects.toSatisfy(isAbortError);
  });
});
