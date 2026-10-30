import { beforeEach, describe, expect, it } from 'vitest';
import { queryClient } from './client';
import {
  gridQueryContext,
  endQuerySession,
  setQuerySession,
  queryScope,
  scopeRequestOptions,
  assertRequestScope,
} from './context';

beforeEach(() => {
  endQuerySession();
  queryClient.clear();
});

describe('application query scope', () => {
  it('notifies GridList only after the domain has changed, including readiness edges', () => {
    const captures: ReturnType<typeof gridQueryContext.capture>[] = [];
    const stop = gridQueryContext.subscribe(() => captures.push(gridQueryContext.capture()));
    const first = setQuerySession(1, [], []);
    endQuerySession();
    const second = setQuerySession(1, [], []);
    stop();
    expect(captures.map((capture) => capture.ready)).toEqual([true, false, true]);
    expect(captures[0].version).toBe(first.key);
    expect(captures[2].version).toBe(second.key);
    expect(first.key).not.toBe(second.key);
  });
  it('removes only its old scope and rejects a queued request after logout', () => {
    const first = setQuerySession(1, ['admin'], ['read']);
    const options = scopeRequestOptions(first);
    queryClient.setQueryData(['ruoyi', first.key, 'dict'], []);
    queryClient.setQueryData(['other-app', 'data'], 'keep');
    endQuerySession();
    expect(queryScope.value).toBeNull();
    expect(queryClient.getQueryData(['ruoyi', first.key, 'dict'])).toBeUndefined();
    expect(queryClient.getQueryData(['other-app', 'data'])).toBe('keep');
    setQuerySession(2, [], []);
    expect(() => assertRequestScope(options)).toThrow('会话已结束');
  });

  it('preserves scope for unchanged authorization and rotates on authorization or login changes', () => {
    const first = setQuerySession(1, ['admin'], ['write', 'read']);
    expect(setQuerySession(1, ['admin'], ['read', 'write'])).toBe(first);
    expect(setQuerySession(1, ['user'], ['read']).key).not.toBe(first.key);
    endQuerySession();
    expect(setQuerySession(1, ['admin'], ['write', 'read']).key).not.toBe(first.key);
  });
});
