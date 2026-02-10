import { ref, toRefs } from 'vue';
import useDictStore from '@/store/modules/dict';
import { getDicts } from '@/api/system/dict/data';

interface DictItem {
  label: string;
  value: string;
  elTagType?: string;
  elTagClass?: string;
}

interface DictDataItem {
  dictLabel: string;
  dictValue: string;
  listClass?: string;
  cssClass?: string;
}

// Track pending dictionary requests to prevent duplicates
const pendingDictRequests = new Map<string, Promise<any>>();

/**
 * 获取字典数据
 */
export function useDict(...args: string[]) {
  console.log(3333)
  const res = ref<Record<string, DictItem[]>>({});
  return (() => {
    args.forEach((dictType: string, index: number) => {
      res.value[dictType] = [];
      const dicts = useDictStore().getDict(dictType);
      if (dicts) {
        res.value[dictType] = dicts;
      } else {
        // Check if there's already a pending request for this dict type
        console.log('dictType', dictType)
        let dictPromise = pendingDictRequests.get(dictType);
        
        if (!dictPromise) {
          // Create new request and cache the promise
          dictPromise = getDicts(dictType)
            .then((resp: any) => {
              const dictData = resp.map((p: DictDataItem) => ({
                label: p.dictLabel,
                value: p.dictValue,
                elTagType: p.listClass,
                elTagClass: p.cssClass,
              }));
              useDictStore().setDict(dictType, dictData);
              return dictData;
            })
            .catch((error: any) => {
              // Silently handle errors to prevent "canceled" toasts
              console.warn(`Failed to load dictionary: ${dictType}`, error);
              return [];
            })
            .finally(() => {
              // Clean up pending request
              pendingDictRequests.delete(dictType);
            });
          
          pendingDictRequests.set(dictType, dictPromise);
        }
        
        // Use the cached promise (either new or existing)
        dictPromise.then((dictData: DictItem[]) => {
          res.value[dictType] = dictData;
        });
      }
    });
    return toRefs(res.value);
  })();
}
