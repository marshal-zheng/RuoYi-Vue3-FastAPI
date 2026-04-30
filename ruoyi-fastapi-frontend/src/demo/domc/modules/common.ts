import {
  DEMO_HANDLER_COVERAGE,
  DEMO_INDEXED_DB_MAPPING,
  DEMO_INVARIANTS,
  DEMO_MODULE_CONTRACTS,
} from '../../scenarios/contract';
import type {
  DemoDomcFieldContract,
  DemoDomcFieldSemanticKind,
  DemoDomcHandlerCoverageRef,
  DemoDomcIndexedDbTableRef,
  DemoDomcInvariantRef,
} from '../types';

export function tableRef(sourcePath: string): DemoDomcIndexedDbTableRef {
  const table = DEMO_INDEXED_DB_MAPPING.tables.find((item) => item.sourcePath === sourcePath);
  if (!table) {
    throw new Error(`DOMC sourcePath "${sourcePath}" is missing from DEMO_INDEXED_DB_MAPPING.`);
  }
  return table;
}

export function tableRefs(sourcePaths: readonly string[]): DemoDomcIndexedDbTableRef[] {
  return sourcePaths.map(tableRef);
}

export function handlerRefs(modules: readonly string[]): DemoDomcHandlerCoverageRef[] {
  return DEMO_HANDLER_COVERAGE.filter((handler) => modules.includes(handler.module));
}

export function invariantRefs(ids: readonly string[]): DemoDomcInvariantRef[] {
  return DEMO_INVARIANTS.filter((invariant) => ids.includes(invariant.id));
}

export function moduleSummaryInvariant(moduleId: string, fallbackId: string): DemoDomcInvariantRef[] {
  const summary = DEMO_MODULE_CONTRACTS.find((contract) => contract.module === moduleId);
  return (summary?.invariants ?? []).map((description, index) => ({
    id: `${fallbackId}_${index + 1}`,
    description,
    severity: 'error',
    paths: [moduleId],
  }));
}

export function field(
  name: string,
  semanticKind: DemoDomcFieldSemanticKind,
  options: Partial<Pick<DemoDomcFieldContract, 'required' | 'nullable' | 'enumValues' | 'defaultRepair'>> = {}
): DemoDomcFieldContract {
  return {
    name,
    required: options.required ?? true,
    nullable: options.nullable ?? false,
    semanticKind,
    ...(options.enumValues ? { enumValues: options.enumValues } : {}),
    defaultRepair: options.defaultRepair ?? (options.required === false ? 'derive' : 'block'),
  };
}
