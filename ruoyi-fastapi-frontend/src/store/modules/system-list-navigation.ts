import { ref, watch } from 'vue';
import { defineStore } from 'pinia';
import { queryScope } from '@/queries/context';

type ListName = 'users' | 'roles';
interface ListSnapshot {
  filters: Record<string, string | number | undefined>;
  page: number;
  size: number;
}

/** A return from authorization restores submitted list state, never editor or selection drafts. */
export const useSystemListNavigation = defineStore('system-list-navigation', () => {
  const snapshots = ref<Partial<Record<ListName, ListSnapshot>>>({});
  watch(queryScope, () => (snapshots.value = {}), { flush: 'sync' });

  function remember(name: ListName, snapshot: ListSnapshot): void {
    if (!queryScope.value) return;
    snapshots.value[name] = { ...snapshot, filters: { ...snapshot.filters } };
  }

  function take(name: ListName): ListSnapshot | undefined {
    const snapshot = snapshots.value[name];
    delete snapshots.value[name];
    return snapshot ? { ...snapshot, filters: { ...snapshot.filters } } : undefined;
  }

  return { remember, take };
});
