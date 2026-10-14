import { listMockOverlaySummaries, loadMockOverlayRegistry, sortMockOverlayEntries } from './index';
import type {
  MockOverlayActivationInput,
  MockOverlayActivationSource,
  MockOverlayRegistryEntry,
  MockOverlayRegistrySummary,
  MockOverlayState,
} from './types';

export interface MockOverlayRuntimeOptions {
  registry?: MockOverlayRegistryEntry[];
  allowOverlays?: boolean;
  initialOverlays?: MockOverlayActivationInput;
  source?: MockOverlayActivationSource;
}

function emptyState(): MockOverlayState {
  return {
    activeIds: [],
    activeEntries: [],
    source: 'none',
  };
}

function cloneEntry(entry: MockOverlayRegistryEntry): MockOverlayRegistryEntry {
  return {
    ...entry,
    target: { ...entry.target },
    pages: [...entry.pages],
    tests: [...entry.tests],
    composition: {
      ...(entry.composition.compatibleWith
        ? { compatibleWith: [...entry.composition.compatibleWith] }
        : {}),
      ...(entry.composition.conflictsWith
        ? { conflictsWith: [...entry.composition.conflictsWith] }
        : {}),
    },
    ...(entry.contract ? { contract: { ...entry.contract } } : {}),
    ...(entry.response ? { response: { ...entry.response } } : {}),
  };
}

function cloneState(state: MockOverlayState): MockOverlayState {
  return {
    activeIds: [...state.activeIds],
    activeEntries: state.activeEntries.map(cloneEntry),
    source: state.source,
  };
}

function overlayIds(input: MockOverlayActivationInput): string[] {
  if (!input) return [];
  if (Array.isArray(input)) return [...input];
  return [...input.activeIds];
}

function pairKey(entry: MockOverlayRegistryEntry) {
  return `${entry.target.method} ${entry.target.openapiPath}`;
}

function hasIntersection(left: string[], right: string[]) {
  return left.some((item) => right.includes(item));
}

function isCompatible(left: MockOverlayRegistryEntry, right: MockOverlayRegistryEntry) {
  return (
    left.composition.compatibleWith?.includes(right.id) ||
    right.composition.compatibleWith?.includes(left.id)
  );
}

function explicitConflict(left: MockOverlayRegistryEntry, right: MockOverlayRegistryEntry) {
  return (
    left.composition.conflictsWith?.includes(right.id) ||
    right.composition.conflictsWith?.includes(left.id)
  );
}

function sameStateSemantic(left: MockOverlayRegistryEntry, right: MockOverlayRegistryEntry) {
  return (
    left.stateType === right.stateType &&
    left.response?.status === right.response?.status &&
    hasIntersection(left.pages, right.pages)
  );
}

export function resolveMockOverlayEntries(
  input: MockOverlayActivationInput,
  registry: MockOverlayRegistryEntry[] = loadMockOverlayRegistry()
): MockOverlayRegistryEntry[] {
  const ids = overlayIds(input);
  const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
  if (duplicateIds.length) {
    throw new Error(
      `Duplicate overlay activation id(s): ${Array.from(new Set(duplicateIds)).join(', ')}`
    );
  }

  const byId = new Map(registry.map((entry) => [entry.id, entry]));
  const entries = ids.map((id) => {
    const entry = byId.get(id);
    if (!entry) {
      throw new Error(`Unknown mock overlay id: ${id}`);
    }
    return entry;
  });

  for (let leftIndex = 0; leftIndex < entries.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < entries.length; rightIndex += 1) {
      const left = entries[leftIndex];
      const right = entries[rightIndex];
      if (!left || !right) continue;

      if (explicitConflict(left, right)) {
        throw new Error(`Mock overlay conflict: ${left.id} conflicts with ${right.id}.`);
      }

      const sameEndpoint = pairKey(left) === pairKey(right);
      const sameHandler = left.target.handlerTag === right.target.handlerTag;
      if (
        (sameEndpoint || sameHandler || sameStateSemantic(left, right)) &&
        !isCompatible(left, right)
      ) {
        throw new Error(
          `Mock overlay conflict: ${left.id} cannot be combined with ${right.id} without compatibleWith metadata.`
        );
      }
    }
  }

  return sortMockOverlayEntries(entries).map(cloneEntry);
}

export class MockOverlayRuntime {
  private readonly registry: MockOverlayRegistryEntry[];
  private readonly allowOverlays: boolean;
  private state: MockOverlayState = emptyState();

  constructor(options: MockOverlayRuntimeOptions = {}) {
    this.registry = options.registry ?? loadMockOverlayRegistry();
    this.allowOverlays = options.allowOverlays ?? true;

    const ids = overlayIds(options.initialOverlays);
    if (ids.length) {
      this.state = this.resolveState(ids, options.source ?? 'bootstrap');
    }
  }

  listOverlays(): MockOverlayRegistrySummary[] {
    return listMockOverlaySummaries(this.registry);
  }

  getOverlayState(): MockOverlayState {
    return cloneState(this.state);
  }

  activateOverlays(
    ids: string[],
    source: MockOverlayActivationSource = 'runtime-api'
  ): MockOverlayState {
    const nextState = this.resolveState(ids, source);
    this.state = nextState;
    return this.getOverlayState();
  }

  resetOverlays(): MockOverlayState {
    this.state = emptyState();
    return this.getOverlayState();
  }

  private resolveState(ids: string[], source: MockOverlayActivationSource): MockOverlayState {
    if (!this.allowOverlays && ids.length) {
      throw new Error('Mock overlays are not available in the current runtime mode.');
    }

    const activeEntries = resolveMockOverlayEntries(ids, this.registry);
    return {
      activeIds: activeEntries.map((entry) => entry.id),
      activeEntries,
      source: activeEntries.length ? source : 'none',
    };
  }
}

export function createMockOverlayRuntime(options: MockOverlayRuntimeOptions = {}) {
  return new MockOverlayRuntime(options);
}
