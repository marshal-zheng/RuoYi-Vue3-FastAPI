import type { DemoOfflineDb } from '@/demo/db';
import { nextDemoSequence, SystemAdminRepository } from '@/demo/repositories';
import type {
  DemoAccount,
  DemoDepartment,
  DemoDictData,
  DemoDictType,
  DemoMenu,
  DemoPost,
  DemoRole,
  DemoSystemUser,
} from '@/demo/scenarios';

import { DemoAuthError } from './auth';

const DEFAULT_PAGE_SIZE = 10;
const DEFAULT_USER_PASSWORD = '123456';

type DemoStatus = '0' | '1';
type DemoMenuType = 'M' | 'C' | 'F';

export interface DemoPageResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface DemoGeneratedFile {
  filename: string;
  contentType: string;
  body: string;
}

export interface DemoSystemTreeNode {
  id: number;
  label: string;
  disabled?: boolean;
  children?: DemoSystemTreeNode[];
}

export interface DemoUserListQuery {
  page?: number | string;
  pageSize?: number | string;
  userName?: string;
  phonenumber?: string;
  status?: DemoStatus;
  deptId?: number | string;
  beginTime?: string;
  endTime?: string;
}

export interface DemoRoleListQuery {
  page?: number | string;
  pageSize?: number | string;
  roleName?: string;
  roleKey?: string;
  status?: DemoStatus;
  beginTime?: string;
  endTime?: string;
}

export interface DemoMenuListQuery {
  menuName?: string;
  status?: DemoStatus;
}

export interface DemoDeptListQuery {
  deptName?: string;
  status?: DemoStatus;
}

export interface DemoDictTypeListQuery {
  page?: number | string;
  pageSize?: number | string;
  dictName?: string;
  dictType?: string;
  status?: DemoStatus;
  beginTime?: string;
  endTime?: string;
}

export interface DemoDictDataListQuery {
  page?: number | string;
  pageSize?: number | string;
  dictType?: string;
  dictLabel?: string;
  status?: DemoStatus;
  beginTime?: string;
  endTime?: string;
}

export interface DemoUserPayload {
  userId?: number | string | null;
  deptId?: number | string | null;
  userName?: string;
  nickName?: string;
  password?: string;
  email?: string;
  phonenumber?: string;
  sex?: '0' | '1' | '2';
  status?: DemoStatus;
  avatar?: string;
  remark?: string;
  roleIds?: Array<number | string>;
  postIds?: Array<number | string>;
}

export interface DemoRolePayload {
  roleId?: number | string | null;
  roleName?: string;
  roleKey?: string;
  roleSort?: number | string | null;
  status?: DemoStatus;
  remark?: string;
  dataScope?: string;
  menuIds?: Array<number | string>;
  deptIds?: Array<number | string>;
  menuCheckStrictly?: boolean;
  deptCheckStrictly?: boolean;
}

export interface DemoMenuPayload {
  menuId?: number | string | null;
  parentId?: number | string | null;
  menuName?: string;
  menuType?: DemoMenuType;
  icon?: string;
  orderNum?: number | string | null;
  isFrame?: '0' | '1';
  isCache?: '0' | '1';
  visible?: '0' | '1';
  status?: DemoStatus;
  path?: string;
  component?: string;
  perms?: string;
  query?: string;
}

export interface DemoDeptPayload {
  deptId?: number | string | null;
  parentId?: number | string | null;
  deptName?: string;
  orderNum?: number | string | null;
  leader?: string;
  phone?: string;
  email?: string;
  status?: DemoStatus;
}

export interface DemoDictTypePayload {
  dictId?: number | string | null;
  dictName?: string;
  dictType?: string;
  status?: DemoStatus;
  remark?: string;
}

export interface DemoDictDataPayload {
  dictCode?: number | string | null;
  dictId?: number | string | null;
  dictType?: string;
  dictLabel?: string;
  dictValue?: string;
  dictSort?: number | string | null;
  cssClass?: string;
  listClass?: string;
  status?: DemoStatus;
  remark?: string;
}

export interface DemoUserRolePayload {
  userId?: number | string | null;
  roleIds?: string | Array<number | string>;
}

export interface DemoRoleUserPayload {
  roleId?: number | string | null;
  userId?: number | string | null;
  userIds?: string | Array<number | string>;
}

export interface DemoResetPasswordPayload {
  userId?: number | string | null;
  password?: string;
}

export interface DemoProfilePasswordPayload {
  oldPassword?: string;
  newPassword?: string;
}

export class DemoSystemAdminError extends DemoAuthError {
  constructor(message: string, status = 400, code = status) {
    super(message, status, code);
    this.name = 'DemoSystemAdminError';
  }
}

function hasText(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function normalizeText(value: unknown, fallback = ''): string {
  return hasText(value) ? value.trim() : fallback;
}

function resolvePage(value: number | string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }

  return Math.floor(parsed);
}

function resolveOptionalNumber(value: number | string | null | undefined): number | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new DemoSystemAdminError('请求参数格式错误', 400);
  }

  return Math.floor(parsed);
}

function ensureNumber(value: number | string | null | undefined, fieldLabel: string): number {
  const parsed = resolveOptionalNumber(value);
  if (!parsed) {
    throw new DemoSystemAdminError(`${fieldLabel}不能为空`, 400);
  }
  return parsed;
}

function parseIdList(value: string | number | Array<string | number> | null | undefined): number[] {
  if (value === undefined || value === null || value === '') {
    return [];
  }

  const rawValues = Array.isArray(value) ? value : String(value).split(',');
  const ids = rawValues
    .map((item) => resolveOptionalNumber(item))
    .filter((item): item is number => Boolean(item));

  return Array.from(new Set(ids));
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function withinDateRange(value: string | undefined, beginTime?: string, endTime?: string): boolean {
  if (!beginTime && !endTime) {
    return true;
  }

  const current = Date.parse(value ?? '');
  if (Number.isNaN(current)) {
    return true;
  }

  if (beginTime) {
    const begin = Date.parse(`${beginTime}T00:00:00`);
    if (!Number.isNaN(begin) && current < begin) {
      return false;
    }
  }

  if (endTime) {
    const end = Date.parse(`${endTime}T23:59:59.999`);
    if (!Number.isNaN(end) && current > end) {
      return false;
    }
  }

  return true;
}

function paginate<T>(items: T[], page: number, pageSize: number): DemoPageResult<T> {
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    pageSize,
  };
}

function sortByText<T>(accessor: (value: T) => string) {
  return (left: T, right: T) =>
    accessor(left).localeCompare(accessor(right), 'zh-Hans-CN', {
      numeric: true,
    });
}

function buildAncestors(parent: DemoDepartment | undefined): string {
  if (!parent) {
    return '0';
  }

  return [normalizeText(parent.ancestors, '0'), parent.deptId].filter(Boolean).join(',');
}

function buildTree<T extends { id: number; parentId: number }>(
  rows: T[],
  render: (row: T, children: DemoSystemTreeNode[]) => DemoSystemTreeNode,
  parentId = 0
): DemoSystemTreeNode[] {
  return rows
    .filter((row) => row.parentId === parentId)
    .sort((left, right) => left.id - right.id)
    .map((row) => render(row, buildTree(rows, render, row.id)));
}

function createDelimitedFile(
  filename: string,
  headers: string[],
  rows: Array<Array<string | number | undefined | null>>
): DemoGeneratedFile {
  const body = [
    '\uFEFF' + headers.join('\t'),
    ...rows.map((row) => row.map((item) => String(item ?? '')).join('\t')),
  ].join('\n');

  return {
    filename,
    contentType: 'text/tab-separated-values; charset=utf-8',
    body,
  };
}

function normalizeRole(role: DemoRole): DemoRole {
  return {
    ...role,
    roleName: normalizeText(role.roleName, `角色-${role.roleId}`),
    roleKey: normalizeText(role.roleKey, `role_${role.roleId}`),
    roleSort: Number(role.roleSort ?? role.roleId),
    dataScope: normalizeText(role.dataScope, '1'),
    menuIds: unique((role.menuIds ?? []).map((item) => Number(item)).filter(Boolean)),
    deptIds: unique((role.deptIds ?? []).map((item) => Number(item)).filter(Boolean)),
    permissions: unique((role.permissions ?? []).filter(Boolean)),
    menuCheckStrictly: role.menuCheckStrictly ?? true,
    deptCheckStrictly: role.deptCheckStrictly ?? true,
    status: role.status ?? '0',
    remark: normalizeText(role.remark),
    createTime: normalizeText(role.createTime, new Date().toISOString()),
    updateTime: normalizeText(role.updateTime, role.createTime ?? new Date().toISOString()),
  };
}

function normalizeMenu(menu: DemoMenu): DemoMenu {
  const meta = (menu.meta ?? {}) as Record<string, unknown>;
  const menuName = normalizeText(menu.menuName ?? meta.title ?? menu.name, `菜单-${menu.menuId}`);
  const routeName = normalizeText(menu.routeName ?? menu.name, `Menu${menu.menuId}`);
  const icon = normalizeText(menu.icon ?? meta.icon);
  const menuType =
    menu.menuType ??
    (hasText(menu.perms) && !hasText(menu.component) ? 'F' : menu.parentId === 0 ? 'M' : 'C');

  return {
    ...menu,
    name: routeName,
    routeName,
    menuName,
    icon,
    menuType,
    isFrame: menu.isFrame ?? '1',
    isCache: menu.isCache ?? '0',
    visible: menu.visible ?? '0',
    status: menu.status ?? '0',
    query: normalizeText(menu.query),
    perms: normalizeText(menu.perms),
    path: normalizeText(menu.path),
    component: normalizeText(menu.component),
    roles: unique((menu.roles ?? []).filter(Boolean)),
    createTime: normalizeText(menu.createTime, new Date().toISOString()),
    updateTime: normalizeText(menu.updateTime, menu.createTime ?? new Date().toISOString()),
    meta: {
      ...meta,
      title: menuName,
      icon,
    },
  };
}

function normalizeDepartment(department: DemoDepartment): DemoDepartment {
  return {
    ...department,
    ancestors: normalizeText(department.ancestors, department.parentId === 0 ? '0' : ''),
    deptName: normalizeText(department.deptName, `部门-${department.deptId}`),
    orderNum: Number(department.orderNum ?? department.deptId),
    leader: normalizeText(department.leader),
    phone: normalizeText(department.phone),
    email: normalizeText(department.email),
    status: department.status ?? '0',
    createTime: normalizeText(department.createTime, new Date().toISOString()),
    updateTime: normalizeText(
      department.updateTime,
      department.createTime ?? new Date().toISOString()
    ),
  };
}

function normalizeDictType(dictType: DemoDictType): DemoDictType {
  return {
    ...dictType,
    dictName: normalizeText(dictType.dictName, dictType.dictType),
    dictType: normalizeText(dictType.dictType),
    status: dictType.status ?? '0',
    remark: normalizeText(dictType.remark),
    createTime: normalizeText(dictType.createTime, new Date().toISOString()),
    updateTime: normalizeText(dictType.updateTime, dictType.createTime ?? new Date().toISOString()),
  };
}

function normalizeDictData(dictData: DemoDictData): DemoDictData & { dictCode: number } {
  return {
    ...dictData,
    dictId: dictData.dictId,
    dictType: normalizeText(dictData.dictType),
    dictLabel: normalizeText(dictData.dictLabel),
    dictValue: normalizeText(dictData.dictValue),
    dictSort: Number(dictData.dictSort ?? 0),
    cssClass: normalizeText(dictData.cssClass),
    listClass: normalizeText(dictData.listClass, 'default'),
    isDefault: dictData.isDefault ?? 'N',
    status: dictData.status ?? '0',
    remark: normalizeText(dictData.remark),
    createTime: normalizeText(dictData.createTime, new Date().toISOString()),
    updateTime: normalizeText(dictData.updateTime, dictData.createTime ?? new Date().toISOString()),
    dictCode: dictData.id,
  };
}

function normalizePost(post: DemoPost): DemoPost {
  return {
    ...post,
    postCode: normalizeText(post.postCode, `POST_${post.postId}`),
    postName: normalizeText(post.postName, `岗位-${post.postId}`),
    postSort: Number(post.postSort ?? post.postId),
    status: post.status ?? '0',
    remark: normalizeText(post.remark),
    createTime: normalizeText(post.createTime, new Date().toISOString()),
    updateTime: normalizeText(post.updateTime, post.createTime ?? new Date().toISOString()),
  };
}

function normalizeUser(user: DemoSystemUser): DemoSystemUser {
  return {
    ...user,
    deptId: Number(user.deptId ?? 0),
    userName: normalizeText(user.userName),
    nickName: normalizeText(user.nickName, user.userName),
    userType: normalizeText(user.userType, '00'),
    email: normalizeText(user.email),
    phonenumber: normalizeText(user.phonenumber),
    sex: user.sex ?? '2',
    avatar: normalizeText(user.avatar),
    status: user.status ?? '0',
    delFlag: user.delFlag ?? '0',
    loginIp: normalizeText(user.loginIp),
    loginDate: normalizeText(user.loginDate),
    createBy: normalizeText(user.createBy, 'demo-offline'),
    createTime: normalizeText(user.createTime, new Date().toISOString()),
    updateBy: normalizeText(user.updateBy, user.createBy ?? 'demo-offline'),
    updateTime: normalizeText(user.updateTime, user.createTime ?? new Date().toISOString()),
    remark: normalizeText(user.remark),
    roleIds: unique((user.roleIds ?? []).map((item) => Number(item)).filter(Boolean)),
    postIds: unique((user.postIds ?? []).map((item) => Number(item)).filter(Boolean)),
  };
}

function toUserAuthPayload(
  user: DemoSystemUser,
  departments: DemoDepartment[],
  roles: DemoRole[]
): Record<string, unknown> {
  const department = departments.find((item) => item.deptId === user.deptId);
  const currentRoles = roles.filter((role) => user.roleIds.includes(role.roleId));

  return {
    ...user,
    dept: department
      ? {
          deptId: department.deptId,
          deptName: department.deptName,
        }
      : undefined,
    role: currentRoles,
    admin: user.userId === 1,
  };
}

export class DemoSystemAdminService {
  constructor(
    private readonly repository: SystemAdminRepository,
    private readonly db: DemoOfflineDb
  ) {}

  async listUsers(query: DemoUserListQuery = {}): Promise<DemoPageResult<Record<string, unknown>>> {
    const page = resolvePage(query.page, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const [users, departments, roles] = await Promise.all([
      this.repository.listUsers(),
      this.repository.listDepartments(),
      this.repository.listRoles(),
    ]);

    const deptIds = query.deptId
      ? this.collectDeptIds(departments, ensureNumber(query.deptId, '部门'))
      : [];

    const rows = users
      .map(normalizeUser)
      .filter((user) => {
        if (user.delFlag === '2') {
          return false;
        }

        if (deptIds.length > 0 && !deptIds.includes(user.deptId)) {
          return false;
        }

        if (
          hasText(query.userName) &&
          !user.userName.toLowerCase().includes(query.userName.toLowerCase())
        ) {
          return false;
        }

        if (
          hasText(query.phonenumber) &&
          !normalizeText(user.phonenumber).includes(query.phonenumber.trim())
        ) {
          return false;
        }

        if (hasText(query.status) && user.status !== query.status) {
          return false;
        }

        return withinDateRange(user.createTime, query.beginTime, query.endTime);
      })
      .sort((left, right) => {
        const leftTime = Date.parse(left.createTime ?? '') || 0;
        const rightTime = Date.parse(right.createTime ?? '') || 0;
        return rightTime - leftTime || left.userId - right.userId;
      })
      .map((user) => {
        const dept = departments.find((item) => item.deptId === user.deptId);
        const role = roles.filter((item) => user.roleIds.includes(item.roleId));
        return {
          ...user,
          dept: dept
            ? {
                deptId: dept.deptId,
                deptName: dept.deptName,
              }
            : undefined,
          role,
          admin: user.userId === 1,
        };
      });

    return paginate(rows, page, pageSize);
  }

  async getUserDetail(userId?: number): Promise<Record<string, unknown>> {
    const [roles, posts] = await Promise.all([
      this.getAssignableRoles(),
      this.getAssignablePosts(),
    ]);

    if (!userId) {
      return {
        posts,
        roles,
        postIds: [],
        roleIds: [],
      };
    }

    const [user, departments, allRoles] = await Promise.all([
      this.requireUser(userId),
      this.repository.listDepartments(),
      this.repository.listRoles(),
    ]);

    const normalizedUser = normalizeUser(user);

    return {
      ...normalizedUser,
      dept: departments.find((item) => item.deptId === normalizedUser.deptId),
      role: allRoles
        .filter((item) => normalizedUser.roleIds.includes(item.roleId))
        .map(normalizeRole),
      posts,
      roles,
      postIds: normalizedUser.postIds,
      roleIds: normalizedUser.roleIds,
    };
  }

  async createUser(payload: DemoUserPayload, operator: string): Promise<Record<string, unknown>> {
    const userName = normalizeText(payload.userName);
    const nickName = normalizeText(payload.nickName);
    const password = normalizeText(payload.password);
    const deptId = ensureNumber(payload.deptId, '归属部门');

    if (!userName) {
      throw new DemoSystemAdminError('用户名称不能为空', 400);
    }
    if (!nickName) {
      throw new DemoSystemAdminError('用户昵称不能为空', 400);
    }
    if (!password) {
      throw new DemoSystemAdminError('用户密码不能为空', 400);
    }

    const existing = await this.repository.getUserByUsername(userName);
    if (existing) {
      throw new DemoSystemAdminError('新增用户失败，登录账号已存在', 400);
    }

    await this.requireDepartment(deptId);
    const roleIds = await this.validateRoleIds(parseIdList(payload.roleIds ?? []));
    const postIds = await this.validatePostIds(parseIdList(payload.postIds ?? []));
    const userId = await nextDemoSequence(this.db, 'users', 1);
    const now = new Date().toISOString();
    const user: DemoSystemUser = normalizeUser({
      userId,
      deptId,
      userName,
      nickName,
      password,
      email: normalizeText(payload.email),
      phonenumber: normalizeText(payload.phonenumber),
      sex: payload.sex ?? '2',
      avatar: normalizeText(payload.avatar),
      status: payload.status ?? '0',
      createBy: operator,
      createTime: now,
      updateBy: operator,
      updateTime: now,
      remark: normalizeText(payload.remark),
      roleIds,
      postIds,
    });

    await this.repository.saveUser(user);
    await this.syncAccountByUser(user, password);
    return {
      userId,
    };
  }

  async updateUser(payload: DemoUserPayload, operator: string): Promise<void> {
    const userId = ensureNumber(payload.userId, '用户ID');
    const current = normalizeUser(await this.requireUser(userId));
    const deptId =
      payload.deptId !== undefined ? ensureNumber(payload.deptId, '归属部门') : current.deptId;
    await this.requireDepartment(deptId);

    const roleIds =
      payload.roleIds !== undefined
        ? await this.validateRoleIds(parseIdList(payload.roleIds))
        : current.roleIds;
    const postIds =
      payload.postIds !== undefined
        ? await this.validatePostIds(parseIdList(payload.postIds))
        : current.postIds;

    if (payload.userName && payload.userName !== current.userName) {
      const duplicated = await this.repository.getUserByUsername(payload.userName);
      if (duplicated && duplicated.userId !== userId) {
        throw new DemoSystemAdminError('修改用户失败，登录账号已存在', 400);
      }
    }

    const now = new Date().toISOString();
    const user = normalizeUser({
      ...current,
      deptId,
      userName: normalizeText(payload.userName, current.userName),
      nickName: normalizeText(payload.nickName, current.nickName),
      email: payload.email !== undefined ? normalizeText(payload.email) : current.email,
      phonenumber:
        payload.phonenumber !== undefined
          ? normalizeText(payload.phonenumber)
          : current.phonenumber,
      sex: payload.sex ?? current.sex,
      avatar: payload.avatar !== undefined ? normalizeText(payload.avatar) : current.avatar,
      status: payload.status ?? current.status,
      remark: payload.remark !== undefined ? normalizeText(payload.remark) : current.remark,
      roleIds,
      postIds,
      updateBy: operator,
      updateTime: now,
    });

    await this.repository.saveUser(user);
    await this.syncAccountByUser(
      user,
      payload.password ? normalizeText(payload.password) : undefined
    );
  }

  async deleteUsers(userIds: Array<number | string>, currentUserId?: number): Promise<void> {
    const normalizedUserIds = parseIdList(userIds);
    if (!normalizedUserIds.length) {
      return;
    }

    if (currentUserId && normalizedUserIds.includes(currentUserId)) {
      throw new DemoSystemAdminError('当前登录用户不能删除', 400);
    }

    const users = await Promise.all(
      normalizedUserIds.map((userId) => this.repository.getUser(userId))
    );
    const existingUsers = users.filter((item): item is DemoSystemUser => Boolean(item));
    const usernames = existingUsers.map((item) => item.userName);

    await this.repository.deleteUsers(normalizedUserIds);
    if (usernames.length) {
      await this.repository.deleteAccounts(usernames);
    }
  }

  async changeUserStatus(
    userId: number | string,
    status: DemoStatus,
    operator: string
  ): Promise<void> {
    const current = normalizeUser(await this.requireUser(ensureNumber(userId, '用户ID')));
    const nextUser = normalizeUser({
      ...current,
      status,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser);
  }

  async resetUserPassword(payload: DemoResetPasswordPayload, operator: string): Promise<void> {
    const userId = ensureNumber(payload.userId, '用户ID');
    const password = normalizeText(payload.password);
    if (!password) {
      throw new DemoSystemAdminError('新密码不能为空', 400);
    }

    const current = normalizeUser(await this.requireUser(userId));
    const nextUser = normalizeUser({
      ...current,
      password,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser, password);
  }

  async getUserAuthRole(userId: number | string): Promise<Record<string, unknown>> {
    const normalizedUserId = ensureNumber(userId, '用户ID');
    const [user, roles, departments] = await Promise.all([
      this.requireUser(normalizedUserId),
      this.repository.listRoles(),
      this.repository.listDepartments(),
    ]);

    const normalizedUser = normalizeUser(user);
    const normalizedRoles = roles
      .map(normalizeRole)
      .sort((left, right) => left.roleId - right.roleId);

    return {
      user: toUserAuthPayload(
        normalizedUser,
        departments.map(normalizeDepartment),
        normalizedRoles
      ),
      roles: normalizedRoles.map((role) => ({
        ...role,
        flag: normalizedUser.roleIds.includes(role.roleId),
      })),
    };
  }

  async updateUserAuthRole(payload: DemoUserRolePayload, operator: string): Promise<void> {
    const userId = ensureNumber(payload.userId, '用户ID');
    const roleIds = await this.validateRoleIds(parseIdList(payload.roleIds ?? []));
    const current = normalizeUser(await this.requireUser(userId));
    const nextUser = normalizeUser({
      ...current,
      roleIds,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser);
  }

  async getUserProfile(userId: number): Promise<Record<string, unknown>> {
    const [user, departments, roles, posts] = await Promise.all([
      this.requireUser(userId),
      this.repository.listDepartments(),
      this.repository.listRoles(),
      this.repository.listPosts(),
    ]);
    const normalizedUser = normalizeUser(user);

    return {
      data: toUserAuthPayload(
        normalizedUser,
        departments.map(normalizeDepartment),
        roles.map(normalizeRole)
      ),
      postGroup: posts
        .filter((item) => normalizedUser.postIds.includes(item.postId))
        .sort((left, right) => left.postSort - right.postSort)
        .map((item) => item.postName)
        .join(' / '),
      roleGroup: roles
        .filter((item) => normalizedUser.roleIds.includes(item.roleId))
        .sort((left, right) => Number(left.roleSort ?? 0) - Number(right.roleSort ?? 0))
        .map((item) => item.roleName)
        .join(' / '),
    };
  }

  async updateUserProfile(
    userId: number,
    payload: DemoUserPayload,
    operator: string
  ): Promise<void> {
    const current = normalizeUser(await this.requireUser(userId));
    const nextUser = normalizeUser({
      ...current,
      nickName: payload.nickName !== undefined ? normalizeText(payload.nickName) : current.nickName,
      email: payload.email !== undefined ? normalizeText(payload.email) : current.email,
      phonenumber:
        payload.phonenumber !== undefined
          ? normalizeText(payload.phonenumber)
          : current.phonenumber,
      sex: payload.sex ?? current.sex,
      avatar: payload.avatar !== undefined ? normalizeText(payload.avatar) : current.avatar,
      remark: payload.remark !== undefined ? normalizeText(payload.remark) : current.remark,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser);
  }

  async updateProfilePassword(
    userId: number,
    payload: DemoProfilePasswordPayload,
    operator: string
  ): Promise<void> {
    const current = normalizeUser(await this.requireUser(userId));
    const oldPassword = normalizeText(payload.oldPassword);
    const newPassword = normalizeText(payload.newPassword);

    if (!newPassword) {
      throw new DemoSystemAdminError('新密码不能为空', 400);
    }

    const currentPassword = normalizeText(current.password);
    if (currentPassword && oldPassword && currentPassword !== oldPassword) {
      throw new DemoSystemAdminError('旧密码不正确', 400);
    }

    const nextUser = normalizeUser({
      ...current,
      password: newPassword,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser, newPassword);
  }

  async updateUserAvatar(userId: number, avatar: string, operator: string): Promise<string> {
    const current = normalizeUser(await this.requireUser(userId));
    const nextUser = normalizeUser({
      ...current,
      avatar,
      updateBy: operator,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveUser(nextUser);
    await this.syncAccountByUser(nextUser);
    return avatar;
  }

  async listRoles(query: DemoRoleListQuery = {}): Promise<DemoPageResult<DemoRole>> {
    const page = resolvePage(query.page, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const rows = (await this.repository.listRoles())
      .map(normalizeRole)
      .filter((role) => {
        if (
          hasText(query.roleName) &&
          !role.roleName.toLowerCase().includes(query.roleName.toLowerCase())
        ) {
          return false;
        }
        if (
          hasText(query.roleKey) &&
          !role.roleKey.toLowerCase().includes(query.roleKey.toLowerCase())
        ) {
          return false;
        }
        if (hasText(query.status) && role.status !== query.status) {
          return false;
        }
        return withinDateRange(role.createTime, query.beginTime, query.endTime);
      })
      .sort(
        (left, right) =>
          Number(left.roleSort) - Number(right.roleSort) || left.roleId - right.roleId
      );

    return paginate(rows, page, pageSize);
  }

  async getRoleDetail(roleId: number | string): Promise<Record<string, unknown>> {
    const role = normalizeRole(await this.requireRole(ensureNumber(roleId, '角色ID')));
    return {
      ...role,
      data: role,
    };
  }

  async createRole(payload: DemoRolePayload, operator: string): Promise<Record<string, unknown>> {
    const roleName = normalizeText(payload.roleName);
    const roleKey = normalizeText(payload.roleKey);
    const roleSort = Number(payload.roleSort ?? 0);
    if (!roleName) {
      throw new DemoSystemAdminError('角色名称不能为空', 400);
    }
    if (!roleKey) {
      throw new DemoSystemAdminError('权限字符不能为空', 400);
    }

    const allRoles = (await this.repository.listRoles()).map(normalizeRole);
    if (allRoles.some((item) => item.roleName === roleName)) {
      throw new DemoSystemAdminError('新增角色失败，角色名称已存在', 400);
    }
    if (allRoles.some((item) => item.roleKey === roleKey)) {
      throw new DemoSystemAdminError('新增角色失败，权限字符已存在', 400);
    }

    const roleId = await nextDemoSequence(this.db, 'roles', 1);
    const menuIds = await this.validateMenuIds(parseIdList(payload.menuIds ?? []));
    const deptIds = await this.validateDeptIds(parseIdList(payload.deptIds ?? []));
    const now = new Date().toISOString();
    const role = normalizeRole({
      roleId,
      roleName,
      roleKey,
      roleSort,
      status: payload.status ?? '0',
      dataScope: normalizeText(payload.dataScope, '1'),
      menuIds,
      deptIds,
      permissions: unique(
        (await this.repository.listMenus())
          .map(normalizeMenu)
          .filter((menu) => menuIds.includes(menu.menuId) && hasText(menu.perms))
          .map((menu) => menu.perms as string)
      ),
      menuCheckStrictly: payload.menuCheckStrictly ?? true,
      deptCheckStrictly: payload.deptCheckStrictly ?? true,
      remark: normalizeText(payload.remark),
      createTime: now,
      updateTime: now,
    });

    await this.repository.saveRole(role);
    return {
      roleId,
    };
  }

  async updateRole(payload: DemoRolePayload, operator: string): Promise<void> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    const current = normalizeRole(await this.requireRole(roleId));
    if (roleId === 1 && payload.status === '1') {
      throw new DemoSystemAdminError('超级管理员角色不能停用', 400);
    }

    const allRoles = (await this.repository.listRoles()).map(normalizeRole);
    const roleName = normalizeText(payload.roleName, current.roleName);
    const roleKey = normalizeText(payload.roleKey, current.roleKey);
    if (allRoles.some((item) => item.roleId !== roleId && item.roleName === roleName)) {
      throw new DemoSystemAdminError('修改角色失败，角色名称已存在', 400);
    }
    if (allRoles.some((item) => item.roleId !== roleId && item.roleKey === roleKey)) {
      throw new DemoSystemAdminError('修改角色失败，权限字符已存在', 400);
    }

    const menuIds =
      payload.menuIds !== undefined
        ? await this.validateMenuIds(parseIdList(payload.menuIds))
        : current.menuIds;
    const deptIds =
      payload.deptIds !== undefined
        ? await this.validateDeptIds(parseIdList(payload.deptIds))
        : (current.deptIds ?? []);
    const permissions = unique(
      (await this.repository.listMenus())
        .map(normalizeMenu)
        .filter((menu) => menuIds.includes(menu.menuId) && hasText(menu.perms))
        .map((menu) => menu.perms as string)
    );

    const role = normalizeRole({
      ...current,
      roleName,
      roleKey,
      roleSort: payload.roleSort !== undefined ? Number(payload.roleSort) : current.roleSort,
      status: payload.status ?? current.status,
      dataScope: payload.dataScope ?? current.dataScope,
      menuIds,
      deptIds,
      permissions,
      menuCheckStrictly: payload.menuCheckStrictly ?? current.menuCheckStrictly,
      deptCheckStrictly: payload.deptCheckStrictly ?? current.deptCheckStrictly,
      remark: payload.remark !== undefined ? normalizeText(payload.remark) : current.remark,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveRole(role);
    await this.syncAccountsByRole(roleId);
  }

  async changeRoleStatus(
    roleId: number | string,
    status: DemoStatus,
    _operator: string
  ): Promise<void> {
    const normalizedRoleId = ensureNumber(roleId, '角色ID');
    if (normalizedRoleId === 1 && status === '1') {
      throw new DemoSystemAdminError('超级管理员角色不能停用', 400);
    }
    const current = normalizeRole(await this.requireRole(normalizedRoleId));
    await this.repository.saveRole(
      normalizeRole({
        ...current,
        status,
        updateTime: new Date().toISOString(),
      })
    );
    await this.syncAccountsByRole(normalizedRoleId);
  }

  async updateRoleDataScope(payload: DemoRolePayload): Promise<void> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    const current = normalizeRole(await this.requireRole(roleId));
    const deptIds =
      payload.deptIds !== undefined
        ? await this.validateDeptIds(parseIdList(payload.deptIds))
        : (current.deptIds ?? []);

    await this.repository.saveRole(
      normalizeRole({
        ...current,
        dataScope: normalizeText(payload.dataScope, current.dataScope ?? '1'),
        deptIds,
        deptCheckStrictly: payload.deptCheckStrictly ?? current.deptCheckStrictly,
        updateTime: new Date().toISOString(),
      })
    );
  }

  async deleteRoles(roleIds: Array<number | string>): Promise<void> {
    const normalizedRoleIds = parseIdList(roleIds);
    if (!normalizedRoleIds.length) {
      return;
    }
    if (normalizedRoleIds.includes(1)) {
      throw new DemoSystemAdminError('超级管理员角色不能删除', 400);
    }

    const users = (await this.repository.listUsers()).map(normalizeUser);
    if (users.some((user) => normalizedRoleIds.some((roleId) => user.roleIds.includes(roleId)))) {
      throw new DemoSystemAdminError('存在已分配用户的角色，不能删除', 400);
    }

    await this.repository.deleteRoles(normalizedRoleIds);
  }

  async listAllocatedUsers(
    payload: DemoRoleUserPayload
  ): Promise<DemoPageResult<Record<string, unknown>>> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    return this.listUsersByRole(roleId, true, payload);
  }

  async listUnallocatedUsers(
    payload: DemoRoleUserPayload
  ): Promise<DemoPageResult<Record<string, unknown>>> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    return this.listUsersByRole(roleId, false, payload);
  }

  async addUsersToRole(payload: DemoRoleUserPayload, operator: string): Promise<void> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    await this.requireRole(roleId);
    const userIds = parseIdList(payload.userIds ?? []);
    if (!userIds.length) {
      throw new DemoSystemAdminError('用户ID不能为空', 400);
    }

    await Promise.all(
      userIds.map(async (userId) => {
        const user = normalizeUser(await this.requireUser(userId));
        await this.repository.saveUser(
          normalizeUser({
            ...user,
            roleIds: unique([...user.roleIds, roleId]),
            updateBy: operator,
            updateTime: new Date().toISOString(),
          })
        );
        await this.syncAccountsByUserId(userId);
      })
    );
  }

  async cancelUserRole(payload: DemoRoleUserPayload, operator: string): Promise<void> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    const userId = ensureNumber(payload.userId, '用户ID');
    const user = normalizeUser(await this.requireUser(userId));
    const nextRoleIds = user.roleIds.filter((item) => item !== roleId);

    await this.repository.saveUser(
      normalizeUser({
        ...user,
        roleIds: nextRoleIds,
        updateBy: operator,
        updateTime: new Date().toISOString(),
      })
    );
    await this.syncAccountsByUserId(userId);
  }

  async cancelUsersRole(payload: DemoRoleUserPayload, operator: string): Promise<void> {
    const roleId = ensureNumber(payload.roleId, '角色ID');
    const userIds = parseIdList(payload.userIds ?? []);
    await Promise.all(
      userIds.map((userId) =>
        this.cancelUserRole(
          {
            roleId,
            userId,
          },
          operator
        )
      )
    );
  }

  async getRoleDeptTree(roleId: number | string): Promise<Record<string, unknown>> {
    const normalizedRole = normalizeRole(await this.requireRole(ensureNumber(roleId, '角色ID')));
    const departments = (await this.repository.listDepartments()).map(normalizeDepartment);
    return {
      depts: this.buildDepartmentSelectTree(departments),
      checkedKeys: normalizedRole.deptIds ?? [],
    };
  }

  async listMenus(query: DemoMenuListQuery = {}): Promise<DemoMenu[]> {
    return (await this.repository.listMenus())
      .map(normalizeMenu)
      .filter((menu) => {
        if (
          hasText(query.menuName) &&
          !menu.menuName?.toLowerCase().includes(query.menuName.toLowerCase())
        ) {
          return false;
        }
        if (hasText(query.status) && menu.status !== query.status) {
          return false;
        }
        return true;
      })
      .sort((left, right) => left.orderNum - right.orderNum || left.menuId - right.menuId);
  }

  async getMenuDetail(menuId: number | string): Promise<DemoMenu> {
    return normalizeMenu(await this.requireMenu(ensureNumber(menuId, '菜单ID')));
  }

  async getMenuTreeSelect(): Promise<DemoSystemTreeNode[]> {
    return this.buildMenuSelectTree((await this.repository.listMenus()).map(normalizeMenu));
  }

  async getRoleMenuTree(roleId: number | string): Promise<Record<string, unknown>> {
    const normalizedRole = normalizeRole(await this.requireRole(ensureNumber(roleId, '角色ID')));
    const menus = (await this.repository.listMenus()).map(normalizeMenu);
    return {
      menus: this.buildMenuSelectTree(menus),
      checkedKeys: normalizedRole.menuIds,
    };
  }

  async createMenu(payload: DemoMenuPayload, operator: string): Promise<Record<string, unknown>> {
    const menuId = await nextDemoSequence(this.db, 'menus', 1);
    const parentId = resolveOptionalNumber(payload.parentId) ?? 0;
    const parentMenu = parentId ? normalizeMenu(await this.requireMenu(parentId)) : undefined;
    const now = new Date().toISOString();

    const menu = normalizeMenu({
      menuId,
      parentId,
      name: normalizeText(payload.menuName, `Menu${menuId}`),
      menuName: normalizeText(payload.menuName, `菜单-${menuId}`),
      routeName: normalizeText(payload.menuName, `Menu${menuId}`),
      path: normalizeText(payload.path),
      component: normalizeText(payload.component),
      orderNum: Number(payload.orderNum ?? 0),
      visible: payload.visible ?? '0',
      status: payload.status ?? '0',
      roles: parentMenu?.roles ?? [],
      perms: normalizeText(payload.perms),
      menuType: payload.menuType ?? 'M',
      icon: normalizeText(payload.icon),
      isFrame: payload.isFrame ?? '1',
      isCache: payload.isCache ?? '0',
      query: normalizeText(payload.query),
      createTime: now,
      updateTime: now,
      meta: {
        title: normalizeText(payload.menuName, `菜单-${menuId}`),
        icon: normalizeText(payload.icon),
      },
    });

    await this.repository.saveMenu(menu);
    return {
      menuId,
    };
  }

  async updateMenu(payload: DemoMenuPayload): Promise<void> {
    const menuId = ensureNumber(payload.menuId, '菜单ID');
    const current = normalizeMenu(await this.requireMenu(menuId));
    const parentId =
      payload.parentId !== undefined
        ? (resolveOptionalNumber(payload.parentId) ?? 0)
        : current.parentId;

    if (parentId === menuId) {
      throw new DemoSystemAdminError('上级菜单不能选择自己', 400);
    }

    if (parentId) {
      const descendants = this.collectMenuIds(
        (await this.repository.listMenus()).map(normalizeMenu),
        menuId
      );
      if (descendants.includes(parentId)) {
        throw new DemoSystemAdminError('上级菜单不能选择当前菜单的子节点', 400);
      }
    }

    await this.repository.saveMenu(
      normalizeMenu({
        ...current,
        parentId,
        name:
          payload.menuName !== undefined
            ? normalizeText(payload.menuName, current.name)
            : current.name,
        routeName:
          payload.menuName !== undefined
            ? normalizeText(payload.menuName, current.routeName)
            : current.routeName,
        menuName:
          payload.menuName !== undefined
            ? normalizeText(payload.menuName, current.menuName)
            : current.menuName,
        path: payload.path !== undefined ? normalizeText(payload.path) : current.path,
        component:
          payload.component !== undefined ? normalizeText(payload.component) : current.component,
        orderNum: payload.orderNum !== undefined ? Number(payload.orderNum) : current.orderNum,
        visible: payload.visible ?? current.visible,
        status: payload.status ?? current.status,
        perms: payload.perms !== undefined ? normalizeText(payload.perms) : current.perms,
        menuType: payload.menuType ?? current.menuType,
        icon: payload.icon !== undefined ? normalizeText(payload.icon) : current.icon,
        isFrame: payload.isFrame ?? current.isFrame,
        isCache: payload.isCache ?? current.isCache,
        query: payload.query !== undefined ? normalizeText(payload.query) : current.query,
        updateTime: new Date().toISOString(),
        meta: {
          ...(current.meta ?? {}),
          title:
            payload.menuName !== undefined
              ? normalizeText(payload.menuName, current.menuName)
              : current.menuName,
          icon: payload.icon !== undefined ? normalizeText(payload.icon) : current.icon,
        },
      })
    );
  }

  async deleteMenus(menuIds: Array<number | string>): Promise<void> {
    const normalizedMenuIds = parseIdList(menuIds);
    if (!normalizedMenuIds.length) {
      return;
    }

    const menus = (await this.repository.listMenus()).map(normalizeMenu);
    const menuIdSet = new Set<number>();
    normalizedMenuIds.forEach((menuId) => {
      this.collectMenuIds(menus, menuId).forEach((id) => menuIdSet.add(id));
    });
    const allDeleteIds = Array.from(menuIdSet);

    await this.repository.deleteMenus(allDeleteIds);

    const roles = (await this.repository.listRoles()).map(normalizeRole);
    await Promise.all(
      roles.map(async (role) => {
        const nextMenuIds = role.menuIds.filter((menuId) => !menuIdSet.has(menuId));
        if (nextMenuIds.length !== role.menuIds.length) {
          await this.repository.saveRole(
            normalizeRole({
              ...role,
              menuIds: nextMenuIds,
              permissions: role.permissions,
              updateTime: new Date().toISOString(),
            })
          );
        }
      })
    );
  }

  async listDepartments(query: DemoDeptListQuery = {}): Promise<DemoDepartment[]> {
    return (await this.repository.listDepartments())
      .map(normalizeDepartment)
      .filter((department) => {
        if (
          hasText(query.deptName) &&
          !department.deptName.toLowerCase().includes(query.deptName.toLowerCase())
        ) {
          return false;
        }
        if (hasText(query.status) && department.status !== query.status) {
          return false;
        }
        return true;
      })
      .sort((left, right) => left.orderNum - right.orderNum || left.deptId - right.deptId);
  }

  async listDepartmentsExcludeChildren(deptId: number | string): Promise<DemoDepartment[]> {
    const normalizedDeptId = ensureNumber(deptId, '部门ID');
    const departments = (await this.repository.listDepartments()).map(normalizeDepartment);
    const excludeIds = new Set(this.collectDeptIds(departments, normalizedDeptId));
    excludeIds.add(normalizedDeptId);
    return departments.filter((department) => !excludeIds.has(department.deptId));
  }

  async getDepartmentDetail(deptId: number | string): Promise<DemoDepartment> {
    return normalizeDepartment(await this.requireDepartment(ensureNumber(deptId, '部门ID')));
  }

  async createDepartment(
    payload: DemoDeptPayload,
    operator: string
  ): Promise<Record<string, unknown>> {
    const deptId = await nextDemoSequence(this.db, 'departments', 1);
    const parentId = resolveOptionalNumber(payload.parentId) ?? 0;
    const parent = parentId
      ? normalizeDepartment(await this.requireDepartment(parentId))
      : undefined;
    const now = new Date().toISOString();

    const department = normalizeDepartment({
      deptId,
      parentId,
      ancestors: buildAncestors(parent),
      deptName: normalizeText(payload.deptName),
      orderNum: Number(payload.orderNum ?? 0),
      leader: normalizeText(payload.leader),
      phone: normalizeText(payload.phone),
      email: normalizeText(payload.email),
      status: payload.status ?? '0',
      createTime: now,
      updateTime: now,
    });

    if (!department.deptName) {
      throw new DemoSystemAdminError('部门名称不能为空', 400);
    }

    await this.repository.saveDepartment(department);
    return {
      deptId,
    };
  }

  async updateDepartment(payload: DemoDeptPayload): Promise<void> {
    const deptId = ensureNumber(payload.deptId, '部门ID');
    const current = normalizeDepartment(await this.requireDepartment(deptId));
    const parentId =
      payload.parentId !== undefined
        ? (resolveOptionalNumber(payload.parentId) ?? 0)
        : current.parentId;

    if (parentId === deptId) {
      throw new DemoSystemAdminError('上级部门不能选择自己', 400);
    }

    const allDepartments = (await this.repository.listDepartments()).map(normalizeDepartment);
    const descendants = this.collectDeptIds(allDepartments, deptId);
    if (descendants.includes(parentId)) {
      throw new DemoSystemAdminError('上级部门不能选择当前部门的子节点', 400);
    }

    const parent = parentId
      ? normalizeDepartment(await this.requireDepartment(parentId))
      : undefined;

    await this.repository.saveDepartment(
      normalizeDepartment({
        ...current,
        parentId,
        ancestors: buildAncestors(parent),
        deptName:
          payload.deptName !== undefined ? normalizeText(payload.deptName) : current.deptName,
        orderNum: payload.orderNum !== undefined ? Number(payload.orderNum) : current.orderNum,
        leader: payload.leader !== undefined ? normalizeText(payload.leader) : current.leader,
        phone: payload.phone !== undefined ? normalizeText(payload.phone) : current.phone,
        email: payload.email !== undefined ? normalizeText(payload.email) : current.email,
        status: payload.status ?? current.status,
        updateTime: new Date().toISOString(),
      })
    );
  }

  async deleteDepartments(deptIds: Array<number | string>): Promise<void> {
    const normalizedDeptIds = parseIdList(deptIds);
    if (!normalizedDeptIds.length) {
      return;
    }

    const departments = (await this.repository.listDepartments()).map(normalizeDepartment);
    const users = (await this.repository.listUsers()).map(normalizeUser);

    for (const deptId of normalizedDeptIds) {
      const deleteIds = this.collectDeptIds(departments, deptId);
      const nestedIds = deleteIds.filter((item) => item !== deptId);
      if (nestedIds.length > 0) {
        throw new DemoSystemAdminError('存在下级部门，不允许删除', 400);
      }
      if (users.some((user) => user.deptId === deptId)) {
        throw new DemoSystemAdminError('部门下存在用户，不允许删除', 400);
      }
    }

    await this.repository.deleteDepartments(normalizedDeptIds);
  }

  async getDepartmentTreeSelect(): Promise<DemoSystemTreeNode[]> {
    return this.buildDepartmentSelectTree(
      (await this.repository.listDepartments()).map(normalizeDepartment)
    );
  }

  async listDictTypes(query: DemoDictTypeListQuery = {}): Promise<DemoPageResult<DemoDictType>> {
    const page = resolvePage(query.page, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const rows = (await this.repository.listDictTypes())
      .map(normalizeDictType)
      .filter((dictType) => {
        if (
          hasText(query.dictName) &&
          !dictType.dictName.toLowerCase().includes(query.dictName.toLowerCase())
        ) {
          return false;
        }
        if (
          hasText(query.dictType) &&
          !dictType.dictType.toLowerCase().includes(query.dictType.toLowerCase())
        ) {
          return false;
        }
        if (hasText(query.status) && dictType.status !== query.status) {
          return false;
        }
        return withinDateRange(dictType.createTime, query.beginTime, query.endTime);
      })
      .sort(sortByText((item) => `${item.dictName}-${item.dictId}`));

    return paginate(rows, page, pageSize);
  }

  async getDictTypeDetail(dictId: number | string): Promise<DemoDictType> {
    return normalizeDictType(await this.requireDictType(ensureNumber(dictId, '字典类型ID')));
  }

  async createDictType(payload: DemoDictTypePayload): Promise<Record<string, unknown>> {
    const dictTypeValue = normalizeText(payload.dictType);
    const dictName = normalizeText(payload.dictName);
    if (!dictName) {
      throw new DemoSystemAdminError('字典名称不能为空', 400);
    }
    if (!dictTypeValue) {
      throw new DemoSystemAdminError('字典类型不能为空', 400);
    }

    const duplicated = await this.repository.getDictTypeByType(dictTypeValue);
    if (duplicated) {
      throw new DemoSystemAdminError('字典类型已存在', 400);
    }

    const dictId = await nextDemoSequence(this.db, 'dictTypes', 1);
    const now = new Date().toISOString();
    await this.repository.saveDictType(
      normalizeDictType({
        dictId,
        dictName,
        dictType: dictTypeValue,
        status: payload.status ?? '0',
        remark: normalizeText(payload.remark),
        createTime: now,
        updateTime: now,
      })
    );
    return {
      dictId,
    };
  }

  async updateDictType(payload: DemoDictTypePayload): Promise<void> {
    const dictId = ensureNumber(payload.dictId, '字典类型ID');
    const current = normalizeDictType(await this.requireDictType(dictId));
    const dictTypeValue = normalizeText(payload.dictType, current.dictType);

    const duplicated = await this.repository.getDictTypeByType(dictTypeValue);
    if (duplicated && duplicated.dictId !== dictId) {
      throw new DemoSystemAdminError('字典类型已存在', 400);
    }

    const nextDictType = normalizeDictType({
      ...current,
      dictName: payload.dictName !== undefined ? normalizeText(payload.dictName) : current.dictName,
      dictType: dictTypeValue,
      status: payload.status ?? current.status,
      remark: payload.remark !== undefined ? normalizeText(payload.remark) : current.remark,
      updateTime: new Date().toISOString(),
    });

    await this.repository.saveDictType(nextDictType);

    if (nextDictType.dictType !== current.dictType) {
      const dictRows = (await this.repository.listDictData()).map(normalizeDictData);
      await Promise.all(
        dictRows
          .filter((item) => item.dictType === current.dictType)
          .map((item) =>
            this.repository.saveDictData({
              ...item,
              id: item.id,
              dictType: nextDictType.dictType,
            })
          )
      );
    }
  }

  async deleteDictTypes(dictIds: Array<number | string>): Promise<void> {
    const normalizedDictIds = parseIdList(dictIds);
    if (!normalizedDictIds.length) {
      return;
    }

    const dictTypes = await Promise.all(
      normalizedDictIds.map((dictId) => this.requireDictType(dictId))
    );
    const dictTypeValues = new Set(dictTypes.map((item) => item.dictType));
    const dictRows = (await this.repository.listDictData()).map(normalizeDictData);
    const deleteCodes = dictRows
      .filter((item) => dictTypeValues.has(item.dictType))
      .map((item) => item.dictCode);

    await this.repository.deleteDictTypes(normalizedDictIds);
    if (deleteCodes.length) {
      await this.repository.deleteDictData(deleteCodes);
    }
  }

  async refreshDictCache(): Promise<void> {
    return Promise.resolve();
  }

  async listDictTypeOptions(): Promise<DemoDictType[]> {
    return (await this.repository.listDictTypes())
      .map(normalizeDictType)
      .filter((item) => item.status === '0')
      .sort(sortByText((item) => `${item.dictName}-${item.dictId}`));
  }

  async listDictData(
    query: DemoDictDataListQuery = {}
  ): Promise<DemoPageResult<DemoDictData & { dictCode: number }>> {
    const page = resolvePage(query.page, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const rows = (await this.repository.listDictData())
      .map(normalizeDictData)
      .filter((dictData) => {
        if (hasText(query.dictType) && dictData.dictType !== query.dictType) {
          return false;
        }
        if (
          hasText(query.dictLabel) &&
          !dictData.dictLabel.toLowerCase().includes(query.dictLabel.toLowerCase())
        ) {
          return false;
        }
        if (hasText(query.status) && dictData.status !== query.status) {
          return false;
        }
        return withinDateRange(dictData.createTime, query.beginTime, query.endTime);
      })
      .sort((left, right) => left.dictSort - right.dictSort || left.dictCode - right.dictCode);

    return paginate(rows, page, pageSize);
  }

  async getDictDataDetail(dictCode: number | string): Promise<Record<string, unknown>> {
    const dictData = normalizeDictData(
      await this.requireDictData(ensureNumber(dictCode, '字典编码'))
    );
    return {
      ...dictData,
      dictCode: dictData.id,
    };
  }

  async createDictData(payload: DemoDictDataPayload): Promise<Record<string, unknown>> {
    const dictType = normalizeText(payload.dictType);
    if (!dictType) {
      throw new DemoSystemAdminError('字典类型不能为空', 400);
    }
    const dictTypeEntity = await this.repository.getDictTypeByType(dictType);
    if (!dictTypeEntity) {
      throw new DemoSystemAdminError('字典类型不存在', 400);
    }

    const dictCode = await nextDemoSequence(this.db, 'dicts', 1);
    const now = new Date().toISOString();
    await this.repository.saveDictData({
      id: dictCode,
      dictId: dictTypeEntity.dictId,
      dictType,
      dictLabel: normalizeText(payload.dictLabel),
      dictValue: normalizeText(payload.dictValue),
      dictSort: Number(payload.dictSort ?? 0),
      cssClass: normalizeText(payload.cssClass),
      listClass: normalizeText(payload.listClass, 'default'),
      isDefault: 'N',
      status: payload.status ?? '0',
      remark: normalizeText(payload.remark),
      createTime: now,
      updateTime: now,
    });

    return {
      dictCode,
    };
  }

  async updateDictData(payload: DemoDictDataPayload): Promise<void> {
    const dictCode = ensureNumber(payload.dictCode, '字典编码');
    const current = normalizeDictData(await this.requireDictData(dictCode));
    const dictType = normalizeText(payload.dictType, current.dictType);
    const dictTypeEntity = await this.repository.getDictTypeByType(dictType);
    if (!dictTypeEntity) {
      throw new DemoSystemAdminError('字典类型不存在', 400);
    }

    await this.repository.saveDictData({
      ...current,
      id: dictCode,
      dictId: dictTypeEntity.dictId,
      dictType,
      dictLabel:
        payload.dictLabel !== undefined ? normalizeText(payload.dictLabel) : current.dictLabel,
      dictValue:
        payload.dictValue !== undefined ? normalizeText(payload.dictValue) : current.dictValue,
      dictSort: payload.dictSort !== undefined ? Number(payload.dictSort) : current.dictSort,
      cssClass: payload.cssClass !== undefined ? normalizeText(payload.cssClass) : current.cssClass,
      listClass:
        payload.listClass !== undefined ? normalizeText(payload.listClass) : current.listClass,
      status: payload.status ?? current.status,
      remark: payload.remark !== undefined ? normalizeText(payload.remark) : current.remark,
      updateTime: new Date().toISOString(),
    });
  }

  async deleteDictData(dictCodes: Array<number | string>): Promise<void> {
    const normalizedDictCodes = parseIdList(dictCodes);
    if (!normalizedDictCodes.length) {
      return;
    }
    await this.repository.deleteDictData(normalizedDictCodes);
  }

  async exportUsers(query: DemoUserListQuery = {}): Promise<DemoGeneratedFile> {
    const page = await this.listUsers({
      ...query,
      page: 1,
      pageSize: Number.MAX_SAFE_INTEGER,
    });
    return createDelimitedFile(
      'demo-users.tsv',
      ['用户编号', '用户名称', '用户昵称', '部门', '手机号', '状态', '创建时间'],
      page.items.map((row) => [
        Number(row.userId),
        normalizeText(row.userName),
        normalizeText(row.nickName),
        normalizeText((row.dept as Record<string, unknown> | undefined)?.deptName),
        normalizeText(row.phonenumber),
        normalizeText(row.status),
        normalizeText(row.createTime),
      ])
    );
  }

  async exportRoles(query: DemoRoleListQuery = {}): Promise<DemoGeneratedFile> {
    const page = await this.listRoles({
      ...query,
      page: 1,
      pageSize: Number.MAX_SAFE_INTEGER,
    });
    return createDelimitedFile(
      'demo-roles.tsv',
      ['角色编号', '角色名称', '权限字符', '显示顺序', '状态', '创建时间'],
      page.items.map((row) => [
        row.roleId,
        row.roleName,
        row.roleKey,
        Number(row.roleSort ?? 0),
        row.status,
        row.createTime,
      ])
    );
  }

  async exportDictTypes(query: DemoDictTypeListQuery = {}): Promise<DemoGeneratedFile> {
    const page = await this.listDictTypes({
      ...query,
      page: 1,
      pageSize: Number.MAX_SAFE_INTEGER,
    });
    return createDelimitedFile(
      'demo-dict-types.tsv',
      ['字典编号', '字典名称', '字典类型', '状态', '备注', '创建时间'],
      page.items.map((row) => [
        row.dictId,
        row.dictName,
        row.dictType,
        row.status,
        row.remark,
        row.createTime,
      ])
    );
  }

  async exportDictData(query: DemoDictDataListQuery = {}): Promise<DemoGeneratedFile> {
    const page = await this.listDictData({
      ...query,
      page: 1,
      pageSize: Number.MAX_SAFE_INTEGER,
    });
    return createDelimitedFile(
      'demo-dict-data.tsv',
      ['字典编码', '字典标签', '字典键值', '字典类型', '排序', '状态', '备注'],
      page.items.map((row) => [
        Number(row.dictCode),
        normalizeText(row.dictLabel),
        normalizeText(row.dictValue),
        normalizeText(row.dictType),
        Number(row.dictSort),
        normalizeText(row.status),
        normalizeText(row.remark),
      ])
    );
  }

  getUserImportTemplate(): DemoGeneratedFile {
    return createDelimitedFile(
      'demo-user-import-template.tsv',
      ['userName', 'nickName', 'deptName', 'phonenumber', 'email', 'status'],
      [['demo_user', '演示用户', '研发中心', '13800000000', 'demo@example.com', '0']]
    );
  }

  private async listUsersByRole(
    roleId: number,
    allocated: boolean,
    payload: DemoRoleUserPayload
  ): Promise<DemoPageResult<Record<string, unknown>>> {
    const page = resolvePage(
      (payload as Record<string, unknown>).page as string | number | undefined,
      1
    );
    const pageSize = resolvePage(
      (payload as Record<string, unknown>).pageSize as string | number | undefined,
      DEFAULT_PAGE_SIZE
    );
    const [users, departments, roles] = await Promise.all([
      this.repository.listUsers(),
      this.repository.listDepartments(),
      this.repository.listRoles(),
    ]);

    const userName = normalizeText((payload as Record<string, unknown>).userName);
    const phonenumber = normalizeText((payload as Record<string, unknown>).phonenumber);

    const rows = users
      .map(normalizeUser)
      .filter((user) => user.roleIds.includes(roleId) === allocated)
      .filter((user) => {
        if (userName && !user.userName.toLowerCase().includes(userName.toLowerCase())) {
          return false;
        }
        if (phonenumber && !normalizeText(user.phonenumber).includes(phonenumber)) {
          return false;
        }
        return true;
      })
      .sort((left, right) => left.userId - right.userId)
      .map((user) =>
        toUserAuthPayload(user, departments.map(normalizeDepartment), roles.map(normalizeRole))
      );

    return paginate(rows, page, pageSize);
  }

  private buildDepartmentSelectTree(departments: DemoDepartment[]): DemoSystemTreeNode[] {
    const treeRows = departments.map((department) => ({
      id: department.deptId,
      parentId: department.parentId,
      label: department.deptName,
      disabled: department.status !== '0',
    }));

    return buildTree(
      treeRows,
      (row, children) => ({
        id: row.id,
        label: row.label,
        disabled: row.disabled,
        ...(children.length ? { children } : {}),
      }),
      0
    );
  }

  private buildMenuSelectTree(menus: DemoMenu[]): DemoSystemTreeNode[] {
    const treeRows = menus.map((menu) => ({
      id: menu.menuId,
      parentId: menu.parentId,
      label: normalizeText(menu.menuName, menu.name),
      disabled: menu.status !== '0',
    }));

    return buildTree(
      treeRows,
      (row, children) => ({
        id: row.id,
        label: row.label,
        disabled: row.disabled,
        ...(children.length ? { children } : {}),
      }),
      0
    );
  }

  private collectDeptIds(departments: DemoDepartment[], deptId: number): number[] {
    const childIds = departments
      .filter((item) => item.parentId === deptId)
      .map((item) => item.deptId);
    return [deptId, ...childIds.flatMap((childId) => this.collectDeptIds(departments, childId))];
  }

  private collectMenuIds(menus: DemoMenu[], menuId: number): number[] {
    const childIds = menus.filter((item) => item.parentId === menuId).map((item) => item.menuId);
    return [menuId, ...childIds.flatMap((childId) => this.collectMenuIds(menus, childId))];
  }

  private async validateRoleIds(roleIds: number[]): Promise<number[]> {
    const roles = (await this.repository.listRoles()).map(normalizeRole);
    const roleIdSet = new Set(roles.map((role) => role.roleId));
    const invalidId = roleIds.find((roleId) => !roleIdSet.has(roleId));
    if (invalidId) {
      throw new DemoSystemAdminError(`角色 ${invalidId} 不存在`, 400);
    }
    return unique(roleIds);
  }

  private async validatePostIds(postIds: number[]): Promise<number[]> {
    const posts = (await this.repository.listPosts()).map(normalizePost);
    const postIdSet = new Set(posts.map((post) => post.postId));
    const invalidId = postIds.find((postId) => !postIdSet.has(postId));
    if (invalidId) {
      throw new DemoSystemAdminError(`岗位 ${invalidId} 不存在`, 400);
    }
    return unique(postIds);
  }

  private async validateMenuIds(menuIds: number[]): Promise<number[]> {
    const menus = (await this.repository.listMenus()).map(normalizeMenu);
    const menuIdSet = new Set(menus.map((menu) => menu.menuId));
    const invalidId = menuIds.find((menuId) => !menuIdSet.has(menuId));
    if (invalidId) {
      throw new DemoSystemAdminError(`菜单 ${invalidId} 不存在`, 400);
    }
    return unique(menuIds);
  }

  private async validateDeptIds(deptIds: number[]): Promise<number[]> {
    const departments = (await this.repository.listDepartments()).map(normalizeDepartment);
    const deptIdSet = new Set(departments.map((department) => department.deptId));
    const invalidId = deptIds.find((deptId) => !deptIdSet.has(deptId));
    if (invalidId) {
      throw new DemoSystemAdminError(`部门 ${invalidId} 不存在`, 400);
    }
    return unique(deptIds);
  }

  private async getAssignableRoles(): Promise<DemoRole[]> {
    return (await this.repository.listRoles())
      .map(normalizeRole)
      .sort(
        (left, right) =>
          Number(left.roleSort) - Number(right.roleSort) || left.roleId - right.roleId
      );
  }

  private async getAssignablePosts(): Promise<DemoPost[]> {
    return (await this.repository.listPosts())
      .map(normalizePost)
      .sort((left, right) => left.postSort - right.postSort || left.postId - right.postId);
  }

  private async syncAccountsByRole(roleId: number): Promise<void> {
    const users = (await this.repository.listUsers()).map(normalizeUser);
    const relatedUsers = users.filter((user) => user.roleIds.includes(roleId));
    await Promise.all(relatedUsers.map((user) => this.syncAccountByUser(user)));
  }

  private async syncAccountsByUserId(userId: number): Promise<void> {
    const user = await this.repository.getUser(userId);
    if (!user) {
      return;
    }
    await this.syncAccountByUser(normalizeUser(user));
  }

  private async syncAccountByUser(user: DemoSystemUser, password?: string): Promise<void> {
    const [existingAccount, roles] = await Promise.all([
      this.repository.getAccountByUsername(user.userName),
      this.repository.listRoles(),
    ]);
    const currentRoles = roles
      .map(normalizeRole)
      .filter((role) => user.roleIds.includes(role.roleId));
    const account: DemoAccount = {
      username: user.userName,
      password:
        password ??
        normalizeText(user.password) ??
        existingAccount?.password ??
        DEFAULT_USER_PASSWORD,
      userId: user.userId,
      roleIds: user.roleIds,
      roles: currentRoles.map((role) => role.roleKey),
      permissions: unique(currentRoles.flatMap((role) => role.permissions ?? [])),
      token: existingAccount?.token,
      user: {
        userId: user.userId,
        deptId: user.deptId,
        userName: user.userName,
        nickName: user.nickName,
        status: user.status,
        sex: user.sex,
        phonenumber: user.phonenumber,
        email: user.email,
        avatar: user.avatar,
        remark: user.remark,
        admin: user.userId === 1,
      },
    };

    await this.repository.saveAccount(account);
  }

  private async requireUser(userId: number): Promise<DemoSystemUser> {
    const user = await this.repository.getUser(userId);
    if (!user) {
      throw new DemoSystemAdminError('用户不存在', 404);
    }
    return user;
  }

  private async requireRole(roleId: number): Promise<DemoRole> {
    const role = await this.repository.getRole(roleId);
    if (!role) {
      throw new DemoSystemAdminError('角色不存在', 404);
    }
    return role;
  }

  private async requireMenu(menuId: number): Promise<DemoMenu> {
    const menu = await this.repository.getMenu(menuId);
    if (!menu) {
      throw new DemoSystemAdminError('菜单不存在', 404);
    }
    return menu;
  }

  private async requireDepartment(deptId: number): Promise<DemoDepartment> {
    const department = await this.repository.getDepartment(deptId);
    if (!department) {
      throw new DemoSystemAdminError('部门不存在', 404);
    }
    return department;
  }

  private async requireDictType(dictId: number): Promise<DemoDictType> {
    const dictType = await this.repository.getDictType(dictId);
    if (!dictType) {
      throw new DemoSystemAdminError('字典类型不存在', 404);
    }
    return dictType;
  }

  private async requireDictData(dictCode: number): Promise<DemoDictData> {
    const dictData = await this.repository.getDictData(dictCode);
    if (!dictData) {
      throw new DemoSystemAdminError('字典数据不存在', 404);
    }
    return dictData;
  }
}
