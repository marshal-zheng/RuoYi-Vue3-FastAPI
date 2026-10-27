import { onScopeDispose, shallowRef, watch } from 'vue';
import {
  isAIContextReady,
  provideAIContextStatus,
  type AIContextStatus,
} from '@zxio/zxui/ai-context';
import { getTextFieldAIStatus } from '@/api/system/textFieldAi';
import useUserStore from '@/store/modules/user';
import { manifestRevision } from './manifest-revision';

const unavailable = (): AIContextStatus => ({
  state: 'unavailable',
  contract: 'ai-context/v1',
  manifestRevision: null,
  policyRevision: null,
  policy: null,
});
const status = shallowRef<AIContextStatus>(unavailable());
let active = false;
let request: AbortController | undefined;

export async function reloadAIContextStatus() {
  request?.abort();
  const controller = new AbortController();
  request = controller;
  status.value = { ...unavailable(), state: 'loading' };
  if (!active || !useUserStore().token) {
    status.value = unavailable();
    return;
  }
  try {
    const wire = await getTextFieldAIStatus({ signal: controller.signal });
    if (controller.signal.aborted) return;
    const candidate: AIContextStatus = {
      state: 'ready',
      contract: wire.contract ?? 'ai-context/v1',
      manifestRevision: wire.manifestRevision ?? null,
      policyRevision: wire.policyRevision ?? null,
      policy:
        wire.policy && wire.providerClass
          ? {
              ...wire.policy,
              maxItems: wire.policy.maxItems ?? 0,
              maxChars: wire.policy.maxChars ?? 0,
              providerClass: wire.providerClass,
            }
          : null,
    };
    status.value =
      wire.available === true &&
      wire.contract === 'ai-context/v1' &&
      wire.manifestRevision === manifestRevision &&
      isAIContextReady(candidate)
        ? candidate
        : unavailable();
  } catch {
    if (!controller.signal.aborted) status.value = unavailable();
  }
}

export function useAIContextStatusProvider() {
  active = true;
  provideAIContextStatus(() => status.value);
  watch(
    () => useUserStore().token,
    () => {
      void reloadAIContextStatus();
    },
    { immediate: true, flush: 'sync' }
  );
  onScopeDispose(() => {
    active = false;
    request?.abort();
    status.value = unavailable();
  });
  return status;
}
