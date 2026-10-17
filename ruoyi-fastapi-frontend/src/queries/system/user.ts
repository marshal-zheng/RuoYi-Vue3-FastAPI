import { isCancelledError, queryOptions, skipToken } from '@tanstack/vue-query';
import { AbortError, queryRequest, type RequestOptions } from '@zxio/http';
import { invalidateQueryGroups, type QueryGroupFilter } from '@zxio/vue-query/core';
import * as api from '@/api/system/user';
import * as roleApi from '@/api/system/role';
import type {
  UserCreateModel,
  UserUpdateModel,
  UserStatusUpdateModel,
  UserRolesAssignModel,
  UserProfileUpdateModel,
  UserPageQueryModel,
  RoleUserRevokeModel,
  RoleUsersRevokeModel,
  RoleUsersGrantModel,
} from '@/api/_generated/types.gen';
import type { MenuTreeNode } from '@/api/system/menu';
import { queryClient } from '../client';
import {
  assertRequestScope,
  requireQueryScope,
  scopeRequestOptions,
  type QueryScope,
} from '../context';

export type UserFilters = Pick<
  UserPageQueryModel,
  'userName' | 'phonenumber' | 'status' | 'deptId' | 'beginTime' | 'endTime'
>;

/** Only submitted business filters enter requests, keys and full-list exports. */
export function normalizeUserFilters(input: Readonly<Record<string, unknown>> = {}): UserFilters {
  const filters: UserFilters = {};
  for (const field of ['userName', 'phonenumber'] as const) {
    const value = typeof input[field] === 'string' ? input[field].trim() : '';
    if (value) filters[field] = value;
  }
  if (input.status === '0' || input.status === '1') filters.status = input.status;
  const deptId = Number(input.deptId);
  if (Number.isSafeInteger(deptId) && deptId > 0) filters.deptId = deptId;
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
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : fallback;
}
export const userKeys = {
  all: (scope: QueryScope) => ['ruoyi', scope.key, 'users'] as const,
  lists: (scope: QueryScope) => [...userKeys.all(scope), 'list'] as const,
  list: (scope: QueryScope, params: UserPageQueryModel) =>
    [...userKeys.lists(scope), params] as const,
  details: (scope: QueryScope) => [...userKeys.all(scope), 'detail'] as const,
  detail: (scope: QueryScope, id: number) => [...userKeys.details(scope), id] as const,
  formOptions: (scope: QueryScope) => [...userKeys.all(scope), 'form-options'] as const,
  departments: (scope: QueryScope) => [...userKeys.all(scope), 'departments'] as const,
};

export function userListOptions(
  scope: QueryScope | null,
  input: Readonly<Record<string, unknown>> = {}
) {
  const params = {
    ...normalizeUserFilters(input),
    page: positiveInteger(input.page, 1),
    pageSize: positiveInteger(input.pageSize, 10),
  };
  return queryOptions({
    queryKey: scope
      ? userKeys.list(scope, params)
      : (['ruoyi', 'disabled', 'users', 'list', params] as const),
    queryFn: scope
      ? ({ signal }) => api.listUser(params, queryRequest(signal, scopeRequestOptions(scope)))
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}
export function userDeptTreeOptions(scope: QueryScope | null) {
  return queryOptions({
    queryKey: scope
      ? userKeys.departments(scope)
      : (['ruoyi', 'disabled', 'users', 'departments'] as const),
    queryFn: scope
      ? async ({ signal }): Promise<readonly MenuTreeNode[]> => {
          const response = await api.deptTreeSelect(
            queryRequest(signal, scopeRequestOptions(scope))
          );
          return response.items;
        }
      : skipToken,
    enabled: scope !== null,
    staleTime: 30_000,
    retry: false,
  });
}
export function userDetailOptions(scope: QueryScope | null, input: unknown) {
  const id = Number(input);
  const ready = scope !== null && Number.isSafeInteger(id) && id > 0;
  return queryOptions({
    queryKey: ready
      ? userKeys.detail(scope, id)
      : (['ruoyi', scope?.key ?? 'disabled', 'users', 'detail', 0] as const),
    queryFn: ready
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.getUser(id, { signal: context.signal, requestOptions: context.options });
        }
      : skipToken,
    enabled: ready,
    // This response embeds role/post catalogs whose writes are not Query resources yet.
    staleTime: 0,
    retry: false,
  });
}
export function userCreateOptions(scope: QueryScope | null) {
  return queryOptions({
    queryKey: scope
      ? userKeys.formOptions(scope)
      : (['ruoyi', 'disabled', 'users', 'form-options'] as const),
    queryFn: scope
      ? ({ signal }) => {
          const context = queryRequest(signal, scopeRequestOptions(scope));
          return api.getUser(undefined, {
            signal: context.signal,
            requestOptions: context.options,
          });
        }
      : skipToken,
    enabled: scope !== null,
    // Each editor opening waits for current role/post catalogs; concurrent openings still share.
    staleTime: 0,
    retry: false,
  });
}

/** A dialog opening consumes a fresh resource once; its editable draft remains local. */
export async function readUserEditor(
  scope: QueryScope | null,
  id?: number | string,
  openingSignal?: AbortSignal
) {
  if (!scope || (id !== undefined && (!Number.isSafeInteger(Number(id)) || Number(id) <= 0))) {
    throw new AbortError({ message: '用户编辑条件已失效' });
  }
  const ended = () => new AbortError({ message: '用户编辑已结束' });
  if (openingSignal?.aborted) throw ended();
  let removeAbortListener: (() => void) | undefined;
  // End only the opening's wait. Another subscriber keeps the native read.
  const openingEnded = openingSignal
    ? new Promise<never>((_, reject) => {
        const abort = () => reject(ended());
        openingSignal.addEventListener('abort', abort, { once: true });
        removeAbortListener = () => openingSignal.removeEventListener('abort', abort);
      })
    : undefined;
  try {
    while (true) {
      if (openingSignal?.aborted) throw ended();
      assertRequestScope(scopeRequestOptions(scope));
      try {
        const reading =
          id === undefined
            ? queryClient.fetchQuery(userCreateOptions(scope))
            : queryClient.fetchQuery(userDetailOptions(scope, id));
        return await (openingEnded ? Promise.race([reading, openingEnded]) : reading);
      } catch (error) {
        if (!isCancelledError(error)) throw error;
        // A resource write can cancel the first snapshot. Join its replacement
        // while this opening is current, without displaying cancellation.
      }
    }
  } finally {
    removeAbortListener?.();
  }
}
export interface UserCommand<T> {
  readonly scope: QueryScope;
  readonly input: T;
}
/** Capture before confirmation/queued mutation; copy editable array fields, not immutable files. */
export function captureUserCommand<T extends object | number | string>(
  input: T,
  scope = requireQueryScope()
): UserCommand<T> {
  let snapshot: unknown = input;
  if (input instanceof FormData) {
    const form = new FormData();
    for (const [key, value] of input.entries()) form.append(key, value);
    snapshot = form;
  } else if (Array.isArray(input)) {
    snapshot = [...input];
  } else if (typeof input === 'object' && input !== null) {
    snapshot = Object.fromEntries(
      Object.entries(input).map(([key, value]) => [key, Array.isArray(value) ? [...value] : value])
    );
  }
  return { scope, input: snapshot as T };
}
export const userEffects = (scope: QueryScope): readonly QueryGroupFilter[] => [
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
    void invalidateQueryGroups(queryClient, userEffects(scope)).catch(reportCoordinationError);
  } catch (error) {
    reportCoordinationError(error);
  }
  return result;
}
function reportCoordinationError(error: unknown): void {
  window.dispatchEvent(new CustomEvent('ruoyi:query-coordination-error', { detail: error }));
}
export const userCommands = {
  createUser: ({ scope, input }: UserCommand<UserCreateModel>) =>
    write(scope, (options) => api.addUser(input, options)),
  updateUser: ({ scope, input }: UserCommand<UserUpdateModel>) =>
    write(scope, (options) => api.updateUser(input, options)),
  deleteUsers: ({ scope, input }: UserCommand<number | string | readonly (number | string)[]>) =>
    write(scope, (options) =>
      api.delUser(Array.isArray(input) ? input.join(',') : String(input), options)
    ),
  changeStatus: ({ scope, input }: UserCommand<UserStatusUpdateModel>) =>
    write(scope, (options) => api.changeUserStatus(input.userId, input.status, options)),
  resetPassword: ({ scope, input }: UserCommand<{ userId: number | string; password: string }>) =>
    write(scope, (options) => api.resetUserPwd(input.userId, input.password, options)),
  assignRoles: ({ scope, input }: UserCommand<UserRolesAssignModel>) =>
    write(scope, (options) => api.updateAuthRole(input, options)),
  unassignRoleUser: ({ scope, input }: UserCommand<RoleUserRevokeModel>) =>
    write(scope, (options) => roleApi.authUserCancel(input, options)),
  unassignRoleUsers: ({ scope, input }: UserCommand<RoleUsersRevokeModel>) =>
    write(scope, (options) => roleApi.authUserCancelAll(input, options)),
  assignRoleUsers: ({ scope, input }: UserCommand<RoleUsersGrantModel>) =>
    write(scope, (options) => roleApi.authUserSelectAll(input, options)),
  updateProfile: ({ scope, input }: UserCommand<UserProfileUpdateModel>) =>
    write(scope, (options) => api.updateUserProfile(input, options)),
  updatePassword: ({ scope, input }: UserCommand<{ oldPassword: string; newPassword: string }>) =>
    write(scope, (options) => api.updateUserPwd(input.oldPassword, input.newPassword, options)),
  uploadAvatar: ({ scope, input }: UserCommand<FormData>) =>
    write(scope, (options) => api.uploadAvatar(input, options)),
  importExcel: (
    { scope, input }: UserCommand<{ file: File; updateSupport: boolean }>,
    config?: Pick<Parameters<typeof api.importUserExcel>[2] & {}, 'signal' | 'onUploadProgress'>
  ) =>
    write(scope, (options) =>
      api.importUserExcel(input.file, input.updateSupport, { ...config, requestOptions: options })
    ),
};
