import { queryOptions, skipToken } from '@tanstack/vue-query';
import { invalidateQueryGroups, type QueryGroupFilter } from '@zxio/vue-query/core';
import { queryRequest } from '@zxio/http';
import { queryClient } from '../client';
import {
  queryScope,
  requireQueryScope,
  scopeRequestOptions,
  assertRequestScope,
  type QueryScope,
} from '../context';
import * as dataApi from '@/api/system/dict/data';
import * as typeApi from '@/api/system/dict/type';
import type { DictDataModel, DictTypeModel } from '@/api/_generated/types.gen';

export interface DictItem {
  readonly label: string;
  readonly value: string;
  readonly disabled?: boolean;
  readonly elTagType?: string;
  readonly elTagClass?: string;
  readonly _raw?: Readonly<dataApi.DictData>;
}

export const dictKeys = {
  all: (scope: QueryScope) => ['ruoyi', scope.key, 'dict-data'] as const,
  group: (scope: QueryScope, dictType: string) =>
    [...dictKeys.all(scope), dictType.trim()] as const,
  options: (scope: QueryScope, dictType: string) =>
    [...dictKeys.group(scope, dictType), 'options'] as const,
  types: (scope: QueryScope) => ['ruoyi', scope.key, 'dict-types'] as const,
};

export function dictOptions(scope: QueryScope | null, type: string) {
  const dictType = type.trim();
  const ready = scope !== null && dictType !== '';
  return queryOptions({
    queryKey: ready
      ? dictKeys.options(scope, dictType)
      : (['ruoyi', 'disabled', 'dict-data', dictType, 'options'] as const),
    queryFn: ready
      ? async ({ signal }): Promise<readonly DictItem[]> => {
          const response = await dataApi.getDicts(
            dictType,
            queryRequest(signal, scopeRequestOptions(scope))
          );
          return response.items.map((item) => ({
            label: item.dictLabel,
            value: item.dictValue,
            disabled: item.status === '1',
            elTagType: item.listClass,
            elTagClass: item.cssClass,
            _raw: item,
          }));
        }
      : skipToken,
    enabled: ready,
    staleTime: 30_000,
    gcTime: 10 * 60_000,
    retry: false,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}

/** Type choices and route metadata share the type resource's write invalidation. */
export type DictTypeOption = DictTypeModel & { readonly label: string; readonly value: string };

export function dictTypeOptions(scope: QueryScope | null) {
  return queryOptions({
    queryKey: ['ruoyi', scope?.key ?? 'disabled', 'dict-types', 'options'] as const,
    queryFn: scope
      ? async ({ signal }): Promise<readonly DictTypeOption[]> => {
          const response = await typeApi.optionselect(
            queryRequest(signal, scopeRequestOptions(scope))
          );
          return response.items.map((item) => ({
            ...item,
            label: item.dictName ?? '',
            value: item.dictType ?? '',
          }));
        }
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}

export function dictTypeDetailOptions(scope: QueryScope | null, input: unknown) {
  const id = Number(input);
  const ready = scope !== null && Number.isSafeInteger(id) && id > 0;
  return queryOptions({
    queryKey: ['ruoyi', scope?.key ?? 'disabled', 'dict-types', 'detail', ready ? id : 0] as const,
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return typeApi.getType(id, { signal: context.signal, requestOptions: context.options });
        }
      : skipToken,
    enabled: ready,
    staleTime: 30_000,
    retry: false,
  });
}

/** Wait for data that meets this resource's freshness policy; never fetch a disabled query. */
export async function readDict(type: string): Promise<readonly DictItem[]> {
  const scope = queryScope.value;
  if (!scope || !type.trim()) return [];
  return queryClient.fetchQuery(dictOptions(scope, type));
}

// Coarse invalidation deliberately covers unknown old membership, labels and all option variants.
export const dictEffects = {
  data: (scope: QueryScope): readonly QueryGroupFilter[] => [{ queryKey: dictKeys.all(scope) }],
  type: (scope: QueryScope): readonly QueryGroupFilter[] => [
    { queryKey: dictKeys.all(scope) },
    { queryKey: dictKeys.types(scope) },
  ],
};

function invalidateAfterWrite(
  scope: QueryScope,
  effects: (scope: QueryScope) => readonly QueryGroupFilter[]
): void {
  // Coordination is separate from the server write result. Reads own their refresh errors.
  try {
    void invalidateQueryGroups(queryClient, effects(scope)).catch(reportCoordinationError);
  } catch (error) {
    reportCoordinationError(error);
  }
}

function reportCoordinationError(error: unknown): void {
  // A programming/coordination failure is observable without turning a successful write into a retry.
  window.dispatchEvent(new CustomEvent('ruoyi:query-coordination-error', { detail: error }));
}

export interface DictCommand<T> {
  readonly scope: QueryScope;
  readonly input: T;
}

/** Capture before calling mutateAsync: a paused native mutation has not run mutationFn yet. */
type DictCommandInput = DictDataModel | DictTypeModel | number | string | readonly number[] | null;

export function captureDictCommand<T extends DictCommandInput>(input: T): DictCommand<T> {
  const snapshot = Array.isArray(input)
    ? [...input]
    : input !== null && typeof input === 'object'
      ? { ...input }
      : input;
  return { scope: requireQueryScope(), input: snapshot as T };
}

async function write<T>(
  scope: QueryScope,
  execute: (options: ReturnType<typeof scopeRequestOptions>) => Promise<T>,
  effects: (scope: QueryScope) => readonly QueryGroupFilter[]
): Promise<T> {
  assertRequestScope(scopeRequestOptions(scope));
  const result = await execute(scopeRequestOptions(scope));
  invalidateAfterWrite(scope, effects);
  return result;
}

export const dictCommands = {
  createItem({ scope, input }: DictCommand<DictDataModel>) {
    const dto = { ...input };
    return write(scope, (options) => dataApi.addData(dto, options), dictEffects.data);
  },
  updateItem({ scope, input }: DictCommand<DictDataModel>) {
    const dto = { ...input };
    return write(scope, (options) => dataApi.updateData(dto, options), dictEffects.data);
  },
  deleteItems({ scope, input: ids }: DictCommand<number | string | readonly number[]>) {
    const value = Array.isArray(ids) ? ids.join(',') : String(ids);
    return write(scope, (options) => dataApi.delData(value, options), dictEffects.data);
  },
  createType({ scope, input }: DictCommand<DictTypeModel>) {
    const dto = { ...input };
    return write(scope, (options) => typeApi.addType(dto, options), dictEffects.type);
  },
  updateType({ scope, input }: DictCommand<DictTypeModel>) {
    const dto = { ...input };
    return write(scope, (options) => typeApi.updateType(dto, options), dictEffects.type);
  },
  deleteTypes({ scope, input: ids }: DictCommand<number | string>) {
    return write(scope, (options) => typeApi.delType(ids, options), dictEffects.type);
  },
  refreshCache({ scope }: DictCommand<null>) {
    return write(scope, (options) => typeApi.refreshCache(options), dictEffects.type);
  },
};
