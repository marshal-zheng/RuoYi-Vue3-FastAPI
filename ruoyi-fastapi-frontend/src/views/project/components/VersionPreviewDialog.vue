<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <RichEditor v-model="state.data.description" :bordered="false" auto-height />
  </ZxDialog>
</template>

<script setup name="VersionPreviewDialog">
import { useDialog } from '@zxio/zxui';
import { Editor as RichEditor } from '@/components/ui/RichEditor';

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  dialogSize: 'xl',
  title: '预览版本',

  okText: '确定',
  defaultData: () => ({
    versionNumber: '',
    versionName: '',
    description: '',
  }),
});

function openDialog(data) {
  open({
    versionNumber: data?.versionNumber || '',
    versionName: data?.versionName || '',
    description: data?.description || '<p>暂无描述内容</p>',
  });
}

defineExpose({ open: openDialog, close });
</script>
