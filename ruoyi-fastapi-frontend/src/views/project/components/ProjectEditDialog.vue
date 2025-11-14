<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <div class="dialog-form-container">
      <el-form
        ref="formRef"
        :model="state.data"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="项目名称" prop="projectName">
          <el-input v-model="state.data.projectName" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="state.data.description" 
            type="textarea" 
            placeholder="请输入项目描述"
            :rows="4"
          />
        </el-form-item>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup name="ProjectEditDialog">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useDialog } from '@zxio/zxui'
import { getProject, addProject, updateProject } from "@/api/project"

// 定义组件的 emits
const emit = defineEmits(['success'])

// 表单引用
const formRef = ref()

// 表单验证规则
const formRules = computed(() => ({
  projectName: [
    { required: true, message: "项目名称不能为空", trigger: "blur" }
  ]
}))

// 使用 useDialog hook
const { state, dialogProps, dialogEvents, open, close, setLoading } = useDialog({
  // 动态标题
  title: (data) => {
    return data.projectId ? "修改项目" : "添加项目"
  },

  // 对话框配置
  width: '500px',

  // 表单配置
  formRef: formRef,
  preValidate: true,
  autoScrollToError: true,

  // 默认数据
  defaultData: () => ({
    projectId: null,
    projectName: "",
    description: ""
  }),

  // 数据转换
  dataTransform: (raw) => ({
    projectId: raw.projectId || null,
    projectName: raw.projectName || "",
    description: raw.description || ""
  }),

  // 确认回调
  onConfirm: async (data) => {
    if (data.projectId) {
      // 修改
      const response = await updateProject(data)
      ElMessage.success("修改成功")
      emit('success')
      return response
    } else {
      // 新增
      const response = await addProject(data)
      ElMessage.success("新增成功")
      emit('success')
      return response
    }
  },

  // 错误处理回调
  onConfirmError: (error) => {
    const errorMsg = error?.response?.data?.message || error?.message || '操作失败，请重试'
    ElMessage.error(errorMsg)
  }
})

/** 获取项目详情 */
async function getProjectInfo(projectId) {
  const response = await getProject(projectId)
  return response.data
}

/** 打开弹框 */
async function openDialog(projectId) {
  if (projectId) {
    // 编辑模式，先获取数据再打开
    const projectData = await getProjectInfo(projectId)
    open(projectData)
  } else {
    // 新增模式
    open()
  }
}

// 暴露方法给父组件调用
defineExpose({
  open: openDialog,
  close
})
</script>

<style scoped lang="scss">
.dialog-form-container {
  padding: 16px 0;
}
</style>






