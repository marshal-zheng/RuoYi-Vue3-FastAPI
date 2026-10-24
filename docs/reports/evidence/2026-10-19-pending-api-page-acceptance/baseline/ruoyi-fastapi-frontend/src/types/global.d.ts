import type modal from '@/plugins/modal';
/** Global component helpers retain the exact signatures of their implementations. */
import type { HttpClientImpl } from '@zxio/http';
import type { useDict } from '@/utils/dict';
import type { download } from '@/utils/request';
import type {
  parseTime,
  resetForm,
  handleTree,
  addDateRange,
  selectDictLabel,
  selectDictLabels,
} from '@/utils/ruoyi';

declare module 'vue' {
  interface GlobalComponents {
    DictSelect: (typeof import('@/components/business/DictSelect/index.vue'))['default'];
    DictTypeSelect: (typeof import('@/components/business/DictTypeSelect/index.vue'))['default'];
    DictStatus: (typeof import('@/components/business/DictStatus/index.vue'))['default'];
    DictTag: (typeof import('@/components/ui/DictTag/index.vue'))['default'];
  }

  interface ComponentCustomProperties {
    $http: HttpClientImpl;
    $modal: typeof modal;
    useDict: typeof useDict;
    download: typeof download;
    parseTime: typeof parseTime;
    resetForm: typeof resetForm;
    handleTree: typeof handleTree;
    addDateRange: typeof addDateRange;
    selectDictLabel: typeof selectDictLabel;
    selectDictLabels: typeof selectDictLabels;
  }
}
