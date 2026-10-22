import { mockRemark } from '../data/remark';
import { http, HttpResponse } from 'msw';

import type {
  ConfigDetailReadModel,
  DictTypeDetailReadModel,
  UserInfoModel,
} from '@/api/_generated/types.gen';

import { createApiPath } from '../constants';
import type { MockRuntimeHandler, MockStrategy } from '../types';
import type { MockDataSource } from '../store';
import { resultSuccess } from '../utils/response';
import { getSearchParams } from '../utils/request';
import { withBackendFallback } from '../utils/with-backend-fallback';
import { buildDeptTree, buildSystemRoutes, projectDictData } from './projections';
import type { MockDictData } from '../data';

const mockConfigs = [
  {
    configId: 1,
    configName: '系统名称',
    configKey: 'sys.index.skinName',
    configValue: 'skin-blue',
    configType: 'Y',
    createBy: 'mock',
    remark: mockRemark('主框架页默认皮肤', 'config1'),
    remarkText: '主框架页默认皮肤',
  },
  {
    configId: 2,
    configName: '验证码开关',
    configKey: 'sys.account.captchaEnabled',
    configValue: 'true',
    configType: 'Y',
    createBy: 'mock',
    remark: mockRemark('登录验证码开关', 'config2'),
    remarkText: '登录验证码开关',
  },
] satisfies ConfigDetailReadModel[];

function toPositiveNumber(value: string | null, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function page<T>(items: T[], request: Request) {
  const params = getSearchParams(request);
  const pageNo = toPositiveNumber(params.get('page'), 1);
  const pageSize = toPositiveNumber(params.get('pageSize') ?? params.get('page_size'), 10);
  const start = (pageNo - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page: pageNo,
    pageSize,
  };
}

function includesQuery(value: unknown, query: string | null): boolean {
  if (!query) return true;
  return String(value ?? '').includes(query);
}

function dictTypesFromData(dicts: MockDictData[]): DictTypeDetailReadModel[] {
  const byType = new Map<string, MockDictData[]>();
  dicts.forEach((dict) => {
    const siblings = byType.get(dict.dictType) ?? [];
    siblings.push(dict);
    byType.set(dict.dictType, siblings);
  });
  return Array.from(byType.entries()).map(([dictType, values], index) => ({
    dictId: index + 1,
    dictName: values[0]?.dictLabel.includes('正常') ? '系统状态' : '用户性别',
    dictType,
    status: values.every((value) => value.status === '0') ? '0' : '1',
    createBy: 'mock',
    remark: mockRemark('mock dict type', `dict${index}`),
    remarkText: 'mock dict type',
  }));
}

function roleUser(name: string, userId: number, roleId: number): UserInfoModel {
  return {
    userId,
    userName: name,
    nickName: name === 'admin' ? '若依' : '访客',
    status: '0',
    roleIds: String(roleId),
    remark: null,
    remarkText: '',
  };
}

function unsupportedSystemWrite(request: Request) {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;
  return HttpResponse.json(
    {
      type: 'about:blank',
      title: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED',
      status: 501,
      detail: `MOCK_SYSTEM_WRITE_NOT_SUPPORTED: ${request.method} ${path} 当前系统数据源只读，尚未实现状态写入`,
      instance: path,
      errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED',
    },
    { status: 501, headers: { 'Content-Type': 'application/problem+json' } }
  );
}

export function createSystemHandlers(
  strategy: MockStrategy,
  dataSource: MockDataSource
): MockRuntimeHandler[] {
  return [
    http.get(createApiPath('/getRouters'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const menus = await dataSource.system.listMenus();
          return HttpResponse.json(resultSuccess({ items: buildSystemRoutes(menus) }));
        },
        {
          strategy,
          tag: 'system:getRouters',
        }
      )
    ),
    http.get(createApiPath('/system/dict/data/type/:dictType'), ({ request, params }) => {
      const dictType = String(params.dictType ?? '');
      return withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const dicts = await dataSource.system.listDictData(dictType);
          return HttpResponse.json(
            resultSuccess({
              items: dicts.map(projectDictData),
            })
          );
        },
        { strategy, tag: 'system:dict:type' }
      );
    }),
    http.get(createApiPath('/system/dept/treeselect'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const departments = await dataSource.system.listDepartments();
          return HttpResponse.json(resultSuccess({ items: buildDeptTree(departments) }));
        },
        {
          strategy,
          tag: 'system:deptTree',
        }
      )
    ),
    http.get(createApiPath('/system/role/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const params = getSearchParams(request);
          const roleName = params.get('roleName');
          const roleKey = params.get('roleKey');
          const roles = (await dataSource.system.listRoles()).filter(
            (role) => includesQuery(role.roleName, roleName) && includesQuery(role.roleKey, roleKey)
          );
          return HttpResponse.json(resultSuccess(page(roles, request)));
        },
        { strategy, tag: 'system:roles' }
      )
    ),
    http.get(createApiPath('/system/role/authUser/allocatedList'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          const params = getSearchParams(request);
          const roleId = toPositiveNumber(params.get('roleId'), 1);
          return HttpResponse.json(resultSuccess(page([roleUser('admin', 1, roleId)], request)));
        },
        { strategy, tag: 'system:roleAllocatedUsers' }
      )
    ),
    http.get(createApiPath('/system/role/authUser/unallocatedList'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          const params = getSearchParams(request);
          const roleId = toPositiveNumber(params.get('roleId'), 1);
          return HttpResponse.json(resultSuccess(page([roleUser('guest', 2, roleId)], request)));
        },
        { strategy, tag: 'system:roleUnallocatedUsers' }
      )
    ),
    http.get(createApiPath('/system/role/deptTree/:roleId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const departments = await dataSource.system.listDepartments();
          return HttpResponse.json(
            resultSuccess({
              roleId: Number(params.roleId),
              depts: buildDeptTree(departments),
              checkedKeys: [departments[0]?.deptId].filter(Boolean),
            })
          );
        },
        { strategy, tag: 'system:roleDeptTree' }
      )
    ),
    http.get(createApiPath('/system/role/:roleId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const roleId = Number(params.roleId);
          const role = (await dataSource.system.listRoles()).find((item) => item.roleId === roleId);
          return role
            ? HttpResponse.json(resultSuccess(role))
            : HttpResponse.json({ detail: '角色不存在', status: 404 }, { status: 404 });
        },
        { strategy, tag: 'system:roleDetail' }
      )
    ),
    http.post(createApiPath('/system/role'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleCreate',
      })
    ),
    http.put(createApiPath('/system/role/dataScope'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleDataScope',
      })
    ),
    http.put(createApiPath('/system/role/changeStatus'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleChangeStatus',
      })
    ),
    http.put(createApiPath('/system/role/authUser/cancel'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleAuthCancel',
      })
    ),
    http.put(createApiPath('/system/role/authUser/cancelAll'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleAuthCancelAll',
      })
    ),
    http.put(createApiPath('/system/role/authUser/selectAll'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleAuthSelectAll',
      })
    ),
    http.put(createApiPath('/system/role'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleUpdate',
      })
    ),
    http.delete(createApiPath('/system/role/:roleIds'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:roleDelete',
      })
    ),
    http.get(createApiPath('/system/menu/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const params = getSearchParams(request);
          const menuName = params.get('menuName');
          const menus = (await dataSource.system.listMenus()).filter((menu) =>
            includesQuery(menu.menuName, menuName)
          );
          return HttpResponse.json(resultSuccess({ items: menus }));
        },
        { strategy, tag: 'system:menus' }
      )
    ),
    http.get(createApiPath('/system/menu/treeselect'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const menus = await dataSource.system.listMenus();
          return HttpResponse.json(
            resultSuccess({
              items: menus
                .filter((menu) => menu.parentId === 0)
                .map((menu) => ({ id: menu.menuId, label: menu.menuName })),
            })
          );
        },
        { strategy, tag: 'system:menuTree' }
      )
    ),
    http.get(createApiPath('/system/menu/roleMenuTreeselect/:roleId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const menus = await dataSource.system.listMenus();
          return HttpResponse.json(
            resultSuccess({
              roleId: Number(params.roleId),
              menus: menus.map((menu) => ({
                id: menu.menuId,
                label: menu.menuName,
              })),
              checkedKeys: menus
                .filter((menu) => menu.roles?.includes('admin'))
                .map((menu) => menu.menuId),
            })
          );
        },
        { strategy, tag: 'system:roleMenuTree' }
      )
    ),
    http.get(createApiPath('/system/menu/:menuId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const menuId = Number(params.menuId);
          const menu = (await dataSource.system.listMenus()).find((item) => item.menuId === menuId);
          return menu
            ? HttpResponse.json(resultSuccess(menu))
            : HttpResponse.json({ detail: '菜单不存在', status: 404 }, { status: 404 });
        },
        { strategy, tag: 'system:menuDetail' }
      )
    ),
    http.post(createApiPath('/system/menu'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:menuCreate',
      })
    ),
    http.put(createApiPath('/system/menu'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:menuUpdate',
      })
    ),
    http.delete(createApiPath('/system/menu/:menuId'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:menuDelete',
      })
    ),
    http.get(createApiPath('/system/dept/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const departments = await dataSource.system.listDepartments();
          return HttpResponse.json(resultSuccess({ items: departments }));
        },
        { strategy, tag: 'system:departments' }
      )
    ),
    http.get(createApiPath('/system/config/list'), ({ request }) =>
      withBackendFallback(
        request,
        () => {
          const params = getSearchParams(request);
          const filtered = mockConfigs.filter(
            (config) =>
              includesQuery(config.configName, params.get('configName')) &&
              includesQuery(config.configKey, params.get('configKey'))
          );
          return HttpResponse.json(resultSuccess(page(filtered, request)));
        },
        { strategy, tag: 'system:configList' }
      )
    ),
    http.get(createApiPath('/system/config/configKey/:configKey'), ({ request, params }) =>
      withBackendFallback(
        request,
        () => {
          const config = mockConfigs.find((item) => item.configKey === String(params.configKey));
          return HttpResponse.json(
            resultSuccess({
              configKey: String(params.configKey),
              configValue: config?.configValue ?? '',
            })
          );
        },
        { strategy, tag: 'system:configKey' }
      )
    ),
    http.get(createApiPath('/system/config/:configId'), ({ request, params }) =>
      withBackendFallback(
        request,
        () => {
          const configId = Number(params.configId);
          const config = mockConfigs.find((item) => item.configId === configId) ?? mockConfigs[0];
          return HttpResponse.json(resultSuccess(config));
        },
        { strategy, tag: 'system:configDetail' }
      )
    ),
    http.post(createApiPath('/system/config'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:configCreate',
      })
    ),
    http.put(createApiPath('/system/config'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:configUpdate',
      })
    ),
    http.delete(createApiPath('/system/config/refreshCache'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:configRefreshCache',
      })
    ),
    http.delete(createApiPath('/system/config/:configIds'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:configDelete',
      })
    ),
    http.get(createApiPath('/system/dict/data/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const params = getSearchParams(request);
          const dicts = (await dataSource.system.listDictData(params.get('dictType') ?? undefined))
            .filter((dict) => includesQuery(dict.dictLabel, params.get('dictLabel')))
            .map(projectDictData);
          return HttpResponse.json(resultSuccess(page(dicts, request)));
        },
        { strategy, tag: 'system:dictDataList' }
      )
    ),
    http.get(createApiPath('/system/dict/data/:dictCode'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const dictCode = Number(params.dictCode);
          const dict = (await dataSource.system.listDictData())
            .map(projectDictData)
            .find((item) => item.dictCode === dictCode);
          return HttpResponse.json(resultSuccess(dict));
        },
        { strategy, tag: 'system:dictDataDetail' }
      )
    ),
    http.post(createApiPath('/system/dict/data'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictDataCreate',
      })
    ),
    http.put(createApiPath('/system/dict/data'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictDataUpdate',
      })
    ),
    http.delete(createApiPath('/system/dict/data/:dictCodes'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictDataDelete',
      })
    ),
    http.get(createApiPath('/system/dict/type/list'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const params = getSearchParams(request);
          const dictTypes = dictTypesFromData(await dataSource.system.listDictData()).filter(
            (dictType) =>
              includesQuery(dictType.dictName, params.get('dictName')) &&
              includesQuery(dictType.dictType, params.get('dictType'))
          );
          return HttpResponse.json(resultSuccess(page(dictTypes, request)));
        },
        { strategy, tag: 'system:dictTypeList' }
      )
    ),
    http.get(createApiPath('/system/dict/type/optionselect'), ({ request }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          return HttpResponse.json(
            resultSuccess({ items: dictTypesFromData(await dataSource.system.listDictData()) })
          );
        },
        { strategy, tag: 'system:dictTypeOptions' }
      )
    ),
    http.get(createApiPath('/system/dict/type/:dictId'), ({ request, params }) =>
      withBackendFallback(
        request,
        async () => {
          await dataSource.init();
          const dictId = Number(params.dictId);
          const dictType = dictTypesFromData(await dataSource.system.listDictData()).find(
            (item) => item.dictId === dictId
          );
          return HttpResponse.json(resultSuccess(dictType));
        },
        { strategy, tag: 'system:dictTypeDetail' }
      )
    ),
    http.post(createApiPath('/system/dict/type'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictTypeCreate',
      })
    ),
    http.put(createApiPath('/system/dict/type'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictTypeUpdate',
      })
    ),
    http.delete(createApiPath('/system/dict/type/refreshCache'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictTypeRefreshCache',
      })
    ),
    http.delete(createApiPath('/system/dict/type/:dictIds'), ({ request }) =>
      withBackendFallback(request, () => unsupportedSystemWrite(request), {
        strategy,
        tag: 'system:dictTypeDelete',
      })
    ),
  ];
}
