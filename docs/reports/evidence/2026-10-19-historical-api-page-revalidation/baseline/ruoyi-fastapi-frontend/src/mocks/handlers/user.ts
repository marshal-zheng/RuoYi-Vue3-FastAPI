import { http, HttpResponse } from 'msw';

import { createApiPath } from '../constants';
import type { MockCurrentUserResponse, MockLoginResponse } from '../contracts';
import type { MockAccount } from '../data';
import { MOCK_DEPT_IDS, MOCK_REFERENCE_DATETIME, MOCK_TOKEN_ISSUED_AT } from '../data';
import type { MockDataSource } from '../store';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import { getRequestToken, getSearchParams, readJsonBody } from '../utils/request';
import { pagination, resultError, resultSuccess } from '../utils/response';
import { withBackendFallback } from '../utils/with-backend-fallback';
import { buildDeptTree } from './projections';

function accountToUser(account: MockAccount) {
  const deptId = account.username === 'admin' ? MOCK_DEPT_IDS.platform : MOCK_DEPT_IDS.delivery;
  return {
    userId: account.userId,
    deptId,
    userName: account.username,
    nickName: account.displayName,
    email: `${account.username}@mock.local`,
    phonenumber: account.username === 'admin' ? '15888888888' : '15666666666',
    sex: account.username === 'admin' ? '1' : '0',
    avatar: account.avatar ?? null,
    status: account.status,
    delFlag: '0',
    loginIp: '127.0.0.1',
    loginDate: MOCK_REFERENCE_DATETIME,
    createBy: 'mock',
    createTime: MOCK_REFERENCE_DATETIME,
    updateBy: null,
    updateTime: null,
    remark: account.username === 'admin' ? '管理员' : '编辑员',
  } satisfies NonNullable<MockCurrentUserResponse['user']>;
}

async function findAccountByToken(dataSource: MockDataSource, token?: string) {
  if (!token) return undefined;
  const session = await dataSource.auth.findSessionByToken(token);
  if (!session) return undefined;
  return dataSource.auth.findAccountByUsername(session.username);
}

export function createUserHandlers(
  strategy: MockStrategy,
  dataSource: MockDataSource
): MockRuntimeHandler[] {
  return [
    http.get(createApiPath('/captchaImage'), ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              captchaEnabled: false,
              img: '',
              uuid: `mock-uuid-${MOCK_TOKEN_ISSUED_AT}`,
            })
          ),
        { strategy, tag: 'user:captcha' }
      )
    ),
    http.post(createApiPath('/login'), async ({ request }) => {
      const payload = (await readJsonBody<{ username?: string; password?: string }>(request)) ?? {};
      return withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const { username = '', password = '' } = payload;
          if (!username) {
            return HttpResponse.json(resultError('用户名不能为空', { code: 500 }));
          }
          if (!password) {
            return HttpResponse.json(resultError('密码不能为空', { code: 500 }));
          }

          const account = await dataSource.auth.findAccountByUsername(username);
          if (!account || account.password !== password || account.status !== '0') {
            return HttpResponse.json(resultError('用户名或密码错误', { code: 500 }));
          }

          const session = await dataSource.auth.createSession(username);
          return HttpResponse.json(
            {
              accessToken: session.token,
              tokenType: 'bearer',
              token: session.token,
            } satisfies MockLoginResponse,
            {
              status: 200,
              headers: {
                'Set-Cookie': `ruoyi_at=${encodeURIComponent(session.token)}; Path=/; SameSite=Lax`,
              },
            }
          );
        },
        { strategy, tag: 'user:login' }
      );
    }),
    http.get(createApiPath('/getInfo'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const token = getRequestToken(request);
          if (!token) {
            return HttpResponse.json(resultError('Token 不能为空', { code: 401 }), {
              status: 401,
            });
          }

          const account = await findAccountByToken(dataSource, token);
          if (!account) {
            return HttpResponse.json(resultError('登录信息已过期，请重新登录', { code: 401 }), {
              status: 401,
            });
          }

          return HttpResponse.json(
            {
              user: accountToUser(account),
              roles: account.roles,
              permissions: account.permissions,
              isDefaultModifyPwd: false,
              isPasswordExpired: false,
            } satisfies MockCurrentUserResponse,
            { status: 200 }
          );
        },
        { strategy, tag: 'user:getInfo' }
      )
    ),
    http.post(createApiPath('/auth/logout'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const token = getRequestToken(request);
          if (token) {
            await dataSource.auth.deleteSession(token);
          }
          return new HttpResponse(null, {
            status: 204,
            headers: { 'Set-Cookie': 'ruoyi_at=; Path=/; Max-Age=0; SameSite=Lax' },
          });
        },
        {
          strategy,
          tag: 'user:authLogout',
        }
      )
    ),
    http.post(createApiPath('/auth/csrf-token'), ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              csrfToken: 'mock-csrf-token',
              csrf_token: 'mock-csrf-token',
            })
          ),
        { strategy, tag: 'user:csrfToken' }
      )
    ),
    http.post(createApiPath('/auth/refresh'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const token = getRequestToken(request);
          const account = token
            ? await findAccountByToken(dataSource, token)
            : await dataSource.auth.findAccountByUsername('admin');
          if (!account) {
            return HttpResponse.json(resultError('登录信息已过期，请重新登录', { code: 401 }), {
              status: 401,
            });
          }
          const session = await dataSource.auth.createSession(account.username);
          return HttpResponse.json(
            resultSuccess({
              token: session.token,
              csrfToken: 'mock-csrf-refreshed',
              csrf_token: 'mock-csrf-refreshed',
            })
          );
        },
        { strategy, tag: 'user:refresh' }
      )
    ),
    http.post(createApiPath('/auth/ws-ticket'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          const payload = (await readJsonBody<{ session_id?: string }>(request)) ?? {};
          const sessionId = String(payload.session_id ?? '').trim();
          if (!sessionId) {
            return HttpResponse.json(resultError('会话不能为空', { code: 422 }), { status: 422 });
          }

          return HttpResponse.json(
            resultSuccess({
              wsTicket: `mock-ws-ticket-${sessionId}-${MOCK_TOKEN_ISSUED_AT}`,
              ws_ticket: `mock-ws-ticket-${sessionId}-${MOCK_TOKEN_ISSUED_AT}`,
              expiresIn: 30,
            })
          );
        },
        { strategy, tag: 'user:wsTicket' }
      )
    ),
    http.get(createApiPath('/system/user/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const searchParams = getSearchParams(request);
          const page = Number(searchParams.get('page') ?? 1);
          const size = Number(searchParams.get('pageSize') ?? 10);
          const accounts = ['admin', 'editor']
            .map((username) => dataSource.auth.findAccountByUsername(username))
            .map((promise) =>
              promise.then((account) => (account ? accountToUser(account) : undefined))
            );
          const users = (await Promise.all(accounts)).filter((user) => user !== undefined);
          const items = pagination(page, size, users);
          return HttpResponse.json(
            resultSuccess({
              items,
              total: users.length,
              page,
              pageSize: size,
            })
          );
        },
        { strategy, tag: 'user:list' }
      )
    ),
    http.get(createApiPath('/system/user/deptTree'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const departments = await dataSource.system.listDepartments();
          return HttpResponse.json(resultSuccess({ items: buildDeptTree(departments) }));
        },
        {
          strategy,
          tag: 'user:deptTree',
        }
      )
    ),
  ];
}
