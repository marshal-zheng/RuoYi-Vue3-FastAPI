import projectOverlays from "./registry/project.json";
import simulationOverlays from "./registry/simulation.json";
import topologyOverlays from "./registry/topology.json";
import versionOverlays from "./registry/version.json";
import type {
  MockOverlayRegistryEntry,
  MockOverlayRegistrySummary,
} from "./types";

export * from "./types";

const registryDocuments = [
  projectOverlays,
  versionOverlays,
  topologyOverlays,
  simulationOverlays,
] as unknown as MockOverlayRegistryEntry[][];

function cloneEntry(entry: MockOverlayRegistryEntry): MockOverlayRegistryEntry {
  const composition = {
    ...(entry.composition.compatibleWith
      ? { compatibleWith: [...entry.composition.compatibleWith] }
      : {}),
    ...(entry.composition.conflictsWith
      ? { conflictsWith: [...entry.composition.conflictsWith] }
      : {}),
  };

  return {
    ...entry,
    target: { ...entry.target },
    pages: [...entry.pages],
    tests: [...entry.tests],
    composition,
    ...(entry.contract ? { contract: { ...entry.contract } } : {}),
    ...(entry.response ? { response: { ...entry.response } } : {}),
  };
}

export function sortMockOverlayEntries<
  T extends Pick<MockOverlayRegistryEntry, "id" | "target" | "coreMatrix">,
>(entries: T[]): T[] {
  return [...entries].sort(
    (left, right) =>
      Number(right.coreMatrix) - Number(left.coreMatrix) ||
      left.target.openapiPath.localeCompare(right.target.openapiPath) ||
      left.target.method.localeCompare(right.target.method) ||
      left.id.localeCompare(right.id),
  );
}

export function validateMockOverlayRegistryEntries(
  entries: MockOverlayRegistryEntry[],
): void {
  const seenIds = new Set<string>();

  entries.forEach((entry) => {
    if (seenIds.has(entry.id)) {
      throw new Error(`Duplicate mock overlay id: ${entry.id}`);
    }
    seenIds.add(entry.id);

    const selfConflicts = entry.composition.conflictsWith?.includes(entry.id);
    if (selfConflicts) {
      throw new Error(`Mock overlay ${entry.id} cannot conflict with itself.`);
    }

    const selfCompatible = entry.composition.compatibleWith?.includes(entry.id);
    if (selfCompatible) {
      throw new Error(
        `Mock overlay ${entry.id} cannot be compatible with itself.`,
      );
    }
  });
}

export function loadMockOverlayRegistry(
  documents: MockOverlayRegistryEntry[][] = registryDocuments,
): MockOverlayRegistryEntry[] {
  const entries = documents.flatMap((document) => document.map(cloneEntry));
  validateMockOverlayRegistryEntries(entries);
  return sortMockOverlayEntries(entries);
}

export function listMockOverlaySummaries(
  entries: MockOverlayRegistryEntry[] = loadMockOverlayRegistry(),
): MockOverlayRegistrySummary[] {
  return sortMockOverlayEntries(entries).map((entry) => ({
    id: entry.id,
    name: entry.name,
    stateType: entry.stateType,
    method: entry.target.method,
    openapiPath: entry.target.openapiPath,
    mswPath: entry.target.mswPath,
    handlerTag: entry.target.handlerTag,
    pages: [...entry.pages],
    owner: entry.owner,
    tests: [...entry.tests],
    coreMatrix: entry.coreMatrix,
    e2eEnabled: entry.e2eEnabled,
    resetStrategy: entry.resetStrategy,
    risk: entry.risk,
  }));
}

export function getMockOverlayEntry(
  id: string,
): MockOverlayRegistryEntry | undefined {
  return loadMockOverlayRegistry().find((entry) => entry.id === id);
}

export const mockOverlayRegistry = loadMockOverlayRegistry();
