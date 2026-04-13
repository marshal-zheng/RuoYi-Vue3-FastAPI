import Dexie, { type Table } from 'dexie';

import type {
  DemoAccount,
  DemoDepartment,
  DemoDictData,
  DemoMenu,
  DemoPermission,
  DemoProject,
  DemoProjectVersion,
  DemoRole,
  DemoSimulationAlarm,
  DemoSimulationBandwidth,
  DemoSimulationEvent,
  DemoSimulationFault,
  DemoSimulationFrame,
  DemoSimulationMessage,
  DemoSimulationSession,
  DemoTopology,
} from '@/demo/scenarios';

export const DEMO_OFFLINE_DB_NAME = 'ruoyi-demo-offline';

export interface DemoMetaRecord<T = unknown> {
  key: string;
  value: T;
  updatedAt: string;
}

export interface DemoAuthSession {
  token: string;
  username: string;
  expiresAt: string;
}

export interface DemoCsrfToken {
  token: string;
  sessionToken: string;
  expiresAt: string;
}

export interface DemoWsTicket {
  ticket: string;
  sessionId: string;
  expiresAt: string;
  used: boolean;
}

export interface DemoSequence {
  name: string;
  value: number;
}

export class DemoOfflineDb extends Dexie {
  meta!: Table<DemoMetaRecord, string>;
  accounts!: Table<DemoAccount, string>;
  roles!: Table<DemoRole, number>;
  permissions!: Table<DemoPermission, string>;
  menus!: Table<DemoMenu, number>;
  dicts!: Table<DemoDictData, number>;
  departments!: Table<DemoDepartment, number>;
  authSessions!: Table<DemoAuthSession, string>;
  csrfTokens!: Table<DemoCsrfToken, string>;
  wsTickets!: Table<DemoWsTicket, string>;
  projects!: Table<DemoProject, number>;
  projectVersions!: Table<DemoProjectVersion, number>;
  topologies!: Table<DemoTopology, string>;
  simulationSessions!: Table<DemoSimulationSession, string>;
  simulationMessages!: Table<DemoSimulationMessage, string>;
  simulationBandwidth!: Table<DemoSimulationBandwidth, string>;
  simulationAlarms!: Table<DemoSimulationAlarm, string>;
  simulationFaults!: Table<DemoSimulationFault, string>;
  simulationEvents!: Table<DemoSimulationEvent, string>;
  simulationFrames!: Table<DemoSimulationFrame, string>;
  sequences!: Table<DemoSequence, string>;

  constructor(name = DEMO_OFFLINE_DB_NAME) {
    super(name);

    this.version(1).stores({
      meta: '&key',
      accounts: '&username, userId, *roleIds',
      roles: '&roleId, roleKey',
      permissions: '&id, code',
      menus: '&menuId, parentId, path, *roles',
      dicts: '&id, dictType, dictValue',
      departments: '&deptId, parentId',
      authSessions: '&token, username, expiresAt',
      csrfTokens: '&token, sessionToken, expiresAt',
      wsTickets: '&ticket, sessionId, expiresAt, used',
      projects: '&projectId, projectName, status, createTime',
      projectVersions: '&versionId, projectId, versionName, locked, createTime',
      topologies: '&id, projectId, versionId',
      simulationSessions: '&sessionId, projectId, versionId, status',
      simulationMessages: '&id, sessionId, timestamp',
      simulationBandwidth: '&id, sessionId, portId, timestamp',
      simulationAlarms: '&alarmId, sessionId, timestamp, severity',
      simulationFaults: '&faultId, sessionId, timestamp',
      simulationEvents: '&eventId, sessionId, triggerTime',
      simulationFrames: '&frameId, sessionId, order',
      sequences: '&name',
    });
  }
}

let demoOfflineDb: DemoOfflineDb | undefined;

export function getDemoOfflineDb(): DemoOfflineDb {
  if (!demoOfflineDb) {
    demoOfflineDb = new DemoOfflineDb();
  }

  return demoOfflineDb;
}

export function replaceDemoOfflineDb(db: DemoOfflineDb | undefined) {
  demoOfflineDb = db;
}
