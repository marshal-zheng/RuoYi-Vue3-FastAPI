import { shallowRef, watch } from 'vue';
import { provideAIContextScope, type AIContextBindings } from '@zxio/zxui/ai-context';
import { aiContextDefinitions } from './definitions';

/** Observe the owning form clock, never execute a deferred context getter for revision tracking. */
export function useAIContextHost(
  name: keyof typeof aiContextDefinitions,
  options: {
    instanceKey: () => string | number;
    revisionSource: () => unknown;
    bindings: AIContextBindings;
  }
) {
  const revision = shallowRef(0);
  watch(
    options.revisionSource,
    () => {
      revision.value++;
    },
    { deep: true, flush: 'sync' }
  );
  return provideAIContextScope(aiContextDefinitions[name], {
    instanceKey: options.instanceKey,
    revision: () => revision.value,
    bindings: options.bindings,
  });
}
