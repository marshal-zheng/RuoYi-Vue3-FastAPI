import { computed, type Ref } from 'vue';
import { useDictQuery } from '@/queries/system/use-dict-query';
import type { DictItem } from '@/queries/system/dict';

export type { DictItem } from '@/queries/system/dict';
const EMPTY: readonly DictItem[] = Object.freeze([]);

/** Reactive legacy array aliases; public DictStatus and selectors present the same query state. */
export function useDict(...types: string[]): Record<string, Readonly<Ref<readonly DictItem[]>>> {
  return Object.fromEntries(
    types.map((type) => {
      const { query } = useDictQuery(type);
      return [type, computed(() => query.data.value ?? EMPTY)];
    })
  ) as Record<string, Readonly<Ref<readonly DictItem[]>>>;
}
