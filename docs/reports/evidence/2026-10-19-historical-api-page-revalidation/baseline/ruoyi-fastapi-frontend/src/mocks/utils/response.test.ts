import { describe, expect, it } from 'vitest';

import { resultError, resultPageSuccess, resultSuccess } from './response';

describe('mock response helpers', () => {
  it('preserves the new page payload without legacy remapping', () => {
    expect(
      resultSuccess({
        items: [{ userId: 1 }],
        total: 3,
        page: 2,
        pageSize: 20,
      })
    ).toEqual({
      items: [{ userId: 1 }],
      total: 3,
      page: 2,
      pageSize: 20,
    });
  });

  it('emits page results with items/page/pageSize fields', () => {
    expect(resultPageSuccess(1, 10, [{ id: 1 }, { id: 2 }])).toEqual({
      items: [{ id: 1 }, { id: 2 }],
      total: 2,
      page: 1,
      pageSize: 10,
    });
  });

  it('returns problem-details-shaped errors', () => {
    expect(resultError('请求失败', { code: 429 })).toEqual({
      type: 'about:blank',
      title: '请求失败',
      status: 429,
      detail: '请求失败',
      instance: '',
    });
  });
});
