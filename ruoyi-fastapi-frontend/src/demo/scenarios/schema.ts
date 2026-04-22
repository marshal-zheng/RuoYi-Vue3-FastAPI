export const DEMO_SCENARIO_SCHEMA_VERSION = 1 as const;

export type DemoScenarioSchemaVersion = typeof DEMO_SCENARIO_SCHEMA_VERSION;
export type DemoEntityId = string | number;
export type DemoRecord = Record<string, unknown>;

export interface DemoScenarioIdentity {
  id: string;
  name: string;
  version: string;
  fingerprint: string;
  seed?: string;
}

export interface DemoAccount {
  username: string;
  password: string;
  userId: number;
  roleIds: number[];
  roles: string[];
  permissions: string[];
  token?: string;
  user: DemoRecord;
}

export interface DemoRole {
  roleId: number;
  roleKey: string;
  roleName: string;
  menuIds: number[];
  permissions: string[];
  roleSort?: number;
  dataScope?: string;
  menuCheckStrictly?: boolean;
  deptCheckStrictly?: boolean;
  deptIds?: number[];
  status?: '0' | '1';
  remark?: string;
  createTime?: string;
  updateTime?: string;
}

export interface DemoPermission {
  id: string;
  code: string;
  label: string;
}

export interface DemoMenu {
  menuId: number;
  parentId: number;
  name: string;
  menuName?: string;
  routeName?: string;
  path: string;
  component?: string;
  redirect?: string;
  orderNum: number;
  visible: '0' | '1';
  status: '0' | '1';
  roles: string[];
  perms?: string;
  menuType?: 'M' | 'C' | 'F';
  icon?: string;
  isFrame?: '0' | '1';
  isCache?: '0' | '1';
  query?: string;
  createTime?: string;
  updateTime?: string;
  remark?: string;
  meta?: DemoRecord;
}

export interface DemoDictType {
  dictId: number;
  dictName: string;
  dictType: string;
  status: '0' | '1';
  remark?: string;
  createTime?: string;
  updateTime?: string;
}

export interface DemoDictData {
  id: number;
  dictId?: number;
  dictType: string;
  dictLabel: string;
  dictValue: string;
  dictSort: number;
  status: '0' | '1';
  cssClass?: string;
  listClass?: string;
  isDefault?: 'Y' | 'N';
  remark?: string;
  createTime?: string;
  updateTime?: string;
}

export interface DemoDepartment {
  deptId: number;
  parentId: number;
  ancestors?: string;
  deptName: string;
  orderNum: number;
  status: '0' | '1';
  leader?: string;
  phone?: string;
  email?: string;
  createTime?: string;
  updateTime?: string;
}

export interface DemoPost {
  postId: number;
  postCode: string;
  postName: string;
  postSort: number;
  status: '0' | '1';
  remark?: string;
  createTime?: string;
  updateTime?: string;
}

export interface DemoSystemUser {
  userId: number;
  deptId: number;
  userName: string;
  nickName: string;
  userType?: string;
  email?: string;
  phonenumber?: string;
  sex?: '0' | '1' | '2';
  avatar?: string;
  password?: string;
  status: '0' | '1';
  delFlag?: '0' | '2';
  loginIp?: string;
  loginDate?: string;
  createBy?: string;
  createTime?: string;
  updateBy?: string;
  updateTime?: string;
  remark?: string;
  roleIds: number[];
  postIds: number[];
}

export interface DemoProject {
  projectId: number;
  projectName: string;
  status: '0' | '1';
  createTime: string;
  updateTime: string;
  remark?: string;
  owner?: string;
  [key: string]: unknown;
}

export interface DemoProjectVersion {
  versionId: number;
  projectId: number;
  versionName: string;
  locked: boolean;
  status: '0' | '1';
  createTime: string;
  updateTime: string;
  remark?: string;
  [key: string]: unknown;
}

export interface DemoTopology {
  id: string;
  projectId: number;
  versionId?: number;
  graph: DemoRecord;
  updateTime: string;
}

export interface DemoSimulationSession {
  sessionId: string;
  projectId: number;
  versionId: number;
  status: string;
  createTime: string;
  updateTime: string;
  [key: string]: unknown;
}

export interface DemoSimulationMessage {
  id: string;
  sessionId: string;
  timestamp: string;
  [key: string]: unknown;
}

export interface DemoSimulationBandwidth {
  id: string;
  sessionId: string;
  portId: string;
  timestamp: string;
  [key: string]: unknown;
}

export interface DemoSimulationAlarm {
  alarmId: string;
  sessionId: string;
  timestamp: string;
  severity: string;
  [key: string]: unknown;
}

export interface DemoSimulationFault {
  faultId: string;
  sessionId: string;
  timestamp: string;
  [key: string]: unknown;
}

export interface DemoSimulationEvent {
  eventId: string;
  sessionId: string;
  triggerTime: string;
  [key: string]: unknown;
}

export interface DemoSimulationFrame {
  frameId: string;
  sessionId: string;
  order: number;
  type: string;
  delayMs: number;
  payload: DemoRecord;
}

export interface DemoScenarioPackage {
  schemaVersion: DemoScenarioSchemaVersion;
  scenario: DemoScenarioIdentity;
  auth: {
    accounts: DemoAccount[];
    roles: DemoRole[];
    permissions: DemoPermission[];
  };
  system: {
    menus: DemoMenu[];
    dictTypes: DemoDictType[];
    dicts: DemoDictData[];
    departments: DemoDepartment[];
    posts: DemoPost[];
    users: DemoSystemUser[];
  };
  project: {
    projects: DemoProject[];
    versions: DemoProjectVersion[];
    topologies: DemoTopology[];
  };
  simulation: {
    sessions: DemoSimulationSession[];
    messages: DemoSimulationMessage[];
    bandwidth: DemoSimulationBandwidth[];
    alarms: DemoSimulationAlarm[];
    faults: DemoSimulationFault[];
    events: DemoSimulationEvent[];
    streamFrames: DemoSimulationFrame[];
  };
}

export interface DemoScenarioDescriptor {
  schemaVersion: DemoScenarioSchemaVersion;
  scenarioId: string;
  scenarioVersion: string;
  fingerprint: string;
  name: string;
}

function hasText(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function ensureArray(value: unknown, path: string): void {
  if (!Array.isArray(value)) {
    throw new Error(`Invalid demo scenario package: ${path} must be an array.`);
  }
}

export function describeDemoScenarioPackage(
  scenarioPackage: DemoScenarioPackage
): DemoScenarioDescriptor {
  return {
    schemaVersion: scenarioPackage.schemaVersion,
    scenarioId: scenarioPackage.scenario.id,
    scenarioVersion: scenarioPackage.scenario.version,
    fingerprint: scenarioPackage.scenario.fingerprint,
    name: scenarioPackage.scenario.name,
  };
}

export function validateDemoScenarioPackage(
  scenarioPackage: DemoScenarioPackage
): DemoScenarioPackage {
  const normalizedScenarioPackage: DemoScenarioPackage = {
    ...scenarioPackage,
    system: {
      ...scenarioPackage.system,
      menus: scenarioPackage.system?.menus ?? [],
      dictTypes: scenarioPackage.system?.dictTypes ?? [],
      dicts: scenarioPackage.system?.dicts ?? [],
      departments: scenarioPackage.system?.departments ?? [],
      posts: scenarioPackage.system?.posts ?? [],
      users: scenarioPackage.system?.users ?? [],
    },
  };

  if (normalizedScenarioPackage.schemaVersion !== DEMO_SCENARIO_SCHEMA_VERSION) {
    throw new Error(
      `Unsupported demo scenario schema version "${normalizedScenarioPackage.schemaVersion}". Expected ${DEMO_SCENARIO_SCHEMA_VERSION}.`
    );
  }

  if (!hasText(normalizedScenarioPackage.scenario?.id)) {
    throw new Error('Invalid demo scenario package: scenario.id is required.');
  }

  if (!hasText(normalizedScenarioPackage.scenario?.version)) {
    throw new Error('Invalid demo scenario package: scenario.version is required.');
  }

  if (!hasText(normalizedScenarioPackage.scenario?.fingerprint)) {
    throw new Error('Invalid demo scenario package: scenario.fingerprint is required.');
  }

  ensureArray(normalizedScenarioPackage.auth?.accounts, 'auth.accounts');
  ensureArray(normalizedScenarioPackage.auth?.roles, 'auth.roles');
  ensureArray(normalizedScenarioPackage.auth?.permissions, 'auth.permissions');
  ensureArray(normalizedScenarioPackage.system?.menus, 'system.menus');
  ensureArray(normalizedScenarioPackage.system?.dictTypes, 'system.dictTypes');
  ensureArray(normalizedScenarioPackage.system?.dicts, 'system.dicts');
  ensureArray(normalizedScenarioPackage.system?.departments, 'system.departments');
  ensureArray(normalizedScenarioPackage.system?.posts, 'system.posts');
  ensureArray(normalizedScenarioPackage.system?.users, 'system.users');
  ensureArray(normalizedScenarioPackage.project?.projects, 'project.projects');
  ensureArray(normalizedScenarioPackage.project?.versions, 'project.versions');
  ensureArray(normalizedScenarioPackage.project?.topologies, 'project.topologies');
  ensureArray(normalizedScenarioPackage.simulation?.sessions, 'simulation.sessions');
  ensureArray(normalizedScenarioPackage.simulation?.messages, 'simulation.messages');
  ensureArray(normalizedScenarioPackage.simulation?.bandwidth, 'simulation.bandwidth');
  ensureArray(normalizedScenarioPackage.simulation?.alarms, 'simulation.alarms');
  ensureArray(normalizedScenarioPackage.simulation?.faults, 'simulation.faults');
  ensureArray(normalizedScenarioPackage.simulation?.events, 'simulation.events');
  ensureArray(normalizedScenarioPackage.simulation?.streamFrames, 'simulation.streamFrames');

  return normalizedScenarioPackage;
}
