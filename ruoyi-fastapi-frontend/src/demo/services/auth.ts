import type { DemoAuthSession, DemoCsrfToken, DemoWsTicket } from '@/demo/db';
import { AuthRepository } from '@/demo/repositories';
import type { DemoAccount, DemoRole } from '@/demo/scenarios';

const SESSION_TTL_MS = 12 * 60 * 60 * 1000;
const CSRF_TTL_MS = 2 * 60 * 60 * 1000;
const WS_TICKET_TTL_MS = 30 * 1000;

export class DemoAuthError extends Error {
  constructor(
    message: string,
    readonly status = 401,
    readonly code = status
  ) {
    super(message);
    this.name = 'DemoAuthError';
  }
}

export interface DemoLoginInput {
  username?: string;
  password?: string;
}

export interface DemoCaptchaResponse {
  captchaEnabled: false;
  img: string;
  uuid: string;
}

export interface DemoLoginResponse {
  code: 200;
  msg: string;
  type: 'success';
  token: string;
  expiresIn: number;
  csrfToken: string;
}

export interface DemoCurrentUserResponse {
  code: 200;
  msg: string;
  type: 'success';
  user: Record<string, unknown>;
  roles: string[];
  permissions: string[];
  isDefaultModifyPwd: false;
  isPasswordExpired: false;
}

export interface DemoRefreshResponse {
  code: 200;
  msg: string;
  type: 'success';
  token: string;
  expiresIn: number;
  csrfToken: string;
}

export interface DemoCsrfResponse {
  code: 200;
  msg: string;
  type: 'success';
  csrfToken: string;
  csrf_token: string;
}

export interface DemoWsTicketInput {
  sessionId?: string;
  session_id?: string;
}

export interface DemoWsTicketResponse {
  code: 200;
  msg: string;
  type: 'success';
  wsTicket: string;
  ws_ticket: string;
  expiresIn: number;
}

function expiresAt(ttlMs: number): string {
  return new Date(Date.now() + ttlMs).toISOString();
}

function isExpired(expiresAtValue: string): boolean {
  return Date.parse(expiresAtValue) <= Date.now();
}

function randomToken(prefix: string): string {
  const randomId =
    typeof globalThis.crypto?.randomUUID === 'function'
      ? globalThis.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  return `${prefix}-${randomId}`;
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)));
}

export class DemoAuthService {
  constructor(private readonly authRepository: AuthRepository) {}

  getCaptcha(): DemoCaptchaResponse {
    return {
      captchaEnabled: false,
      img: '',
      uuid: 'demo-offline-captcha',
    };
  }

  async login(input: DemoLoginInput): Promise<DemoLoginResponse> {
    const username = String(input.username ?? '').trim();
    const password = String(input.password ?? '');

    if (!username) {
      throw new DemoAuthError('用户名不能为空', 400);
    }

    if (!password) {
      throw new DemoAuthError('密码不能为空', 400);
    }

    const account = await this.authRepository.getAccount(username);

    if (!account || account.password !== password) {
      throw new DemoAuthError('用户名或密码错误', 401);
    }

    const token = account.token || randomToken(`demo-token-${username}`);
    const session: DemoAuthSession = {
      token,
      username,
      expiresAt: expiresAt(SESSION_TTL_MS),
    };

    await this.authRepository.saveSession(session);
    const csrfToken = await this.ensureCsrfToken(session);

    return {
      code: 200,
      msg: '登录成功',
      type: 'success',
      token,
      expiresIn: Math.floor(SESSION_TTL_MS / 1000),
      csrfToken: csrfToken.token,
    };
  }

  async getInfo(token: string | undefined): Promise<DemoCurrentUserResponse> {
    const session = await this.resolveSession(token);
    const account = await this.authRepository.getAccount(session.username);

    if (!account) {
      throw new DemoAuthError('登录信息已过期，请重新登录', 401);
    }

    const roles = await this.authRepository.listRoles();
    const roleKeys = this.resolveRoleKeys(account, roles);
    const permissions = this.resolvePermissions(account, roles, roleKeys);

    return {
      code: 200,
      msg: '操作成功',
      type: 'success',
      user: account.user,
      roles: roleKeys.length ? roleKeys : ['ROLE_DEFAULT'],
      permissions,
      isDefaultModifyPwd: false,
      isPasswordExpired: false,
    };
  }

  async refresh(token: string | undefined): Promise<DemoRefreshResponse> {
    const session = await this.resolveSession(token, { allowLatest: true });
    const refreshedSession: DemoAuthSession = {
      ...session,
      expiresAt: expiresAt(SESSION_TTL_MS),
    };

    await this.authRepository.saveSession(refreshedSession);
    const csrfToken = await this.ensureCsrfToken(refreshedSession);

    return {
      code: 200,
      msg: '刷新成功',
      type: 'success',
      token: refreshedSession.token,
      expiresIn: Math.floor(SESSION_TTL_MS / 1000),
      csrfToken: csrfToken.token,
    };
  }

  async getCsrfToken(token: string | undefined): Promise<DemoCsrfResponse> {
    const session = await this.resolveSession(token, { allowLatest: true });
    const csrfToken = await this.ensureCsrfToken(session);

    return {
      code: 200,
      msg: '操作成功',
      type: 'success',
      csrfToken: csrfToken.token,
      csrf_token: csrfToken.token,
    };
  }

  async issueWsTicket(
    token: string | undefined,
    input: DemoWsTicketInput
  ): Promise<DemoWsTicketResponse> {
    await this.resolveSession(token);
    const sessionId = String(input.sessionId ?? input.session_id ?? '').trim();

    if (!sessionId) {
      throw new DemoAuthError('仿真会话ID不能为空', 400);
    }

    const ticket = randomToken('demo-ws-ticket');
    const record: DemoWsTicket = {
      ticket,
      sessionId,
      expiresAt: expiresAt(WS_TICKET_TTL_MS),
      used: false,
    };

    await this.authRepository.saveWsTicket(record);

    return {
      code: 200,
      msg: '操作成功',
      type: 'success',
      wsTicket: ticket,
      ws_ticket: ticket,
      expiresIn: Math.floor(WS_TICKET_TTL_MS / 1000),
    };
  }

  async consumeWsTicket(ticket: string | undefined, sessionId: string): Promise<DemoWsTicket> {
    const normalizedTicket = String(ticket ?? '').trim();

    if (!normalizedTicket) {
      throw new DemoAuthError('WebSocket ticket 不能为空', 401);
    }

    const record = await this.authRepository.getWsTicket(normalizedTicket);

    if (!record || isExpired(record.expiresAt)) {
      throw new DemoAuthError('WebSocket ticket 无效或已过期', 401);
    }

    if (record.used) {
      throw new DemoAuthError('WebSocket ticket 已被使用', 401);
    }

    if (record.sessionId !== sessionId) {
      throw new DemoAuthError('WebSocket ticket 与仿真会话不匹配', 401);
    }

    await this.authRepository.markWsTicketUsed(record.ticket);

    return record;
  }

  async logout(token: string | undefined): Promise<{ code: 200; msg: string; type: 'success' }> {
    if (token) {
      await this.authRepository.removeSession(token);
      await this.authRepository.removeCsrfTokensBySession(token);
    } else {
      await this.authRepository.clearSessions();
      await this.authRepository.clearCsrfTokens();
    }

    return {
      code: 200,
      msg: '退出成功',
      type: 'success',
    };
  }

  private async resolveSession(
    token: string | undefined,
    options: { allowLatest?: boolean } = {}
  ): Promise<DemoAuthSession> {
    if (token) {
      const session = await this.authRepository.getSession(token);

      if (session && !isExpired(session.expiresAt)) {
        return session;
      }

      if (session) {
        await this.authRepository.removeSession(token);
        await this.authRepository.removeCsrfTokensBySession(token);
      }
    }

    if (options.allowLatest) {
      const latestSession = await this.findLatestValidSession();

      if (latestSession) {
        return latestSession;
      }
    }

    throw new DemoAuthError('登录状态已过期，请重新登录', 401);
  }

  private async findLatestValidSession(): Promise<DemoAuthSession | undefined> {
    const sessions = await this.authRepository.listSessions();
    return sessions
      .filter((session) => !isExpired(session.expiresAt))
      .sort((left, right) => Date.parse(right.expiresAt) - Date.parse(left.expiresAt))[0];
  }

  private async ensureCsrfToken(session: DemoAuthSession): Promise<DemoCsrfToken> {
    const existing = await this.authRepository.getCsrfTokenBySession(session.token);

    if (existing && !isExpired(existing.expiresAt)) {
      return existing;
    }

    const token: DemoCsrfToken = {
      token: randomToken(`demo-csrf-${session.username}`),
      sessionToken: session.token,
      expiresAt: expiresAt(CSRF_TTL_MS),
    };

    await this.authRepository.saveCsrfToken(token);
    return token;
  }

  private resolveRoleKeys(account: DemoAccount, roles: DemoRole[]): string[] {
    if (account.roles.length) {
      return account.roles;
    }

    return roles
      .filter((role) => account.roleIds.includes(role.roleId))
      .map((role) => role.roleKey);
  }

  private resolvePermissions(
    account: DemoAccount,
    roles: DemoRole[],
    roleKeys: string[]
  ): string[] {
    return unique([
      ...account.permissions,
      ...roles
        .filter((role) => roleKeys.includes(role.roleKey))
        .flatMap((role) => role.permissions),
    ]);
  }
}
