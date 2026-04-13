import { SystemRepository } from '@/demo/repositories';
import type { DemoDepartment, DemoDictData, DemoMenu } from '@/demo/scenarios';

interface DemoRouteMeta {
  title: string;
  icon?: string;
  noCache?: boolean;
  link?: string | null;
  [key: string]: unknown;
}

export interface DemoRouteRecord {
  name: string;
  path: string;
  hidden: boolean;
  component: string;
  redirect?: string;
  alwaysShow?: boolean;
  meta: DemoRouteMeta;
  children?: DemoRouteRecord[];
}

export interface DemoTreeNode {
  id: number;
  label: string;
  disabled: boolean;
  children?: DemoTreeNode[];
}

function isHttpPath(path: string): boolean {
  return /^https?:\/\//i.test(path);
}

function normalizeTopLevelPath(menu: DemoMenu): string {
  if (
    menu.parentId !== 0 ||
    menu.path === '/' ||
    menu.path.startsWith('/') ||
    isHttpPath(menu.path)
  ) {
    return menu.path;
  }

  return `/${menu.path}`;
}

function sortMenus(left: DemoMenu, right: DemoMenu): number {
  return left.orderNum - right.orderNum || left.menuId - right.menuId;
}

function sortDepartments(left: DemoDepartment, right: DemoDepartment): number {
  return left.orderNum - right.orderNum || left.deptId - right.deptId;
}

function createMenuMeta(menu: DemoMenu): DemoRouteMeta {
  const rawMeta = (menu.meta ?? {}) as Record<string, unknown>;
  return {
    ...rawMeta,
    title: String(rawMeta.title ?? menu.name),
    icon: rawMeta.icon as string | undefined,
    noCache: Boolean(rawMeta.noCache ?? false),
    link: (rawMeta.link as string | null | undefined) ?? (isHttpPath(menu.path) ? menu.path : null),
  };
}

function createRoute(menu: DemoMenu, children: DemoRouteRecord[]): DemoRouteRecord {
  const route: DemoRouteRecord = {
    name: menu.name,
    path: normalizeTopLevelPath(menu),
    hidden: menu.visible === '1',
    component:
      menu.component || (menu.parentId === 0 ? 'Layout' : children.length ? 'ParentView' : ''),
    meta: createMenuMeta(menu),
  };

  if (menu.redirect || children.length) {
    route.redirect = menu.redirect ?? 'noRedirect';
  }

  if (children.length) {
    route.alwaysShow = children.length > 1;
    route.children = children;
  }

  return route;
}

function buildMenuRoutes(menus: DemoMenu[], parentId = 0): DemoRouteRecord[] {
  return menus
    .filter((menu) => menu.parentId === parentId)
    .sort(sortMenus)
    .map((menu) => createRoute(menu, buildMenuRoutes(menus, menu.menuId)));
}

function createDeptNode(department: DemoDepartment, children: DemoTreeNode[]): DemoTreeNode {
  const node: DemoTreeNode = {
    id: department.deptId,
    label: department.deptName,
    disabled: department.status !== '0',
  };

  if (children.length) {
    node.children = children;
  }

  return node;
}

function buildDepartmentTree(departments: DemoDepartment[], parentId = 0): DemoTreeNode[] {
  return departments
    .filter((department) => department.parentId === parentId)
    .sort(sortDepartments)
    .map((department) =>
      createDeptNode(department, buildDepartmentTree(departments, department.deptId))
    );
}

function normalizeDictData(dict: DemoDictData): DemoDictData & { dictCode: number } {
  return {
    ...dict,
    dictCode: dict.id,
  };
}

export class DemoSystemService {
  constructor(private readonly systemRepository: SystemRepository) {}

  async getRouters(roleKeys: string[]): Promise<DemoRouteRecord[]> {
    const menus = await this.systemRepository.listMenus();
    const accessibleMenus = menus.filter(
      (menu) =>
        menu.status === '0' &&
        (roleKeys.includes('admin') ||
          menu.roles.length === 0 ||
          menu.roles.some((role) => roleKeys.includes(role)))
    );

    return buildMenuRoutes(accessibleMenus);
  }

  async getDictsByType(dictType: string): Promise<Array<DemoDictData & { dictCode: number }>> {
    const dicts = await this.systemRepository.listDictsByType(dictType);
    return dicts.filter((dict) => dict.status === '0').map(normalizeDictData);
  }

  async getDepartmentTree(): Promise<DemoTreeNode[]> {
    return buildDepartmentTree(await this.systemRepository.listDepartments());
  }
}
