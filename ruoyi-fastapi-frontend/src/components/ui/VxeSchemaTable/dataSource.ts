import { ref, computed, shallowRef, onMounted } from 'vue';

export type DataSourceItem = Record<string, unknown>;

export type DataSourceFetcher = () => Promise<DataSourceItem[]>;

export type DataSourceOptions = {
  fetch?: DataSourceFetcher;
  static?: DataSourceItem[];
  labelKey?: string;
  valueKey?: string;
  cacheKey?: string;
};

const cacheStore = new Map<string, DataSourceItem[]>();

export function useDataSource(options: DataSourceOptions) {
  const loading = ref(false);
  const error = shallowRef<unknown>(null);
  const items = shallowRef<DataSourceItem[]>([]);

  const labelKey = options.labelKey ?? 'label';
  const valueKey = options.valueKey ?? 'value';

  const transformed = computed(() =>
    (items.value || []).map((item) => ({
      label: item[labelKey],
      value: item[valueKey],
      raw: item,
    }))
  );

  const fetchData = async () => {
    if (options.cacheKey && cacheStore.has(options.cacheKey)) {
      items.value = cacheStore.get(options.cacheKey) || [];
      return;
    }

    if (!options.fetch) return;
    loading.value = true;
    error.value = null;
    try {
      const list = await options.fetch();
      items.value = Array.isArray(list) ? list : [];
      if (options.cacheKey) {
        cacheStore.set(options.cacheKey, items.value);
      }
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    if (options.static) {
      items.value = options.static;
      if (options.cacheKey) cacheStore.set(options.cacheKey, items.value);
      return;
    }
    fetchData();
  });

  return {
    loading,
    error,
    items,
    options: transformed,
    reload: fetchData,
  };
}
