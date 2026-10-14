import type { HttpCollection, HttpOffsetPage } from '@/types/http-contract';
import type {
  AddUserModel,
  CrudUserRoleModel,
  EditUserModel,
  UserDetailModel,
  UserInfoModel,
  UserPageQueryModel,
  UserProfileModel,
  UserRoleResponseModel,
} from '@/api/_generated/types.gen';
import request from '@/utils/request';
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
export function listUser(query?: UserPageQueryModel) {
  return request<HttpOffsetPage<UserInfoModel>>({
    url: '/system/user/list',
    method: 'get',
    params: query,
  });
}

// 查询用户详细
export function getUser(userId: number | string) {
  return request<UserDetailModel>({
    url: '/system/user/' + parseStrEmpty(userId),
    method: 'get',
  });
}

// 新增用户
export function addUser(data: AddUserModel) {
  const payload = sanitizePasswordField(data, ['password']);
  return request<UserInfoModel>({
    url: '/system/user',
    method: 'post',
    data: payload,
    feedback: { mode: 'auto', key: 'system.user.create' },
  });
}

// 修改用户
export function updateUser(data: EditUserModel) {
  const payload = sanitizePasswordField(data, ['password']);
  return request<UserInfoModel>({
    url: '/system/user',
    method: 'put',
    data: payload,
    feedback: { mode: 'auto', key: 'system.user.update' },
  });
}

// 删除用户
export function delUser(userId: number | string) {
  return request<null>({
    url: '/system/user/' + userId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.user.delete' },
  });
}

// 用户密码重置
export function resetUserPwd(userId: number | string, password: string) {
  const data = sanitizePasswordField(
    {
      userId,
      password,
    },
    ['password']
  );
  return request<null>({
    url: '/system/user/resetPwd',
    method: 'put',
    data: data,
    feedback: { mode: 'manual', key: 'system.user.reset-password' },
  });
}

// 用户状态修改
export function changeUserStatus(userId: number | string, status: string) {
  const data = {
    userId,
    status,
  };
  return request<UserInfoModel>({
    url: '/system/user/changeStatus',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.user.change-status' },
  });
}

// 查询用户个人信息
export function getUserProfile() {
  return request<UserProfileModel>({
    url: '/system/user/profile',
    method: 'get',
  });
}

// 修改用户个人信息
export function updateUserProfile(data: UserInfoModel) {
  return request<UserProfileModel>({
    url: '/system/user/profile',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.user.update-profile' },
  });
}

// 用户密码重置
export function updateUserPwd(oldPassword: string, newPassword: string) {
  const data = sanitizePasswordField(
    {
      oldPassword,
      newPassword,
    },
    ['oldPassword', 'newPassword']
  );
  return request<null>({
    url: '/system/user/profile/updatePwd',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.user.update-password' },
  });
}

// 用户头像上传
export function uploadAvatar(data: FormData) {
  return request<{ imgUrl: string }>({
    url: '/system/user/profile/avatar',
    method: 'post',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    data: data,
    feedback: { mode: 'auto', key: 'system.user.upload-avatar' },
  });
}

// 查询授权角色
export function getAuthRole(userId: number | string) {
  return request<UserRoleResponseModel>({
    url: '/system/user/authRole/' + userId,
    method: 'get',
  });
}

// 保存授权角色
export function updateAuthRole(data: CrudUserRoleModel) {
  return request<null>({
    url: '/system/user/authRole',
    method: 'put',
    params: data,
    feedback: { mode: 'auto', key: 'system.user.assign-role' },
  });
}

// 查询部门下拉树结构
export function deptTreeSelect() {
  return request<HttpCollection<import('@/api/system/menu').MenuTreeNode>>({
    url: '/system/user/deptTree',
    method: 'get',
  });
}
