import { computed, nextTick, onActivated, toValue, type MaybeRefOrGetter, type Ref } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { dictOptions, dictTypeDetailOptions } from './dict';
import { queryScope } from '../context';

/** The autocomplete, state boundary and legacy aliases share this native observer path. */
export function useDictQuery(type: MaybeRefOrGetter<string>) {
  const options = computed(() => dictOptions(queryScope.value, toValue(type)));
  return bindDictRead(useQuery(options));
}

export function useDictTypeDetailQuery(id: MaybeRefOrGetter<unknown>) {
  return bindDictRead(
    useQuery(computed(() => dictTypeDetailOptions(queryScope.value, toValue(id))))
  );
}

interface DictReadState {
  isEnabled: Readonly<Ref<boolean>>;
  isStale: Readonly<Ref<boolean>>;
  refetch: (options: { cancelRefetch: boolean; throwOnError: boolean }) => Promise<unknown>;
}
function bindDictRead<T extends DictReadState>(query: T) {
  async function refresh(force = true): Promise<void> {
    await nextTick();
    if (!queryScope.value || !query.isEnabled.value) return;
    if (force || query.isStale.value) {
      await query.refetch({ cancelRefetch: false, throwOnError: true });
    }
  }
  const ensureFresh = () => refresh(false);
  onActivated(() => {
    void ensureFresh().catch(() => {
      /* Query state owns the failure. */
    });
  });
  return { query, refresh, ensureFresh };
}
