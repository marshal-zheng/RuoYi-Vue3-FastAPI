import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import { AuthRepository, ScenarioRepository } from '@/demo/repositories';
import { defaultDemoScenario } from '@/demo/scenarios';

import { DemoAuthService } from './auth';

let db: DemoOfflineDb;
let authService: DemoAuthService;

describe('DemoAuthService', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-auth-service-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    authService = new DemoAuthService(new AuthRepository(db));
  });

  afterEach(async () => {
    await db.delete();
  });

  it('logs in with scenario account data and restores user info', async () => {
    const login = await authService.login({
      username: 'admin',
      password: 'admin123',
    });
    const info = await authService.getInfo(login.token);

    expect(login).toMatchObject({
      code: 200,
      token: 'demo-token-admin',
      csrfToken: expect.any(String),
    });
    expect(info).toMatchObject({
      user: expect.objectContaining({ userName: 'admin' }),
      roles: expect.arrayContaining(['admin']),
      permissions: expect.arrayContaining(['*:*:*']),
    });
  });

  it('refreshes from the latest local demo session when no token header is available', async () => {
    const login = await authService.login({
      username: 'admin',
      password: 'admin123',
    });
    const refresh = await authService.refresh(undefined);

    expect(refresh).toMatchObject({
      token: login.token,
      csrfToken: expect.any(String),
    });
  });

  it('issues single-use WebSocket tickets', async () => {
    const login = await authService.login({
      username: 'admin',
      password: 'admin123',
    });
    const issued = await authService.issueWsTicket(login.token, {
      session_id: 'demo-session-1001',
    });

    expect(issued).toMatchObject({
      code: 200,
      wsTicket: expect.stringMatching(/^demo-ws-ticket-/),
      ws_ticket: issued.wsTicket,
      expiresIn: 30,
    });

    await expect(
      authService.consumeWsTicket(issued.wsTicket, 'demo-session-1001')
    ).resolves.toMatchObject({
      ticket: issued.wsTicket,
      sessionId: 'demo-session-1001',
      used: false,
    });

    await expect(authService.consumeWsTicket(issued.wsTicket, 'demo-session-1001')).rejects.toEqual(
      expect.objectContaining({
        name: 'DemoAuthError',
        status: 401,
      })
    );
  });

  it('rejects invalid credentials with an auth error', async () => {
    await expect(authService.login({ username: 'admin', password: 'bad' })).rejects.toEqual(
      expect.objectContaining({
        name: 'DemoAuthError',
        status: 401,
      })
    );
  });
});
