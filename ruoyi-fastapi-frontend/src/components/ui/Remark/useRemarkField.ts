import { ref } from 'vue';
import { readRemark } from './contract';
import type RemarkEditor from './RemarkEditor.vue';

/** Native ElForm keeps ownership; this only contributes its normal field rule. */
export function useRemarkField() {
  const remarkRef = ref<InstanceType<typeof RemarkEditor>>();
  const remarkRule = {
    validator: (_rule: unknown, value: unknown, callback: (error?: Error) => void) => {
      // The editor's own reason (unfinished input, a content limit) comes first.
      if (remarkRef.value && !remarkRef.value.validate()) {
        callback(new Error(remarkRef.value.blockingReason() ?? '请完成备注编辑并检查内容限制'));
        return;
      }
      try {
        readRemark(value);
        callback();
      } catch (error) {
        callback(error instanceof Error ? error : new Error('备注格式不正确'));
      }
    },
    trigger: 'change',
  };
  return { remarkRef, remarkRule };
}
