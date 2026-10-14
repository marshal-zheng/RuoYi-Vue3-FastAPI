import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { MOCK_PROJECT_IDS, MOCK_SIMULATION_IDS, MOCK_VERSION_IDS } from '../data';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';
import { mockServer } from '../../../tests/mocks/server';
import { validateOpenApiResponse } from '../../../tests/mocks/contracts/openapi-schema-validator';

import { createMockHandlers } from './index';

import { buildMockContractReport } from '../../../scripts/mock-contracts-core.mjs';

interface RequestCase {
  method: string;
  openapiPath: string;
  requestPath: string;
  init?: RequestInit;
}

const report = buildMockContractReport({ cwd: process.cwd() });
const loginCase: RequestCase = {
  method: 'POST',
  openapiPath: '/login',
  requestPath: '/api/login',
  init: {
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' }),
  },
};

function caseKey(testCase: Pick<RequestCase, 'method' | 'openapiPath'>) {
  return `${testCase.method} ${testCase.openapiPath}`;
}

function openApiValidatedCases(token: string): RequestCase[] {
  return [
    loginCase,
    {
      method: 'GET',
      openapiPath: '/getInfo',
      requestPath: '/api/getInfo',
      init: { headers: { authorization: `Bearer ${token}` } },
    },
    {
      method: 'GET',
      openapiPath: '/project/list',
      requestPath: '/api/project/list?page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/project/{project_id}',
      requestPath: `/api/project/${MOCK_PROJECT_IDS.commandCenter}`,
    },
    {
      method: 'GET',
      openapiPath: '/project/version/list',
      requestPath: `/api/project/version/list?projectId=${MOCK_PROJECT_IDS.commandCenter}`,
    },
    {
      method: 'GET',
      openapiPath: '/project/version/{version_id}',
      requestPath: `/api/project/version/${MOCK_VERSION_IDS.commandCenterReview}`,
    },
    {
      method: 'GET',
      openapiPath: '/system/role/list',
      requestPath: '/api/system/role/list?page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/role/{role_id}',
      requestPath: '/api/system/role/1',
    },
    {
      method: 'GET',
      openapiPath: '/system/role/authUser/allocatedList',
      requestPath: '/api/system/role/authUser/allocatedList?roleId=1&page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/role/authUser/unallocatedList',
      requestPath: '/api/system/role/authUser/unallocatedList?roleId=1&page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/dict/data/list',
      requestPath: '/api/system/dict/data/list?dictType=sys_user_sex&page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/dict/data/{dict_code}',
      requestPath: '/api/system/dict/data/1',
    },
    {
      method: 'GET',
      openapiPath: '/system/dict/type/list',
      requestPath: '/api/system/dict/type/list?page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/dict/type/optionselect',
      requestPath: '/api/system/dict/type/optionselect',
    },
    {
      method: 'GET',
      openapiPath: '/system/dict/type/{dict_id}',
      requestPath: '/api/system/dict/type/1',
    },
    {
      method: 'GET',
      openapiPath: '/system/menu/list',
      requestPath: '/api/system/menu/list',
    },
    {
      method: 'GET',
      openapiPath: '/system/menu/{menu_id}',
      requestPath: '/api/system/menu/1',
    },
    {
      method: 'GET',
      openapiPath: '/system/config/list',
      requestPath: '/api/system/config/list?page=1&pageSize=10',
    },
    {
      method: 'GET',
      openapiPath: '/system/config/{config_id}',
      requestPath: '/api/system/config/1',
    },
    {
      method: 'GET',
      openapiPath: '/system/user/list',
      requestPath: '/api/system/user/list?page=1&pageSize=10',
    },
  ];
}

function registryEntry(method: string, openapiPath: string) {
  const entry = report.entries.find(
    (item: { method: string; openapiPath: string }) =>
      item.method === method && item.openapiPath === openapiPath
  );
  if (!entry) {
    throw new Error(`Missing registry entry for ${method} ${openapiPath}`);
  }
  return entry;
}

async function readJsonCase(testCase: RequestCase) {
  const entry = registryEntry(testCase.method, testCase.openapiPath);
  const response = await fetch(testCase.requestPath, {
    method: testCase.method,
    ...testCase.init,
    headers: {
      ...(testCase.init?.headers ?? {}),
    },
  });
  expect(response.headers.get('X-Mock-Handler')).toBe(entry.handlerTag);
  const body = await response.json();
  return { body, response, entry };
}

describe('mock handlers OpenAPI schema metadata', () => {
  it('requires every openapi-validated registry entry to have a runtime schema case', () => {
    const expected = report.entries
      .filter((entry: { schemaStatus: string }) => entry.schemaStatus === 'openapi-validated')
      .map(caseKey)
      .sort();
    const actual = openApiValidatedCases('__schema_guard_token__').map(caseKey).sort();

    expect(actual).toEqual(expected);
  });
});

describe('mock handlers OpenAPI schema gate', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;
  let token: string;

  beforeEach(async () => {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-api-contract-schema-test`);
    replaceMockDemoDb(db);
    dataSource = createMockDataSource(db);
    replaceMockDataSource(dataSource);
    await dataSource.init();
    mockServer.use(...createMockHandlers({ strategy: 'pure', dataSource }));

    const login = await readJsonCase(loginCase);
    token = login.body.token;
    const validation = validateOpenApiResponse({
      method: 'POST',
      openapiPath: '/login',
      body: login.body,
    });
    expect(validation).toEqual({ ok: true });
  });

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db.delete();
  });

  it('validates core openapi-validated JSON responses through MSW', async () => {
    const validatedCases = openApiValidatedCases(token);

    for (const testCase of validatedCases) {
      expect(registryEntry(testCase.method, testCase.openapiPath).schemaStatus).toBe(
        'openapi-validated'
      );
      const { body } = await readJsonCase(testCase);
      const validation = validateOpenApiResponse({
        method: testCase.method,
        openapiPath: testCase.openapiPath,
        body,
      });
      expect(validation, `${testCase.method} ${testCase.openapiPath}`).toEqual({
        ok: true,
      });
    }
  });

  it('keeps schema-unavailable critical responses explicit and tagged', async () => {
    const exceptionCases: RequestCase[] = [
      {
        method: 'GET',
        openapiPath: '/captchaImage',
        requestPath: '/api/captchaImage',
      },
      {
        method: 'GET',
        openapiPath: '/getRouters',
        requestPath: '/api/getRouters',
      },
      {
        method: 'GET',
        openapiPath: '/system/dict/data/type/{dict_type}',
        requestPath: '/api/system/dict/data/type/sys_user_sex',
      },
      {
        method: 'GET',
        openapiPath: '/system/dept/list',
        requestPath: '/api/system/dept/list',
      },
      {
        method: 'GET',
        openapiPath: '/device/list',
        requestPath: '/api/device/list?page=1&pageSize=10',
      },
      {
        method: 'GET',
        openapiPath: '/project/topology/{project_id}',
        requestPath: `/api/project/topology/${MOCK_PROJECT_IDS.commandCenter}?version_id=${MOCK_VERSION_IDS.commandCenterReview}`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/sessions/{session_id}/status',
        requestPath: `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/status`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/sessions/{session_id}/messages',
        requestPath: `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/messages?limit=1`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/sessions/{session_id}/bandwidth',
        requestPath: `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/bandwidth`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/sessions/{session_id}/alarms',
        requestPath: `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/alarms`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/sessions/{session_id}/events',
        requestPath: `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/events`,
      },
      {
        method: 'GET',
        openapiPath: '/simulation/strategies',
        requestPath: '/api/simulation/strategies',
      },
    ];

    for (const testCase of exceptionCases) {
      const entry = registryEntry(testCase.method, testCase.openapiPath);
      expect(entry.schemaStatus).toBe('schema-unavailable');
      expect(entry.reason).toBeTruthy();
      await readJsonCase(testCase);
    }
  });

  it('validates unsupported-501 and binary response classifications', async () => {
    const unsupported = registryEntry('POST', '/simulation/sessions/{session_id}/pause');
    const pauseResponse = await fetch(
      `/api/simulation/sessions/${MOCK_SIMULATION_IDS.commandCenterSession}/pause`,
      { method: 'POST' }
    );
    expect(pauseResponse.status).toBe(501);
    expect(pauseResponse.headers.get('X-Mock-Handler')).toBe(unsupported.handlerTag);
    await expect(pauseResponse.json()).resolves.toMatchObject({
      status: 501,
      errorCode: 'MOCK_SIMULATION_NOT_SUPPORTED',
    });

    const binary = registryEntry('GET', '/project/export/{project_id}');
    expect(binary.schemaStatus).toBe('binary-response');
    const exportResponse = await fetch(`/api/project/export/${MOCK_PROJECT_IDS.commandCenter}`);
    expect(exportResponse.headers.get('X-Mock-Handler')).toBe(binary.handlerTag);
    expect(exportResponse.headers.get('content-disposition')).toContain('attachment');
    await expect(exportResponse.text()).resolves.toContain('mock project export');
  });
});
