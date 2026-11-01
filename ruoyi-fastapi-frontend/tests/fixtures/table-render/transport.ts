import { reactive } from 'vue';
import type { AxiosAdapter } from 'axios';
import { mockRemark } from '@/mocks/data/remark';
import { http } from '@/utils/http';
export const probe = reactive({
  reads: 0,
  writes: 0,
  failNext: false,
  requests: [] as { method: string; url: string; params: unknown; data: unknown }[],
});
const created = '2026-11-01 08:00:00';
let configs = Array.from({ length: 26 }, (_, index) => ({
  configId: index + 1,
  configName: `参数 ${index + 1}`,
  configKey: `system.config.${index + 1}`,
  configValue: `value-${index + 1}`,
  configType: index % 2 ? 'N' : 'Y',
  remark: mockRemark(`参数 ${index + 1} 的业务备注`, `config${index + 1}`),
  remarkText: `参数 ${index + 1} 的业务备注`,
  createTime: created,
}));
let roles = Array.from({ length: 24 }, (_, index) => ({
  roleId: index + 1,
  roleName: index ? `测试角色 ${index + 1}` : '超级管理员',
  roleKey: index ? `role${index + 1}` : 'admin',
  roleSort: index,
  status: index % 3 ? '0' : '1',
  createTime: created,
}));
let menus = [
  {
    menuId: 1,
    parentId: 0,
    menuName: '系统管理',
    menuType: 'M',
    path: 'system',
    icon: 'system',
    orderNum: 1,
    perms: '',
    component: '',
    status: '0',
    createTime: created,
  },
  {
    menuId: 2,
    parentId: 1,
    menuName: '参数配置',
    menuType: 'C',
    path: 'config',
    icon: 'edit',
    orderNum: 1,
    perms: 'system:config:list',
    component: 'system/config/index',
    status: '0',
    createTime: created,
  },
  {
    menuId: 3,
    parentId: 2,
    menuName: '查询参数',
    menuType: 'F',
    path: '',
    icon: '',
    orderNum: 1,
    perms: 'system:config:query',
    component: '',
    status: '0',
    createTime: created,
  },
];
const assigned = new Set<number>();
let departments = [
  {
    deptId: 1,
    parentId: 0,
    deptName: '总部',
    orderNum: 1,
    status: '0',
    createTime: '2026-11-01 08:00:00',
  },
  {
    deptId: 2,
    parentId: 1,
    deptName: '研发部',
    orderNum: 2,
    status: '0',
    createTime: '2026-11-01 08:00:00',
  },
  {
    deptId: 3,
    parentId: 2,
    deptName: '平台组',
    orderNum: 3,
    status: '1',
    createTime: '2026-11-01 08:00:00',
  },
];
const users = Array.from({ length: 34 }, (_, index) => ({
  userId: index + 1,
  userName: `user-${index + 1}`,
  nickName: `用户 ${index + 1}`,
  phonenumber: `1380000${String(index).padStart(4, '0')}`,
  email: `user${index}@example.test`,
  status: '0',
  createTime: '2026-11-01 08:00:00',
}));
// Fixture-only Axios adapter: all requests terminate here, including unsupported ones.
const adapter: AxiosAdapter = async (config) => {
  const url = config.url ?? '';
  const method = config.method?.toLowerCase() ?? 'get';
  if (method === 'get') {
    probe.reads++;
    if (probe.failNext) {
      probe.failNext = false;
      throw new Error('离线试点模拟读取失败');
    }
  } else probe.writes++;
  const params = config.params ?? {};
  let body = config.data;
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body);
    } catch {
      body = Object.fromEntries(new URLSearchParams(body));
    }
  }
  probe.requests.push({ method, url, params, data: body });
  await new Promise((resolve) => setTimeout(resolve, method === 'get' ? 60 : 180));
  let data: unknown;
  if (url.endsWith('/export')) {
    data = new Blob(['Offline fixture export'], { type: 'application/octet-stream' });
  } else if (url === '/system/config/list' || url === '/system/role/list') {
    const rows = url.includes('/config/') ? configs : roles;
    const name = url.includes('/config/') ? 'configName' : 'roleName';
    const key = url.includes('/config/') ? 'configKey' : 'roleKey';
    const filtered = rows.filter(
      (row) =>
        (!params[name] || String(Reflect.get(row, name)).includes(params[name])) &&
        (!params[key] || String(Reflect.get(row, key)).includes(params[key])) &&
        (!params.status || Reflect.get(row, 'status') === params.status) &&
        (!params.configType || Reflect.get(row, 'configType') === params.configType)
    );
    const page = Number(params.page ?? 1),
      pageSize = Number(params.pageSize ?? 10);
    data = {
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      total: filtered.length,
      page,
      pageSize,
    };
  } else if (url === '/system/config/refreshCache') {
    data = { status: 'refreshed' };
  } else if (method === 'delete' && /^\/system\/(config|role|menu)\/[\d,]+$/.test(url)) {
    const ids = url.split('/').at(-1)!.split(',').map(Number);
    if (url.includes('/config/')) configs = configs.filter((row) => !ids.includes(row.configId));
    if (url.includes('/role/')) roles = roles.filter((row) => !ids.includes(row.roleId));
    if (url.includes('/menu/')) menus = menus.filter((row) => !ids.includes(row.menuId));
    data = null;
  } else if (url === '/system/role/changeStatus') {
    roles = roles.map((row) =>
      row.roleId === body.roleId ? { ...row, status: body.status } : row
    );
    data = null;
  } else if (url === '/system/menu/list') {
    data = {
      items: menus.filter(
        (row) =>
          (!params.menuName || row.menuName.includes(params.menuName)) &&
          (!params.status || row.status === params.status)
      ),
    };
  } else if (url === '/system/menu/treeselect') {
    data = { items: [{ id: 1, label: '系统管理', children: [{ id: 2, label: '参数配置' }] }] };
  } else if (/^\/system\/menu\/roleMenuTreeselect\/\d+$/.test(url)) {
    data = { menus: [{ id: 1, label: '系统管理' }], checkedKeys: [] };
  } else if (method === 'get' && /^\/system\/(config|role|menu)\/\d+$/.test(url)) {
    const id = Number(url.split('/').at(-1));
    data = url.includes('/config/')
      ? configs.find((row) => row.configId === id)
      : url.includes('/role/')
        ? roles.find((row) => row.roleId === id)
        : menus.find((row) => row.menuId === id);
  } else if (url === '/system/role/authUser/unallocatedList') {
    const filtered = users.filter(
      (user) =>
        !assigned.has(user.userId) &&
        (!params.userName || user.userName.includes(params.userName)) &&
        (!params.phonenumber || user.phonenumber.includes(params.phonenumber))
    );
    const page = Number(params.page ?? 1),
      size = Number(params.pageSize ?? 10);
    data = {
      items: filtered.slice((page - 1) * size, page * size),
      total: filtered.length,
      page,
      pageSize: size,
    };
  } else if (url === '/system/role/authUser/selectAll') {
    const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data;
    body.userIds.forEach((id: number) => assigned.add(id));
    data = null;
  } else if (url === '/system/dept/list') {
    data = {
      items: departments.filter(
        (dept) =>
          (!params.deptName || dept.deptName.includes(params.deptName)) &&
          (!params.status || dept.status === params.status)
      ),
    };
  } else if (method === 'delete' && /^\/system\/dept\/\d+$/.test(url)) {
    departments = departments.filter((dept) => dept.deptId !== Number(url.split('/').at(-1)));
    data = null;
  } else if (url.includes('/dict/'))
    data = {
      items: url.includes('sys_yes_no')
        ? [
            { dictLabel: '是', dictValue: 'Y', label: '是', value: 'Y' },
            { dictLabel: '否', dictValue: 'N', label: '否', value: 'N' },
          ]
        : [
            { dictLabel: '正常', dictValue: '0', label: '正常', value: '0' },
            { dictLabel: '停用', dictValue: '1', label: '停用', value: '1' },
          ],
    };
  else throw new Error(`离线试点未提供此请求：${method} ${url}`);
  return { data, status: 200, statusText: 'OK', headers: {}, config };
};
// HttpClient merges its own axiosConfig before each request, so changing Axios
// defaults alone cannot replace the configured session transport.
http.extendTransforms({ beforeRequest: (config) => ({ ...config, adapter }) });
