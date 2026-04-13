<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form :model="state.data" :rules="formRules" label-width="80px">
      <el-row>
        <el-col :span="12">
          <el-form-item label="公告标题" prop="noticeTitle">
            <el-input v-model="state.data.noticeTitle" placeholder="请输入公告标题" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
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
        </el-col>
        <el-col :span="24">
          <el-form-item label="状态">
            <el-radio-group v-model="state.data.status">
              <el-radio v-for="dict in sys_notice_status" :key="dict.value" :value="dict.value">
                {{ dict.label }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="内容">
            <editor v-model="state.data.noticeContent" :min-height="192" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </ZxDialog>
</template>

<script setup lang="ts" name="NoticeDlg">
import { addNotice, updateNotice } from '@/api/system/notice';
import { useDialog } from '@zxio/zxui';
import { ElMessage } from 'element-plus';
import { ref } from 'vue';

const proxy = getCurrentInstance()?.proxy as any;

// 延迟加载字典数据
const sys_notice_status = ref<any[]>([]);
const sys_notice_type = ref<any[]>([]);
let dictLoaded = false;

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

const { state, dialogProps, dialogEvents, open } = useDialog<NoticeForm>({
  title: (data: NoticeForm) => (data?.noticeId ? '修改公告' : '添加公告'),
  width: '780px',
  defaultData: () => ({
    noticeId: undefined,
    noticeTitle: undefined,
    noticeType: undefined,
    noticeContent: undefined,
    status: '0',
  }),
  onOpen: () => {
    // 只在第一次打开时加载字典
    if (!dictLoaded) {
      const dict = proxy.useDict('sys_notice_status', 'sys_notice_type');
      sys_notice_status.value = dict.sys_notice_status?.value || [];
      sys_notice_type.value = dict.sys_notice_type?.value || [];
      dictLoaded = true;
    }
  },
  onConfirm: async (data: NoticeForm) => {
    if (data.noticeId !== undefined) {
      await updateNotice(data);
      ElMessage.success('修改成功');
    } else {
      await addNotice(data);
      ElMessage.success('新增成功');
    }
    emit('success');
    return true;
  },
  onConfirmError: (e: any) => {
    ElMessage.error(e?.message || '提交失败，请重试');
  },
});

defineExpose({ open });
</script>
