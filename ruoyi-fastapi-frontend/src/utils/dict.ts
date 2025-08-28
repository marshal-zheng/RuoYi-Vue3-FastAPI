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

/**
 * 获取字典数据
 */
export function useDict(...args: string[]) {
  const res = ref<Record<string, DictItem[]>>({});
  return (() => {
    args.forEach((dictType: string, index: number) => {
      res.value[dictType] = [];
      const dicts = useDictStore().getDict(dictType);
      if (dicts) {
        res.value[dictType] = dicts;
      } else {
        getDicts(dictType).then((resp: any) => {
          res.value[dictType] = resp.data.map((p: DictDataItem) => ({
            label: p.dictLabel,
            value: p.dictValue,
            elTagType: p.listClass,
            elTagClass: p.cssClass,
          }));
          useDictStore().setDict(dictType, res.value[dictType]);
        });
      }
    });
    return toRefs(res.value);
  })();
}
