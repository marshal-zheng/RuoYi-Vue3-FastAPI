<template>
  <!-- 创建表 -->
  <ZxDialog
    v-model="visible"
    title="创建表"
    width="800px"
    @confirm="handleImportTable"
  >
    <div class="create-table-content">
      <div class="mb-3">创建表语句(支持多个建表语句)：</div>
      <el-input
        type="textarea"
        :rows="10"
        placeholder="请输入建表语句"
        v-model="content"
      />
    </div>
  </ZxDialog>
</template>

<script setup>
import { createTable } from '@/api/tool/gen';

const visible = ref(false);
const content = ref('');
const { proxy } = getCurrentInstance();
const emit = defineEmits(['ok']);

/** 显示弹框 */
function show() {
  content.value = '';
  visible.value = true;
}

/** 导入按钮操作 */
function handleImportTable() {
  if (content.value === '') {
    proxy.$modal.msgError('请输入建表语句');
    return Promise.reject();
  }
  return createTable({ sql: content.value }).then(() => {
    visible.value = false;
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
