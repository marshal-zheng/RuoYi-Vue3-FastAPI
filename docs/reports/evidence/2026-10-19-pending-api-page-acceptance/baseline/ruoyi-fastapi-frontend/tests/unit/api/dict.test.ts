import { describe, expect, it } from 'vitest';

import * as dictDataApi from '@/api/system/dict/data';
import * as dictTypeApi from '@/api/system/dict/type';
import { createStatusHandler } from '@/mocks/handlers/error-common';
import { expectRequestTimeout } from '../../helpers/error-assertions';
import { setupMainlineMockHandlers } from '../../mocks/mainline';
import { mockServer } from '../../mocks/server';

describe('Dict Data API contract', () => {
  setupMainlineMockHandlers();

  it('loads paged dict data and typed dict options through MSW', async () => {
    const result = await dictDataApi.listData({
      dictType: 'sys_user_sex',
      dictLabel: '男',
      page: 1,
      pageSize: 10,
    });

    expect(result).toMatchObject({
      total: 1,
      items: [
        expect.objectContaining({
          dictType: 'sys_user_sex',
          dictLabel: '男',
        }),
      ],
    });
    expect(result.pager).toMatchObject({
      mode: 'offset',
      page: 1,
      size: 10,
      total: 1,
    });

    await expect(dictDataApi.getDicts('sys_user_sex')).resolves.toMatchObject({
      items: expect.arrayContaining([
        expect.objectContaining({ dictType: 'sys_user_sex', dictValue: '0' }),
        expect.objectContaining({ dictType: 'sys_user_sex', dictValue: '1' }),
      ]),
    });
  });

  it('loads and mutates dict data through the real request path', async () => {
    await expect(dictDataApi.getData(1)).resolves.toMatchObject({
      dictCode: 1,
      dictLabel: '男',
    });

    await expect(
      dictDataApi.addData({
        dictType: 'sys_user_sex',
        dictLabel: '未知',
        dictValue: '2',
        dictSort: 3,
        status: '0',
      })
    ).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });

    await expect(
      dictDataApi.updateData({
        dictCode: 1,
        dictLabel: '男性',
        dictValue: '0',
      })
    ).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });

    await expect(dictDataApi.delData('1,2,3')).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });
  });

  it('surfaces dict data failures from the request error mapping', async () => {
    mockServer.use(createStatusHandler('get', '/system/dict/data/list', 503));
    await expect(dictDataApi.listData({})).rejects.toMatchObject({
      status: 503,
    });

    mockServer.use(createStatusHandler('get', '/system/dict/data/list', 429));
    await expect(dictDataApi.listData({})).rejects.toMatchObject({
      status: 429,
    });

    await expectRequestTimeout('get', '/system/dict/data/list');
  });
});

describe('Dict Type API contract', () => {
  setupMainlineMockHandlers();

  it('loads paged dict types and option select data through MSW', async () => {
    const result = await dictTypeApi.listType({
      dictName: '用户性别',
      dictType: 'sys_user_sex',
      status: '0',
      page: 1,
      pageSize: 20,
    });

    expect(result).toMatchObject({
      total: 1,
      page: 1,
      pageSize: 20,
      items: [expect.objectContaining({ dictType: 'sys_user_sex' })],
    });
    expect(result.pager).toMatchObject({
      mode: 'offset',
      page: 1,
      size: 20,
      total: 1,
    });

    await expect(dictTypeApi.optionselect()).resolves.toMatchObject({
      items: expect.arrayContaining([expect.objectContaining({ dictType: 'sys_user_sex' })]),
    });
  });

  it('loads and mutates dict types through the real request path', async () => {
    await expect(dictTypeApi.getType(1)).resolves.toMatchObject({
      dictId: 1,
      dictType: 'sys_user_sex',
    });

    await expect(
      dictTypeApi.addType({
        dictName: '测试字典',
        dictType: 'test_dict',
        status: '0',
      })
    ).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });

    await expect(
      dictTypeApi.updateType({
        dictId: 1,
        dictName: '更新字典',
        dictType: 'test_dict',
      })
    ).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });

    await expect(dictTypeApi.delType('1,2,3')).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });
    await expect(dictTypeApi.refreshCache()).rejects.toMatchObject({
      status: 501,
      problem: { errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED' },
    });
  });

  it('surfaces dict type failures from the request error mapping', async () => {
    mockServer.use(createStatusHandler('get', '/system/dict/type/list', 429));
    await expect(dictTypeApi.listType({})).rejects.toMatchObject({
      status: 429,
    });

    mockServer.use(createStatusHandler('get', '/system/dict/type/list', 503));
    await expect(dictTypeApi.listType({})).rejects.toMatchObject({
      status: 503,
    });

    await expectRequestTimeout('get', '/system/dict/type/list');
  });
});
