<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="formRules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="公告标题" prop="noticeTitle">
          <zx-input v-model="state.data.noticeTitle" placeholder="请输入公告标题" />
        </el-form-item>

        <el-form-item label="公告类型" prop="noticeType">
          <el-select v-model="state.data.noticeType" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="dict in sys_notice_type"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item data-form-full label="状态">
          <el-radio-group v-model="state.data.status">
            <el-radio v-for="dict in sys_notice_status" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item data-form-full label="内容">
          <editor v-model="state.data.noticeContent" :min-height="192" />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup lang="ts" name="NoticeDlg">
import type { FormInstance } from 'element-plus';
const formRef = ref<FormInstance>();

import { addNotice, updateNotice } from '@/api/system/notice';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { ref } from 'vue';
import { useDict } from '@/utils/dict';

const proxy = getCurrentInstance()?.proxy as any;

// 延迟加载字典数据
const { sys_notice_status, sys_notice_type } = useDict('sys_notice_status', 'sys_notice_type');

interface NoticeForm {
  noticeId?: number;
  noticeTitle?: string;
  noticeType?: string;
  noticeContent?: string;
  status?: string;
}

const emit = defineEmits(['success']);

const formRules = {
  noticeTitle: [{ required: true, message: '公告标题不能为空', trigger: 'blur' }],
  noticeType: [{ required: true, message: '公告类型不能为空', trigger: 'change' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } =
  useFormDialog<NoticeForm>({
    columns: 2,
    formRef: formRef,
    title: (data: NoticeForm) => (data?.noticeId ? '修改公告' : '添加公告'),

    defaultData: () => ({
      noticeId: undefined,
      noticeTitle: undefined,
      noticeType: undefined,
      noticeContent: undefined,
      status: '0',
    }),
    onConfirm: async (data: NoticeForm) => {
      if (data.noticeId !== undefined) {
        await updateNotice(data);
      } else {
        await addNotice(data);
      }
      emit('success');
      return true;
    },
  });

defineExpose({ open });
</script>
