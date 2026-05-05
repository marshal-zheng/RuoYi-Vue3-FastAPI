import { describe, expect, it } from 'vitest';

import * as configApi from '@/api/system/config';
import { createStatusHandler } from '@/mocks/handlers/error-common';
import { expectRequestTimeout } from '../../helpers/error-assertions';
import { setupMainlineMockHandlers } from '../../mocks/mainline';
import { mockServer } from '../../mocks/server';

describe('Config API contract', () => {
  setupMainlineMockHandlers();

  it('loads paged configs with query params through the HTTP contract', async () => {
    const result = await configApi.listConfig({
      configName: '系统名称',
      configKey: 'sys.index.skinName',
      page: 1,
      pageSize: 20,
    });

    expect(result).toMatchObject({
      total: 1,
      page: 1,
      pageSize: 20,
      items: [
        expect.objectContaining({
          configName: '系统名称',
          configKey: 'sys.index.skinName',
        }),
      ],
    });
    expect(result.pager).toMatchObject({
      mode: 'offset',
      page: 1,
      size: 20,
      total: 1,
    });
  });

  it('loads config detail and key-value lookups via MSW', async () => {
    await expect(configApi.getConfig(1)).resolves.toMatchObject({
      configId: 1,
      configValue: 'skin-blue',
    });

    await expect(configApi.getConfig('1')).resolves.toMatchObject({
      configId: 1,
      configKey: 'sys.index.skinName',
    });

    await expect(configApi.getConfigKey('sys.index.skinName')).resolves.toBe('skin-blue');
    await expect(configApi.getConfigKey('sys.account.captchaEnabled')).resolves.toBe('true');
  });

  it('handles config mutations through real request serialization', async () => {
    await expect(
      configApi.addConfig({
        configName: '测试参数',
        configKey: 'test.config.key',
        configValue: 'test-value',
        configType: 'N',
      })
    ).resolves.toMatchObject({
      configId: 1000,
      configKey: 'test.config.key',
      configValue: 'test-value',
    });

    await expect(
      configApi.updateConfig({
        configId: 1,
        configName: '更新参数',
        configValue: 'updated-value',
      })
    ).resolves.toMatchObject({
      configId: 1,
      configValue: 'updated-value',
    });

    await expect(configApi.delConfig('1,2,3')).resolves.toBeNull();
    await expect(configApi.refreshCache()).resolves.toBeNull();
  });

  it('surfaces config API failures from the request error mapping', async () => {
    mockServer.use(createStatusHandler('get', '/system/config/list', 503));
    await expect(configApi.listConfig({})).rejects.toMatchObject({
      status: 503,
    });

    mockServer.use(createStatusHandler('get', '/system/config/list', 429));
    await expect(configApi.listConfig({})).rejects.toMatchObject({
      status: 429,
    });

    await expectRequestTimeout('get', '/system/config/list');
  });
});
