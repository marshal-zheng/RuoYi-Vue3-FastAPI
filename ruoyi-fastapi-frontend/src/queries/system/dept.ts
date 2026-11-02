import { commandRequest, queryRequest, type RequestOptions } from '@zxio/http';
import {
  defineCommand,
  defineRead,
  defineResource,
  type ResourceContext,
} from '@zxio/vue-query/resources';
import { invalidateQueryGroups } from '@zxio/vue-query/core';
import type { DeepReadonly } from 'vue';
import * as api from '@/api/system/dept';
import { deptTreeSelect } from '@/api/system/user';
import type { MenuTreeNode } from '@/api/system/menu';
import type { DeptCreateModel, DeptQueryModel, DeptUpdateModel } from '@/api/_generated/types.gen';
import { queryClient } from '../client';
import { queryScope, scopeRequestOptions } from '../context';
import { userKeys } from './user';

export type DeptFilters = {
  deptName?: string;
  status?: NonNullable<DeptQueryModel['status']>;
};

export function normalizeDeptFilters(input: Readonly<Record<string, unknown>> = {}): DeptFilters {
  const filters: DeptFilters = {};
  const deptName = typeof input.deptName === 'string' ? input.deptName.trim() : '';
  if (deptName) filters.deptName = deptName;
  if (input.status === '0' || input.status === '1') filters.status = input.status;
  return filters;
}

function departmentId(input: number | string | undefined): number {
  const id = Number(input);
  return Number.isSafeInteger(id) && id > 0 ? id : 0;
}

function readConfig({ signal, scope }: ResourceContext) {
  const context = queryRequest(signal, scopeRequestOptions(scope));
  return { signal: context.signal, requestOptions: context.options };
}

async function write<T>(
  context: ResourceContext,
  execute: (options: RequestOptions, signal: AbortSignal) => Promise<T>
) {
  let data: T;
  try {
    const transport = commandRequest(context.signal, scopeRequestOptions(context.scope));
    data = await execute(transport.options, transport.signal);
  } catch (error) {
    const failure = error as {
      status?: number;
      response?: { status?: number };
      name?: string;
    };
    const status = failure?.status ?? failure?.response?.status ?? 0;
    // A real 4xx rejection is definite; transport loss/timeout and 5xx do not prove rollback.
    if (
      (status >= 400 && status < 500 && status !== 408) ||
      failure?.name === 'RequestPreparationError'
    )
      return { kind: 'rejected' as const, error };
    return { kind: 'unknown' as const, error };
  }
  // Actual user-list consumers still use native Query and embed department names.
  // Keep their existing domain effect; department reads use the resource's declared effects.
  const session = queryScope.value;
  if (context.isCurrent() && session?.key === context.scope.key) {
    const report = (error: unknown) =>
      window.dispatchEvent(new CustomEvent('ruoyi:query-coordination-error', { detail: error }));
    try {
      void invalidateQueryGroups(queryClient, [{ queryKey: userKeys.lists(session) }]).catch(
        report
      );
    } catch (error) {
      report(error);
    }
  }
  return { kind: 'succeeded' as const, data };
}

export const departmentResource = defineResource({
  name: 'ruoyi-departments',
  reads: {
    list: defineRead({
      normalize: normalizeDeptFilters,
      staleTime: 30_000,
      run: (filters, context) => api.listDept(filters, readConfig(context)),
    }),
    detail: defineRead({
      normalize: departmentId,
      enabled: (id) => id > 0,
      run: (id, context) => api.getDept(id, readConfig(context)),
    }),
    excludeChild: defineRead({
      normalize: departmentId,
      enabled: (id) => id > 0,
      staleTime: 30_000,
      run: (id, context) => api.listDeptExcludeChild(id, readConfig(context)),
    }),
    // User-tree permissions and normal-department filtering are server-owned and differ from list.
    userTree: defineRead({
      staleTime: 30_000,
      run: async (_: void, { signal, scope }) =>
        (await deptTreeSelect(queryRequest(signal, scopeRequestOptions(scope)))).items,
    }),
  },
  commands: (self) => {
    const collections = () => [self.read('list'), self.read('excludeChild'), self.read('userTree')];
    return {
      create: defineCommand({
        run: (input: DeptCreateModel, context) =>
          write(context, (options, signal) => api.addDept(input, options, signal)),
        effects: collections,
      }),
      update: defineCommand({
        run: (input: DeptUpdateModel, context) =>
          write(context, (options, signal) => api.updateDept(input, options, signal)),
        effects: ({ input }) => [...collections(), self.read('detail', input.deptId)],
      }),
      delete: defineCommand({
        run: (input: number, context) =>
          write(context, (options, signal) => api.delDept(input, options, signal)),
        effects: ({ input }) => [...collections(), self.read('detail', input)],
      }),
    };
  },
});

/** Native tree controls attach metadata; each view owns a mutable projection, never cached nodes. */
export function copyUserDeptTree(items: DeepReadonly<MenuTreeNode[]>): MenuTreeNode[] {
  return items.map(({ children, ...item }) => ({
    ...item,
    ...(children ? { children: copyUserDeptTree(children) } : {}),
  }));
}

/** Copy only editable DTO fields once; server metadata never becomes an editor's save payload. */
export function departmentDraft(data: DeepReadonly<api.DeptRecord>) {
  return {
    deptId: data.deptId,
    parentId: data.parentId ?? undefined,
    deptName: data.deptName ?? undefined,
    orderNum: data.orderNum ?? undefined,
    leader: data.leader ?? undefined,
    phone: data.phone ?? undefined,
    email: data.email ?? undefined,
    status: data.status ?? undefined,
  };
}
