import { http, HttpResponse } from 'msw';

import type { MockRuntimeHandler, MockStrategy } from '../types';
import { createApiPath } from '../constants';
import { buildAccountCollections, createDeptTree, createUserList } from '../factories';
import { pagination, resultError, resultSuccess } from '../utils/response';
import { getRequestToken, getSearchParams, readJsonBody } from '../utils/request';
import { withBackendFallback } from '../utils/with-backend-fallback';

const accountCollections = buildAccountCollections([
  {
    username: 'admin',
    password: 'admin123',
    roles: ['admin'],
    permissions: ['*:*:*'],
    name: '若依',
    introduction: 'I am a super administrator',
    userOverrides: {
      userId: 1,
      deptId: 103,
      userName: 'admin',
      nickName: '若依',
      status: '0',
      sex: '1',
      phonenumber: '15888888888',
      remark: '管理员',
    },
  },
  {
    username: 'editor',
    password: 'editor123',
    roles: ['editor'],
    permissions: ['system:user:query', 'system:user:add', 'system:user:edit'],
    name: '编辑员',
    introduction: 'I am an editor',
    userOverrides: {
      userId: 2,
      deptId: 105,
      userName: 'editor',
      nickName: '编辑员',
      status: '0',
      sex: '0',
      phonenumber: '15666666666',
      remark: '编辑员',
    },
  },
]);

const mockUsers = createUserList(40, (index) => ({
  userId: index + 10,
  userName: `user${index + 1}`,
  nickName: `Mock用户${index + 1}`,
  status: index % 6 === 0 ? '1' : '0',
}));

export function createUserHandlers(strategy: MockStrategy): MockRuntimeHandler[] {
  return [
    http.get(createApiPath('/captchaImage'), ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              captchaEnabled: false,
              img: '',
              uuid: `mock-uuid-${Date.now()}`,
            })
          ),
        { strategy, tag: 'user:captcha' }
      )
    ),
    http.post(createApiPath('/login'), async ({ request }) => {
      const payload = (await readJsonBody<{ username?: string; password?: string }>(request)) ?? {};
      return withBackendFallback(
        request,
        () => {
          const { username = '', password = '' } = payload;
          if (!username) {
            return HttpResponse.json(resultError('用户名不能为空', { code: 500 }));
          }
          if (!password) {
            return HttpResponse.json(resultError('密码不能为空', { code: 500 }));
          }

          const account = accountCollections.credentials[username];
          if (!account || account.password !== password) {
            return HttpResponse.json(resultError('用户名或密码错误', { code: 500 }));
          }

          return HttpResponse.json(
            {
              token: account.token,
            },
            { status: 200 }
          );
        },
        { strategy, tag: 'user:login' }
      );
    }),
    http.get(createApiPath('/getInfo'), ({ request }) =>
      withBackendFallback(
        request,
        () => {
          const token = getRequestToken(request);
          if (!token) {
            return HttpResponse.json(resultError('Token 不能为空', { code: 401 }), {
              status: 401,
            });
          }

          const info = accountCollections.accountsByToken[token];
          if (!info) {
            return HttpResponse.json(resultError('登录信息已过期，请重新登录', { code: 401 }), {
              status: 401,
            });
          }

          return HttpResponse.json(
            {
              user: info.user,
              roles: info.roles,
              permissions: info.permissions,
              isDefaultModifyPwd: false,
              isPasswordExpired: false,
            },
            { status: 200 }
          );
        },
        { strategy, tag: 'user:getInfo' }
      )
    ),
    http.post(createApiPath('/logout'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json(resultSuccess(null)), {
        strategy,
        tag: 'user:logout',
      })
    ),
    http.post(createApiPath('/auth/logout'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json(resultSuccess(null)), {
        strategy,
        tag: 'user:authLogout',
      })
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
        () =>
          HttpResponse.json(
            resultSuccess({
              token: 'mock-token-refreshed',
              csrfToken: 'mock-csrf-refreshed',
              csrf_token: 'mock-csrf-refreshed',
            })
          ),
        { strategy, tag: 'user:refresh' }
      )
    ),
    http.get(createApiPath('/system/user/list'), ({ request }) =>
      withBackendFallback(
        request,
        () => {
          const searchParams = getSearchParams(request);
          const page = Number(searchParams.get('page') ?? 1);
          const size = Number(searchParams.get('pageSize') ?? 10);
          const items = pagination(page, size, mockUsers);
          return HttpResponse.json(
            resultSuccess({
              items,
              total: mockUsers.length,
              page,
              pageSize: size,
            })
          );
        },
        { strategy, tag: 'user:list' }
      )
    ),
    http.get(createApiPath('/system/user/deptTree'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json(resultSuccess(createDeptTree())), {
        strategy,
        tag: 'user:deptTree',
      })
    ),
  ];
}
