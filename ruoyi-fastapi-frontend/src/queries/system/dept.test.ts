import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useQuery, VueQueryPlugin } from '@tanstack/vue-query';
import { defineComponent } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { isCommandRequest, isQueryRequest } from '@zxio/http';
import { useResourceQuery } from '@zxio/vue-query/resources';
import * as api from '@/api/system/dept';
import * as userApi from '@/api/system/user';
import type { MenuTreeNode } from '@/api/system/menu';
import type { HttpCollection } from '@/types/http-contract';
import { dataClient, queryClient } from '../client';
import { endQuerySession, setQuerySession } from '../context';
import { userKeys } from './user';
import { departmentResource as departments, copyUserDeptTree, normalizeDeptFilters } from './dept';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));
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

describe('department resource integration', () => {
  it('copies tree nodes recursively without changing shared cache data', () => {
    const cached: MenuTreeNode[] = [{ id: 1, label: '总部', children: [{ id: 7, label: '研发' }] }];
    Object.freeze(cached[0].children![0]);
    Object.freeze(cached[0].children);
    Object.freeze(cached[0]);
    Object.freeze(cached);
    const view = copyUserDeptTree(cached);
    view[0].children![0].label = '本地选择';
    expect(cached[0].children![0].label).toBe('研发');
  });

  it('uses one normalized snapshot for the resource key and scoped HTTP arguments', async () => {
    const draft = { deptName: ' 研发 ', status: '0', page: 2, parentId: 999 };
    const options = dataClient.options(departments, 'list', draft);
    draft.deptName = 'later';
    const rows = collection();
    const list = vi.spyOn(api, 'listDept').mockResolvedValue(rows);
    expect(normalizeDeptFilters({ deptName: ' ', status: '' })).toEqual({});
    expect(await queryClient.fetchQuery(options)).toBe(rows);
    expect(list).toHaveBeenCalledWith(
      { deptName: '研发', status: '0' },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(isQueryRequest(list.mock.calls[0][1]?.requestOptions)).toBe(true);
    expect(options.queryKey).toEqual(
      dataClient.options(departments, 'list', { deptName: '研发', status: '0' }).queryKey
    );
    expect(rows.items[0]).not.toHaveProperty('children');
  });

  it('keeps permission-specific endpoints separate and prevents invalid reads', async () => {
    vi.spyOn(api, 'listDept').mockResolvedValue(collection());
    vi.spyOn(api, 'listDeptExcludeChild').mockResolvedValue(collection());
    vi.spyOn(api, 'getDept').mockResolvedValue(collection().items[0]);
    vi.spyOn(userApi, 'deptTreeSelect').mockResolvedValue({
      items: [{ id: 7, label: '研发' }],
    });
    const reads = [
      dataClient.read(departments, 'list', {}),
      dataClient.read(departments, 'excludeChild', 7),
      dataClient.read(departments, 'detail', '7'),
      dataClient.read(departments, 'userTree', undefined),
    ];
    expect((await Promise.all(reads)).every((result) => result.kind === 'loaded')).toBe(true);
    expect(
      new Set(
        queryClient
          .getQueryCache()
          .getAll()
          .map((query) => query.queryHash)
      ).size
    ).toBe(4);
    expect((await dataClient.read(departments, 'detail', 0)).kind).toBe('not-started');
    expect((await dataClient.read(departments, 'excludeChild', 'invalid')).kind).toBe(
      'not-started'
    );
    endQuerySession();
    expect((await dataClient.read(departments, 'list', {})).kind).toBe('not-started');
    expect(api.getDept).toHaveBeenCalledTimes(1);
  });

  it('shares one real adapter invocation between native and resource readers', async () => {
    const response = deferred<Awaited<ReturnType<typeof userApi.deptTreeSelect>>>();
    const tree = vi.spyOn(userApi, 'deptTreeSelect').mockReturnValue(response.promise);
    let native: unknown, resource: unknown;
    wrappers.push(
      mount(
        defineComponent({
          setup() {
            const a = useQuery(dataClient.options(departments, 'userTree', undefined));
            const b = useResourceQuery(departments, 'userTree', undefined, {
              client: dataClient,
            });
            native = a;
            resource = b;
            return () => null;
          },
        }),
        { global: { plugins: [[VueQueryPlugin, { queryClient }]] } }
      )
    );
    const imperative = dataClient.read(departments, 'userTree', undefined);
    expect(tree).toHaveBeenCalledTimes(1);
    response.resolve({ items: [{ id: 7, label: '研发' }] });
    expect((await imperative).kind).toBe('loaded');
    await flushPromises();
    expect((native as { data: { value: unknown } }).data.value).toEqual(
      (resource as { data: { value: unknown } }).data.value
    );
  });

  it.each(['create', 'update', 'delete'] as const)(
    '%s invalidates department collections and actual native user lists',
    async (name) => {
      const scope = setQuerySession(1, [], []);
      vi.spyOn(api, 'addDept').mockResolvedValue(collection().items[0]);
      vi.spyOn(api, 'updateDept').mockResolvedValue(collection().items[0]);
      vi.spyOn(api, 'delDept').mockResolvedValue(null);
      const keys = [
        dataClient.options(departments, 'list', {}).queryKey,
        dataClient.options(departments, 'excludeChild', 7).queryKey,
        dataClient.options(departments, 'userTree', undefined).queryKey,
        [...userKeys.lists(scope), 'probe'],
      ];
      keys.forEach((key) => queryClient.setQueryData(key, []));
      const untouched = dataClient.options(departments, 'detail', 8).queryKey;
      queryClient.setQueryData(untouched, collection().items[0]);
      const receipt =
        name === 'delete'
          ? await dataClient.execute(departments, name, 7)
          : name === 'create'
            ? await dataClient.execute(departments, name, {
                parentId: 1,
                deptName: '研发',
                orderNum: 0,
              })
            : await dataClient.execute(departments, name, {
                deptId: 7,
                deptName: '研发',
              });
      expect(receipt.kind).toBe('succeeded');
      await receipt.refresh;
      for (const key of keys) expect(queryClient.getQueryState(key)?.isInvalidated).toBe(true);
      expect(queryClient.getQueryState(untouched)?.isInvalidated).toBe(false);
      const call =
        name === 'create'
          ? vi.mocked(api.addDept).mock.calls[0]
          : name === 'update'
            ? vi.mocked(api.updateDept).mock.calls[0]
            : vi.mocked(api.delDept).mock.calls[0];
      expect(isCommandRequest(call[1])).toBe(true);
      expect(call[1]?.retry).toBe(false);
      expect(call[2]).toBeInstanceOf(AbortSignal);
    }
  );

  it('reports confirmed save separately from a failed refresh and preserves old rows', async () => {
    const list = vi.spyOn(api, 'listDept').mockResolvedValue(collection());
    let query!: ReturnType<
      typeof useResourceQuery<typeof departments.reads, typeof departments.commands, 'list'>
    >;
    wrappers.push(
      mount(
        defineComponent({
          setup() {
            query = useResourceQuery(departments, 'list', {}, { client: dataClient });
            return () => null;
          },
        })
      )
    );
    await flushPromises();
    list.mockRejectedValue(new Error('refresh failed'));
    vi.spyOn(api, 'updateDept').mockResolvedValue(collection('saved').items[0]);
    const receipt = await dataClient.execute(departments, 'update', {
      deptId: 7,
      deptName: 'saved',
    });
    expect(receipt.kind).toBe('succeeded');
    expect((await receipt.refresh).kind).toBe('failed');
    expect(query.data.value?.items[0].deptName).toBe('研发');
    expect(api.updateDept).toHaveBeenCalledTimes(1);
  });

  it('captures confirmation input, rejects an expired scope, and never sends the write', async () => {
    const confirm = deferred<boolean>();
    const write = vi.spyOn(api, 'updateDept');
    const input = { deptId: 7, deptName: 'captured' };
    const before = vi.fn<
      (input: Readonly<{ deptId: number; deptName?: string | null }>) => Promise<boolean>
    >(() => confirm.promise);
    const pending = dataClient.execute(departments, 'update', input, {
      beforeExecute: before,
    });
    input.deptName = 'later';
    expect(before.mock.calls[0][0]).toMatchObject({ deptName: 'captured' });
    setQuerySession(2, [], []);
    confirm.resolve(true);
    expect((await pending).kind).toBe('not-started');
    expect(write).not.toHaveBeenCalled();
  });

  it.each([
    [422, 'rejected'],
    [500, 'unknown'],
    [0, 'unknown'],
  ] as const)('classifies HTTP %s without invalidation or write retry', async (status, kind) => {
    const key = dataClient.options(departments, 'userTree', undefined).queryKey;
    queryClient.setQueryData(key, []);
    const write = vi
      .spyOn(api, 'updateDept')
      .mockRejectedValue(Object.assign(new Error('failure'), { status }));
    expect((await dataClient.execute(departments, 'update', { deptId: 7 })).kind).toBe(kind);
    expect(queryClient.getQueryState(key)?.isInvalidated).toBe(false);
    expect(write).toHaveBeenCalledTimes(1);
  });
});
