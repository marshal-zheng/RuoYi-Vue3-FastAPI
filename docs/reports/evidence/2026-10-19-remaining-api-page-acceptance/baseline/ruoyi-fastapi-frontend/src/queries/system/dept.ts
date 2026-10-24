import { queryOptions, skipToken } from '@tanstack/vue-query';
import { AbortError, queryRequest, type RequestOptions } from '@zxio/http';
import { invalidateQueryGroups, type QueryGroupFilter } from '@zxio/vue-query/core';
import * as api from '@/api/system/dept';
import { deptTreeSelect } from '@/api/system/user';
import type { MenuTreeNode } from '@/api/system/menu';
import type { DeptCreateModel, DeptQueryModel, DeptUpdateModel } from '@/api/_generated/types.gen';
import type { HttpCollection } from '@/types/http-contract';
import { queryClient } from '../client';
import {
  assertRequestScope,
  requireQueryScope,
  scopeRequestOptions,
  type QueryScope,
} from '../context';
import { readEditorResource } from '../editor-read';
import { userKeys } from './user';

export type DeptFilters = {
  deptName?: string;
  status?: NonNullable<DeptQueryModel['status']>;
};

/** Submitted department filters are shared by the request and its resource identity. */
export function normalizeDeptFilters(input: Readonly<Record<string, unknown>> = {}): DeptFilters {
  const filters: DeptFilters = {};
  const deptName = typeof input.deptName === 'string' ? input.deptName.trim() : '';
  if (deptName) filters.deptName = deptName;
  if (input.status === '0' || input.status === '1') filters.status = input.status;
  return filters;
}

function departmentId(input: unknown): number | undefined {
  const id = Number(input);
  return Number.isSafeInteger(id) && id > 0 ? id : undefined;
}

export const deptKeys = {
  all: (scope: QueryScope) => ['ruoyi', scope.key, 'departments'] as const,
  lists: (scope: QueryScope) => [...deptKeys.all(scope), 'list'] as const,
  list: (scope: QueryScope, filters: DeptFilters) => [...deptKeys.lists(scope), filters] as const,
  details: (scope: QueryScope) => [...deptKeys.all(scope), 'detail'] as const,
  detail: (scope: QueryScope, id: number) => [...deptKeys.details(scope), id] as const,
  parentOptions: (scope: QueryScope) => [...deptKeys.all(scope), 'parent-options'] as const,
  excludeChild: (scope: QueryScope, id: number) =>
    [...deptKeys.parentOptions(scope), 'exclude', id] as const,
  userTree: (scope: QueryScope) => [...deptKeys.all(scope), 'user-tree'] as const,
};

export function deptListOptions(
  scope: QueryScope | null,
  input: Readonly<Record<string, unknown>> = {}
) {
  const filters = normalizeDeptFilters(input);
  return queryOptions<HttpCollection<api.DeptRecord>>({
    queryKey: scope
      ? deptKeys.list(scope, filters)
      : (['ruoyi', 'disabled', 'departments', 'list', filters] as const),
    queryFn: scope
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.listDept(filters, {
            signal: context.signal,
            requestOptions: context.options,
          });
        }
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}

export function deptDetailOptions(scope: QueryScope | null, input: unknown) {
  const id = departmentId(input);
  const ready = scope !== null && id !== undefined;
  return queryOptions({
    queryKey: ready
      ? deptKeys.detail(scope, id)
      : (['ruoyi', scope?.key ?? 'disabled', 'departments', 'detail', 0] as const),
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.getDept(id, {
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

export function deptExcludeChildOptions(scope: QueryScope | null, input: unknown) {
  const id = departmentId(input);
  const ready = scope !== null && id !== undefined;
  return queryOptions<HttpCollection<api.DeptRecord>>({
    queryKey: ready
      ? deptKeys.excludeChild(scope, id)
      : ([
          'ruoyi',
          scope?.key ?? 'disabled',
          'departments',
          'parent-options',
          'exclude',
          0,
        ] as const),
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.listDeptExcludeChild(id, {
            signal: context.signal,
            requestOptions: context.options,
          });
        }
      : skipToken,
    enabled: ready,
    staleTime: 30_000,
    retry: false,
  });
}

/** Creation uses the unfiltered management list; editing uses the server's exclusion contract. */
export function deptParentOptions(scope: QueryScope | null, id?: number | string) {
  return id === undefined ? deptListOptions(scope) : deptExcludeChildOptions(scope, id);
}

/** The user endpoint has a different permission and normal-department policy from management. */
export function userDeptTreeOptions(scope: QueryScope | null) {
  return queryOptions({
    queryKey: scope
      ? deptKeys.userTree(scope)
      : (['ruoyi', 'disabled', 'departments', 'user-tree'] as const),
    queryFn: scope
      ? async ({ signal }): Promise<readonly MenuTreeNode[]> => {
          const response = await deptTreeSelect(queryRequest(signal, scopeRequestOptions(scope)));
          return response.items;
        }
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}

/** Native tree controls may attach node metadata; each view owns its mutable projection. */
export function copyUserDeptTree(items: readonly MenuTreeNode[]): MenuTreeNode[] {
  return items.map((item) => ({
    ...item,
    ...(item.children ? { children: copyUserDeptTree(item.children) } : {}),
  }));
}

/** An opening consumes each resource once; cancellation rejoins only that resource's replacement. */
export async function readDeptEditor(
  scope: QueryScope | null,
  id?: number | string,
  openingSignal?: AbortSignal
): Promise<{
  data: api.DeptRecord | undefined;
  options: HttpCollection<api.DeptRecord>;
}> {
  if (!scope || (id !== undefined && departmentId(id) === undefined)) {
    throw new AbortError({ message: '部门编辑条件已失效' });
  }
  const [data, options] = await Promise.all([
    id === undefined
      ? Promise.resolve(undefined)
      : readEditorResource(
          scope,
          () => queryClient.fetchQuery(deptDetailOptions(scope, id)),
          openingSignal
        ),
    readEditorResource(
      scope,
      () => queryClient.fetchQuery(deptParentOptions(scope, id)),
      openingSignal
    ),
  ]);
  return { data, options };
}

export interface DeptCommand<T> {
  readonly scope: QueryScope;
  readonly input: T;
}

/** Capture DTO fields and authorization before a confirmation or deferred mutation. */
export function captureDeptCommand<T extends object | number | string>(
  input: T,
  scope = requireQueryScope()
): DeptCommand<T> {
  const snapshot = input !== null && typeof input === 'object' ? { ...input } : input;
  return { scope, input: snapshot as T };
}

export const deptEffects = (scope: QueryScope): readonly QueryGroupFilter[] => [
  { queryKey: deptKeys.all(scope) },
  // User rows embed department names; a rename also changes this existing display.
  { queryKey: userKeys.lists(scope) },
];

async function write<T>(
  scope: QueryScope,
  execute: (options: RequestOptions) => Promise<T>
): Promise<T> {
  const options = scopeRequestOptions(scope);
  assertRequestScope(options);
  const result = await execute(options);
  try {
    void invalidateQueryGroups(queryClient, deptEffects(scope)).catch(reportCoordinationError);
  } catch (error) {
    reportCoordinationError(error);
  }
  return result;
}

function reportCoordinationError(error: unknown): void {
  window.dispatchEvent(new CustomEvent('ruoyi:query-coordination-error', { detail: error }));
}

export const deptCommands = {
  createDept: ({ scope, input }: DeptCommand<DeptCreateModel>) =>
    write(scope, (options) => api.addDept(input, options)),
  updateDept: ({ scope, input }: DeptCommand<DeptUpdateModel>) =>
    write(scope, (options) => api.updateDept(input, options)),
  deleteDept: ({ scope, input }: DeptCommand<number | string>) =>
    write(scope, (options) => api.delDept(input, options)),
};
