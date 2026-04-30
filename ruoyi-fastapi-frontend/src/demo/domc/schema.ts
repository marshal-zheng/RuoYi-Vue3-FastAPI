import type { DemoDomcRegistry } from './types';

type JsonSchema = Record<string, unknown>;

const stringSchema = { type: 'string', minLength: 1 } as const;
const numberSchema = { type: 'number' } as const;
const booleanSchema = { type: 'boolean' } as const;

function objectSchema(
  required: readonly string[],
  properties: Record<string, JsonSchema>,
  additionalProperties = false
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

const qualityGateSchema = objectSchema(['gate', 'severity', 'description'], {
  gate: stringSchema,
  severity: { enum: ['error', 'warning'] },
  description: stringSchema,
});

const indexedDbTableSchema = objectSchema(
  ['table', 'sourcePath', 'primaryKey', 'indexes'],
  {
    table: stringSchema,
    sourcePath: stringSchema,
    primaryKey: stringSchema,
    indexes: arraySchema(stringSchema),
    minItems: numberSchema,
  },
  false
);

const handlerCoverageSchema = objectSchema(
  ['module', 'source', 'apiPrefix', 'coveredRoutes', 'unsupportedBehavior'],
  {
    module: stringSchema,
    source: stringSchema,
    apiPrefix: stringSchema,
    coveredRoutes: arraySchema(stringSchema, 1),
    unsupportedBehavior: { enum: ['DEMO_API_NOT_IMPLEMENTED', 'DEMO_NOT_SUPPORTED'] },
  },
  false
);

const fieldSchema = objectSchema(['name', 'required', 'nullable', 'semanticKind'], {
  name: stringSchema,
  required: booleanSchema,
  nullable: booleanSchema,
  semanticKind: {
    enum: [
      'identifier',
      'displayName',
      'description',
      'status',
      'enum',
      'timestamp',
      'owner',
      'department',
      'metric',
      'risk',
      'money',
      'quantity',
      'foreignKey',
      'opaquePayload',
    ],
  },
  enumValues: arraySchema(stringSchema),
  defaultRepair: { enum: ['derive', 'copy-default', 'block'] },
});

const referenceSchema = objectSchema(['field', 'targetEntity', 'targetField', 'relation', 'required'], {
  field: stringSchema,
  targetEntity: stringSchema,
  targetField: stringSchema,
  relation: { enum: ['one-to-one', 'many-to-one', 'one-to-many', 'many-to-many'] },
  required: booleanSchema,
});

const entitySchema = objectSchema(
  ['entity', 'sourcePath', 'indexedDbTable', 'primaryKey', 'minItems', 'fields', 'references', 'ownership'],
  {
    entity: stringSchema,
    sourcePath: stringSchema,
    indexedDbTable: stringSchema,
    primaryKey: stringSchema,
    minItems: numberSchema,
    fields: arraySchema(fieldSchema, 1),
    references: arraySchema(referenceSchema),
    ownership: objectSchema(['recordOwner', 'mergePolicy'], {
      recordOwner: { enum: ['adapter', 'default-scenario', 'runtime-required'] },
      mergePolicy: { enum: ['replace-sourcePath', 'append-shards', 'copy-only'] },
    }),
  }
);

const uiJourneySchema = objectSchema(
  [
    'journeyId',
    'entry',
    'primarySourcePath',
    'requiredSupportSourcePaths',
    'listFields',
    'detailFields',
    'keyActions',
    'emptyState',
    'errorState',
    'minimumDemoChain',
  ],
  {
    journeyId: stringSchema,
    entry: stringSchema,
    primarySourcePath: stringSchema,
    requiredSupportSourcePaths: arraySchema(stringSchema),
    listFields: arraySchema(stringSchema, 1),
    detailFields: arraySchema(stringSchema, 1),
    keyActions: arraySchema(
      objectSchema(['action', 'demoBehavior'], {
        action: stringSchema,
        demoBehavior: stringSchema,
      }),
      1
    ),
    emptyState: stringSchema,
    errorState: stringSchema,
    minimumDemoChain: arraySchema(stringSchema, 1),
  }
);

const diversityRuleSchema = objectSchema(
  [
    'ruleId',
    'primarySourcePath',
    'fields',
    'dimensions',
    'duplicateThreshold',
    'templateSimilarityThreshold',
    'severity',
    'explainableExceptions',
  ],
  {
    ruleId: stringSchema,
    primarySourcePath: stringSchema,
    fields: arraySchema(stringSchema, 1),
    dimensions: arraySchema(stringSchema, 1),
    duplicateThreshold: numberSchema,
    templateSimilarityThreshold: numberSchema,
    severity: { enum: ['error', 'warning'] },
    explainableExceptions: arraySchema(stringSchema),
  }
);

const moduleSchema = objectSchema(
  [
    'moduleId',
    'moduleVersion',
    'lifecycle',
    'capability',
    'owner',
    'sourcePaths',
    'indexedDbTables',
    'handlerCoverage',
    'uiJourneys',
    'entities',
    'stateMachines',
    'invariants',
    'diversityRules',
    'materializationPolicy',
    'migrationSources',
  ],
  {
    moduleId: stringSchema,
    moduleVersion: stringSchema,
    lifecycle: { enum: ['active', 'deprecated', 'experimental'] },
    capability: { enum: ['generatable', 'copyOnly', 'unsupported'] },
    owner: stringSchema,
    sourcePaths: arraySchema(stringSchema, 1),
    indexedDbTables: arraySchema(indexedDbTableSchema, 1),
    handlerCoverage: arraySchema(handlerCoverageSchema, 1),
    uiJourneys: arraySchema(uiJourneySchema, 1),
    entities: arraySchema(entitySchema, 1),
    stateMachines: arraySchema(
      objectSchema(['field', 'allowedStates', 'defaultState', 'terminalStates', 'transitions', 'illegalCombinations', 'defaultRepair'], {
        field: stringSchema,
        allowedStates: arraySchema(stringSchema, 1),
        defaultState: stringSchema,
        terminalStates: arraySchema(stringSchema),
        transitions: arraySchema(
          objectSchema(['from', 'to'], {
            from: stringSchema,
            to: arraySchema(stringSchema),
          })
        ),
        illegalCombinations: arraySchema(
          objectSchema(['fields', 'reason'], {
            fields: arraySchema(stringSchema, 1),
            reason: stringSchema,
          })
        ),
        defaultRepair: { enum: ['derive', 'copy-default', 'block'] },
      })
    ),
    invariants: arraySchema(
      objectSchema(['id', 'description', 'severity', 'paths'], {
        id: stringSchema,
        description: stringSchema,
        severity: { enum: ['error', 'warning'] },
        paths: arraySchema(stringSchema, 1),
      })
    ),
    diversityRules: arraySchema(diversityRuleSchema),
    semanticAnchors: arraySchema(
      objectSchema(['ruleId', 'sourcePath', 'minAnchorTypes', 'requiredAnchorTypes', 'supportCategories'], {
        ruleId: stringSchema,
        sourcePath: stringSchema,
        minAnchorTypes: numberSchema,
        requiredAnchorTypes: arraySchema(stringSchema, 1),
        supportCategories: arraySchema(stringSchema),
      })
    ),
    materializationPolicy: arraySchema(
      objectSchema(['sourcePath', 'order', 'materializationReason', 'minItems'], {
        sourcePath: stringSchema,
        order: numberSchema,
        materializationReason: { enum: ['semantic-generated', 'copied-default', 'runtime-required'] },
        minItems: numberSchema,
      }),
      1
    ),
    adapterRef: objectSchema(['adapterId', 'adapterVersionRange', 'capabilities', 'outputSourcePaths'], {
      adapterId: stringSchema,
      adapterVersionRange: stringSchema,
      capabilities: arraySchema(stringSchema, 1),
      outputSourcePaths: arraySchema(stringSchema, 1),
      priority: numberSchema,
    }),
    copyOnly: objectSchema(['source', 'sourcePaths', 'reason', 'minItems'], {
      source: { enum: ['demo-contract/default-scenario.json', 'bundle-default-v2'] },
      sourcePaths: arraySchema(stringSchema, 1),
      reason: stringSchema,
      minItems: { type: 'object', additionalProperties: { type: 'number' } },
    }),
    unsupportedReason: stringSchema,
    migrationSources: arraySchema(stringSchema, 1),
  }
);

export const demoDomcRegistryJsonSchema = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  title: 'DemoDomcRegistry',
  type: 'object',
  required: [
    'schemaVersion',
    'registryVersion',
    'generatedAt',
    'domcFingerprint',
    'contractVersion',
    'platformLayer',
    'modules',
    'qualityGates',
    'migrationSources',
  ],
  additionalProperties: false,
  properties: {
    schemaVersion: { enum: [1] },
    registryVersion: stringSchema,
    generatedAt: stringSchema,
    domcFingerprint: { type: 'string', pattern: '^[a-f0-9]{64}$' },
    contractVersion: { enum: [1] },
    platformLayer: { enum: ['DOMC'] },
    modules: arraySchema(moduleSchema, 1),
    qualityGates: arraySchema(qualityGateSchema, 1),
    migrationSources: arraySchema(stringSchema, 1),
  },
} as const satisfies JsonSchema;

export type DemoDomcRegistryJsonSchema = typeof demoDomcRegistryJsonSchema;

export type DemoDomcRegistryJson = DemoDomcRegistry;
