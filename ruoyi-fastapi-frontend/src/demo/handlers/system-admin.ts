import { http, type HttpHandler } from 'msw';

import { getDemoOfflineDb } from '@/demo/db';
import { AuthRepository, SystemAdminRepository } from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { DemoAuthService, DemoSystemAdminService } from '@/demo/services';

import {
  createDemoApiPath,
  demoErrorResponse,
  demoFileResponse,
  demoJsonResponse,
  getDemoRequestToken,
  readDemoRequestBody,
} from './utils';

export interface CreateDemoSystemAdminHandlersOptions {
  config: RuntimeConfig;
  logger: DemoRuntimeLogger;
}

function createAuthService(): DemoAuthService {
  return new DemoAuthService(new AuthRepository(getDemoOfflineDb()));
}

function createSystemAdminService(): DemoSystemAdminService {
  const db = getDemoOfflineDb();
  return new DemoSystemAdminService(new SystemAdminRepository(db), db);
}

async function ensureCurrentUser(request: Request) {
  return createAuthService().getInfo(getDemoRequestToken(request));
}

async function ensureCurrentOperator(
  request: Request
): Promise<{ userId: number; userName: string }> {
  const currentUser = await ensureCurrentUser(request);
  const user = currentUser.user as Record<string, unknown>;
  return {
    userId: Number(user.userId ?? 0),
    userName: String(user.userName ?? user.nickName ?? 'demo-offline'),
  };
}

function readSearchParam(
  request: Request,
  name: string,
  fallbackName?: string
): string | undefined {
  const searchParams = new URL(request.url).searchParams;
  return (
    searchParams.get(name) ?? (fallbackName ? searchParams.get(fallbackName) : null) ?? undefined
  );
}

function toBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
}

export function createDemoSystemAdminHandlers({
  config,
  logger,
}: CreateDemoSystemAdminHandlersOptions): HttpHandler[] {
  const path = (value: string) => createDemoApiPath(config, value);

  return [
    http.get(path('/system/user/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listUsers({
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          userName: readSearchParam(request, 'userName'),
          phonenumber: readSearchParam(request, 'phonenumber'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
          deptId: readSearchParam(request, 'deptId'),
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(config, 'system-admin:user:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:list');
      }
    }),
    http.get(path('/system/user/:userId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const userId = Number(params.userId);
        const detail =
          Number.isFinite(userId) && userId > 0
            ? await createSystemAdminService().getUserDetail(userId)
            : await createSystemAdminService().getUserDetail();

        return demoJsonResponse(config, 'system-admin:user:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: detail,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:get');
      }
    }),
    http.get(path('/system/user/'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const detail = await createSystemAdminService().getUserDetail();

        return demoJsonResponse(config, 'system-admin:user:get-empty', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: detail,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:get-empty');
      }
    }),
    http.post(path('/system/user'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createUser(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:user:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:create');
      }
    }),
    http.put(path('/system/user'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateUser(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:user:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:update');
      }
    }),
    http.delete(path('/system/user/:userIds'), async ({ request, params }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        await createSystemAdminService().deleteUsers(
          String(params.userIds ?? '').split(','),
          operator.userId
        );

        return demoJsonResponse(config, 'system-admin:user:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:delete');
      }
    }),
    http.put(path('/system/user/changeStatus'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{ userId?: string | number; status?: '0' | '1' }>(
          request
        );
        await createSystemAdminService().changeUserStatus(
          body.userId ?? '',
          body.status ?? '0',
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:user:change-status', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:change-status');
      }
    }),
    http.put(path('/system/user/resetPwd'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{ userId?: string | number; password?: string }>(
          request
        );
        await createSystemAdminService().resetUserPassword(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:user:reset-pwd', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:reset-pwd');
      }
    }),
    http.get(path('/system/user/authRole/:userId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getUserAuthRole(String(params.userId ?? ''));

        return demoJsonResponse(config, 'system-admin:user:auth-role', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:auth-role');
      }
    }),
    http.put(path('/system/user/authRole'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const url = new URL(request.url);
        await createSystemAdminService().updateUserAuthRole(
          {
            userId: url.searchParams.get('userId') ?? '',
            roleIds: url.searchParams.get('roleIds') ?? '',
          },
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:user:update-auth-role', {
          code: 200,
          msg: '分配成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:update-auth-role');
      }
    }),
    http.post(path('/system/user/export'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const file = await createSystemAdminService().exportUsers(body);
        return demoFileResponse(config, 'system-admin:user:export', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:export');
      }
    }),
    http.post(path('/system/user/importTemplate'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const file = createSystemAdminService().getUserImportTemplate();
        return demoFileResponse(config, 'system-admin:user:import-template', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:import-template');
      }
    }),
    http.post(path('/system/user/importData'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const url = new URL(request.url);
        const updateSupport = url.searchParams.get('updateSupport') === '1';
        let fileName = '未提供文件';

        try {
          const formData = await request.clone().formData();
          const upload = formData.get('file');
          if (upload instanceof File && upload.name) {
            fileName = upload.name;
          }
        } catch {
          // ignore
        }

        return demoJsonResponse(config, 'system-admin:user:import-data', {
          code: 200,
          msg: `demo-offline 已接收导入文件：${fileName}。为保证离线模式稳定性，当前版本不解析 Excel 内容，请使用“新增用户”完成数据演示。updateSupport=${updateSupport ? '1' : '0'}`,
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:import-data');
      }
    }),
    http.get(path('/system/user/profile'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const data = await createSystemAdminService().getUserProfile(operator.userId);

        return demoJsonResponse(config, 'system-admin:user:profile', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:profile');
      }
    }),
    http.put(path('/system/user/profile'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateUserProfile(
          operator.userId,
          body,
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:user:update-profile', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:update-profile');
      }
    }),
    http.put(path('/system/user/profile/updatePwd'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateProfilePassword(
          operator.userId,
          body,
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:user:update-profile-pwd', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:update-profile-pwd');
      }
    }),
    http.post(path('/system/user/profile/avatar'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const formData = await request.clone().formData();
        const file = formData.get('avatarfile');
        let avatar = `data:image/svg+xml;base64,${btoa(
          `<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect width="120" height="120" rx="24" fill="#0f766e"/><text x="60" y="68" font-size="42" text-anchor="middle" fill="#fff">${operator.userName.slice(0, 1).toUpperCase()}</text></svg>`
        )}`;

        if (file instanceof File) {
          const contentType = file.type || 'image/png';
          avatar = `data:${contentType};base64,${toBase64(await file.arrayBuffer())}`;
        }

        const imgUrl = await createSystemAdminService().updateUserAvatar(
          operator.userId,
          avatar,
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:user:update-avatar', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: {
            imgUrl,
          },
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:user:update-avatar');
      }
    }),

    http.get(path('/system/role/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listRoles({
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          roleName: readSearchParam(request, 'roleName'),
          roleKey: readSearchParam(request, 'roleKey'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(config, 'system-admin:role:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:list');
      }
    }),
    http.get(path('/system/role/:roleId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getRoleDetail(String(params.roleId ?? ''));

        return demoJsonResponse(config, 'system-admin:role:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:get');
      }
    }),
    http.post(path('/system/role'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createRole(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:role:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:create');
      }
    }),
    http.put(path('/system/role'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateRole(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:role:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:update');
      }
    }),
    http.put(path('/system/role/dataScope'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateRoleDataScope(body);

        return demoJsonResponse(config, 'system-admin:role:data-scope', {
          code: 200,
          msg: '分配成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:data-scope');
      }
    }),
    http.put(path('/system/role/changeStatus'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody<{ roleId?: string | number; status?: '0' | '1' }>(
          request
        );
        await createSystemAdminService().changeRoleStatus(
          body.roleId ?? '',
          body.status ?? '0',
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:role:change-status', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:change-status');
      }
    }),
    http.delete(path('/system/role/:roleIds'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().deleteRoles(String(params.roleIds ?? '').split(','));

        return demoJsonResponse(config, 'system-admin:role:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:delete');
      }
    }),
    http.get(path('/system/role/authUser/allocatedList'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listAllocatedUsers({
          roleId: readSearchParam(request, 'roleId'),
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          userName: readSearchParam(request, 'userName'),
          phonenumber: readSearchParam(request, 'phonenumber'),
        } as Record<string, unknown>);

        return demoJsonResponse(config, 'system-admin:role:allocated-users', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:allocated-users');
      }
    }),
    http.get(path('/system/role/authUser/unallocatedList'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listUnallocatedUsers({
          roleId: readSearchParam(request, 'roleId'),
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          userName: readSearchParam(request, 'userName'),
          phonenumber: readSearchParam(request, 'phonenumber'),
        } as Record<string, unknown>);

        return demoJsonResponse(config, 'system-admin:role:unallocated-users', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:unallocated-users');
      }
    }),
    http.put(path('/system/role/authUser/cancel'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().cancelUserRole(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:role:cancel-user', {
          code: 200,
          msg: '取消授权成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:cancel-user');
      }
    }),
    http.put(path('/system/role/authUser/cancelAll'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const url = new URL(request.url);
        await createSystemAdminService().cancelUsersRole(
          {
            roleId: url.searchParams.get('roleId') ?? '',
            userIds: url.searchParams.get('userIds') ?? '',
          },
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:role:cancel-users', {
          code: 200,
          msg: '取消授权成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:cancel-users');
      }
    }),
    http.put(path('/system/role/authUser/selectAll'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const url = new URL(request.url);
        await createSystemAdminService().addUsersToRole(
          {
            roleId: url.searchParams.get('roleId') ?? '',
            userIds: url.searchParams.get('userIds') ?? '',
          },
          operator.userName
        );

        return demoJsonResponse(config, 'system-admin:role:add-users', {
          code: 200,
          msg: '分配成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:add-users');
      }
    }),
    http.get(path('/system/role/deptTree/:roleId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getRoleDeptTree(String(params.roleId ?? ''));

        return demoJsonResponse(config, 'system-admin:role:dept-tree', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:dept-tree');
      }
    }),
    http.post(path('/system/role/export'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const file = await createSystemAdminService().exportRoles(body);
        return demoFileResponse(config, 'system-admin:role:export', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:role:export');
      }
    }),

    http.get(path('/system/menu/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().listMenus({
          menuName: readSearchParam(request, 'menuName'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
        });

        return demoJsonResponse(config, 'system-admin:menu:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:list');
      }
    }),
    http.get(path('/system/menu/:menuId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getMenuDetail(String(params.menuId ?? ''));

        return demoJsonResponse(config, 'system-admin:menu:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:get');
      }
    }),
    http.get(path('/system/menu/treeselect'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getMenuTreeSelect();

        return demoJsonResponse(config, 'system-admin:menu:treeselect', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:treeselect');
      }
    }),
    http.get(path('/system/menu/roleMenuTreeselect/:roleId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getRoleMenuTree(String(params.roleId ?? ''));

        return demoJsonResponse(config, 'system-admin:menu:role-menu-tree', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:role-menu-tree');
      }
    }),
    http.post(path('/system/menu'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createMenu(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:menu:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:create');
      }
    }),
    http.put(path('/system/menu'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateMenu(body);

        return demoJsonResponse(config, 'system-admin:menu:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:update');
      }
    }),
    http.delete(path('/system/menu/:menuIds'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().deleteMenus(String(params.menuIds ?? '').split(','));

        return demoJsonResponse(config, 'system-admin:menu:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:menu:delete');
      }
    }),

    http.get(path('/system/dept/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().listDepartments({
          deptName: readSearchParam(request, 'deptName'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
        });

        return demoJsonResponse(config, 'system-admin:dept:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:list');
      }
    }),
    http.get(path('/system/dept/list/exclude/:deptId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().listDepartmentsExcludeChildren(
          String(params.deptId ?? '')
        );

        return demoJsonResponse(config, 'system-admin:dept:list-exclude', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:list-exclude');
      }
    }),
    http.get(path('/system/dept/:deptId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getDepartmentDetail(
          String(params.deptId ?? '')
        );

        return demoJsonResponse(config, 'system-admin:dept:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:get');
      }
    }),
    http.post(path('/system/dept'), async ({ request }) => {
      try {
        const operator = await ensureCurrentOperator(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createDepartment(body, operator.userName);

        return demoJsonResponse(config, 'system-admin:dept:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:create');
      }
    }),
    http.put(path('/system/dept'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateDepartment(body);

        return demoJsonResponse(config, 'system-admin:dept:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:update');
      }
    }),
    http.delete(path('/system/dept/:deptIds'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().deleteDepartments(String(params.deptIds ?? '').split(','));

        return demoJsonResponse(config, 'system-admin:dept:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dept:delete');
      }
    }),

    http.get(path('/system/dict/type/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listDictTypes({
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          dictName: readSearchParam(request, 'dictName'),
          dictType: readSearchParam(request, 'dictType'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(config, 'system-admin:dict-type:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:list');
      }
    }),
    http.get(path('/system/dict/type/:dictId'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getDictTypeDetail(
          String(params.dictId ?? '')
        );

        return demoJsonResponse(config, 'system-admin:dict-type:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:get');
      }
    }),
    http.post(path('/system/dict/type'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createDictType(body);

        return demoJsonResponse(config, 'system-admin:dict-type:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:create');
      }
    }),
    http.put(path('/system/dict/type'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateDictType(body);

        return demoJsonResponse(config, 'system-admin:dict-type:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:update');
      }
    }),
    http.delete(path('/system/dict/type/refreshCache'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().refreshDictCache();

        return demoJsonResponse(config, 'system-admin:dict-type:refresh', {
          code: 200,
          msg: '刷新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:refresh');
      }
    }),
    http.delete(path('/system/dict/type/:dictIds'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().deleteDictTypes(String(params.dictIds ?? '').split(','));

        return demoJsonResponse(config, 'system-admin:dict-type:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:delete');
      }
    }),
    http.get(path('/system/dict/type/optionselect'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().listDictTypeOptions();

        return demoJsonResponse(config, 'system-admin:dict-type:optionselect', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:optionselect');
      }
    }),
    http.post(path('/system/dict/type/export'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const file = await createSystemAdminService().exportDictTypes(body);
        return demoFileResponse(config, 'system-admin:dict-type:export', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-type:export');
      }
    }),
    http.get(path('/system/dict/data/list'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const page = await createSystemAdminService().listDictData({
          page: readSearchParam(request, 'page'),
          pageSize: readSearchParam(request, 'pageSize'),
          dictType: readSearchParam(request, 'dictType'),
          dictLabel: readSearchParam(request, 'dictLabel'),
          status: readSearchParam(request, 'status') as '0' | '1' | undefined,
          beginTime: readSearchParam(request, 'beginTime'),
          endTime: readSearchParam(request, 'endTime'),
        });

        return demoJsonResponse(config, 'system-admin:dict-data:list', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data: page,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:list');
      }
    }),
    http.get(path('/system/dict/data/:dictCode'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        const data = await createSystemAdminService().getDictDataDetail(
          String(params.dictCode ?? '')
        );

        return demoJsonResponse(config, 'system-admin:dict-data:get', {
          code: 200,
          msg: '操作成功',
          type: 'success',
          data,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:get');
      }
    }),
    http.post(path('/system/dict/data'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const result = await createSystemAdminService().createDictData(body);

        return demoJsonResponse(config, 'system-admin:dict-data:create', {
          code: 200,
          msg: '新增成功',
          type: 'success',
          data: result,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:create');
      }
    }),
    http.put(path('/system/dict/data'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        await createSystemAdminService().updateDictData(body);

        return demoJsonResponse(config, 'system-admin:dict-data:update', {
          code: 200,
          msg: '更新成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:update');
      }
    }),
    http.delete(path('/system/dict/data/:dictCodes'), async ({ request, params }) => {
      try {
        await ensureCurrentUser(request);
        await createSystemAdminService().deleteDictData(String(params.dictCodes ?? '').split(','));

        return demoJsonResponse(config, 'system-admin:dict-data:delete', {
          code: 200,
          msg: '删除成功',
          type: 'success',
          data: null,
        });
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:delete');
      }
    }),
    http.post(path('/system/dict/data/export'), async ({ request }) => {
      try {
        await ensureCurrentUser(request);
        const body = await readDemoRequestBody(request);
        const file = await createSystemAdminService().exportDictData(body);
        return demoFileResponse(config, 'system-admin:dict-data:export', file.body, file);
      } catch (error) {
        return demoErrorResponse(error, config, logger, 'system-admin:dict-data:export');
      }
    }),
  ];
}
