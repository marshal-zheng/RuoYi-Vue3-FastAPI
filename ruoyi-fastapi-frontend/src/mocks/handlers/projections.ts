import type { MockDepartment, MockDictData, MockMenu } from '../data';
import { MOCK_REFERENCE_DATETIME } from '../data';

export interface DeptTreeNode {
  id: number;
  label: string;
  children?: DeptTreeNode[];
}

function routeNameFromPath(path?: string | null) {
  return (path ?? '')
    .replace(/^\/+/, '')
    .split('/')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

function routeNameFromMenu(menu: MockMenu) {
  return menu.routeName || routeNameFromPath(menu.path) || `Menu${menu.menuId}`;
}

function routeIconFromMenu(menu: MockMenu) {
  if (menu.icon) {
    return menu.icon;
  }
  if (menu.path === 'role') return 'peoples';
  if (menu.path === 'menu') return 'tree-table';
  if (menu.path === 'project') return 'project';
  return 'user';
}

export function buildDeptTree(departments: MockDepartment[]): DeptTreeNode[] {
  const byParent = new Map<number, MockDepartment[]>();
  departments.forEach((department) => {
    const siblings = byParent.get(department.parentId) ?? [];
    siblings.push(department);
    byParent.set(department.parentId, siblings);
  });

  const toNode = (department: MockDepartment): DeptTreeNode => {
    const children = (byParent.get(department.deptId) ?? []).map(toNode);
    return {
      id: department.deptId,
      label: department.deptName,
      ...(children.length > 0 ? { children } : {}),
    };
  };

  return (byParent.get(0) ?? []).map(toNode);
}

export function projectDictData(dict: MockDictData, index: number) {
  return {
    dictCode: dict.id,
    dictLabel: dict.dictLabel,
    dictValue: dict.dictValue,
    dictType: dict.dictType,
    cssClass: '',
    listClass: index === 0 ? 'primary' : 'default',
    isDefault: index === 0 ? 'Y' : 'N',
    status: dict.status,
    createBy: 'mock',
    createTime: MOCK_REFERENCE_DATETIME,
    remark: '',
  };
}

export function buildSystemRoutes(menus: MockMenu[]) {
  const childMenusByParent = new Map<number, MockMenu[]>();
  menus.forEach((menu) => {
    if (menu.parentId === 0) return;
    const siblings = childMenusByParent.get(menu.parentId) ?? [];
    siblings.push(menu);
    childMenusByParent.set(menu.parentId, siblings);
  });

  return menus
    .filter((menu) => menu.parentId === 0 && menu.menuType === 'M')
    .map((menu) => ({
      name: routeNameFromMenu(menu),
      path: menu.path ?? '/',
      hidden: false,
      redirect: 'noRedirect',
      component: 'Layout',
      alwaysShow: true,
      meta: {
        title: menu.menuName,
        icon: menu.icon || 'system',
        noCache: false,
        link: null,
      },
      children: (childMenusByParent.get(menu.menuId) ?? []).map((child) => ({
        name: routeNameFromMenu(child),
        path: child.path ?? '',
        hidden: false,
        component: child.component || `system/${child.path}/index`,
        meta: {
          title: child.menuName,
          icon: routeIconFromMenu(child),
          noCache: false,
          link: null,
        },
      })),
    }));
}
