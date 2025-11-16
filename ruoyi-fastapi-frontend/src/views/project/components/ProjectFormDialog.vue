<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="py-4">
      <el-form
        ref="formRef"
        :model="state.data"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="工程名称" prop="projectName">
          <el-input v-model="state.data.projectName" placeholder="请输入工程名称" />
        </el-form-item>
        <el-form-item label="工程描述" prop="projectDesc">
          <el-input v-model="state.data.projectDesc" type="textarea" :rows="4" placeholder="请输入工程描述" />
        </el-form-item>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup>
import { ref, computed, getCurrentInstance } from 'vue'
import { useDialog } from '@zxio/zxui'
import { ElMessage } from 'element-plus'
import { getProject, addProject, updateProject } from '@/api/project/project'

const emit = defineEmits(['success'])

const formRef = ref()

const formRules = computed(() => ({
  projectName: [{ required: true, message: '工程名称不能为空', trigger: 'blur' }]
}))

const { state, dialogProps, dialogEvents, open, close, setLoading } = useDialog({
  title: (data) => (data?.projectId ? '编辑工程' : '添加工程'),
  width: '600px',
  okText: computed(() => (state.data.projectId ? '保存' : '创建')),
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    projectId: null,
    projectName: '',
    projectDesc: ''
  }),
  onConfirm: async (data) => {
    if (data.projectId) {
      const res = await updateProject(data)
      ElMessage.success('修改成功')
      emit('success', res)
      return res
    }
    const res = await addProject(data)
    ElMessage.success('新增成功')
    emit('success', res)
    return res
  },
  onConfirmError: (e) => {
    ElMessage.error(e?.message || '提交失败，请重试')
  }
})

async function openDialog(payload) {
  if (payload && (payload.projectId || typeof payload === 'number' || typeof payload === 'string')) {
    const id = payload.projectId || payload
    setLoading(true)
    try {
      const resp = await getProject(id)
      const detail = resp?.data || {}
      open({
        projectId: detail.projectId,
        projectName: detail.projectName,
        projectDesc: detail.projectDesc
      })
    } finally {
      setLoading(false)
    }
  } else {
    open()
  }
}

defineExpose({ open: openDialog, close })
</script>

<style scoped>
</style>