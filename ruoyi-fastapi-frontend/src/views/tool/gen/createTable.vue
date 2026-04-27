<template>
  <!-- 创建表 -->
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="create-table-content">
      <div class="mb-3">创建表语句(支持多个建表语句)：</div>
      <el-input type="textarea" :rows="10" placeholder="请输入建表语句" v-model="state.data.sql" />
    </div>
  </ZxDialog>
</template>

<script setup>
import { ElMessage } from 'element-plus';
import { createTable } from '@/api/tool/gen';
import { useDialog } from '@zxio/zxui';

const emit = defineEmits(['ok']);

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  title: '创建表',
  width: '800px',
  defaultData: () => ({ sql: '' }),
  onConfirm: handleImportTable,
});

/** 显示弹框 */
function show() {
  open({ sql: '' });
}

/** 导入按钮操作 */
function handleImportTable() {
  if (state.data.sql === '') {
    ElMessage.error('请输入建表语句');
    return Promise.reject();
  }
  return createTable({ sql: state.data.sql }).then(() => {
    close();
    emit('ok');
  });
}

defineExpose({
  show,
});
</script>

<style scoped>
.create-table-content {
  padding: 8px 0;
}

.mb-3 {
  margin-bottom: 12px;
  color: var(--el-text-color-regular);
  font-size: 14px;
}
</style>
