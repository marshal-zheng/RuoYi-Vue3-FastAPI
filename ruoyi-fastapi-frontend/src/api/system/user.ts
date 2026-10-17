import { requestDetail } from '@/api/detail';
import type { QueryRequestContext, RequestOptions } from '@zxio/http';
import type { BatchResult, HttpCollection, HttpOffsetPage } from '@/types/http-contract';
import type {
  UserCreateModel,
  UserRolesAssignModel,
  UserUpdateModel,
  UserProfileUpdateModel,
  UserStatusUpdateModel,
  UserDetailModel,
  UserInfoModel,
  UserPageQueryModel,
  UserProfileModel,
  UserRoleResponseModel,
} from '@/api/_generated/types.gen';
import request, { type ExtendedAxiosRequestConfig } from '@/utils/request';
import { parseStrEmpty } from '@/utils/ruoyi';
import { clampBcryptPassword } from '@/utils/password';

function sanitizePasswordField<
  T extends { password?: string | null; oldPassword?: string | null; newPassword?: string | null },
>(payload: T, fields: ('password' | 'oldPassword' | 'newPassword')[] = []): T {
  const target = { ...payload };
  fields.forEach((field) => {
    const password = target[field];
    if (password) target[field] = clampBcryptPassword(password);
  });
  return target;
}

// 查询用户列表
export function listUser(query?: UserPageQueryModel, context?: QueryRequestContext) {
  return request<HttpOffsetPage<UserInfoModel>>(
    {
      url: '/system/user/list',
      method: 'get',
      signal: context?.signal,
      params: query,
    },
    context?.options
  );
}

// 查询用户详细
export function getUser(
  userId: number | string | undefined,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'silentError' | 'requestOptions'>
) {
  const requestConfig = {
    ...config,
    url: '/system/user/' + parseStrEmpty(userId),
    method: 'get',
  };
  if (userId === undefined || userId === '') return request<UserDetailModel>(requestConfig);
  return requestDetail<UserDetailModel>(
    requestConfig,
    'userId',
    userId,
    (payload) => payload?.data
  );
}

// 导入结果、失败反馈与取消由当前导入操作负责，避免关闭后产生全局提示。
export function importUserExcel(
  file: File,
  updateSupport: boolean,
  config?: Pick<ExtendedAxiosRequestConfig, 'signal' | 'onUploadProgress' | 'requestOptions'>
) {
  const data = new FormData();
  data.append('file', file);
  return request<BatchResult>({
    ...config,
    url: '/system/user/importData',
    method: 'post',
    params: { updateSupport },
    data,
    // 保留原生 Upload 不设短超时的行为；批量处理期间仍可由 signal 取消。
    timeout: 0,
    feedback: { mode: 'silent' },
    silentError: true,
  });
}

// 新增用户
export function addUser(data: UserCreateModel, options?: RequestOptions) {
  const payload = sanitizePasswordField(data, ['password']);
  return request<UserInfoModel>(
    {
      url: '/system/user',
      method: 'post',
      data: payload,
      feedback: { mode: 'auto', key: 'system.user.create' },
    },
    options
  );
}

// 修改用户
export function updateUser(data: UserUpdateModel, options?: RequestOptions) {
  return request<UserInfoModel>(
    {
      url: '/system/user',
      method: 'put',
      data,
      feedback: { mode: 'auto', key: 'system.user.update' },
    },
    options
  );
}

// 删除用户
export function delUser(userId: number | string, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/user/' + userId,
      method: 'delete',
      feedback: { mode: 'auto', key: 'system.user.delete' },
    },
    options
  );
}

// 用户密码重置
export function resetUserPwd(userId: number | string, password: string, options?: RequestOptions) {
  const data = sanitizePasswordField(
    {
      userId,
      password,
    },
    ['password']
  );
  return request<null>(
    {
      url: '/system/user/resetPwd',
      method: 'put',
      data: data,
      feedback: { mode: 'manual', key: 'system.user.reset-password' },
    },
    options
  );
}

// 用户状态修改
export function changeUserStatus(
  userId: UserStatusUpdateModel['userId'],
  status: UserStatusUpdateModel['status'],
  options?: RequestOptions
) {
  const data = {
    userId,
    status,
  };
  return request<UserInfoModel>(
    {
      url: '/system/user/changeStatus',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.user.change-status' },
    },
    options
  );
}

// 查询用户个人信息
export function getUserProfile() {
  return request<UserProfileModel>({
    url: '/system/user/profile',
    method: 'get',
  });
}

// 修改用户个人信息
export function updateUserProfile(data: UserProfileUpdateModel, options?: RequestOptions) {
  return request<UserProfileModel>(
    {
      url: '/system/user/profile',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.user.update-profile' },
    },
    options
  );
}

// 用户密码重置
export function updateUserPwd(oldPassword: string, newPassword: string, options?: RequestOptions) {
  const data = sanitizePasswordField(
    {
      oldPassword,
      newPassword,
    },
    ['oldPassword', 'newPassword']
  );
  return request<null>(
    {
      url: '/system/user/profile/updatePwd',
      method: 'put',
      data: data,
      feedback: { mode: 'auto', key: 'system.user.update-password' },
    },
    options
  );
}

// 用户头像上传
export function uploadAvatar(data: FormData, options?: RequestOptions) {
  return request<{ imgUrl: string }>(
    {
      url: '/system/user/profile/avatar',
      method: 'post',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: data,
      feedback: { mode: 'auto', key: 'system.user.upload-avatar' },
    },
    options
  );
}

// 查询授权角色
export function getAuthRole(
  userId: number | string,
  config?: Pick<ExtendedAxiosRequestConfig, 'requestOptions'>
) {
  return request<UserRoleResponseModel>({
    ...config,
    url: '/system/user/authRole/' + userId,
    method: 'get',
  });
}

// 保存授权角色
export function updateAuthRole(data: UserRolesAssignModel, options?: RequestOptions) {
  return request<null>(
    {
      url: '/system/user/authRole',
      method: 'put',
      data,
      feedback: { mode: 'auto', key: 'system.user.assign-role' },
    },
    options
  );
}

// 查询部门下拉树结构
export function deptTreeSelect(context?: QueryRequestContext) {
  return request<HttpCollection<import('@/api/system/menu').MenuTreeNode>>(
    {
      url: '/system/user/deptTree',
      method: 'get',
      signal: context?.signal,
    },
    context?.options
  );
}
