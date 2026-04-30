import type { Table } from 'dexie';

import type { DemoOfflineDb, DemoMetaRecord } from '@/demo/db';
import {
  describeDemoScenarioPackage,
  validateDemoScenarioPackage,
  type DemoScenarioDescriptor,
  type DemoScenarioPackage,
  type RuntimeScenarioLoadIssue,
  type RuntimeScenarioSource,
  type RuntimeValidationSummary,
} from '@/demo/scenarios';

const ACTIVE_SCENARIO_META_KEY = 'activeScenario';

export interface DemoActiveScenarioMeta extends DemoScenarioDescriptor {
  importedAt: string;
  source: RuntimeScenarioSource;
  contractFingerprint?: string;
  fallbackReason?: RuntimeScenarioLoadIssue;
  validationSummary?: RuntimeValidationSummary;
}

export interface DemoScenarioImportResult {
  imported: boolean;
  activeScenario: DemoActiveScenarioMeta;
}

export interface DemoScenarioImportContext {
  source?: RuntimeScenarioSource;
  contractFingerprint?: string;
  fallbackReason?: RuntimeScenarioLoadIssue;
  validationSummary?: RuntimeValidationSummary;
}

function metaRecord(value: DemoActiveScenarioMeta): DemoMetaRecord<DemoActiveScenarioMeta> {
  return {
    key: ACTIVE_SCENARIO_META_KEY,
    value,
    updatedAt: new Date().toISOString(),
  };
}

function sameScenario(left: DemoActiveScenarioMeta | undefined, right: DemoScenarioDescriptor) {
  return (
    left?.schemaVersion === right.schemaVersion &&
    left.scenarioId === right.scenarioId &&
    left.scenarioVersion === right.scenarioVersion &&
    left.fingerprint === right.fingerprint
  );
}

function createActiveScenarioMeta(
  descriptor: DemoScenarioDescriptor,
  importedAt: string,
  context: DemoScenarioImportContext = {}
): DemoActiveScenarioMeta {
  return {
    ...descriptor,
    importedAt,
    source: context.source ?? 'bundle-default-v2',
    contractFingerprint: context.contractFingerprint,
    fallbackReason: context.fallbackReason,
    validationSummary: context.validationSummary,
  };
}

function mergeActiveScenarioContext(
  activeScenario: DemoActiveScenarioMeta,
  context: DemoScenarioImportContext
): DemoActiveScenarioMeta {
  return {
    ...activeScenario,
    source: context.source ?? activeScenario.source ?? 'bundle-default-v2',
    contractFingerprint: context.contractFingerprint ?? activeScenario.contractFingerprint,
    fallbackReason:
      context.fallbackReason === undefined ? activeScenario.fallbackReason : context.fallbackReason,
    validationSummary: context.validationSummary ?? activeScenario.validationSummary,
  };
}

function maxNumericValue<T extends object>(records: T[], key: keyof T): number {
  return records.reduce((max, record) => {
    const value = record[key];
    return typeof value === 'number' && value > max ? value : max;
  }, 0);
}

export class ScenarioRepository {
  constructor(private readonly db: DemoOfflineDb) {}

  async getActiveScenario(): Promise<DemoActiveScenarioMeta | undefined> {
    const record = await this.db.meta.get(ACTIVE_SCENARIO_META_KEY);
    return record?.value as DemoActiveScenarioMeta | undefined;
  }

  async ensureScenario(
    scenarioPackage: DemoScenarioPackage,
    context: DemoScenarioImportContext = {}
  ): Promise<DemoScenarioImportResult> {
    const validScenarioPackage = validateDemoScenarioPackage(scenarioPackage);
    const descriptor = describeDemoScenarioPackage(validScenarioPackage);
    const activeScenario = await this.getActiveScenario();

    if (activeScenario && sameScenario(activeScenario, descriptor)) {
      const nextActiveScenario = mergeActiveScenarioContext(activeScenario, context);
      await this.db.meta.put(metaRecord(nextActiveScenario));

      return {
        imported: false,
        activeScenario: nextActiveScenario,
      };
    }

    return this.importScenario(validScenarioPackage, context);
  }

  resetScenario(
    scenarioPackage: DemoScenarioPackage,
    context: DemoScenarioImportContext = {}
  ): Promise<DemoScenarioImportResult> {
    return this.importScenario(validateDemoScenarioPackage(scenarioPackage), context);
  }

  switchScenario(
    scenarioPackage: DemoScenarioPackage,
    context: DemoScenarioImportContext = {}
  ): Promise<DemoScenarioImportResult> {
    return this.importScenario(validateDemoScenarioPackage(scenarioPackage), context);
  }

  async exportCurrentScenario(): Promise<DemoScenarioPackage> {
    const activeScenario = await this.getActiveScenario();

    if (!activeScenario) {
      throw new Error('No active demo scenario is available to export.');
    }

    return {
      schemaVersion: activeScenario.schemaVersion,
      scenario: {
        id: activeScenario.scenarioId,
        name: activeScenario.name,
        version: activeScenario.scenarioVersion,
        fingerprint: activeScenario.fingerprint,
      },
      auth: {
        accounts: await this.db.accounts.toArray(),
        roles: await this.db.roles.toArray(),
        permissions: await this.db.permissions.toArray(),
      },
      system: {
        menus: await this.db.menus.toArray(),
        dictTypes: await this.db.dictTypes.toArray(),
        dicts: await this.db.dicts.toArray(),
        departments: await this.db.departments.toArray(),
        posts: await this.db.posts.toArray(),
        users: await this.db.systemUsers.toArray(),
      },
      project: {
        projects: await this.db.projects.toArray(),
        versions: await this.db.projectVersions.toArray(),
        topologies: await this.db.topologies.toArray(),
      },
      simulation: {
        sessions: await this.db.simulationSessions.toArray(),
        messages: await this.db.simulationMessages.toArray(),
        bandwidth: await this.db.simulationBandwidth.toArray(),
        alarms: await this.db.simulationAlarms.toArray(),
        faults: await this.db.simulationFaults.toArray(),
        events: await this.db.simulationEvents.toArray(),
        streamFrames: await this.db.simulationFrames.toArray(),
      },
    };
  }

  private async importScenario(
    scenarioPackage: DemoScenarioPackage,
    context: DemoScenarioImportContext = {}
  ): Promise<DemoScenarioImportResult> {
    const descriptor = describeDemoScenarioPackage(scenarioPackage);
    const importedAt = new Date().toISOString();
    const activeScenario = createActiveScenarioMeta(descriptor, importedAt, context);

    await this.db.transaction('rw', this.scenarioTables(), async () => {
      await this.clearScenarioData();

      await this.db.accounts.bulkPut(scenarioPackage.auth.accounts);
      await this.db.roles.bulkPut(scenarioPackage.auth.roles);
      await this.db.permissions.bulkPut(scenarioPackage.auth.permissions);
      await this.db.menus.bulkPut(scenarioPackage.system.menus);
      await this.db.dictTypes.bulkPut(scenarioPackage.system.dictTypes);
      await this.db.dicts.bulkPut(scenarioPackage.system.dicts);
      await this.db.departments.bulkPut(scenarioPackage.system.departments);
      await this.db.posts.bulkPut(scenarioPackage.system.posts);
      await this.db.systemUsers.bulkPut(scenarioPackage.system.users);
      await this.db.projects.bulkPut(scenarioPackage.project.projects);
      await this.db.projectVersions.bulkPut(scenarioPackage.project.versions);
      await this.db.topologies.bulkPut(scenarioPackage.project.topologies);
      await this.db.simulationSessions.bulkPut(scenarioPackage.simulation.sessions);
      await this.db.simulationMessages.bulkPut(scenarioPackage.simulation.messages);
      await this.db.simulationBandwidth.bulkPut(scenarioPackage.simulation.bandwidth);
      await this.db.simulationAlarms.bulkPut(scenarioPackage.simulation.alarms);
      await this.db.simulationFaults.bulkPut(scenarioPackage.simulation.faults);
      await this.db.simulationEvents.bulkPut(scenarioPackage.simulation.events);
      await this.db.simulationFrames.bulkPut(scenarioPackage.simulation.streamFrames);

      await this.db.sequences.bulkPut([
        {
          name: 'projects',
          value: maxNumericValue(scenarioPackage.project.projects, 'projectId') + 1,
        },
        {
          name: 'projectVersions',
          value: maxNumericValue(scenarioPackage.project.versions, 'versionId') + 1,
        },
        {
          name: 'roles',
          value: maxNumericValue(scenarioPackage.auth.roles, 'roleId') + 1,
        },
        {
          name: 'dicts',
          value: maxNumericValue(scenarioPackage.system.dicts, 'id') + 1,
        },
        {
          name: 'menus',
          value: maxNumericValue(scenarioPackage.system.menus, 'menuId') + 1,
        },
        {
          name: 'dictTypes',
          value: maxNumericValue(scenarioPackage.system.dictTypes, 'dictId') + 1,
        },
        {
          name: 'departments',
          value: maxNumericValue(scenarioPackage.system.departments, 'deptId') + 1,
        },
        {
          name: 'posts',
          value: maxNumericValue(scenarioPackage.system.posts, 'postId') + 1,
        },
        {
          name: 'users',
          value: maxNumericValue(scenarioPackage.system.users, 'userId') + 1,
        },
      ]);
      await this.db.meta.put(metaRecord(activeScenario));
    });

    return {
      imported: true,
      activeScenario,
    };
  }

  private async clearScenarioData(): Promise<void> {
    const tables = this.scenarioTables().filter((table) => table !== this.db.meta);
    await Promise.all(tables.map((table) => table.clear()));
  }

  private scenarioTables(): Table[] {
    return [
      this.db.meta,
      this.db.accounts,
      this.db.roles,
      this.db.permissions,
      this.db.menus,
      this.db.dictTypes,
      this.db.dicts,
      this.db.departments,
      this.db.posts,
      this.db.systemUsers,
      this.db.authSessions,
      this.db.csrfTokens,
      this.db.wsTickets,
      this.db.projects,
      this.db.projectVersions,
      this.db.topologies,
      this.db.simulationSessions,
      this.db.simulationMessages,
      this.db.simulationBandwidth,
      this.db.simulationAlarms,
      this.db.simulationFaults,
      this.db.simulationEvents,
      this.db.simulationFrames,
      this.db.sequences,
    ];
  }
}
