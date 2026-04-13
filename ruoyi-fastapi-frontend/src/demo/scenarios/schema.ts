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
  path: string;
  component?: string;
  redirect?: string;
  orderNum: number;
  visible: '0' | '1';
  status: '0' | '1';
  roles: string[];
  perms?: string;
  meta?: DemoRecord;
}

export interface DemoDictData {
  id: number;
  dictType: string;
  dictLabel: string;
  dictValue: string;
  dictSort: number;
  status: '0' | '1';
}

export interface DemoDepartment {
  deptId: number;
  parentId: number;
  deptName: string;
  orderNum: number;
  status: '0' | '1';
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
    dicts: DemoDictData[];
    departments: DemoDepartment[];
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
  if (scenarioPackage.schemaVersion !== DEMO_SCENARIO_SCHEMA_VERSION) {
    throw new Error(
      `Unsupported demo scenario schema version "${scenarioPackage.schemaVersion}". Expected ${DEMO_SCENARIO_SCHEMA_VERSION}.`
    );
  }

  if (!hasText(scenarioPackage.scenario?.id)) {
    throw new Error('Invalid demo scenario package: scenario.id is required.');
  }

  if (!hasText(scenarioPackage.scenario?.version)) {
    throw new Error('Invalid demo scenario package: scenario.version is required.');
  }

  if (!hasText(scenarioPackage.scenario?.fingerprint)) {
    throw new Error('Invalid demo scenario package: scenario.fingerprint is required.');
  }

  ensureArray(scenarioPackage.auth?.accounts, 'auth.accounts');
  ensureArray(scenarioPackage.auth?.roles, 'auth.roles');
  ensureArray(scenarioPackage.auth?.permissions, 'auth.permissions');
  ensureArray(scenarioPackage.system?.menus, 'system.menus');
  ensureArray(scenarioPackage.system?.dicts, 'system.dicts');
  ensureArray(scenarioPackage.system?.departments, 'system.departments');
  ensureArray(scenarioPackage.project?.projects, 'project.projects');
  ensureArray(scenarioPackage.project?.versions, 'project.versions');
  ensureArray(scenarioPackage.project?.topologies, 'project.topologies');
  ensureArray(scenarioPackage.simulation?.sessions, 'simulation.sessions');
  ensureArray(scenarioPackage.simulation?.messages, 'simulation.messages');
  ensureArray(scenarioPackage.simulation?.bandwidth, 'simulation.bandwidth');
  ensureArray(scenarioPackage.simulation?.alarms, 'simulation.alarms');
  ensureArray(scenarioPackage.simulation?.faults, 'simulation.faults');
  ensureArray(scenarioPackage.simulation?.events, 'simulation.events');
  ensureArray(scenarioPackage.simulation?.streamFrames, 'simulation.streamFrames');

  return scenarioPackage;
}
