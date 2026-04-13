import { DEMO_SCENARIO_SCHEMA_VERSION, type DemoScenarioPackage } from './schema';

const now = '2026-04-11T00:00:00.000Z';

export const defaultDemoScenario: DemoScenarioPackage = {
  schemaVersion: DEMO_SCENARIO_SCHEMA_VERSION,
  scenario: {
    id: 'default',
    name: '默认离线演示场景',
    version: '1.0.0',
    fingerprint: 'default-demo-offline-v1',
    seed: 'ruoyi-demo-offline-default',
  },
  auth: {
    accounts: [
      {
        username: 'admin',
        password: 'admin123',
        userId: 1,
        roleIds: [1],
        roles: ['admin'],
        permissions: ['*:*:*'],
        token: 'demo-token-admin',
        user: {
          userId: 1,
          deptId: 100,
          userName: 'admin',
          nickName: '离线演示管理员',
          status: '0',
          sex: '1',
          phonenumber: '15888888888',
          remark: 'demo-offline 本地演示账号',
        },
      },
    ],
    roles: [
      {
        roleId: 1,
        roleKey: 'admin',
        roleName: '超级管理员',
        menuIds: [1, 2, 10, 11],
        permissions: ['*:*:*'],
      },
    ],
    permissions: [
      {
        id: 'all',
        code: '*:*:*',
        label: '全部权限',
      },
    ],
  },
  system: {
    menus: [
      {
        menuId: 1,
        parentId: 0,
        name: 'Dashboard',
        path: '/',
        component: 'Layout',
        redirect: '/index',
        orderNum: 1,
        visible: '0',
        status: '0',
        roles: ['admin'],
        meta: { title: '首页', icon: 'dashboard' },
      },
      {
        menuId: 2,
        parentId: 1,
        name: 'Index',
        path: 'index',
        component: 'dashboard/index',
        orderNum: 1,
        visible: '0',
        status: '0',
        roles: ['admin'],
        perms: 'dashboard:index:view',
        meta: { title: '首页', icon: 'dashboard', affix: true },
      },
      {
        menuId: 10,
        parentId: 0,
        name: 'Project',
        path: '/project',
        component: 'Layout',
        redirect: '/project/project',
        orderNum: 2,
        visible: '0',
        status: '0',
        roles: ['admin'],
        meta: { title: '工程管理', icon: 'build' },
      },
      {
        menuId: 11,
        parentId: 10,
        name: 'ProjectList',
        path: 'project',
        component: 'project/index',
        orderNum: 1,
        visible: '0',
        status: '0',
        roles: ['admin'],
        perms: 'project:project:list',
        meta: { title: '工程列表', icon: 'list' },
      },
    ],
    dicts: [
      {
        id: 1,
        dictType: 'sys_normal_disable',
        dictLabel: '正常',
        dictValue: '0',
        dictSort: 1,
        status: '0',
      },
      {
        id: 2,
        dictType: 'sys_normal_disable',
        dictLabel: '停用',
        dictValue: '1',
        dictSort: 2,
        status: '0',
      },
      {
        id: 3,
        dictType: 'sys_user_sex',
        dictLabel: '男',
        dictValue: '0',
        dictSort: 1,
        status: '0',
      },
      {
        id: 4,
        dictType: 'sys_user_sex',
        dictLabel: '女',
        dictValue: '1',
        dictSort: 2,
        status: '0',
      },
      {
        id: 5,
        dictType: 'sys_user_sex',
        dictLabel: '未知',
        dictValue: '2',
        dictSort: 3,
        status: '0',
      },
    ],
    departments: [
      {
        deptId: 100,
        parentId: 0,
        deptName: '离线演示组织',
        orderNum: 1,
        status: '0',
      },
    ],
  },
  project: {
    projects: [
      {
        projectId: 1001,
        projectName: '星载总线演示项目',
        status: '0',
        createTime: now,
        updateTime: now,
        owner: '售前演示组',
        remark: '默认 demo-offline 项目，可被客户本地修改。',
      },
    ],
    versions: [
      {
        versionId: 2001,
        projectId: 1001,
        versionName: 'V1.0 演示基线',
        locked: true,
        status: '0',
        createTime: now,
        updateTime: now,
        remark: '只读演示流默认版本。',
      },
    ],
    topologies: [
      {
        id: 'topology-1001-2001',
        projectId: 1001,
        versionId: 2001,
        updateTime: now,
        graph: {
          nodes: [
            { id: 'node-platform', label: '平台控制器', type: 'controller' },
            { id: 'node-payload', label: '载荷设备', type: 'payload' },
          ],
          edges: [
            {
              id: 'edge-main-bus',
              source: 'node-platform',
              target: 'node-payload',
            },
          ],
        },
      },
    ],
  },
  simulation: {
    sessions: [
      {
        sessionId: 'demo-session-1001',
        projectId: 1001,
        versionId: 2001,
        status: 'running',
        createTime: now,
        updateTime: now,
      },
    ],
    messages: [
      {
        id: 'message-1',
        sessionId: 'demo-session-1001',
        timestamp: now,
        source: '平台控制器',
        target: '载荷设备',
        protocol: '1553B',
        content: '演示遥控指令',
      },
    ],
    bandwidth: [
      {
        id: 'bandwidth-1',
        sessionId: 'demo-session-1001',
        portId: 'bus-a',
        timestamp: now,
        value: 42,
        unit: 'Mbps',
      },
    ],
    alarms: [
      {
        alarmId: 'alarm-1',
        sessionId: 'demo-session-1001',
        timestamp: now,
        severity: 'info',
        message: '离线演示告警样例',
      },
    ],
    faults: [
      {
        faultId: 'fault-1',
        sessionId: 'demo-session-1001',
        timestamp: now,
        status: 'inactive',
        description: '预置故障样例',
      },
    ],
    events: [
      {
        eventId: 'event-1',
        sessionId: 'demo-session-1001',
        triggerTime: now,
        status: 'ready',
        name: '默认演示事件',
      },
    ],
    streamFrames: [
      {
        frameId: 'frame-1',
        sessionId: 'demo-session-1001',
        order: 1,
        type: 'status',
        delayMs: 0,
        payload: { status: 'running' },
      },
      {
        frameId: 'frame-2',
        sessionId: 'demo-session-1001',
        order: 2,
        type: 'pong',
        delayMs: 1000,
        payload: {},
      },
    ],
  },
};
