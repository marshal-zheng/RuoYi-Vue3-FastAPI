import type { DemoDomcModuleContract } from '../types';
import { field, handlerRefs, moduleSummaryInvariant, tableRef, tableRefs } from './common';

const sourcePaths = ['auth.accounts', 'auth.roles', 'auth.permissions'] as const;

export const authDomcModule = {
  moduleId: 'auth',
  moduleVersion: '1.0.0',
  lifecycle: 'active',
  capability: 'copyOnly',
  owner: 'demo-offline-platform',
  sourcePaths,
  indexedDbTables: tableRefs(sourcePaths),
  handlerCoverage: handlerRefs(['auth']),
  uiJourneys: [
    {
      journeyId: 'auth-login-bootstrap',
      entry: '/login',
      primarySourcePath: 'auth.accounts',
      requiredSupportSourcePaths: ['auth.roles', 'auth.permissions'],
      listFields: ['username', 'roles', 'permissions'],
      detailFields: ['userId', 'user.nickName', 'roleIds', 'permissions'],
      keyActions: [
        { action: 'login', demoBehavior: 'Authenticate against copied default demo accounts.' },
        { action: 'getInfo', demoBehavior: 'Resolve copied roles and permissions for current account.' },
        { action: 'logout', demoBehavior: 'Clear local demo session state without changing copied auth records.' },
      ],
      emptyState: 'Block activation because auth.accounts requires at least one copied account.',
      errorState: 'Return DEMO_API_NOT_IMPLEMENTED for auth routes outside the offline contract.',
      minimumDemoChain: ['auth.accounts', 'auth.roles', 'auth.permissions'],
    },
  ],
  entities: [
    {
      entity: 'DemoAccount',
      sourcePath: 'auth.accounts',
      indexedDbTable: tableRef('auth.accounts').table,
      primaryKey: 'username',
      minItems: tableRef('auth.accounts').minItems ?? 1,
      fields: [
        field('username', 'identifier'),
        field('password', 'opaquePayload'),
        field('userId', 'foreignKey'),
        field('roleIds', 'foreignKey'),
        field('roles', 'enum'),
        field('permissions', 'opaquePayload'),
        field('token', 'opaquePayload', { required: false }),
        field('user', 'opaquePayload'),
      ],
      references: [
        {
          field: 'userId',
          targetEntity: 'DemoSystemUser',
          targetField: 'userId',
          relation: 'one-to-one',
          required: true,
        },
        {
          field: 'roleIds',
          targetEntity: 'DemoRole',
          targetField: 'roleId',
          relation: 'many-to-many',
          required: true,
        },
      ],
      ownership: {
        recordOwner: 'default-scenario',
        mergePolicy: 'copy-only',
      },
    },
    {
      entity: 'DemoRole',
      sourcePath: 'auth.roles',
      indexedDbTable: tableRef('auth.roles').table,
      primaryKey: 'roleId',
      minItems: tableRef('auth.roles').minItems ?? 1,
      fields: [
        field('roleId', 'identifier'),
        field('roleKey', 'identifier'),
        field('roleName', 'displayName'),
        field('menuIds', 'foreignKey'),
        field('permissions', 'opaquePayload'),
        field('status', 'status', { required: false, enumValues: ['0', '1'] }),
        field('remark', 'description', { required: false }),
      ],
      references: [
        {
          field: 'menuIds',
          targetEntity: 'DemoMenu',
          targetField: 'menuId',
          relation: 'many-to-many',
          required: true,
        },
      ],
      ownership: {
        recordOwner: 'default-scenario',
        mergePolicy: 'copy-only',
      },
    },
    {
      entity: 'DemoPermission',
      sourcePath: 'auth.permissions',
      indexedDbTable: tableRef('auth.permissions').table,
      primaryKey: 'id',
      minItems: tableRef('auth.permissions').minItems ?? 1,
      fields: [
        field('id', 'identifier'),
        field('code', 'identifier'),
        field('label', 'displayName'),
      ],
      references: [],
      ownership: {
        recordOwner: 'default-scenario',
        mergePolicy: 'copy-only',
      },
    },
  ],
  stateMachines: [
    {
      field: 'status',
      allowedStates: ['0', '1'],
      defaultState: '0',
      terminalStates: ['1'],
      transitions: [
        { from: '0', to: ['0', '1'] },
        { from: '1', to: ['0', '1'] },
      ],
      illegalCombinations: [
        {
          fields: ['auth.accounts.roleIds', 'auth.roles.roleId'],
          reason: 'Account roleIds must resolve to copied default roles.',
        },
      ],
      defaultRepair: 'copy-default',
    },
  ],
  invariants: moduleSummaryInvariant('auth', 'auth_copy_only'),
  diversityRules: [],
  materializationPolicy: sourcePaths.map((sourcePath, index) => ({
    sourcePath,
    order: (index + 1) * 100000,
    materializationReason: 'copied-default' as const,
    minItems: tableRef(sourcePath).minItems ?? 0,
  })),
  copyOnly: {
    source: 'demo-contract/default-scenario.json',
    sourcePaths,
    reason: 'Authentication, roles, permissions, and tokens are runtime bootstrap records and must not be semantically generated.',
    minItems: Object.fromEntries(sourcePaths.map((sourcePath) => [sourcePath, tableRef(sourcePath).minItems ?? 0])),
  },
  migrationSources: [
    'DEMO_MODULE_CONTRACTS.auth',
    'DEMO_INDEXED_DB_MAPPING.auth.*',
    'DEMO_HANDLER_COVERAGE.auth',
    'defaultDemoScenario.auth',
  ],
} as const satisfies DemoDomcModuleContract;
