import { describe, expect, it } from 'vitest';
import { normalizeGridParams } from './grid-params';

describe('GridList RuoYi wire contract', () => {
  it('maps logical sort with and without pagination without mutating input', () => {
    const sort = [{ field: 'operTime', order: 'desc' }];
    const input = {
      query: { title: '项目' },
      pager: { page: 2, size: 20 },
      sort,
    };
    expect(normalizeGridParams(input)).toEqual({
      title: '项目',
      page: 2,
      pageSize: 20,
      orderByColumn: 'operTime',
      isAsc: 'desc',
    });
    expect(normalizeGridParams({ sort })).toEqual({
      orderByColumn: 'operTime',
      isAsc: 'desc',
    });
    expect(input.sort).toBe(sort);
    expect(input.pager).toEqual({ page: 2, size: 20 });
  });
  it('clears stale wire sorting on explicit empty sort and preserves ordinary non-list input', () => {
    expect(
      normalizeGridParams({
        query: { orderByColumn: 'old', isAsc: 'asc' },
        sort: [],
      })
    ).toEqual({});
    expect(normalizeGridParams({ orderByColumn: 'old', isAsc: 'asc' })).toEqual({
      orderByColumn: 'old',
      isAsc: 'asc',
    });
  });
});
