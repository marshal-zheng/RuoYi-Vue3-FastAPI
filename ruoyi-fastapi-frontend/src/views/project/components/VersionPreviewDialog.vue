<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <RichEditor
      v-model="versionData.description"
      :editorConfig="{ readOnly: false }"
      height="500px"
    />
  </ZxDialog>
</template>

<script setup name="VersionPreviewDialog">
import { ref } from 'vue';
import { useDialog } from '@zxio/zxui';
import { Editor as RichEditor } from '@/components/RichEditor';

const versionData = ref({
  versionNumber: '',
  versionName: '',
  description: '',
});

const dialog = useDialog({
  title: '预览版本',
  width: '90%',
  height: '80%',
  footer: false,
});

const open = (data) => {
  versionData.value = {
    versionNumber: data.versionNumber || '',
    versionName: data.versionName || '',
    description: data.description || '<p style="color: #909399;">暂无描述内容</p>',
  };
  dialog.open();
};

const close = () => {
  dialog.close();
};

defineExpose({
  open,
  close,
});
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
