import { requestDetail } from '@/api/detail';
import type { QueryRequestContext, RequestOptions } from '@zxio/http';
export type RoleRecord = Omit<RoleDetailReadModel, 'roleId'> & { roleId: number };
import type { HttpOffsetPage } from '@/types/http-contract';
import type {
  RoleCreateModel,
  RoleUpdateModel,
  RoleStatusUpdateModel,
  RoleDataScopeUpdateModel,
  RoleUserRevokeModel,
  RoleUsersRevokeModel,
  RoleUsersGrantModel,
  GetSystemAllocatedUserListSystemRoleAuthUserAllocatedListGetData,
  GetSystemUnallocatedUserListSystemRoleAuthUserUnallocatedListGetData,
  RoleDetailReadModel,
  RolePageQueryModel,
  UserInfoModel,
} from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';

// 查询角色列表
export function listRole(query?: RolePageQueryModel, context?: QueryRequestContext) {
  return request<HttpOffsetPage<RoleRecord>>(
    {
      url: '/system/role/list',
      method: 'get',
      params: query,
      signal: context?.signal,
    },
    context?.options
  );
}

// 查询角色详细
export function getRole(
  roleId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return requestDetail<RoleRecord>(
    {
      ...config,
      url: '/system/role/' + roleId,
      method: 'get',
    },
    'roleId',
    roleId
  );
}

// 新增角色
export function addRole(data: RoleCreateModel, options?: RequestOptions) {
  return request<RoleRecord>(
    {
      url: '/system/role',
      method: 'post',
      data: data,
      feedback: { mode: 'auto', key: 'system.role.create' },
    },
    options
  );
}

// 修改角色
export function updateRole(data: RoleUpdateModel, options?: RequestOptions) {
  return request<RoleRecord>(
    {
      url: '/system/role',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.role.update' },
    },
    options
  );
}

// 角色数据权限
export function dataScope(data: RoleDataScopeUpdateModel, options?: RequestOptions) {
  return request<RoleRecord>(
    {
      url: '/system/role/dataScope',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.role.data-scope' },
    },
    options
  );
}

// 角色状态修改
export function changeRoleStatus(
  roleId: RoleStatusUpdateModel['roleId'],
  status: RoleStatusUpdateModel['status'],
  options?: RequestOptions
) {
  const data = {
    roleId,
    status,
  };
  return request<RoleRecord>(
    {
      url: '/system/role/changeStatus',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.role.change-status' },
    },
    options
  );
}

// 删除角色
export function delRole(roleId: number | string, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/role/' + roleId,
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.role.delete' },
    },
    options
  );
}

// 查询角色已授权用户列表
export function allocatedUserList(
  query?: NonNullable<GetSystemAllocatedUserListSystemRoleAuthUserAllocatedListGetData['query']>,
  context?: QueryRequestContext
) {
  return request<HttpOffsetPage<UserInfoModel>>(
    {
      url: '/system/role/authUser/allocatedList',
      method: 'get',
      params: query,
      signal: context?.signal,
    },
    context?.options
  );
}

// 查询角色未授权用户列表
export function unallocatedUserList(
  query?: NonNullable<
    GetSystemUnallocatedUserListSystemRoleAuthUserUnallocatedListGetData['query']
  >,
  context?: QueryRequestContext
) {
  return request<HttpOffsetPage<UserInfoModel>>(
    {
      url: '/system/role/authUser/unallocatedList',
      method: 'get',
      params: query,
      signal: context?.signal,
    },
    context?.options
  );
}

// 取消用户授权角色
export function authUserCancel(data: RoleUserRevokeModel, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/role/authUser/cancel',
      method: 'put',
      data,
      feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
    },
    options
  );
}

// 批量取消用户授权角色
export function authUserCancelAll(data: RoleUsersRevokeModel, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/role/authUser/cancelAll',
      method: 'put',
      data,
      feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
    },
    options
  );
}

// 授权用户选择
export function authUserSelectAll(data: RoleUsersGrantModel, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/role/authUser/selectAll',
      method: 'put',
      data,
      feedback: { mode: 'auto', key: 'system.role.auth-user.assign' },
    },
    options
  );
}

// 根据角色ID查询部门树结构
export function deptTreeSelect(
  roleId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  return request<{
    depts: import('@/api/system/menu').MenuTreeNode[];
    checkedKeys: number[];
  }>({
    ...config,
    url: '/system/role/deptTree/' + roleId,
    method: 'get',
  });
}
