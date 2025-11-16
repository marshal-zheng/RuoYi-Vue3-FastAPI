<template>
  <el-drawer
    v-model="visible"
    :title="title"
    size="75%"
    direction="rtl"
    @close="onClose"
  >
    <el-tabs v-model="activeTab" class="port-config-tabs">
      <!-- 参数配置 Tab -->
      <el-tab-pane label="参数配置" name="params">
        <ParamsConfigTab
          ref="paramsConfigTabRef"
          :port-info="portInfo"
          v-model="paramsForm"
        />
      </el-tab-pane>

      <!-- 报文配置 Tab -->
      <el-tab-pane label="报文配置" name="message">
        <MessageConfigTab
          ref="messageConfigTabRef"
          :port-info="portInfo"
        />
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="closeDrawer">取消</el-button>
        <el-button type="primary" @click="submitPort">确定</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup name="PortConfigDrawer">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ParamsConfigTab from './ParamsConfigTab.vue'
import MessageConfigTab from './MessageConfigTab.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '端口配置' },
  portInfo: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'close', 'submit'])

// 抽屉显示状态
const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => {
  visible.value = v
})
watch(visible, (v) => emit('update:modelValue', v))

// 当前激活的 Tab
const activeTab = ref('params')

// 表单引用
const paramsConfigTabRef = ref()
const messageConfigTabRef = ref()

// 参数配置表单数据（用于与ParamsConfigTab组件通信）
const paramsForm = reactive({})

/** 提交表单 */
async function submitPort() {
  let dataToSubmit = {
    ...props.portInfo
  }
  
  // 根据当前激活的 Tab 验证和获取数据
  if (activeTab.value === 'params') {
    if (!paramsConfigTabRef.value) {
      visible.value = false
      return
    }
    
    const valid = await paramsConfigTabRef.value.validate()
    if (!valid) return
    
    const params = paramsConfigTabRef.value.getFormData()
    dataToSubmit.params = params
    
    emit('submit', dataToSubmit)
    ElMessage.success('参数配置保存成功')
  } else if (activeTab.value === 'message') {
    if (!messageConfigTabRef.value) {
      visible.value = false
      return
    }
    
    const valid = await messageConfigTabRef.value.validate()
    if (!valid) return
    
    const messageConfig = messageConfigTabRef.value.getFormData()
    dataToSubmit.messageConfig = messageConfig
    
    emit('submit', dataToSubmit)
  }
  
  visible.value = false
}

/** 关闭抽屉 */
function closeDrawer() {
  visible.value = false
}

/** 抽屉关闭回调 */
function onClose() {
  activeTab.value = 'params' // 重置到第一个 tab
  paramsConfigTabRef.value?.clearValidate()
  messageConfigTabRef.value?.clearValidate()
  emit('close')
}
</script>

<style lang="scss" scoped>
.port-config-tabs {
  height: calc(100vh - 180px);
  
  :deep(.el-tabs__content) {
    height: calc(100% - 55px);
    overflow-y: auto;
  }
  
  :deep(.el-tab-pane) {
    height: 100%;
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
}

:deep(.el-drawer__footer) {
  padding: 0;
  margin-top: auto;
}
</style>

