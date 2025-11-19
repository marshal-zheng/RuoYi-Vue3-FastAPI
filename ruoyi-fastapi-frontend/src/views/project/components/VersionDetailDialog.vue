<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <template #descValue="{ item }">
      <template v-if="item.label === '固化状态'">
        <el-tag v-if="versionData.isLocked === '1'" type="warning">
          <el-icon class="mr-1"><Lock /></el-icon>
          已固化
        </el-tag>
        <el-tag v-else type="info">未固化</el-tag>
      </template>
      <template v-else>
        {{ item.value || '-' }}
      </template>
    </template>
  </ZxDialog>
</template>

<script setup name="VersionDetailDialog">
import { ref, computed } from 'vue';
import { Lock } from '@element-plus/icons-vue';
import { parseTime } from '@/utils/ruoyi';
import { useDialog } from '@zxio/zxui';

const versionData = ref({});

const descriptionItems = computed(() => {
  const items = [
    { label: '版本号', value: versionData.value.versionNumber },
    { label: '版本名称', value: versionData.value.versionName },
    { label: '版本描述', value: versionData.value.description },
  ];

  if (versionData.value.isLocked === '1') {
    items.push({ label: '固化状态', value: '已固化' });
    if (versionData.value.lockedBy) {
      items.push({ label: '固化人', value: versionData.value.lockedBy });
    }
    if (versionData.value.lockedTime) {
      items.push({ label: '固化时间', value: parseTime(versionData.value.lockedTime) });
    }
  } else {
    items.push({ label: '固化状态', value: '未固化' });
  }

  items.push(
    { label: '创建人', value: versionData.value.createBy },
    { label: '创建时间', value: parseTime(versionData.value.createTime) }
  );

  return items;
});

const dialog = useDialog({
  title: '查看版本详情',
  width: '600px',
  descriptions: descriptionItems,
  footer: false,
});

const open = (data) => {
  versionData.value = data;
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
.mr-1 {
  margin-right: 4px;
}
</style>
