import { queryOptions, skipToken } from '@tanstack/vue-query';
import { AbortError, queryRequest, type RequestOptions } from '@zxio/http';
import { invalidateQueryGroups, type QueryGroupFilter } from '@zxio/vue-query/core';
import * as api from '@/api/system/role';
import * as menuApi from '@/api/system/menu';
import type {
  RoleCreateModel,
  RoleUpdateModel,
  RolePageQueryModel,
  RoleStatusUpdateModel,
  RoleDataScopeUpdateModel,
} from '@/api/_generated/types.gen';
import { queryClient } from '../client';
import {
  assertRequestScope,
  requireQueryScope,
  scopeRequestOptions,
  type QueryScope,
} from '../context';
import { readEditorResource } from '../editor-read';
import { userKeys } from './user';

export type RoleFilters = Pick<
  RolePageQueryModel,
  'roleName' | 'roleKey' | 'status' | 'beginTime' | 'endTime'
>;
export function normalizeRoleFilters(input: Readonly<Record<string, unknown>> = {}): RoleFilters {
  const filters: RoleFilters = {};
  for (const field of ['roleName', 'roleKey'] as const) {
    const value = typeof input[field] === 'string' ? input[field].trim() : '';
    if (value) filters[field] = value;
  }
  if (input.status === '0' || input.status === '1') filters.status = input.status;
  const range = Array.isArray(input.dateRange) ? input.dateRange : undefined;
  if (range || !Object.hasOwn(input, 'dateRange')) {
    const begin = range ? range[0] : input.beginTime;
    const end = range ? range[1] : input.endTime;
    if (typeof begin === 'string' && begin) filters.beginTime = begin;
    if (typeof end === 'string' && end) filters.endTime = end;
  }
  return filters;
}
function positiveInteger(value: unknown, fallback: number): number {
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : fallback;
}
export const roleKeys = {
  all: (scope: QueryScope) => ['ruoyi', scope.key, 'roles'] as const,
  lists: (scope: QueryScope) => [...roleKeys.all(scope), 'list'] as const,
  list: (scope: QueryScope, params: RolePageQueryModel) =>
    [...roleKeys.lists(scope), params] as const,
  detail: (scope: QueryScope, id: number) => [...roleKeys.all(scope), 'detail', id] as const,
  menu: (scope: QueryScope, id?: number) =>
    [...roleKeys.all(scope), 'menu-tree', id ?? 'create'] as const,
  dept: (scope: QueryScope, id: number) => [...roleKeys.all(scope), 'dept-tree', id] as const,
};
export function roleListOptions(
  scope: QueryScope | null,
  input: Readonly<Record<string, unknown>> = {}
) {
  const params = {
    ...normalizeRoleFilters(input),
    page: positiveInteger(input.page, 1),
    pageSize: positiveInteger(input.pageSize, 10),
  };
  return queryOptions({
    queryKey: scope
      ? roleKeys.list(scope, params)
      : (['ruoyi', 'disabled', 'roles', 'list', params] as const),
    queryFn: scope
      ? ({ signal }) => api.listRole(params, queryRequest(signal, scopeRequestOptions(scope)))
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}
export function roleDetailOptions(scope: QueryScope | null, input: unknown) {
  const id = positiveInteger(input, 0);
  const ready = scope !== null && id > 0;
  return queryOptions({
    queryKey: ready
      ? roleKeys.detail(scope, id)
      : (['ruoyi', scope?.key ?? 'disabled', 'roles', 'detail', 0] as const),
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.getRole(id, {
            signal: context.signal,
            requestOptions: context.options,
          });
        }
      : skipToken,
    enabled: ready,
    staleTime: 0,
    retry: false,
  });
}
/** Menu creation/edit trees use their own permission contract, distinct from department trees. */
export function roleMenuOptions(scope: QueryScope | null, input?: number | string) {
  const id = input === undefined ? undefined : positiveInteger(input, 0);
  const ready = scope !== null && id !== 0;
  return queryOptions({
    queryKey: ready
      ? roleKeys.menu(scope, id)
      : (['ruoyi', scope?.key ?? 'disabled', 'roles', 'menu-tree', 0] as const),
    queryFn: ready
      ? async ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          const config = {
            signal: context.signal,
            requestOptions: context.options,
          };
          if (id !== undefined) return menuApi.roleMenuTreeselect(id, config);
          const response = await menuApi.treeselect(config);
          return { menus: response.items, checkedKeys: [] as number[] };
        }
      : skipToken,
    enabled: ready,
    staleTime: 0,
    retry: false,
  });
}
export function roleDeptOptions(scope: QueryScope | null, input: unknown) {
  const id = positiveInteger(input, 0);
  const ready = scope !== null && id > 0;
  return queryOptions({
    queryKey: ready
      ? roleKeys.dept(scope, id)
      : (['ruoyi', scope?.key ?? 'disabled', 'roles', 'dept-tree', 0] as const),
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.deptTreeSelect(id, {
            signal: context.signal,
            requestOptions: context.options,
          });
        }
      : skipToken,
    enabled: ready,
    staleTime: 0,
    retry: false,
  });
}
/** Trees are mutable native-control drafts, never the shared resource objects. */
function copyTree(nodes: readonly menuApi.MenuTreeNode[]): menuApi.MenuTreeNode[] {
  return nodes.map((node) => ({
    ...node,
    ...(node.children ? { children: copyTree(node.children) } : {}),
  }));
}

export async function readRoleEditor(
  scope: QueryScope | null,
  id?: number | string,
  openingSignal?: AbortSignal
) {
  if (!scope || (id !== undefined && !positiveInteger(id, 0)))
    throw new AbortError({ message: '角色编辑条件已失效' });
  const [data, menus] = await Promise.all([
    id === undefined
      ? Promise.resolve(undefined)
      : readEditorResource(
          scope,
          () => queryClient.fetchQuery(roleDetailOptions(scope, id)),
          openingSignal
        ),
    readEditorResource(
      scope,
      () => queryClient.fetchQuery(roleMenuOptions(scope, id)),
      openingSignal
    ),
  ]);
  return {
    data,
    menus: {
      menus: copyTree(menus.menus),
      checkedKeys: [...menus.checkedKeys],
    },
  };
}
export async function readRoleDataScopeEditor(
  scope: QueryScope | null,
  id: number | string,
  openingSignal?: AbortSignal
) {
  if (!scope || !positiveInteger(id, 0))
    throw new AbortError({ message: '角色数据权限条件已失效' });
  const [data, depts] = await Promise.all([
    readEditorResource(
      scope,
      () => queryClient.fetchQuery(roleDetailOptions(scope, id)),
      openingSignal
    ),
    readEditorResource(
      scope,
      () => queryClient.fetchQuery(roleDeptOptions(scope, id)),
      openingSignal
    ),
  ]);
  return {
    data,
    depts: {
      depts: copyTree(depts.depts),
      checkedKeys: [...depts.checkedKeys],
    },
  };
}
export interface RoleCommand<T> {
  readonly scope: QueryScope;
  readonly input: T;
}
export function captureRoleCommand<T extends object | number | string>(
  input: T,
  scope = requireQueryScope()
): RoleCommand<T> {
  let snapshot: unknown = input;
  if (Array.isArray(input)) snapshot = [...input];
  else if (typeof input === 'object' && input !== null)
    snapshot = Object.fromEntries(
      Object.entries(input).map(([key, value]) => [key, Array.isArray(value) ? [...value] : value])
    );
  return { scope, input: snapshot as T };
}
export const roleEffects = (scope: QueryScope): readonly QueryGroupFilter[] => [
  { queryKey: roleKeys.all(scope) },
  // User detail/options embed role catalogs, and both authorization directions live here.
  { queryKey: userKeys.all(scope) },
];
async function write<T>(
  scope: QueryScope,
  execute: (options: RequestOptions) => Promise<T>
): Promise<T> {
  const options = scopeRequestOptions(scope);
  assertRequestScope(options);
  const result = await execute(options);
  try {
    void invalidateQueryGroups(queryClient, roleEffects(scope)).catch(reportCoordinationError);
  } catch (error) {
    reportCoordinationError(error);
  }
  return result;
}
function reportCoordinationError(error: unknown): void {
  window.dispatchEvent(new CustomEvent('ruoyi:query-coordination-error', { detail: error }));
}
export const roleCommands = {
  createRole: ({ scope, input }: RoleCommand<RoleCreateModel>) =>
    write(scope, (options) => api.addRole(input, options)),
  updateRole: ({ scope, input }: RoleCommand<RoleUpdateModel>) =>
    write(scope, (options) => api.updateRole(input, options)),
  deleteRoles: ({ scope, input }: RoleCommand<number | string | readonly (number | string)[]>) =>
    write(scope, (options) =>
      api.delRole(Array.isArray(input) ? input.join(',') : String(input), options)
    ),
  changeStatus: ({ scope, input }: RoleCommand<RoleStatusUpdateModel>) =>
    write(scope, (options) => api.changeRoleStatus(input.roleId, input.status, options)),
  updateDataScope: ({ scope, input }: RoleCommand<RoleDataScopeUpdateModel>) =>
    write(scope, (options) => api.dataScope(input, options)),
};
