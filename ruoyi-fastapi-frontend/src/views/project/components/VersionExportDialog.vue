<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form label-width="80px" label-position="left">
      <el-form-item label="版本名称">
        <span class="text-gray-700">{{ state.data.versionName }}</span>
      </el-form-item>
      <el-form-item label="导出格式" required>
        <FileTypeSelector v-model="state.data.format" style="width: 100%" />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup name="VersionExportDialog">
import { getCurrentInstance } from 'vue';
import { useDialog } from '@zxio/zxui';
import { exportProjectVersion, exportProjectVersionExcel } from '@/api/project/version';
import { FileTypeSelector } from './selector';

const { proxy } = getCurrentInstance();

const { state, dialogProps, dialogEvents, open, close } = useDialog({
  title: '导出版本',
  width: '500px',
  okText: '确定导出',
  defaultData: () => ({
    versionId: null,
    versionName: '',
    format: 'word',
  }),
  onConfirm: async (data) => {
    if (!data.format) {
      proxy.$modal.msgError('请选择导出格式');
      return;
    }

    let response;
    let mimeType = 'application/octet-stream';
    let extension = '';

    if (data.format === 'word') {
      response = await exportProjectVersion(data.versionId);
      mimeType = 'application/msword';
      extension = 'doc';
    } else if (data.format === 'excel') {
      response = await exportProjectVersionExcel(data.versionId);
      mimeType = 'application/zip';
      extension = 'zip';
    } else if (data.format === 'xml') {
      response = await exportProjectVersion(data.versionId);
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

    proxy.$modal.msgSuccess('导出成功');
    return data;
  },
});

function openDialog(row, defaultFormat = 'word') {
  open({
    versionId: row.versionId,
    versionName: row.versionName || '',
    format: defaultFormat || 'word',
  });
}

defineExpose({ open: openDialog, close });
</script>
