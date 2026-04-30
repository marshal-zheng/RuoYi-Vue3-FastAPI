import { DEMO_SCENARIO_SCHEMA_VERSION } from './schema';

type JsonSchema = Record<string, unknown>;

const stringSchema = { type: 'string' } as const;
const numberSchema = { type: 'number' } as const;
const booleanSchema = { type: 'boolean' } as const;
const recordSchema = { type: 'object', additionalProperties: true } as const;

function objectSchema(
  required: readonly string[],
  properties: Record<string, JsonSchema>,
  additionalProperties = true
): JsonSchema {
  return {
    type: 'object',
    required,
    properties,
    additionalProperties,
  };
}

function arraySchema(items: JsonSchema, minItems = 0): JsonSchema {
  return {
    type: 'array',
    minItems,
    items,
  };
}

const demoAccountSchema = objectSchema(
  ['username', 'password', 'userId', 'roleIds', 'roles', 'permissions', 'user'],
  {
    username: stringSchema,
    password: stringSchema,
    userId: numberSchema,
    roleIds: arraySchema(numberSchema),
    roles: arraySchema(stringSchema),
    permissions: arraySchema(stringSchema),
    token: stringSchema,
    user: recordSchema,
  }
);

const demoRoleSchema = objectSchema(['roleId', 'roleKey', 'roleName', 'menuIds', 'permissions'], {
  roleId: numberSchema,
  roleKey: stringSchema,
  roleName: stringSchema,
  menuIds: arraySchema(numberSchema),
  permissions: arraySchema(stringSchema),
  roleSort: numberSchema,
  dataScope: stringSchema,
  menuCheckStrictly: booleanSchema,
  deptCheckStrictly: booleanSchema,
  deptIds: arraySchema(numberSchema),
  status: { enum: ['0', '1'] },
  remark: stringSchema,
  createTime: stringSchema,
  updateTime: stringSchema,
});

const demoPermissionSchema = objectSchema(['id', 'code', 'label'], {
  id: stringSchema,
  code: stringSchema,
  label: stringSchema,
});

const demoMenuSchema = objectSchema(
  ['menuId', 'parentId', 'name', 'path', 'orderNum', 'visible', 'status', 'roles'],
  {
    menuId: numberSchema,
    parentId: numberSchema,
    name: stringSchema,
    menuName: stringSchema,
    routeName: stringSchema,
    path: stringSchema,
    component: stringSchema,
    redirect: stringSchema,
    orderNum: numberSchema,
    visible: { enum: ['0', '1'] },
    status: { enum: ['0', '1'] },
    roles: arraySchema(stringSchema),
    perms: stringSchema,
    menuType: { enum: ['M', 'C', 'F'] },
    icon: stringSchema,
    isFrame: { enum: ['0', '1'] },
    isCache: { enum: ['0', '1'] },
    query: stringSchema,
    createTime: stringSchema,
    updateTime: stringSchema,
    remark: stringSchema,
    meta: recordSchema,
  }
);

const demoDictTypeSchema = objectSchema(['dictId', 'dictName', 'dictType', 'status'], {
  dictId: numberSchema,
  dictName: stringSchema,
  dictType: stringSchema,
  status: { enum: ['0', '1'] },
  remark: stringSchema,
  createTime: stringSchema,
  updateTime: stringSchema,
});

const demoDictDataSchema = objectSchema(
  ['id', 'dictType', 'dictLabel', 'dictValue', 'dictSort', 'status'],
  {
    id: numberSchema,
    dictId: numberSchema,
    dictType: stringSchema,
    dictLabel: stringSchema,
    dictValue: stringSchema,
    dictSort: numberSchema,
    status: { enum: ['0', '1'] },
    cssClass: stringSchema,
    listClass: stringSchema,
    isDefault: { enum: ['Y', 'N'] },
    remark: stringSchema,
    createTime: stringSchema,
    updateTime: stringSchema,
  }
);

const demoDepartmentSchema = objectSchema(
  ['deptId', 'parentId', 'deptName', 'orderNum', 'status'],
  {
    deptId: numberSchema,
    parentId: numberSchema,
    ancestors: stringSchema,
    deptName: stringSchema,
    orderNum: numberSchema,
    status: { enum: ['0', '1'] },
    leader: stringSchema,
    phone: stringSchema,
    email: stringSchema,
    createTime: stringSchema,
    updateTime: stringSchema,
  }
);

const demoPostSchema = objectSchema(['postId', 'postCode', 'postName', 'postSort', 'status'], {
  postId: numberSchema,
  postCode: stringSchema,
  postName: stringSchema,
  postSort: numberSchema,
  status: { enum: ['0', '1'] },
  remark: stringSchema,
  createTime: stringSchema,
  updateTime: stringSchema,
});

const demoSystemUserSchema = objectSchema(
  ['userId', 'deptId', 'userName', 'nickName', 'status', 'roleIds', 'postIds'],
  {
    userId: numberSchema,
    deptId: numberSchema,
    userName: stringSchema,
    nickName: stringSchema,
    userType: stringSchema,
    email: stringSchema,
    phonenumber: stringSchema,
    sex: { enum: ['0', '1', '2'] },
    avatar: stringSchema,
    password: stringSchema,
    status: { enum: ['0', '1'] },
    delFlag: { enum: ['0', '2'] },
    loginIp: stringSchema,
    loginDate: stringSchema,
    createBy: stringSchema,
    createTime: stringSchema,
    updateBy: stringSchema,
    updateTime: stringSchema,
    remark: stringSchema,
    roleIds: arraySchema(numberSchema),
    postIds: arraySchema(numberSchema),
  }
);

const demoProjectSchema = objectSchema(
  ['projectId', 'projectName', 'status', 'createTime', 'updateTime'],
  {
    projectId: numberSchema,
    projectName: stringSchema,
    status: { enum: ['0', '1'] },
    createTime: stringSchema,
    updateTime: stringSchema,
    remark: stringSchema,
    owner: stringSchema,
  }
);

const demoProjectVersionSchema = objectSchema(
  ['versionId', 'projectId', 'versionName', 'locked', 'status', 'createTime', 'updateTime'],
  {
    versionId: numberSchema,
    projectId: numberSchema,
    versionName: stringSchema,
    locked: booleanSchema,
    status: { enum: ['0', '1'] },
    createTime: stringSchema,
    updateTime: stringSchema,
    remark: stringSchema,
  }
);

const demoTopologySchema = objectSchema(['id', 'projectId', 'graph', 'updateTime'], {
  id: stringSchema,
  projectId: numberSchema,
  versionId: numberSchema,
  graph: recordSchema,
  updateTime: stringSchema,
});

const demoSimulationSessionSchema = objectSchema(
  ['sessionId', 'projectId', 'versionId', 'status', 'createTime', 'updateTime'],
  {
    sessionId: stringSchema,
    projectId: numberSchema,
    versionId: numberSchema,
    status: stringSchema,
    createTime: stringSchema,
    updateTime: stringSchema,
  }
);

const demoSimulationMessageSchema = objectSchema(['id', 'sessionId', 'timestamp'], {
  id: stringSchema,
  sessionId: stringSchema,
  timestamp: stringSchema,
});

const demoSimulationBandwidthSchema = objectSchema(['id', 'sessionId', 'portId', 'timestamp'], {
  id: stringSchema,
  sessionId: stringSchema,
  portId: stringSchema,
  timestamp: stringSchema,
});

const demoSimulationAlarmSchema = objectSchema(['alarmId', 'sessionId', 'timestamp', 'severity'], {
  alarmId: stringSchema,
  sessionId: stringSchema,
  timestamp: stringSchema,
  severity: stringSchema,
});

const demoSimulationFaultSchema = objectSchema(['faultId', 'sessionId', 'timestamp'], {
  faultId: stringSchema,
  sessionId: stringSchema,
  timestamp: stringSchema,
});

const demoSimulationEventSchema = objectSchema(['eventId', 'sessionId', 'triggerTime'], {
  eventId: stringSchema,
  sessionId: stringSchema,
  triggerTime: stringSchema,
});

const demoSimulationFrameSchema = objectSchema(
  ['frameId', 'sessionId', 'order', 'type', 'delayMs', 'payload'],
  {
    frameId: stringSchema,
    sessionId: stringSchema,
    order: numberSchema,
    type: stringSchema,
    delayMs: numberSchema,
    payload: recordSchema,
  }
);

export const demoScenarioJsonSchema = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  title: 'DemoScenarioPackage',
  type: 'object',
  required: ['schemaVersion', 'scenario', 'auth', 'system', 'project', 'simulation'],
  additionalProperties: false,
  properties: {
    schemaVersion: { enum: [DEMO_SCENARIO_SCHEMA_VERSION] },
    scenario: objectSchema(
      ['id', 'name', 'version', 'fingerprint'],
      {
        id: stringSchema,
        name: stringSchema,
        version: stringSchema,
        fingerprint: stringSchema,
        seed: stringSchema,
      },
      false
    ),
    auth: objectSchema(
      ['accounts', 'roles', 'permissions'],
      {
        accounts: arraySchema(demoAccountSchema, 1),
        roles: arraySchema(demoRoleSchema, 1),
        permissions: arraySchema(demoPermissionSchema, 1),
      },
      false
    ),
    system: objectSchema(
      ['menus', 'dictTypes', 'dicts', 'departments', 'posts', 'users'],
      {
        menus: arraySchema(demoMenuSchema, 1),
        dictTypes: arraySchema(demoDictTypeSchema),
        dicts: arraySchema(demoDictDataSchema),
        departments: arraySchema(demoDepartmentSchema),
        posts: arraySchema(demoPostSchema),
        users: arraySchema(demoSystemUserSchema),
      },
      false
    ),
    project: objectSchema(
      ['projects', 'versions', 'topologies'],
      {
        projects: arraySchema(demoProjectSchema, 1),
        versions: arraySchema(demoProjectVersionSchema, 1),
        topologies: arraySchema(demoTopologySchema, 1),
      },
      false
    ),
    simulation: objectSchema(
      ['sessions', 'messages', 'bandwidth', 'alarms', 'faults', 'events', 'streamFrames'],
      {
        sessions: arraySchema(demoSimulationSessionSchema, 1),
        messages: arraySchema(demoSimulationMessageSchema),
        bandwidth: arraySchema(demoSimulationBandwidthSchema),
        alarms: arraySchema(demoSimulationAlarmSchema),
        faults: arraySchema(demoSimulationFaultSchema),
        events: arraySchema(demoSimulationEventSchema),
        streamFrames: arraySchema(demoSimulationFrameSchema),
      },
      false
    ),
  },
} as const satisfies JsonSchema;

export type DemoScenarioJsonSchema = typeof demoScenarioJsonSchema;
