export type MenuRecord = MenuItem & MenuModel;
import type { GetSystemMenuListSystemMenuListGetData, MenuModel } from '@/api/_generated/types.gen';
import request from '@/utils/request';
import type { HttpCollection } from '@/types/http-contract';

export interface MenuItem {
  menuId: number;
  parentId: number;
  menuName: string;
  [key: string]: unknown;
}

export interface MenuTreeNode {
  id: number;
  label: string;
  children?: MenuTreeNode[];
}

// 查询菜单列表
export function listMenu(query?: NonNullable<GetSystemMenuListSystemMenuListGetData['query']>) {
  return request<HttpCollection<MenuItem>>({
    url: '/system/menu/list',
    method: 'get',
    params: query,
  });
}

// 查询菜单详细
export function getMenu(menuId: number | string) {
  return request<MenuRecord>({
    url: '/system/menu/' + menuId,
    method: 'get',
    feedback: { mode: 'auto' },
  });
}

// 查询菜单下拉树结构
export function treeselect() {
  return request<HttpCollection<MenuTreeNode>>({
    url: '/system/menu/treeselect',
    method: 'get',
  });
}

// 根据角色ID查询菜单下拉树结构
export function roleMenuTreeselect(roleId: number | string) {
  return request<{ menus: MenuTreeNode[]; checkedKeys: number[] }>({
    url: '/system/menu/roleMenuTreeselect/' + roleId,
    method: 'get',
  });
}

// 新增菜单
export function addMenu(data: MenuModel) {
  return request<MenuRecord>({
    url: '/system/menu',
    method: 'post',
    data: data,
    feedback: { mode: 'auto', key: 'system.menu.create' },
  });
}

// 修改菜单
export function updateMenu(data: MenuModel) {
  return request<MenuRecord>({
    url: '/system/menu',
    method: 'put',
    data: data,
    feedback: { mode: 'auto', key: 'system.menu.update' },
  });
}

// 删除菜单
export function delMenu(menuId: number | string) {
  return request<null>({
    url: '/system/menu/' + menuId,
    method: 'delete',
    feedback: { mode: 'auto', key: 'system.menu.delete' },
  });
}
