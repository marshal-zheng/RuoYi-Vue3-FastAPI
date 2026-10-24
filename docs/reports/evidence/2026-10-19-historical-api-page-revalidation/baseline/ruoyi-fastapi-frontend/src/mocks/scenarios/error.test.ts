import { describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import { createScenarioHandlers } from './index';

describe('mock error scenarios', () => {
  it('routes error-429 through the scenario factory with debug headers', async () => {
    mockServer.use(...createScenarioHandlers('pure', 'error-429'));

    const response = await fetch('/api/project/list');

    expect(response.status).toBe(429);
    expect(response.headers.get('X-Mock-Handler')).toBe('error-scenario');
    expect(response.headers.get('X-Mock-Scenario')).toBe('error-429');
    expect(response.headers.get('Retry-After')).toBe('30');
    await expect(response.json()).resolves.toMatchObject({
      status: 429,
      errorCode: 429,
    });
  });

  it('routes error-5xx through the scenario factory with problem details', async () => {
    mockServer.use(...createScenarioHandlers('pure', 'error-5xx'));

    const response = await fetch('/api/project/list');

    expect(response.status).toBe(503);
    expect(response.headers.get('X-Mock-Handler')).toBe('error-scenario');
    expect(response.headers.get('X-Mock-Scenario')).toBe('error-5xx');
    await expect(response.json()).resolves.toMatchObject({
      status: 503,
      errorCode: 503,
    });
  });
});
