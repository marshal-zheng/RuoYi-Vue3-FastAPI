import type { AIContextScopeDefinition } from '@zxio/zxui/ai-context';

// Pure metadata only. The generator imports this file without mounting Vue or reading values.
export const aiContextDefinitions = {
  user: {
    id: 'system.user',
    permissions: {
      mode: 'any',
      values: ['system:user:add', 'system:user:edit'],
    },
    purposes: {
      remark: {
        label: '用户备注',
        defaultContextIds: ['deptName', 'postNames', 'roleNames', 'status'],
        selectableContextIds: ['userName', 'nickName', 'phonenumber', 'email'],
      },
    },
    items: [
      { id: 'deptName', label: '部门名称', sensitivity: 'public' },
      { id: 'postNames', label: '岗位', sensitivity: 'public' },
      { id: 'roleNames', label: '角色', sensitivity: 'public' },
      { id: 'status', label: '状态', sensitivity: 'public' },
      {
        id: 'userName',
        label: '用户账号',
        sensitivity: 'personal',
        kind: 'other',
      },
      {
        id: 'nickName',
        label: '用户昵称',
        sensitivity: 'personal',
        kind: 'other',
      },
      {
        id: 'phonenumber',
        label: '手机号码',
        sensitivity: 'personal',
        kind: 'phone',
      },
      { id: 'email', label: '邮箱', sensitivity: 'personal', kind: 'email' },
      { id: 'password', label: '密码', sensitivity: 'secret' },
    ],
  },
  role: {
    id: 'system.role',
    permissions: {
      mode: 'any',
      values: ['system:role:add', 'system:role:edit'],
    },
    purposes: {
      remark: {
        label: '角色备注',
        defaultContextIds: ['roleName', 'roleKey', 'menuNames', 'status'],
        selectableContextIds: [],
      },
    },
    items: [
      { id: 'roleName', label: '角色名称', sensitivity: 'public' },
      { id: 'roleKey', label: '权限字符', sensitivity: 'public' },
      { id: 'menuNames', label: '菜单权限', sensitivity: 'public' },
      { id: 'status', label: '状态', sensitivity: 'public' },
    ],
  },
  post: {
    id: 'system.post',
    permissions: {
      mode: 'any',
      values: ['system:post:add', 'system:post:edit'],
    },
    purposes: {
      remark: {
        label: '岗位备注',
        defaultContextIds: ['postName', 'postCode', 'status'],
        selectableContextIds: [],
      },
    },
    items: [
      { id: 'postName', label: '岗位名称', sensitivity: 'public' },
      { id: 'postCode', label: '岗位编码', sensitivity: 'public' },
      { id: 'status', label: '状态', sensitivity: 'public' },
    ],
  },
  dictType: {
    id: 'system.dict.type',
    permissions: {
      mode: 'any',
      values: ['system:dict:add', 'system:dict:edit'],
    },
    purposes: {
      remark: {
        label: '字典类型备注',
        defaultContextIds: ['dictName', 'dictType', 'status'],
        selectableContextIds: [],
      },
    },
    items: [
      { id: 'dictName', label: '字典名称', sensitivity: 'public' },
      { id: 'dictType', label: '字典类型', sensitivity: 'public' },
      { id: 'status', label: '状态', sensitivity: 'public' },
    ],
  },
  dictData: {
    id: 'system.dict.data',
    permissions: {
      mode: 'any',
      values: ['system:dict:add', 'system:dict:edit'],
    },
    purposes: {
      remark: {
        label: '字典数据备注',
        defaultContextIds: ['dictName', 'dictType', 'dictLabel', 'dictValue', 'status'],
        selectableContextIds: [],
      },
    },
    items: [
      { id: 'dictName', label: '字典名称', sensitivity: 'public' },
      { id: 'dictType', label: '字典类型', sensitivity: 'public' },
      { id: 'dictLabel', label: '字典标签', sensitivity: 'public' },
      { id: 'dictValue', label: '字典键值', sensitivity: 'public' },
      { id: 'status', label: '状态', sensitivity: 'public' },
    ],
  },
  config: {
    id: 'system.config',
    permissions: {
      mode: 'any',
      values: ['system:config:add', 'system:config:edit'],
    },
    purposes: {
      remark: {
        label: '参数备注',
        defaultContextIds: ['configName', 'configKey', 'configType'],
        selectableContextIds: [],
      },
    },
    items: [
      { id: 'configName', label: '参数名称', sensitivity: 'public' },
      { id: 'configKey', label: '参数键名', sensitivity: 'public' },
      { id: 'configType', label: '系统内置', sensitivity: 'public' },
      { id: 'configValue', label: '参数键值', sensitivity: 'secret' },
    ],
  },
  genTable: {
    id: 'tool.gen.table',
    permissions: { mode: 'any', values: ['tool:gen:edit'] },
    purposes: {
      remark: {
        label: '代码生成表备注',
        defaultContextIds: ['tableName', 'tableComment', 'className'],
        selectableContextIds: ['functionAuthor'],
      },
    },
    items: [
      { id: 'tableName', label: '表名称', sensitivity: 'public' },
      { id: 'tableComment', label: '表描述', sensitivity: 'public' },
      { id: 'className', label: '实体类名称', sensitivity: 'public' },
      {
        id: 'functionAuthor',
        label: '作者',
        sensitivity: 'personal',
        kind: 'other',
      },
    ],
  },
} as const satisfies Record<string, AIContextScopeDefinition>;
