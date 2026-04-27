import { http, HttpResponse, type HttpHandler, type JsonBodyType } from 'msw';

const apiPath = (path: string) => `*/api${path.startsWith('/') ? path : `/${path}`}`;

const page = <T>(items: T[], pageNo = 1, pageSize = 10) => ({
  items,
  total: items.length,
  page: pageNo,
  pageSize,
});

const ok = <T>(data: T, status = 200) => HttpResponse.json(data as JsonBodyType, { status });

const problem = (status: number, detail: string, errorCode: string | number = status) =>
  HttpResponse.json(
    {
      type: 'about:blank',
      title: detail,
      status,
      detail,
      instance: '',
      errorCode,
    },
    { status }
  );

async function readBody(request: Request): Promise<Record<string, unknown>> {
  const contentType = request.headers.get('content-type')?.toLowerCase() ?? '';
  if (contentType.includes('application/json')) {
    return (await request.json()) as Record<string, unknown>;
  }
  if (
    contentType.includes('application/x-www-form-urlencoded') ||
    contentType.includes('multipart/form-data')
  ) {
    return Object.fromEntries((await request.formData()).entries());
  }
  const text = await request.text();
  return text ? Object.fromEntries(new URLSearchParams(text).entries()) : {};
}

export function createApiContractHandlers(): HttpHandler[] {
  return [
    http.post(apiPath('/login'), async ({ request }) => {
      const payload = await readBody(request);
      return ok({
        token: `jwt-token-${String(payload.username ?? 'anonymous')}`,
        csrfToken: 'csrf-token-from-login',
        payload,
      });
    }),
    http.post(apiPath('/register'), async ({ request }) =>
      ok({ userId: 10, payload: await readBody(request) })
    ),
    http.get(apiPath('/getInfo'), () =>
      ok({
        user: {
          userId: 1,
          userName: 'admin',
          nickName: '管理员',
          avatar: '',
        },
        roles: ['admin'],
        permissions: ['*:*:*'],
      })
    ),
    http.post(apiPath('/auth/logout'), () => ok(null)),
    http.post(apiPath('/auth/csrf-token'), () =>
      ok({
        csrfToken: 'csrf-token-from-refresh',
        csrf_token: 'csrf-token-from-refresh',
      })
    ),
    http.post(apiPath('/auth/refresh'), () =>
      ok({
        token: 'jwt-token-restored',
        csrfToken: 'csrf-token-restored',
        csrf_token: 'csrf-token-restored',
      })
    ),
    http.get(apiPath('/captchaImage'), () =>
      ok({
        captchaEnabled: false,
        img: '',
        uuid: 'captcha-uuid-1',
      })
    ),

    http.get(apiPath('/project/list'), ({ request }) => {
      const params = new URL(request.url).searchParams;
      return ok(
        page(
          [
            {
              projectId: 1,
              projectName: params.get('projectName') || '星载总线演示工程',
              projectCode: 'PRJ-001',
              projectDesc: 'MSW contract project',
            },
          ],
          Number(params.get('page') ?? 1),
          Number(params.get('pageSize') ?? 10)
        )
      );
    }),
    http.get(apiPath('/project/export/:projectId'), () =>
      new Response(new Blob(['demo project export'], { type: 'application/json' }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      })
    ),
    http.get(apiPath('/project/:projectId/topology'), ({ params }) =>
      ok({
        projectId: Number(params.projectId),
        topologyData: {
          nodes: [{ id: 'node-1', label: '控制器' }],
          edges: [],
        },
      })
    ),
    http.put(apiPath('/project/:projectId/topology'), async ({ request, params }) =>
      ok({
        projectId: Number(params.projectId),
        topologyData: await readBody(request),
      })
    ),
    http.get(apiPath('/project/:projectId'), ({ params }) =>
      ok({
        projectId: Number(params.projectId),
        projectName: '星载总线演示工程',
        projectCode: 'PRJ-001',
      })
    ),
    http.post(apiPath('/project'), async ({ request }) =>
      ok({
        projectId: 2,
        ...(await readBody(request)),
      })
    ),
    http.put(apiPath('/project'), async ({ request }) =>
      ok({
        ...(await readBody(request)),
      })
    ),
    http.delete(apiPath('/project/:projectIds'), () => ok(null)),
    http.post(apiPath('/project/import'), () => ok({ projectId: 3 })),
    http.post(apiPath('/project/export/batch'), () =>
      new Response(new Blob(['demo project batch export'], { type: 'application/zip' }), {
        status: 200,
        headers: {
          'Content-Type': 'application/zip',
        },
      })
    ),

    http.get(apiPath('/system/menu/list'), () =>
      ok([{ menuId: 1, menuName: '系统管理', menuType: 'M', status: '0' }])
    ),
    http.get(apiPath('/system/menu/treeselect'), () =>
      ok([{ id: 1, label: '系统管理', children: [{ id: 2, label: '用户管理' }] }])
    ),
    http.get(apiPath('/system/menu/roleMenuTreeselect/:roleId'), ({ params }) =>
      ok({
        roleId: Number(params.roleId),
        menus: [{ id: 1, label: '系统管理' }],
        checkedKeys: [1, 2],
      })
    ),
    http.get(apiPath('/system/menu/:menuId'), ({ params }) =>
      ok({ menuId: Number(params.menuId), menuName: '系统管理', menuType: 'M' })
    ),
    http.post(apiPath('/system/menu'), async ({ request }) =>
      ok({ menuId: 9, ...(await readBody(request)) })
    ),
    http.put(apiPath('/system/menu'), async ({ request }) => ok(await readBody(request))),
    http.delete(apiPath('/system/menu/:menuId'), () => ok(null)),

    http.get(apiPath('/system/config/list'), ({ request }) => {
      const params = new URL(request.url).searchParams;
      return ok(
        page(
          [
            {
              configId: 1,
              configName: params.get('configName') || '系统名称',
              configKey: params.get('configKey') || 'sys.index.skinName',
              configValue: 'skin-blue',
            },
          ],
          Number(params.get('page') ?? 1),
          Number(params.get('pageSize') ?? 10)
        )
      );
    }),
    http.get(apiPath('/system/config/configKey/:configKey'), ({ params }) =>
      ok(String(params.configKey) === 'sys.account.captchaEnabled' ? 'true' : 'skin-blue')
    ),
    http.get(apiPath('/system/config/:configId'), ({ params }) =>
      ok({
        configId: Number(params.configId),
        configName: '主框架页-默认皮肤样式名称',
        configKey: 'sys.index.skinName',
        configValue: 'skin-blue',
      })
    ),
    http.post(apiPath('/system/config'), async ({ request }) =>
      ok({ configId: 1, ...(await readBody(request)) })
    ),
    http.put(apiPath('/system/config'), async ({ request }) => ok(await readBody(request))),
    http.delete(apiPath('/system/config/:configIds'), () => ok(null)),
    http.delete(apiPath('/system/config/refreshCache'), () => ok(null)),

    http.get(apiPath('/system/dict/data/list'), ({ request }) => {
      const params = new URL(request.url).searchParams;
      return ok(
        page(
          [
            {
              dictCode: 1,
              dictLabel: params.get('dictLabel') || '男',
              dictValue: '0',
              dictType: params.get('dictType') || 'sys_user_sex',
            },
          ],
          Number(params.get('page') ?? 1),
          Number(params.get('pageSize') ?? 10)
        )
      );
    }),
    http.get(apiPath('/system/dict/data/type/:dictType'), ({ params }) =>
      ok([
        { dictLabel: '男', dictValue: '0', dictType: String(params.dictType) },
        { dictLabel: '女', dictValue: '1', dictType: String(params.dictType) },
      ])
    ),
    http.get(apiPath('/system/dict/data/:dictCode'), ({ params }) =>
      ok({ dictCode: Number(params.dictCode), dictLabel: '男', dictValue: '0' })
    ),
    http.post(apiPath('/system/dict/data'), async ({ request }) =>
      ok({ dictCode: 1, ...(await readBody(request)) })
    ),
    http.put(apiPath('/system/dict/data'), async ({ request }) => ok(await readBody(request))),
    http.delete(apiPath('/system/dict/data/:dictCodes'), () => ok(null)),

    http.get(apiPath('/system/dict/type/list'), ({ request }) => {
      const params = new URL(request.url).searchParams;
      return ok(
        page(
          [
            {
              dictId: 1,
              dictName: params.get('dictName') || '用户性别',
              dictType: params.get('dictType') || 'sys_user_sex',
            },
          ],
          Number(params.get('page') ?? 1),
          Number(params.get('pageSize') ?? 10)
        )
      );
    }),
    http.get(apiPath('/system/dict/type/optionselect'), () =>
      ok([{ dictId: 1, dictName: '用户性别', dictType: 'sys_user_sex' }])
    ),
    http.get(apiPath('/system/dict/type/:dictId'), ({ params }) =>
      ok({ dictId: Number(params.dictId), dictName: '用户性别', dictType: 'sys_user_sex' })
    ),
    http.post(apiPath('/system/dict/type'), async ({ request }) =>
      ok({ dictId: 1, ...(await readBody(request)) })
    ),
    http.put(apiPath('/system/dict/type'), async ({ request }) => ok(await readBody(request))),
    http.delete(apiPath('/system/dict/type/:dictIds'), () => ok(null)),
    http.delete(apiPath('/system/dict/type/refreshCache'), () => ok(null)),

    http.get(apiPath('/system/role/list'), ({ request }) => {
      const params = new URL(request.url).searchParams;
      return ok(
        page(
          [
            {
              roleId: 1,
              roleName: params.get('roleName') || '超级管理员',
              roleKey: 'admin',
            },
          ],
          Number(params.get('page') ?? 1),
          Number(params.get('pageSize') ?? 10)
        )
      );
    }),
    http.get(apiPath('/system/role/authUser/allocatedList'), () =>
      ok(page([{ userId: 1, userName: 'admin' }]))
    ),
    http.get(apiPath('/system/role/authUser/unallocatedList'), () =>
      ok(page([{ userId: 2, userName: 'guest' }]))
    ),
    http.get(apiPath('/system/role/deptTree/:roleId'), ({ params }) =>
      ok({
        roleId: Number(params.roleId),
        depts: [{ id: 100, label: '研发部' }],
        checkedKeys: [100],
      })
    ),
    http.get(apiPath('/system/role/:roleId'), ({ params }) =>
      ok({ roleId: Number(params.roleId), roleName: '超级管理员', roleKey: 'admin' })
    ),
    http.post(apiPath('/system/role'), async ({ request }) =>
      ok({ roleId: 1, ...(await readBody(request)) })
    ),
    http.put(apiPath('/system/role/dataScope'), async ({ request }) => ok(await readBody(request))),
    http.put(apiPath('/system/role/changeStatus'), async ({ request }) =>
      ok(await readBody(request))
    ),
    http.put(apiPath('/system/role/authUser/cancel'), async ({ request }) =>
      ok(await readBody(request))
    ),
    http.put(apiPath('/system/role/authUser/cancelAll'), () => ok(null)),
    http.put(apiPath('/system/role/authUser/selectAll'), () => ok(null)),
    http.put(apiPath('/system/role'), async ({ request }) => ok(await readBody(request))),
    http.delete(apiPath('/system/role/:roleIds'), () => ok(null)),

    http.post(apiPath('/simulation/start'), async ({ request }) =>
      ok({
        code: 200,
        data: {
          simulation_id: 1,
          status: 'running',
          request: await readBody(request),
        },
      })
    ),
    http.post(apiPath('/simulation/sessions/:sessionId/pause'), () =>
      ok({ code: 200, data: { status: 'paused' } })
    ),
    http.post(apiPath('/simulation/sessions/:sessionId/resume'), () =>
      ok({ code: 200, data: { status: 'running' } })
    ),
    http.post(apiPath('/simulation/sessions/:sessionId/stop'), () =>
      ok({ code: 200, data: { status: 'stopped', duration: 100.5, total_messages: 1000 } })
    ),
    http.post(apiPath('/simulation/sessions/:sessionId/speed'), async ({ request }) =>
      ok({ code: 200, data: await readBody(request) })
    ),
    http.get(apiPath('/simulation/sessions/:sessionId/status'), () =>
      ok({ code: 200, data: { status: 'running', current_time: 50.5, speed: 1.0 } })
    ),
    http.get(apiPath('/simulation/:sessionId/statistics'), () =>
      ok({
        code: 200,
        data: {
          total_messages: 10000,
          messages_by_protocol: { '1553B': 6000, CAN: 4000 },
        },
      })
    ),
    http.post(apiPath('/simulation/:sessionId/event'), async ({ request }) =>
      ok({ code: 200, data: { success: true, event: await readBody(request) } })
    ),
    http.get(apiPath('/simulation/sessions/:sessionId/messages'), () =>
      ok({ code: 200, data: [{ id: 'msg-1', protocol_type: '1553B' }] })
    ),
    http.get(apiPath('/simulation/sessions/:sessionId/alarms'), () =>
      ok({ code: 200, data: [{ id: 'alarm-1', level: 'warning' }] })
    ),
    http.get(apiPath('/simulation/:sessionId/export'), () =>
      new Response(new Blob(['simulation export'], { type: 'text/csv' }), {
        status: 200,
        headers: {
          'Content-Type': 'text/csv',
        },
      })
    ),
  ];
}

export function createStatusHandler(method: 'get' | 'post' | 'put' | 'delete', path: string, status: number): HttpHandler {
  const resolver = () => problem(status, status === 429 ? '请求过于频繁' : '服务暂不可用');
  const matcher = apiPath(path);
  if (method === 'post') return http.post(matcher, resolver);
  if (method === 'put') return http.put(matcher, resolver);
  if (method === 'delete') return http.delete(matcher, resolver);
  return http.get(matcher, resolver);
}

export function createNetworkErrorHandler(method: 'get' | 'post' | 'put' | 'delete', path: string): HttpHandler {
  const resolver = () => HttpResponse.error();
  const matcher = apiPath(path);
  if (method === 'post') return http.post(matcher, resolver);
  if (method === 'put') return http.put(matcher, resolver);
  if (method === 'delete') return http.delete(matcher, resolver);
  return http.get(matcher, resolver);
}
