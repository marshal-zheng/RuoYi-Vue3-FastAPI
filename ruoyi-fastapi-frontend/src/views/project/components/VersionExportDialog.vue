<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form ref="formRef" v-bind="formProps" label-position="left">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="版本名称">
          <span class="text-gray-700">{{ state.data.versionName }}</span>
        </el-form-item>
        <el-form-item label="导出格式" required>
          <FileTypeSelector v-model="state.data.format" style="width: 100%" />
        </el-form-item>
      </FormGrid>
    </el-form>
    <div v-if="exporting" class="export-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在生成拓扑图...</span>
    </div>
  </ZxDialog>
</template>

<script setup name="VersionExportDialog">
const formRef = ref();

import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import {
  exportProjectVersion,
  exportProjectVersionExcel,
  exportProjectVersionXml,
} from '@/api/project/version';
import { exportTopologyAsImage } from '../composables/topoExportUtils';
import { FileTypeSelector } from './selector';

const exporting = ref(false);

const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close } = useFormDialog({
  columns: 1,
  formRef: formRef,
  title: '导出版本',

  okText: '确定导出',
  defaultData: () => ({
    versionId: null,
    projectId: null,
    versionName: '',
    format: 'word',
  }),
  onConfirm: async (data) => {
    if (!data.format) {
      ElMessage.error('请选择导出格式');
      return;
    }

    let response;
    let mimeType = 'application/octet-stream';
    let extension = '';

    if (data.format === 'word') {
      exporting.value = true;
      let imageBase64 = null;

      // 生成拓扑图图片
      if (data.projectId) {
        imageBase64 = await exportTopologyAsImage({
          projectId: data.projectId,
          versionId: data.versionId,
        });
      }
      exporting.value = false;

      // 调用导出接口，传递图片数据
      response = await exportProjectVersion({
        versionId: data.versionId,
        imageBase64: imageBase64,
      });
      mimeType = 'application/msword';
      extension = 'doc';
    } else if (data.format === 'excel') {
      response = await exportProjectVersionExcel(data.versionId);
      mimeType = 'application/zip';
      extension = 'zip';
    } else if (data.format === 'xml') {
      response = await exportProjectVersionXml(data.versionId);
      mimeType = 'application/xml';
      extension = 'xml';
    }

    const blob = new Blob([response], { type: mimeType });
    const suffixName =
      data.format === 'excel' ? '附录表' : data.format === 'xml' ? '接口控制文件' : '接口控制文件';
    const fileName = `${data.versionName || '接口控制文件'}_${suffixName}.${extension}`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);

    return data;
  },
});

function openDialog(row, defaultFormat = 'word') {
  open({
    versionId: row.versionId,
    projectId: row.projectId,
    versionName: row.versionName || '',
    format: defaultFormat || 'word',
  });
}

defineExpose({ open: openDialog, close });
</script>

<style scoped>
.export-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 0;
  color: var(--el-color-primary);
}
</style>
