<template>
  <ZxDialog
    v-bind="exportDialog.dialogProps.value"
    v-on="exportDialog.dialogEvents.value"
    :draggable="false"
    :show-full-screen="false"
    :destroy-on-close="false"
    :close-on-click-modal="true"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" v-bind="exportDialog.formProps"
      ><FormGrid v-bind="exportDialog.layoutProps">
        <el-form-item label="文件类型" prop="fileType">
          <FileTypeSelector v-model="form.fileType" placeholder="请选择文件类型" clearable />
        </el-form-item>

        <el-form-item label="文件名称" prop="fileName">
          <zx-input v-model="form.fileName" placeholder="请输入文件名称" clearable />
        </el-form-item> </FormGrid
    ></el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取 消</el-button>
        <el-button type="primary" @click="handleExport" :loading="loading">
          <el-icon><Download /></el-icon>
          <span style="margin-left: 4px">导 出</span>
        </el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup name="ExportDialog">
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

import { Download } from '@element-plus/icons-vue';
import { FileTypeSelector } from './selector';

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  projectData: {
    type: Object,
    default: () => ({}),
  },
});

// Emits
const emit = defineEmits(['update:modelValue', 'export']);

// Reactive data
const formRef = ref();
const loading = ref(false);

const exportDialog = useFormDialog({
  columns: 1,
  formRef,
  title: '导出项目',
  closeOnClickModal: true,
  destroyOnClose: false,
  preValidate: false,
  autoResetForm: false,
  defaultData: () => ({
    fileType: 'xlsx',
    fileName: props.projectData.projectName ? `${props.projectData.projectName}_导出` : '项目导出',
  }),
});
const form = toRef(exportDialog.state, 'data');

const rules = {
  fileType: [{ required: true, message: '请选择文件类型', trigger: 'change' }],
  fileName: [
    { required: true, message: '请输入文件名称', trigger: 'blur' },
    { min: 1, max: 50, message: '文件名称长度在 1 到 50 个字符', trigger: 'blur' },
  ],
};

// Computed
const visible = toRef(exportDialog.state, 'visible');
watch(visible, (value) => emit('update:modelValue', value));

// Watch
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      // 弹框打开时，初始化表单数据
      exportDialog.open();
    } else {
      exportDialog.close();
    }
  },
  { immediate: true }
);

const handleClose = () => {
  visible.value = false;
  resetForm();
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

const handleExport = async () => {
  try {
    const valid = await formRef.value.validate();
    if (!valid) return;

    loading.value = true;

    // 构造导出参数
    const exportParams = {
      projectId: props.projectData.projectId,
      projectName: props.projectData.projectName,
      fileType: form.value.fileType,
      fileName: form.value.fileName,
    };

    // 触发导出事件
    emit('export', exportParams);

    // 模拟导出过程
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // 关闭弹框
    handleClose();

    // 显示成功消息
    ElMessage.success(`${form.value.fileName}.${form.value.fileType} 导出成功！`);
  } catch (error) {
    console.error('导出失败:', error);
    ElMessage.error('导出失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 获取文件类型对应的图标
const getFileTypeIcon = (type) => {
  const iconMap = {
    doc: Document,
    xlsx: Grid,
    xml: DocumentCopy,
  };
  return iconMap[type] || Document;
};
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>
