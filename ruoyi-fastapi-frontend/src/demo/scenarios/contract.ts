import {
  DEMO_SCENARIO_SCHEMA_VERSION,
  type DemoScenarioDescriptor,
  type DemoScenarioSchemaVersion,
} from './schema';
import type {
  DemoDomcAdapterReferenceSummary,
  DemoDomcRegistry,
} from '../domc/types';

export const DEMO_OFFLINE_CONTRACT_VERSION = 1 as const;
export const DEMO_OFFLINE_RUNTIME_ADAPTER_VERSION = 'demo-offline-runtime-p0.1';
export const DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION = 'demo-offline-generator-p0.1';
export const DEMO_OFFLINE_CONTRACT_DB_NAME = 'ruoyi-demo-offline';
export const DEMO_OFFLINE_CONTRACT_DB_VERSION = 2;
export const DEMO_OFFLINE_CONTRACT_MANIFEST_PATH = 'demo-contract/contract.json' as const;

export type RuntimeScenarioSource =
  | 'runtime-active-v2'
  | 'runtime-previous-v2'
  | 'bundle-default-v2';
export type RuntimeScenarioLoadStage =
  | 'fetch'
  | 'parse'
  | 'pointer'
  | 'manifest'
  | 'descriptor'
  | 'hash'
  | 'schema'
  | 'contract'
  | 'import';
export type RuntimeScenarioSourceTarget = 'offline-static';

export interface RuntimeValidationSummary {
  schemaValid: boolean;
  contractValid: boolean;
  invariantValid: boolean;
  dryRunValid?: boolean;
  issueCount: number;
}

export interface RuntimeScenarioLoadIssue {
  source: RuntimeScenarioSource;
  stage: RuntimeScenarioLoadStage;
  message: string;
  code: string;
}

export interface RuntimeScenarioSelection<TImportResult = unknown> {
  source: RuntimeScenarioSource;
  package: import('./schema').DemoScenarioPackage;
  meta?: RuntimeScenarioMeta;
  fallbackReason?: RuntimeScenarioLoadIssue;
  importResult?: TImportResult;
}

export interface RuntimeScenarioMeta {
  scenarioId: string;
  topicKey: string;
  schemaVersion: DemoScenarioSchemaVersion;
  contractFingerprint: string;
  generatorVersion: string;
  seed: string;
  generatedAt: string;
  validationSummary: RuntimeValidationSummary;
  sourceTarget: RuntimeScenarioSourceTarget;
  scenarioFingerprint: string;
  packageSha256: string;
  releaseId?: string;
  manifestPath?: string;
  manifestSha256?: string;
  provenancePath?: string;
}

export interface RuntimeScenarioDebugSummary extends DemoScenarioDescriptor {
  source: RuntimeScenarioSource;
  contractFingerprint?: string;
  importedAt: string;
  fallbackReason?: RuntimeScenarioLoadIssue;
  validationSummary?: RuntimeValidationSummary;
}

export type DemoScenarioModule = 'auth' | 'system' | 'project' | 'simulation';
export type DemoGeneratedScenarioModule = 'project' | 'simulation';
export type DemoCopiedScenarioModule = 'auth' | 'system';
export type DemoHandlerCoverageModule =
  | 'auth'
  | 'system'
  | 'system-admin'
  | 'project'
  | 'simulation';

export interface DemoEntityReferenceContract {
  field: string;
  targetEntity: string;
  targetField: string;
}

export interface DemoModuleEntityContract {
  entity: string;
  sourcePath: string;
  primaryKey: string;
  requiredFields: readonly string[];
  minItems: number;
  references?: readonly DemoEntityReferenceContract[];
}

export interface DemoModuleContractSummary {
  module: DemoScenarioModule;
  generatedByCompiler: boolean;
  entities: readonly DemoModuleEntityContract[];
  invariants: readonly string[];
}

export interface DemoIndexedDbTableMapping {
  table: string;
  sourcePath: string;
  primaryKey: string;
  indexes: readonly string[];
  minItems?: number;
}

export interface DemoIndexedDbMapping {
  dbName: typeof DEMO_OFFLINE_CONTRACT_DB_NAME;
  dbVersion: typeof DEMO_OFFLINE_CONTRACT_DB_VERSION;
  tables: readonly DemoIndexedDbTableMapping[];
}

export interface DemoHandlerCoverage {
  module: DemoHandlerCoverageModule;
  source: string;
  apiPrefix: string;
  coveredRoutes: readonly string[];
  unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED' | 'DEMO_NOT_SUPPORTED';
}

export interface DemoInvariantDefinition {
  id: string;
  description: string;
  severity: 'error' | 'warning';
  paths: readonly string[];
}

export interface DemoOfflineContractManifest {
  contractVersion: typeof DEMO_OFFLINE_CONTRACT_VERSION;
  schemaVersion: DemoScenarioSchemaVersion;
  generatedAt: string;
  runtimeAdapterVersion: string;
  generatorAdapterVersion: string;
  contractFingerprint: string;
  supportedModules: readonly DemoScenarioModule[];
  generatedModules: readonly DemoGeneratedScenarioModule[];
  copiedModules: readonly DemoCopiedScenarioModule[];
  domcRegistryFingerprint: string;
  domcRegistryPath: 'demo-contract/domc.registry.json';
  moduleContractFingerprints: Record<string, string>;
  adapterReferences: readonly DemoDomcAdapterReferenceSummary[];
  indexedDbMapping: DemoIndexedDbMapping;
  handlerCoverage: readonly DemoHandlerCoverage[];
  moduleContracts: readonly DemoModuleContractSummary[];
  invariants: readonly DemoInvariantDefinition[];
}

export type DemoOfflineContractManifestDraft = Omit<
  DemoOfflineContractManifest,
  'contractFingerprint'
> & {
  contractFingerprint?: string;
};

export interface CreateDemoOfflineContractManifestDraftOptions {
  domcRegistry?: DemoDomcRegistry;
  moduleContractFingerprints?: Record<string, string>;
  adapterReferences?: readonly DemoDomcAdapterReferenceSummary[];
}

export const DEMO_INDEXED_DB_MAPPING = {
  dbName: DEMO_OFFLINE_CONTRACT_DB_NAME,
  dbVersion: DEMO_OFFLINE_CONTRACT_DB_VERSION,
  tables: [
    {
      table: 'accounts',
      sourcePath: 'auth.accounts',
      primaryKey: 'username',
      indexes: ['userId', '*roleIds'],
      minItems: 1,
    },
    {
      table: 'roles',
      sourcePath: 'auth.roles',
      primaryKey: 'roleId',
      indexes: ['roleKey', 'status'],
      minItems: 1,
    },
    {
      table: 'permissions',
      sourcePath: 'auth.permissions',
      primaryKey: 'id',
      indexes: ['code'],
      minItems: 1,
    },
    {
      table: 'menus',
      sourcePath: 'system.menus',
      primaryKey: 'menuId',
      indexes: ['parentId', 'path', 'menuName', 'menuType', '*roles'],
      minItems: 1,
    },
    {
      table: 'dictTypes',
      sourcePath: 'system.dictTypes',
      primaryKey: 'dictId',
      indexes: ['dictType', 'dictName', 'status'],
    },
    {
      table: 'dicts',
      sourcePath: 'system.dicts',
      primaryKey: 'id',
      indexes: ['dictId', 'dictType', 'dictValue', 'status'],
    },
    {
      table: 'departments',
      sourcePath: 'system.departments',
      primaryKey: 'deptId',
      indexes: ['parentId', 'status'],
    },
    {
      table: 'posts',
      sourcePath: 'system.posts',
      primaryKey: 'postId',
      indexes: ['postCode', 'postName', 'status'],
    },
    {
      table: 'systemUsers',
      sourcePath: 'system.users',
      primaryKey: 'userId',
      indexes: ['deptId', 'userName', 'status', '*roleIds', '*postIds'],
    },
    {
      table: 'projects',
      sourcePath: 'project.projects',
      primaryKey: 'projectId',
      indexes: ['projectName', 'status', 'createTime'],
      minItems: 1,
    },
    {
      table: 'projectVersions',
      sourcePath: 'project.versions',
      primaryKey: 'versionId',
      indexes: ['projectId', 'versionName', 'locked', 'createTime'],
      minItems: 1,
    },
    {
      table: 'topologies',
      sourcePath: 'project.topologies',
      primaryKey: 'id',
      indexes: ['projectId', 'versionId'],
      minItems: 1,
    },
    {
      table: 'simulationSessions',
      sourcePath: 'simulation.sessions',
      primaryKey: 'sessionId',
      indexes: ['projectId', 'versionId', 'status'],
      minItems: 1,
    },
    {
      table: 'simulationMessages',
      sourcePath: 'simulation.messages',
      primaryKey: 'id',
      indexes: ['sessionId', 'timestamp'],
    },
    {
      table: 'simulationBandwidth',
      sourcePath: 'simulation.bandwidth',
      primaryKey: 'id',
      indexes: ['sessionId', 'portId', 'timestamp'],
    },
    {
      table: 'simulationAlarms',
      sourcePath: 'simulation.alarms',
      primaryKey: 'alarmId',
      indexes: ['sessionId', 'timestamp', 'severity'],
    },
    {
      table: 'simulationFaults',
      sourcePath: 'simulation.faults',
      primaryKey: 'faultId',
      indexes: ['sessionId', 'timestamp'],
    },
    {
      table: 'simulationEvents',
      sourcePath: 'simulation.events',
      primaryKey: 'eventId',
      indexes: ['sessionId', 'triggerTime'],
    },
    {
      table: 'simulationFrames',
      sourcePath: 'simulation.streamFrames',
      primaryKey: 'frameId',
      indexes: ['sessionId', 'order'],
    },
  ],
} as const satisfies DemoIndexedDbMapping;

export const DEMO_MODULE_CONTRACTS = [
  {
    module: 'auth',
    generatedByCompiler: false,
    entities: [
      {
        entity: 'DemoAccount',
        sourcePath: 'auth.accounts',
        primaryKey: 'username',
        requiredFields: [
          'username',
          'password',
          'userId',
          'roleIds',
          'roles',
          'permissions',
          'user',
        ],
        minItems: 1,
        references: [
          {
            field: 'userId',
            targetEntity: 'DemoSystemUser',
            targetField: 'userId',
          },
          {
            field: 'roleIds[]',
            targetEntity: 'DemoRole',
            targetField: 'roleId',
          },
        ],
      },
      {
        entity: 'DemoRole',
        sourcePath: 'auth.roles',
        primaryKey: 'roleId',
        requiredFields: ['roleId', 'roleKey', 'roleName', 'menuIds', 'permissions'],
        minItems: 1,
      },
      {
        entity: 'DemoPermission',
        sourcePath: 'auth.permissions',
        primaryKey: 'id',
        requiredFields: ['id', 'code', 'label'],
        minItems: 1,
      },
    ],
    invariants: ['At least one account can authenticate and resolve a role.'],
  },
  {
    module: 'system',
    generatedByCompiler: false,
    entities: [
      {
        entity: 'DemoMenu',
        sourcePath: 'system.menus',
        primaryKey: 'menuId',
        requiredFields: [
          'menuId',
          'parentId',
          'name',
          'path',
          'orderNum',
          'visible',
          'status',
          'roles',
        ],
        minItems: 1,
      },
      {
        entity: 'DemoSystemUser',
        sourcePath: 'system.users',
        primaryKey: 'userId',
        requiredFields: [
          'userId',
          'deptId',
          'userName',
          'nickName',
          'status',
          'roleIds',
          'postIds',
        ],
        minItems: 1,
      },
    ],
    invariants: ['System menus and users remain available for login and navigation.'],
  },
  {
    module: 'project',
    generatedByCompiler: true,
    entities: [
      {
        entity: 'DemoProject',
        sourcePath: 'project.projects',
        primaryKey: 'projectId',
        requiredFields: ['projectId', 'projectName', 'status', 'createTime', 'updateTime'],
        minItems: 1,
      },
      {
        entity: 'DemoProjectVersion',
        sourcePath: 'project.versions',
        primaryKey: 'versionId',
        requiredFields: [
          'versionId',
          'projectId',
          'versionName',
          'locked',
          'status',
          'createTime',
          'updateTime',
        ],
        minItems: 1,
        references: [
          {
            field: 'projectId',
            targetEntity: 'DemoProject',
            targetField: 'projectId',
          },
        ],
      },
      {
        entity: 'DemoTopology',
        sourcePath: 'project.topologies',
        primaryKey: 'id',
        requiredFields: ['id', 'projectId', 'graph', 'updateTime'],
        minItems: 1,
        references: [
          {
            field: 'projectId',
            targetEntity: 'DemoProject',
            targetField: 'projectId',
          },
          {
            field: 'versionId',
            targetEntity: 'DemoProjectVersion',
            targetField: 'versionId',
          },
        ],
      },
    ],
    invariants: [
      'Every visible project has at least one version.',
      'Every topology references an existing project and optional project version.',
      'Topology graph contains enough nodes and edges for read-only viewing.',
    ],
  },
  {
    module: 'simulation',
    generatedByCompiler: true,
    entities: [
      {
        entity: 'DemoSimulationSession',
        sourcePath: 'simulation.sessions',
        primaryKey: 'sessionId',
        requiredFields: [
          'sessionId',
          'projectId',
          'versionId',
          'status',
          'createTime',
          'updateTime',
        ],
        minItems: 1,
        references: [
          {
            field: 'projectId',
            targetEntity: 'DemoProject',
            targetField: 'projectId',
          },
          {
            field: 'versionId',
            targetEntity: 'DemoProjectVersion',
            targetField: 'versionId',
          },
        ],
      },
      {
        entity: 'DemoSimulationMessage',
        sourcePath: 'simulation.messages',
        primaryKey: 'id',
        requiredFields: ['id', 'sessionId', 'timestamp'],
        minItems: 0,
        references: [
          {
            field: 'sessionId',
            targetEntity: 'DemoSimulationSession',
            targetField: 'sessionId',
          },
        ],
      },
      {
        entity: 'DemoSimulationFrame',
        sourcePath: 'simulation.streamFrames',
        primaryKey: 'frameId',
        requiredFields: ['frameId', 'sessionId', 'order', 'type', 'delayMs', 'payload'],
        minItems: 0,
        references: [
          {
            field: 'sessionId',
            targetEntity: 'DemoSimulationSession',
            targetField: 'sessionId',
          },
        ],
      },
    ],
    invariants: [
      'Every simulation session references a valid project and version pair.',
      'Simulation timeline records reference existing sessions.',
      'At least one complete project/version/topology/simulation read-only chain exists.',
    ],
  },
] as const satisfies readonly DemoModuleContractSummary[];

export const DEMO_HANDLER_COVERAGE = [
  {
    module: 'auth',
    source: 'src/demo/handlers/auth.ts',
    apiPrefix: '/api',
    coveredRoutes: [
      'GET /captchaImage',
      'POST /login',
      'GET /getInfo',
      'POST /auth/refresh',
      'POST /auth/csrf-token',
      'POST /auth/ws-ticket',
      'POST /auth/logout',
      'POST /logout',
    ],
    unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED',
  },
  {
    module: 'system',
    source: 'src/demo/handlers/system.ts',
    apiPrefix: '/api',
    coveredRoutes: [
      'GET /getRouters',
      'GET /system/dict/data/type/:dictType',
      'GET /system/user/deptTree',
      'GET /system/dept/treeselect',
    ],
    unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED',
  },
  {
    module: 'system-admin',
    source: 'src/demo/handlers/system-admin.ts',
    apiPrefix: '/api',
    coveredRoutes: [
      'GET /system/user/list',
      'GET /system/role/list',
      'GET /system/menu/list',
      'GET /system/dept/list',
      'GET /system/dict/type/list',
      'GET /system/dict/data/list',
    ],
    unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED',
  },
  {
    module: 'project',
    source: 'src/demo/handlers/project.ts',
    apiPrefix: '/api',
    coveredRoutes: [
      'GET /project/list',
      'GET /project/:projectId',
      'POST /project',
      'PUT /project',
      'DELETE /project/:projectIds',
      'GET /project/topology/:projectId',
      'POST /project/topology/save',
      'GET /project/version/list',
      'GET /project/version/:versionId',
      'POST /project/version',
      'PUT /project/version',
      'DELETE /project/version/:versionIds',
    ],
    unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED',
  },
  {
    module: 'simulation',
    source: 'src/demo/handlers/simulation.ts',
    apiPrefix: '/api',
    coveredRoutes: [
      'WS /simulation/sessions/:sessionId/ws',
      'POST /simulation/sessions',
      'GET /simulation/sessions/:sessionId/status',
      'GET /simulation/sessions/:sessionId/messages',
      'GET /simulation/sessions/:sessionId/bandwidth',
      'GET /simulation/sessions/:sessionId/alarms',
      'GET /simulation/faults',
      'GET /simulation/sessions/:sessionId/faults',
      'GET /simulation/sessions/:sessionId/events',
      'POST /simulation/sessions/:sessionId/export',
      'GET /simulation/strategies',
    ],
    unsupportedBehavior: 'DEMO_NOT_SUPPORTED',
  },
] as const satisfies readonly DemoHandlerCoverage[];

export const DEMO_INVARIANTS = [
  {
    id: 'project_minimum_records',
    description: 'Runtime package contains at least one project, one version, and one topology.',
    severity: 'error',
    paths: ['project.projects', 'project.versions', 'project.topologies'],
  },
  {
    id: 'project_version_reference',
    description: 'Every project version references an existing project.',
    severity: 'error',
    paths: ['project.versions[].projectId'],
  },
  {
    id: 'topology_project_version_reference',
    description:
      'Every topology references an existing project and, when present, a version for that project.',
    severity: 'error',
    paths: ['project.topologies[].projectId', 'project.topologies[].versionId'],
  },
  {
    id: 'topology_graph_minimum_shape',
    description:
      'Topology graph contains the minimum node and edge shape required by read-only pages.',
    severity: 'error',
    paths: ['project.topologies[].graph'],
  },
  {
    id: 'simulation_session_reference',
    description: 'Every simulation session references an existing project/version relationship.',
    severity: 'error',
    paths: ['simulation.sessions[].projectId', 'simulation.sessions[].versionId'],
  },
  {
    id: 'simulation_record_session_reference',
    description: 'Simulation timeline records reference existing sessions.',
    severity: 'error',
    paths: [
      'simulation.messages[].sessionId',
      'simulation.bandwidth[].sessionId',
      'simulation.alarms[].sessionId',
      'simulation.faults[].sessionId',
      'simulation.events[].sessionId',
      'simulation.streamFrames[].sessionId',
    ],
  },
  {
    id: 'readonly_demo_chain',
    description:
      'At least one complete project/version/topology/simulation chain supports the demo pages.',
    severity: 'error',
    paths: ['project', 'simulation'],
  },
] as const satisfies readonly DemoInvariantDefinition[];

export function createDemoOfflineContractManifestDraft(
  generatedAt = new Date().toISOString(),
  options: CreateDemoOfflineContractManifestDraftOptions = {}
): DemoOfflineContractManifestDraft {
  return {
    contractVersion: DEMO_OFFLINE_CONTRACT_VERSION,
    schemaVersion: DEMO_SCENARIO_SCHEMA_VERSION,
    generatedAt,
    runtimeAdapterVersion: DEMO_OFFLINE_RUNTIME_ADAPTER_VERSION,
    generatorAdapterVersion: DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
    supportedModules: ['auth', 'system', 'project', 'simulation'],
    generatedModules: ['project', 'simulation'],
    copiedModules: ['auth', 'system'],
    domcRegistryFingerprint: options.domcRegistry?.domcFingerprint ?? '',
    domcRegistryPath: 'demo-contract/domc.registry.json',
    moduleContractFingerprints: options.moduleContractFingerprints ?? {},
    adapterReferences: options.adapterReferences ?? [],
    indexedDbMapping: DEMO_INDEXED_DB_MAPPING,
    handlerCoverage: DEMO_HANDLER_COVERAGE,
    moduleContracts: DEMO_MODULE_CONTRACTS,
    invariants: DEMO_INVARIANTS,
  };
}
