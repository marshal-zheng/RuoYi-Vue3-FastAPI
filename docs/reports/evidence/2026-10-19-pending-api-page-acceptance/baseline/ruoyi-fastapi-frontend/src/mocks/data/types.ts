import type {
  MockOpenApiAccountUser,
  MockOpenApiDepartment,
  MockOpenApiDevice,
  MockOpenApiDictData,
  MockOpenApiMenu,
  MockOpenApiProject,
  MockOpenApiProjectVersion,
  MockOpenApiRole,
  MockOpenApiTopology,
} from '../contracts';

export interface MockDataset {
  version: string;
  referenceTime: string;
  auth: AuthMockData;
  system: SystemMockData;
  device: DeviceMockData;
  project: ProjectMockData;
  simulation: SimulationMockData;
}

export interface MockFactoryContext {
  seed: string;
  referenceTime: string;
}

export interface AuthMockData {
  accounts: MockAccount[];
  roles: MockRole[];
}

export interface SystemMockData {
  menus: MockMenu[];
  dicts: MockDictData[];
  departments: MockDepartment[];
}

export interface DeviceMockData {
  devices: MockDevice[];
}

export interface ProjectMockData {
  projects: MockProject[];
  versions: MockProjectVersion[];
  topologies: MockTopology[];
}

export interface SimulationMockData {
  sessions: MockSimulationSession[];
  frames: MockSimulationFrame[];
  messages: MockSimulationMessage[];
  events: MockSimulationEvent[];
}

export interface MockAccount extends Pick<MockOpenApiAccountUser, 'userId' | 'avatar' | 'status'> {
  username: string;
  password: string;
  displayName: string;
  introduction: string;
  roles: string[];
  permissions: string[];
}

export interface MockRole extends MockOpenApiRole {
  permissions: string[];
}

export interface MockMenu extends MockOpenApiMenu {
  roles?: string[];
}

export interface MockDictData extends Omit<MockOpenApiDictData, 'dictCode'> {
  id: number;
}

export type MockDepartment = MockOpenApiDepartment;

export type MockDevice = MockOpenApiDevice;

export type MockProject = MockOpenApiProject;

export interface MockProjectVersion extends MockOpenApiProjectVersion {
  versionNumber?: string;
  description?: string;
  isLocked?: '0' | '1';
  lockedBy?: string;
  lockedTime?: string;
}

export type MockTopology = MockOpenApiTopology;

export interface MockSimulationSession {
  sessionId: string;
  projectId: number;
  versionId: number;
  status: string;
}

export interface MockSimulationFrame {
  id: string;
  sessionId: string;
  timestamp: string;
  bandwidthMbps: number;
  latencyMs: number;
  alarmCount: number;
}

export interface MockSimulationMessage {
  id: string;
  sessionId: string;
  timestamp: string;
  payload: unknown;
}

export interface MockSimulationEvent {
  eventId: string;
  sessionId: string;
  triggerTime: string;
  eventType: string;
}
