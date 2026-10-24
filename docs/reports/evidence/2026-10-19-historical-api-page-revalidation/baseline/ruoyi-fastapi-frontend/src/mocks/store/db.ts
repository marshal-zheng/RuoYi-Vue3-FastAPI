import Dexie, { type Table } from 'dexie';

import type {
  MockAccount,
  MockDepartment,
  MockDictData,
  MockMenu,
  MockProject,
  MockProjectVersion,
  MockRole,
  MockSimulationEvent,
  MockSimulationFrame,
  MockSimulationMessage,
  MockSimulationSession,
  MockTopology,
} from '../data';
import type { MockAuthSession } from './repositories';

export const MOCK_DEMO_DB_NAME = 'ruoyi-mock-demo';
export const MOCK_DEMO_SCHEMA_VERSION = 2;

export interface MockMetaRecord<T = unknown> {
  key: string;
  value: T;
  updatedAt: string;
}

export interface MockSequence {
  name: string;
  value: number;
}

export class MockDemoDb extends Dexie {
  meta!: Table<MockMetaRecord, string>;
  accounts!: Table<MockAccount, string>;
  authSessions!: Table<MockAuthSession, string>;
  roles!: Table<MockRole, number>;
  menus!: Table<MockMenu, number>;
  dicts!: Table<MockDictData, number>;
  departments!: Table<MockDepartment, number>;
  projects!: Table<MockProject, number>;
  projectVersions!: Table<MockProjectVersion, number>;
  topologies!: Table<MockTopology, string>;
  simulationSessions!: Table<MockSimulationSession, string>;
  simulationMessages!: Table<MockSimulationMessage, string>;
  simulationEvents!: Table<MockSimulationEvent, string>;
  simulationFrames!: Table<MockSimulationFrame, string>;
  sequences!: Table<MockSequence, string>;

  constructor(name = MOCK_DEMO_DB_NAME) {
    super(name);

    this.version(MOCK_DEMO_SCHEMA_VERSION).stores({
      meta: '&key',
      accounts: '&username, userId',
      authSessions: '&token, username, expiresAt',
      roles: '&roleId, roleKey, status',
      menus: '&menuId, parentId, path, menuName, menuType, *roles',
      dicts: '&id, dictType, dictValue, status',
      departments: '&deptId, parentId, status',
      projects: '&projectId, projectName, status, createTime',
      projectVersions: '&versionId, projectId, versionName, locked, createTime',
      topologies: '&id, projectId, versionId, [projectId+versionId]',
      simulationSessions: '&sessionId, projectId, versionId, status',
      simulationMessages: '&id, sessionId, timestamp',
      simulationEvents: '&eventId, sessionId, triggerTime',
      simulationFrames: '&id, sessionId, timestamp',
      sequences: '&name',
    });
  }
}

let mockDemoDb: MockDemoDb | undefined;

export function getMockDemoDb(): MockDemoDb {
  if (!mockDemoDb) {
    mockDemoDb = new MockDemoDb();
  }
  return mockDemoDb;
}

export function replaceMockDemoDb(db: MockDemoDb | undefined) {
  mockDemoDb = db;
}
