import request from '@/utils/request';

// 查询角色列表
export function listRole(query?: Record<string, any>) {
  return request({
    url: '/system/role/list',
    method: 'get',
    params: query,
  });
}

// 查询角色详细
export function getRole(roleId: number | string) {
  return request({
    url: '/system/role/' + roleId,
    method: 'get',
  });
}

// 新增角色
export function addRole(data: Record<string, any>) {
  return request({
    url: '/system/role',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.create' },
  });
}

// 修改角色
export function updateRole(data: Record<string, any>) {
  return request({
    url: '/system/role',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.update' },
  });
}

// 角色数据权限
export function dataScope(data: Record<string, any>) {
  return request({
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
  return request({
    url: '/system/role/changeStatus',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.change-status' },
  });
}

// 删除角色
export function delRole(roleId: number | string) {
  return request({
    url: '/system/role/' + roleId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.role.delete' },
  });
}

// 查询角色已授权用户列表
export function allocatedUserList(query?: Record<string, any>) {
  return request({
    url: '/system/role/authUser/allocatedList',
    method: 'get',
    params: query,
  });
}

// 查询角色未授权用户列表
export function unallocatedUserList(query?: Record<string, any>) {
  return request({
    url: '/system/role/authUser/unallocatedList',
    method: 'get',
    params: query,
  });
}

// 取消用户授权角色
export function authUserCancel(data: Record<string, any>) {
  return request({
    url: '/system/role/authUser/cancel',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
  });
}

// 批量取消用户授权角色
export function authUserCancelAll(data: Record<string, any>) {
  return request({
    url: '/system/role/authUser/cancelAll',
    method: 'put',
    params: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.remove' },
  });
}

// 授权用户选择
export function authUserSelectAll(data: Record<string, any>) {
  return request({
    url: '/system/role/authUser/selectAll',
    method: 'put',
    params: data,
    feedback: { mode: 'auto', key: 'system.role.auth-user.assign' },
  });
}

// 根据角色ID查询部门树结构
export function deptTreeSelect(roleId: number | string) {
  return request({
    url: '/system/role/deptTree/' + roleId,
    method: 'get',
  });
}
