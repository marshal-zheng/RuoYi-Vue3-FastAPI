export type RoleRecord = Omit<RoleModel, 'roleId'> & { roleId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type {
  AddRoleModel,
  CrudUserRoleModel,
  GetSystemAllocatedUserListSystemRoleAuthUserAllocatedListGetData,
  GetSystemUnallocatedUserListSystemRoleAuthUserUnallocatedListGetData,
  RoleModel,
  RolePageQueryModel,
  UserInfoModel,
} from '@/api/_generated/types.gen';
import request from '@/utils/request';

// 查询角色列表
export function listRole(query?: RolePageQueryModel) {
  return request<HttpOffsetPage<RoleRecord>>({
    url: '/system/role/list',
    method: 'get',
    params: query,
  });
}

// 查询角色详细
export function getRole(roleId: number | string) {
  return request<RoleRecord>({
    url: '/system/role/' + roleId,
    method: 'get',
  });
}

// 新增角色
export function addRole(data: AddRoleModel) {
  return request<RoleRecord>({
    url: '/system/role',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.create' },
  });
}

// 修改角色
export function updateRole(data: RoleModel) {
  return request<RoleRecord>({
    url: '/system/role',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.update' },
  });
}

// 角色数据权限
export function dataScope(data: AddRoleModel) {
  return request<RoleRecord>({
    url: '/system/role/dataScope',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.data-scope' },
  });
}

// 角色状态修改
export function changeRoleStatus(roleId: number | string, status: string) {
  const data = {
    roleId,
    status,
  };
  return request<RoleRecord>({
    url: '/system/role/changeStatus',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.change-status' },
  });
}

// 删除角色
export function delRole(roleId: number | string) {
  return request<null>({
    url: '/system/role/' + roleId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.role.delete' },
  });
}

// 查询角色已授权用户列表
export function allocatedUserList(
  query?: NonNullable<GetSystemAllocatedUserListSystemRoleAuthUserAllocatedListGetData['query']>
) {
  return request<HttpOffsetPage<UserInfoModel>>({
    url: '/system/role/authUser/allocatedList',
    method: 'get',
    params: query,
  });
}

// 查询角色未授权用户列表
export function unallocatedUserList(
  query?: NonNullable<GetSystemUnallocatedUserListSystemRoleAuthUserUnallocatedListGetData['query']>
) {
  return request<HttpOffsetPage<UserInfoModel>>({
    url: '/system/role/authUser/unallocatedList',
    method: 'get',
    params: query,
  });
}

// 取消用户授权角色
export function authUserCancel(data: CrudUserRoleModel) {
  return request<null>({
    url: '/system/role/authUser/cancel',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
  });
}

// 批量取消用户授权角色
export function authUserCancelAll(data: CrudUserRoleModel) {
  return request<null>({
    url: '/system/role/authUser/cancelAll',
    method: 'put',
    params: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
  });
}

// 授权用户选择
export function authUserSelectAll(data: CrudUserRoleModel) {
  return request<null>({
    url: '/system/role/authUser/selectAll',
    method: 'put',
    params: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.assign' },
  });
}

// 根据角色ID查询部门树结构
export function deptTreeSelect(roleId: number | string) {
  return request<{ depts: import('@/api/system/menu').MenuTreeNode[]; checkedKeys: number[] }>({
    url: '/system/role/deptTree/' + roleId,
    method: 'get',
  });
}
