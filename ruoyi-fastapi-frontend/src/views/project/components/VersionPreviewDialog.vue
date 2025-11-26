<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <RichEditor v-model="state.data.description" :bordered="false" auto-height />
  </ZxDialog>
</template>

<script setup name="VersionPreviewDialog">
import { useDialog } from '@zxio/zxui';
import { Editor as RichEditor } from '@/components/RichEditor';

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  title: '预览版本',
  width: '90%',
  height: '80%',
  okText: '确定',
  defaultData: () => ({
    versionNumber: '',
    versionName: '',
    description: '',
  }),
  onConfirm: async () => {
    console.log('富文本编辑器内容:', state.data.description);
    throw new Error('测试弹窗确认的报错');
    return state.data;
  },
});

function openDialog(data) {
  open({
    versionNumber: data?.versionNumber || '',
    versionName: data?.versionName || '',
    description: data?.description || '<p style="color: #909399;">暂无描述内容</p>',
  });
}

defineExpose({ open: openDialog, close });
</script>

<style scoped lang="less">
.version-preview-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-header {
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.preview-info {
  display: flex;
  align-items: center;
  font-size: 14px;

  .info-label {
    color: #606266;
    font-weight: 500;
  }

  .info-value {
    color: #303133;
    margin-right: 16px;
  }

  :deep(.el-divider--vertical) {
    margin: 0 12px;
  }
}

.preview-body {
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
}
</style>
