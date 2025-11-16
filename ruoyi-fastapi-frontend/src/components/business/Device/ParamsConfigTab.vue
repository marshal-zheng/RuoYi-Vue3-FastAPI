<template>
  <div class="params-config-content">
    <!-- 端口基本信息 -->
    <el-descriptions :column="2" border class="port-basic-info">
      <el-descriptions-item label="端口名称">{{ portInfo.interfaceName }}</el-descriptions-item>
      <el-descriptions-item label="总线类型">{{ portInfo.interfaceType }}</el-descriptions-item>
      <el-descriptions-item label="端口位置" :span="2">{{ positionLabel }}</el-descriptions-item>
    </el-descriptions>

    <!-- 参数配置表单 -->
    <el-form
      ref="paramsFormRef"
      :model="paramsForm"
      :rules="paramsFormRules"
      label-position="top"
      class="params-form"
    >
      <!-- RS422/RS485 参数 -->
      <template v-if="portInfo.interfaceType === 'RS422' || portInfo.interfaceType === 'RS485'">
        <el-form-item label="波特率" prop="baudRate">
          <BaudRateSelector
            v-model="paramsForm.baudRate"
            interface-type="serial"
            placeholder="请选择波特率"
          />
        </el-form-item>
        <el-form-item label="数据位" prop="dataBits">
          <DataBitsSelector
            v-model="paramsForm.dataBits"
            placeholder="请选择数据位"
          />
        </el-form-item>
        <el-form-item label="停止位" prop="stopBits">
          <StopBitsSelector
            v-model="paramsForm.stopBits"
            placeholder="请选择停止位"
          />
        </el-form-item>
        <el-form-item label="校验方式" prop="parity">
          <ParitySelector
            v-model="paramsForm.parity"
            placeholder="请选择校验方式"
          />
        </el-form-item>
      </template>

      <!-- CAN 参数 -->
      <template v-if="portInfo.interfaceType === 'CAN'">
        <el-form-item label="波特率" prop="baudRate">
          <BaudRateSelector
            v-model="paramsForm.baudRate"
            interface-type="can"
            placeholder="请选择波特率"
          />
        </el-form-item>
        <el-form-item label="工作模式" prop="canMode">
          <CanModeSelector v-model="paramsForm.canMode" />
        </el-form-item>
      </template>

      <!-- LAN 参数 -->
      <template v-if="portInfo.interfaceType === 'LAN'">
        <el-form-item label="IP 地址" prop="ipAddress">
          <el-input v-model="paramsForm.ipAddress" placeholder="请输入 IP 地址，如：192.168.1.100" />
        </el-form-item>
        <el-form-item label="端口号" prop="port">
          <el-input-number v-model="paramsForm.port" :min="1" :max="65535" placeholder="请输入端口号" />
        </el-form-item>
        <el-form-item label="协议类型" prop="protocol">
          <ProtocolSelector v-model="paramsForm.protocol" />
        </el-form-item>
      </template>

      <!-- 1553B 参数 -->
      <template v-if="portInfo.interfaceType === '1553B'">
        <el-form-item label="总线地址" prop="busAddress">
          <el-input-number v-model="paramsForm.busAddress" :min="0" :max="31" placeholder="请输入总线地址 (0-31)" />
        </el-form-item>
        <el-form-item label="RT 地址" prop="rtAddress">
          <el-input-number v-model="paramsForm.rtAddress" :min="0" :max="31" placeholder="请输入 RT 地址 (0-31)" />
        </el-form-item>
        <el-form-item label="子地址" prop="subAddress">
          <el-input-number v-model="paramsForm.subAddress" :min="0" :max="31" placeholder="请输入子地址 (0-31)" />
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<script setup name="ParamsConfigTab">
import { ref, reactive, computed, watch } from 'vue'
import {
  BaudRateSelector,
  DataBitsSelector,
  StopBitsSelector,
  ParitySelector,
  CanModeSelector,
  ProtocolSelector
} from './selector'

const props = defineProps({
  portInfo: {
    type: Object,
    default: () => ({})
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

// 表单引用
const paramsFormRef = ref()

// 参数配置表单数据
const paramsForm = reactive({
  // RS422/RS485 参数
  baudRate: 115200,
  dataBits: 8,
  stopBits: 1,
  parity: 'None',
  // CAN 参数
  canMode: 'A',
  // LAN 参数
  ipAddress: '',
  port: 8080,
  protocol: 'TCP',
  // 1553B 参数
  busAddress: 0,
  rtAddress: 0,
  subAddress: 0
})

// 监听表单数据变化，向父组件发送更新
watch(paramsForm, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听父组件传入的数据变化
watch(() => props.modelValue, (newValue) => {
  if (newValue && Object.keys(newValue).length > 0) {
    Object.assign(paramsForm, newValue)
  }
}, { immediate: true, deep: true })

// 监听端口信息变化，重新初始化表单
watch(() => props.portInfo, () => {
  initParamsForm()
}, { immediate: true })

// IP 地址验证
const validateIpAddress = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入 IP 地址'))
  } else {
    const ipPattern = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
    if (!ipPattern.test(value)) {
      callback(new Error('请输入正确的 IP 地址格式'))
    } else {
      callback()
    }
  }
}

// 表单验证规则（根据总线类型动态设置）
const paramsFormRules = computed(() => {
  const rules = {}
  const busType = props.portInfo.interfaceType
  
  if (busType === 'RS422' || busType === 'RS485') {
    rules.baudRate = [{ required: true, message: '请选择波特率', trigger: 'change' }]
    rules.dataBits = [{ required: true, message: '请选择数据位', trigger: 'change' }]
    rules.stopBits = [{ required: true, message: '请选择停止位', trigger: 'change' }]
    rules.parity = [{ required: true, message: '请选择校验方式', trigger: 'change' }]
  } else if (busType === 'CAN') {
    rules.baudRate = [{ required: true, message: '请选择波特率', trigger: 'change' }]
    rules.canMode = [{ required: true, message: '请选择工作模式', trigger: 'change' }]
  } else if (busType === 'LAN') {
    rules.ipAddress = [{ required: true, validator: validateIpAddress, trigger: 'blur' }]
    rules.port = [{ required: true, message: '请输入端口号', trigger: 'blur' }]
    rules.protocol = [{ required: true, message: '请选择协议类型', trigger: 'change' }]
  } else if (busType === '1553B') {
    rules.busAddress = [{ required: true, message: '请输入总线地址', trigger: 'blur' }]
    rules.rtAddress = [{ required: true, message: '请输入 RT 地址', trigger: 'blur' }]
    rules.subAddress = [{ required: true, message: '请输入子地址', trigger: 'blur' }]
  }
  
  return rules
})

// 端口位置标签
const positionLabel = computed(() => {
  const positionMap = {
    left: '左侧',
    right: '右侧',
    top: '顶部',
    bottom: '底部'
  }
  return positionMap[props.portInfo.position] || props.portInfo.position
})

/** 初始化参数表单 */
function initParamsForm() {
  // 从 portInfo 中加载已有的参数配置（深拷贝避免引用问题）
  if (props.portInfo.params) {
    Object.assign(paramsForm, JSON.parse(JSON.stringify(props.portInfo.params)))
  } else {
    // 设置默认值
    resetParamsForm()
  }
}

/** 重置参数表单为默认值 */
function resetParamsForm() {
  const busType = props.portInfo.interfaceType
  
  if (busType === 'RS422' || busType === 'RS485') {
    paramsForm.baudRate = 115200
    paramsForm.dataBits = 8
    paramsForm.stopBits = 1
    paramsForm.parity = 'None'
  } else if (busType === 'CAN') {
    paramsForm.baudRate = 250000
    paramsForm.canMode = 'A'
  } else if (busType === 'LAN') {
    paramsForm.ipAddress = '192.168.1.100'
    paramsForm.port = 8080
    paramsForm.protocol = 'TCP'
  } else if (busType === '1553B') {
    paramsForm.busAddress = 0
    paramsForm.rtAddress = 0
    paramsForm.subAddress = 0
  }
}

/** 验证表单 */
function validate() {
  return new Promise((resolve) => {
    if (!paramsFormRef.value) {
      resolve(true)
      return
    }
    
    paramsFormRef.value.validate((valid) => {
      resolve(valid)
    })
  })
}

/** 清除验证 */
function clearValidate() {
  paramsFormRef.value?.clearValidate()
}

/** 获取当前表单数据 */
function getFormData() {
  const busType = props.portInfo.interfaceType
  let params = {}
  
  if (busType === 'RS422' || busType === 'RS485') {
    params = {
      baudRate: paramsForm.baudRate,
      dataBits: paramsForm.dataBits,
      stopBits: paramsForm.stopBits,
      parity: paramsForm.parity
    }
  } else if (busType === 'CAN') {
    params = {
      baudRate: paramsForm.baudRate,
      canMode: paramsForm.canMode
    }
  } else if (busType === 'LAN') {
    params = {
      ipAddress: paramsForm.ipAddress,
      port: paramsForm.port,
      protocol: paramsForm.protocol
    }
  } else if (busType === '1553B') {
    params = {
      busAddress: paramsForm.busAddress,
      rtAddress: paramsForm.rtAddress,
      subAddress: paramsForm.subAddress
    }
  }
  
  return params
}

// 暴露方法给父组件
defineExpose({
  validate,
  clearValidate,
  getFormData,
  resetParamsForm
})
</script>

<style lang="scss" scoped>
.params-config-content {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.port-basic-info {
  margin-bottom: 24px;
}

.params-form {
  :deep(.el-form-item) {
    margin-bottom: 22px;
  }
  
  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number) {
    width: 100%;
  }
}
</style>