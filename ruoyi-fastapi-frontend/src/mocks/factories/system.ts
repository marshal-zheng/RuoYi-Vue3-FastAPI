// @ts-nocheck
import { fakerZH_CN as faker } from '@faker-js/faker'

export interface DeptNode {
  id: number
  label: string
  children?: DeptNode[]
}

type DictDefinition = {
  label: string
  value: string
  listClass?: string
  remark?: string
}

export interface RouteChildConfig {
  name: string
  path: string
  component: string
  title: string
  icon: string
}

let deptSeed = 100

function nextDeptId() {
  return deptSeed++
}

function formatTitle(level: number) {
  const suffix = level === 0 ? '集团' : '部门'
  return `${faker.company.name()}${suffix}`
}

function createDeptNode(level = 0, maxLevel = 2): DeptNode {
  const node: DeptNode = {
    id: nextDeptId(),
    label: formatTitle(level)
  }

  if (level < maxLevel) {
    const childCount = faker.number.int({ min: 1, max: 3 })
    node.children = Array.from({ length: childCount }, () =>
      createDeptNode(level + 1, maxLevel)
    )
  }

  return node
}

export function createDeptTree(rootCount = 1, maxLevel = 2): DeptNode[] {
  deptSeed = 100
  return Array.from({ length: rootCount }, () => createDeptNode(0, maxLevel))
}

const BASE_DICTS: Record<string, DictDefinition[]> = {
  sys_user_sex: [
    { label: '男', value: '0', remark: '性别男' },
    { label: '女', value: '1', remark: '性别女' },
    { label: '未知', value: '2', remark: '性别未知' }
  ],
  sys_normal_disable: [
    { label: '正常', value: '0', listClass: 'primary', remark: '正常状态' },
    { label: '停用', value: '1', listClass: 'danger', remark: '停用状态' }
  ]
}

function formatDateTime(date: Date) {
  const pad = (value: number) => value.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export function createDictData(dictType: string) {
  const dicts = BASE_DICTS[dictType] ?? []
  return dicts.map((item, idx) => ({
    dictCode: idx + 1,
    dictLabel: item.label,
    dictValue: item.value,
    dictType,
    cssClass: '',
    listClass: item.listClass ?? 'default',
    isDefault: idx === 0 ? 'Y' : 'N',
    status: '0',
    createBy: 'mock',
    createTime: formatDateTime(faker.date.recent({ days: 30 })),
    remark: item.remark ?? ''
  }))
}

const DEFAULT_ROUTE_CHILDREN: RouteChildConfig[] = [
  {
    name: 'User',
    path: 'user',
    component: 'system/user/index',
    title: '用户管理',
    icon: 'user'
  },
  {
    name: 'Role',
    path: 'role',
    component: 'system/role/index',
    title: '角色管理',
    icon: 'peoples'
  },
  {
    name: 'Menu',
    path: 'menu',
    component: 'system/menu/index',
    title: '菜单管理',
    icon: 'tree-table'
  }
]

export function createSystemRoutes(
  children: RouteChildConfig[] = DEFAULT_ROUTE_CHILDREN
) {
  return [
    {
      name: 'System',
      path: '/system',
      hidden: false,
      redirect: 'noRedirect',
      component: 'Layout',
      alwaysShow: true,
      meta: {
        title: '系统管理',
        icon: 'system',
        noCache: false,
        link: null
      },
      children: children.map(child => ({
        name: child.name,
        path: child.path,
        hidden: false,
        component: child.component,
        meta: {
          title: child.title,
          icon: child.icon,
          noCache: false,
          link: null
        }
      }))
    }
  ]
}
