<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="formRef"
      :model="state.data"
      :rules="formRules"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="公告标题" prop="noticeTitle">
          <zx-input v-model="state.data.noticeTitle" placeholder="请输入公告标题" />
        </el-form-item>

        <el-form-item label="公告类型" prop="noticeType">
          <DictSelect
            dict-type="sys_notice_type"
            :active="state.visible"
            v-model="state.data.noticeType"
            placeholder="请选择"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item data-form-full label="状态">
          <DictStatus :types="['sys_notice_status']" />
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

import { getNotice, addNotice, updateNotice } from '@/api/system/notice';
import { useEditorRead } from '@/utils/editor-read';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import Editor from '@/components/ui/Editor/index.vue';
import { ref } from 'vue';
import { useDict } from '@/utils/dict';

// 延迟加载字典数据
const { sys_notice_status } = useDict('sys_notice_status');

interface NoticeForm {
  noticeId?: number;
  noticeTitle?: string;
  noticeType?: '1' | '2';
  noticeContent?: string;
  status?: '0' | '1';
}

const detailLoading = ref(false);
let requestedId: number | undefined;

const emit = defineEmits(['success']);

const formRules = {
  noticeTitle: [{ required: true, message: '公告标题不能为空', trigger: 'blur' }],
  noticeType: [{ required: true, message: '公告类型不能为空', trigger: 'change' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close, setDisabled } =
  useFormDialog<NoticeForm>({
    loading: detailLoading,
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
      if (detailLoading.value || loadError.value || data.noticeId !== requestedId) return false;
      if (data.noticeId !== undefined) {
        await updateNotice(data);
      } else {
        await addNotice(data);
      }
      emit('success');
      return true;
    },
  });

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);

function openDialog(id?: number) {
  requestedId = id;
  return runRead(async (read) => {
    open(id ? { noticeId: id } : undefined);
    setDisabled(true);
    if (!id) {
      setDisabled(false);
      return;
    }
    const data = await getNotice(id, { signal: read.signal, silentError: true });
    if (!read.isCurrent()) return;
    open({
      noticeId: data.noticeId ?? undefined,
      noticeTitle: data.noticeTitle ?? undefined,
      noticeType: data.noticeType ?? undefined,
      noticeContent: data.noticeContent ?? undefined,
      status: data.status ?? '0',
    });
    setDisabled(false);
  });
}
function closeDialog() {
  cancelRead();
  return close();
}
function handleRetry() {
  return openDialog(requestedId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

defineExpose({ open: openDialog, close: closeDialog });
</script>
