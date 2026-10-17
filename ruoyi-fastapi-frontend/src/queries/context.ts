import { readonly, shallowRef } from 'vue';
import { AbortError, type RequestOptions } from '@zxio/http';
import { queryClient } from './client';

export interface QueryScope {
  readonly key: string;
  readonly userId: string;
  readonly authorization: string;
}

const currentScope = shallowRef<QueryScope | null>(null);
export const queryScope = readonly(currentScope);
const SCOPE_CONTEXT = 'ruoyi.query-scope';
let generation = 0;

export function endQuerySession(): void {
  const previous = currentScope.value;
  currentScope.value = null;
  if (!previous) return;
  const filters = { queryKey: ['ruoyi', previous.key] };
  // Cancellation starts synchronously. Removal also prevents late completions from reappearing.
  void queryClient.cancelQueries(filters);
  queryClient.removeQueries(filters);
}

export function setQuerySession(
  userId: string | number,
  roles: readonly string[],
  permissions: readonly string[]
): QueryScope {
  const authorization = JSON.stringify([[...roles].sort(), [...permissions].sort()]);
  const previous = currentScope.value;
  if (previous?.userId === String(userId) && previous.authorization === authorization)
    return previous;
  endQuerySession();
  const scope = Object.freeze({
    key: `${String(userId)}:${++generation}`,
    userId: String(userId),
    authorization,
  });
  currentScope.value = scope;
  return scope;
}

export function requireQueryScope(): QueryScope {
  if (!currentScope.value) throw new AbortError({ message: '会话已结束，请重新登录' });
  return currentScope.value;
}

export function scopeRequestOptions(scope: QueryScope): RequestOptions {
  return { context: { [SCOPE_CONTEXT]: scope.key } };
}

export function isRequestScopeCurrent(options?: RequestOptions): boolean {
  const key = options?.context?.[SCOPE_CONTEXT];
  return key === undefined || key === currentScope.value?.key;
}

export function assertRequestScope(options?: RequestOptions): void {
  if (!isRequestScopeCurrent(options)) throw new AbortError({ message: '会话已结束，请重新登录' });
}
