import { beforeEach, describe, expect, it, vi } from 'vitest';
import { effectScope } from 'vue';
import { useDictManagementList } from './dict-management';
import { endQuerySession, setQuerySession } from '../context';

beforeEach(() => {
  endQuerySession();
  setQuerySession(1, [], []);
});

describe('dictionary management request view', () => {
  it('retains the same-filter result on refresh failure and retries only the read', async () => {
    const rows = { items: [{ dictId: 1 }], total: 1 };
    const error = new Error('read failed after write');
    const load = vi
      .fn()
      .mockResolvedValueOnce(rows)
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce({ items: [], total: 0 });
    const scope = effectScope();
    const list = scope.run(() => useDictManagementList(load))!;
    expect(await list.loadData({ page: 1 })).toBe(rows);
    expect(await list.loadData({ page: 1 })).toBe(rows);
    expect(list.status.error).toBe(error);
    expect(list.status.hasData).toBe(true);
    expect(await list.loadData({ page: 1 })).toEqual({ items: [], total: 0 });
    expect(list.status.error).toBeNull();
    scope.stop();
  });

  it('does not serve old filters or an old scope as a successful fallback', async () => {
    const load = vi
      .fn()
      .mockResolvedValueOnce({ items: ['old'], total: 1 })
      .mockRejectedValue(new Error('offline'));
    const scope = effectScope();
    const list = scope.run(() => useDictManagementList(load))!;
    await list.loadData({ page: 1 });
    await expect(list.loadData({ page: 2 })).rejects.toThrow('offline');
    expect(list.status.hasData).toBe(false);
    endQuerySession();
    setQuerySession(2, [], []);
    await expect(list.loadData({ page: 1 })).rejects.toThrow('offline');
    expect(list.status.hasData).toBe(false);
    scope.stop();
  });
  it('does not replace the current fallback snapshot when an older read completes late', async () => {
    let finishOld!: (value: { items: string[]; total: number }) => void;
    const load = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finishOld = resolve;
          })
      )
      .mockResolvedValueOnce({ items: ['after-write'], total: 1 });
    const scope = effectScope();
    const list = scope.run(() => useDictManagementList(load))!;
    const old = list.loadData({ page: 1 });
    const current = await list.loadData({ page: 1 });
    finishOld({ items: ['before-write'], total: 1 });
    await old;
    load.mockRejectedValueOnce(new Error('refresh failed'));
    expect(await list.loadData({ page: 1 })).toBe(current);
    scope.stop();
  });
});
