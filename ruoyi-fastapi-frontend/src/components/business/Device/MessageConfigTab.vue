<template>
  <div class="message-config-tab">
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <el-button type="primary" icon="Upload" size="small" @click="handleImport">导入文件</el-button>
      <el-button type="primary" icon="Plus" size="small" @click="handleAddField">添加字段</el-button>
      <el-button type="danger" icon="Delete" size="small" @click="handleDeleteSelected">删除选中</el-button>
    </div>

    <!-- VXE Table - 包含基本信息和字段列表 -->
    <div class="message-table-wrapper">
      <!-- 表格头部 - 报文基本信息 -->
      <table class="message-header-table" border="1" cellspacing="0">
        <tbody>
          <tr>
            <td class="header-label">发送方</td>
            <td class="header-value" colspan="5">
              <el-input v-model="messageHeader.sender" size="small" placeholder="设备1" />
            </td>
          </tr>
          <tr>
            <td class="header-label">接收方</td>
            <td class="header-value" colspan="5">
              <el-input v-model="messageHeader.receiver" disabled size="small" placeholder="" />
            </td>
          </tr>
          <tr>
            <td class="header-label">传输频率</td>
            <td class="header-value">
              <el-select v-model="messageHeader.frequency" size="small" placeholder="请选择">
                <el-option label="单次" value="once" />
                <el-option label="周期" value="periodic" />
              </el-select>
            </td>
            <td class="header-label">传输速率/bps</td>
            <td class="header-value" colspan="3">
              <el-input-number v-model="messageHeader.baudRate" size="small" :min="1" :controls="false" />
            </td>
          </tr>
          <tr>
            <td class="header-label">传输方式</td>
            <td class="header-value">
              <el-input v-model="messageHeader.method" size="small" placeholder="422" />
            </td>
            <td class="header-label">发送时长/ms</td>
            <td class="header-value" colspan="3">
              <el-input-number v-model="messageHeader.duration" size="small" :min="0" :controls="false" />
            </td>
          </tr>
          <tr>
            <td class="header-label">帧长度/Byte</td>
            <td class="header-value">
              <el-input-number v-model="messageHeader.frameLength" size="small" :min="1" :controls="false" />
            </td>
            <td class="header-label">错误处理</td>
            <td class="header-value" colspan="3">
              <el-select v-model="messageHeader.errorHandling" size="small" placeholder="请选择">
                <el-option label="忽略" value="ignore" />
                <el-option label="重传" value="retransmit" />
                <el-option label="告警" value="alert" />
              </el-select>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 字段列表表格 -->
      <vxe-table
        ref="tableRef"
        border
        resizable
        show-overflow
        keep-source
        :data="messageFields"
        :tree-config="{ transform: true, rowField: 'id', parentField: 'parentId' }"
        :edit-config="{ trigger: 'click', mode: 'cell' }"
        :checkbox-config="{ checkField: 'checked' }"
        height="400"
        class="fields-table"
      >
        <vxe-column type="checkbox" width="60" fixed="left" />
        <vxe-column type="seq" width="60" title="序号" tree-node />
        
        <vxe-column 
          field="fieldName" 
          title="信息名称" 
          width="180" 
          :edit-render="{ name: 'input' }"
        />
        
        <vxe-column 
          field="byteCount" 
          title="字节数" 
          width="100" 
          :edit-render="{ name: 'input', props: { type: 'number' } }"
        />
        
        <vxe-column 
          field="byteSequence" 
          title="字节序号" 
          width="120" 
          :edit-render="{ name: 'input', props: { placeholder: '0~3' } }"
        />
        
        <vxe-column 
          field="valueRange" 
          title="值域及含义" 
          width="200" 
          :edit-render="{ name: 'textarea' }"
        />
        
        <vxe-column 
          field="unit" 
          title="量纲" 
          width="100" 
          :edit-render="{ name: 'input' }"
        />
        
        <vxe-column 
          field="dataType" 
          title="数据类型" 
          width="120"
          :edit-render="{
            name: 'select',
            options: [
              { value: 'UINT8', label: 'UINT8' },
              { value: 'UINT16', label: 'UINT16' },
              { value: 'UINT32', label: 'UINT32' },
              { value: 'INT8', label: 'INT8' },
              { value: 'INT16', label: 'INT16' },
              { value: 'INT32', label: 'INT32' },
              { value: 'FLOAT', label: 'FLOAT' },
              { value: 'DOUBLE', label: 'DOUBLE' },
              { value: 'STRING', label: 'STRING' }
            ]
          }"
        >
          <template #default="slotProps">
            <el-tag
              v-if="slotProps?.row?.dataType"
              :type="getDataTypeTagType(slotProps.row.dataType)"
              size="small"
            >
              {{ slotProps.row.dataType }}
            </el-tag>
          </template>
        </vxe-column>
        
        <vxe-column 
          field="scale" 
          title="比例尺" 
          width="100" 
          :edit-render="{ name: 'input' }"
        />
        
        <vxe-column title="操作" width="150" fixed="right">
          <template #default="slotProps">
            <el-button
              v-if="slotProps?.row"
              link
              type="danger"
              size="small"
              @click="handleDelete(slotProps.row)"
            >
              删除
            </el-button>
          </template>
        </vxe-column>
      </vxe-table>
    </div>

    <!-- 导入文件对话框 -->
    <ImportFileDialog
      v-model="importDialogVisible"
      @confirm="handleImportConfirm"
    />
  </div>
</template>

<script setup name="MessageConfigTab">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ImportFileDialog } from './index'

const props = defineProps({
  portInfo: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

// 表格引用
const tableRef = ref()

// 导入对话框显示状态
const importDialogVisible = ref(false)

// 默认报文头信息
const getDefaultHeader = () => ({
  sender: '设备1',
  receiver: '',
  frequency: 'once',
  baudRate: 460,
  method: '422',
  duration: 6,
  frameLength: 256,
  errorHandling: 'ignore'
})

// 默认报文字段数据
const getDefaultFields = () => [
  {
    id: '1',
    parentId: null,
    fieldName: '同步码1',
    byteCount: 1,
    byteSequence: '0',
    valueRange: '0xEB',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '2',
    parentId: null,
    fieldName: '同步码2',
    byteCount: 1,
    byteSequence: '1',
    valueRange: '0x90',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '3',
    parentId: null,
    fieldName: '报文字节数',
    byteCount: 2,
    byteSequence: '2~3',
    valueRange: '0x0100',
    unit: '',
    dataType: 'UINT16',
    scale: '1'
  },
  {
    id: '4',
    parentId: null,
    fieldName: '发送方节点号',
    byteCount: 4,
    byteSequence: '4~7',
    valueRange: '0x15: 设备1',
    unit: '',
    dataType: 'UINT32',
    scale: '1'
  },
  {
    id: '5',
    parentId: null,
    fieldName: '接收方节点号',
    byteCount: 4,
    byteSequence: '8~11',
    valueRange: '0x00010000: 1号\n0x00020000: 2号\n0x00040000: 3号',
    unit: '',
    dataType: 'UINT32',
    scale: '1'
  },
  {
    id: '6',
    parentId: null,
    fieldName: '帧类别',
    byteCount: 1,
    byteSequence: '12',
    valueRange: '0x02: 有线上行信息',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '7',
    parentId: null,
    fieldName: '指令ID',
    byteCount: 1,
    byteSequence: '13',
    valueRange: '0x70: 参数信息',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '8',
    parentId: null,
    fieldName: '帧计数',
    byteCount: 2,
    byteSequence: '14~15',
    valueRange: '[0,65535]',
    unit: '',
    dataType: 'UINT16',
    scale: '1'
  },
  {
    id: '9',
    parentId: null,
    fieldName: '装定点数量',
    byteCount: 1,
    byteSequence: '16',
    valueRange: '1~16',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '10',
    parentId: null,
    fieldName: '预留',
    byteCount: 2,
    byteSequence: '17~18',
    valueRange: '',
    unit: '',
    dataType: '',
    scale: '1'
  },
  {
    id: '11',
    parentId: null,
    fieldName: '点1',
    byteCount: 9,
    byteSequence: '19~27',
    valueRange: '',
    unit: '',
    dataType: '',
    scale: ''
  },
  {
    id: '11-1',
    parentId: '11',
    fieldName: '点序号',
    byteCount: 1,
    byteSequence: '19',
    valueRange: '1~16',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  },
  {
    id: '11-2',
    parentId: '11',
    fieldName: '经度',
    byteCount: 4,
    byteSequence: '20~23',
    valueRange: '-180~180°',
    unit: '',
    dataType: 'FLOAT',
    scale: '10^7'
  },
  {
    id: '11-3',
    parentId: '11',
    fieldName: '纬度',
    byteCount: 4,
    byteSequence: '24~27',
    valueRange: '-90~90°',
    unit: '',
    dataType: 'FLOAT',
    scale: '10^7'
  },
  {
    id: '18',
    parentId: null,
    fieldName: 'CRC-16',
    byteCount: 2,
    byteSequence: '254~255',
    valueRange: '',
    unit: '',
    dataType: 'UINT16',
    scale: '1'
  }
]

// 报文头信息
const messageHeader = reactive(getDefaultHeader())

// 报文字段数据
const messageFields = ref(getDefaultFields())

// 数据类型标签颜色
function getDataTypeTagType(dataType) {
  const typeMap = {
    'UINT8': 'success',
    'UINT16': 'success',
    'UINT32': 'success',
    'INT8': 'warning',
    'INT16': 'warning',
    'INT32': 'warning',
    'FLOAT': 'info',
    'DOUBLE': 'info',
    'STRING': ''
  }
  return typeMap[dataType] || ''
}

// 打开导入对话框
function handleImport() {
  importDialogVisible.value = true
}

// 处理导入确认
function handleImportConfirm(data) {
  if (data.fields && data.fields.length > 0) {
    // 替换当前字段数据
    messageFields.value = data.fields.map(field => ({
      ...field,
      id: field.id || Date.now().toString() + Math.random(),
      parentId: field.parentId || null
    }))
    ElMessage.success(`成功导入 ${data.fields.length} 个字段`)
  }
  
  // 如果有表头信息，也更新表头
  if (data.header) {
    Object.assign(messageHeader, data.header)
  }
}

// 添加字段
function handleAddField() {
  const newId = Date.now().toString()
  messageFields.value.push({
    id: newId,
    parentId: null,
    fieldName: '新字段',
    byteCount: 1,
    byteSequence: '',
    valueRange: '',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  })
}

// 添加子项
function handleAddChild(row) {
  const newId = `${row.id}-${Date.now()}`
  messageFields.value.push({
    id: newId,
    parentId: row.id,
    fieldName: '子字段',
    byteCount: 1,
    byteSequence: '',
    valueRange: '',
    unit: '',
    dataType: 'UINT8',
    scale: '1'
  })
  ElMessage.success('子字段已添加')
}

// 删除字段
function handleDelete(row) {
  ElMessageBox.confirm('确定要删除该字段吗？', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = messageFields.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      // 同时删除子项
      messageFields.value = messageFields.value.filter(item => 
        item.id !== row.id && item.parentId !== row.id
      )
      ElMessage.success('删除成功')
    }
  }).catch(() => {})
}

// 删除选中
function handleDeleteSelected() {
  const selectRecords = tableRef.value.getCheckboxRecords()
  if (!selectRecords || selectRecords.length === 0) {
    ElMessage.warning('请先选择要删除的字段')
    return
  }
  
  ElMessageBox.confirm(`确定要删除选中的 ${selectRecords.length} 个字段吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const deleteIds = selectRecords.map(item => item.id)
    messageFields.value = messageFields.value.filter(item => 
      !deleteIds.includes(item.id) && !deleteIds.includes(item.parentId)
    )
    ElMessage.success('删除成功')
  }).catch(() => {})
}

// 获取表单数据
function getFormData() {
  return {
    header: { ...messageHeader },
    fields: messageFields.value
  }
}

// 验证表单
async function validate() {
  // 简单验证
  if (!messageHeader.sender) {
    ElMessage.error('请输入发送方')
    return false
  }
  // if (!messageHeader.receiver) {
  //   ElMessage.error('请输入接收方')
  //   return false
  // }
  return true
}

// 清除验证
function clearValidate() {
  // VXE Table 不需要清除验证
}

// 初始化数据
function initializeData() {
  if (props.portInfo.messageConfig) {
    // 加载已有配置（深拷贝避免引用问题）
    Object.assign(messageHeader, JSON.parse(JSON.stringify(props.portInfo.messageConfig.header)))
    messageFields.value = JSON.parse(JSON.stringify(props.portInfo.messageConfig.fields || []))
  } else {
    // 重置为默认值
    Object.assign(messageHeader, getDefaultHeader())
    messageFields.value = getDefaultFields()
  }
}

// 监听 portInfo 变化，每次打开不同端口时重新加载数据
watch(() => props.portInfo, () => {
  initializeData()
}, { deep: true, immediate: true })

// 暴露方法
defineExpose({
  getFormData,
  validate,
  clearValidate
})
</script>

<style lang="scss" scoped>
.message-config-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}

.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
}

.message-table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

// 报文基本信息表格样式
.message-header-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: -1px; // 与下方表格边框重叠
  background: white;
  font-size: 14px;
  
  td {
    border: 1px solid #e8eaec;
    padding: 8px 12px;
    line-height: 1.5;
  }
  
  .header-label {
    background-color: #f8f8f9;
    font-weight: 500;
    color: #515a6e;
    width: 120px;
    text-align: right;
    white-space: nowrap;
  }
  
  .header-value {
    background-color: white;
    
    :deep(.el-input),
    :deep(.el-select),
    :deep(.el-input-number) {
      width: 100%;
    }
    
    :deep(.el-input__wrapper),
    :deep(.el-input-number__wrapper) {
      box-shadow: none;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
    }
    
    :deep(.el-input__inner) {
      height: 28px;
      line-height: 28px;
    }
  }
}

// 字段列表表格样式
.fields-table {
  flex: 1;
  
  :deep(.vxe-table) {
    border-top: none; // 与上方表格连接
  }
  
  :deep(.vxe-body--row.row--hover) {
    background-color: #f5f7fa;
  }
  
  :deep(.vxe-cell) {
    padding: 4px 8px;
  }
  
  :deep(.vxe-input),
  :deep(.vxe-select),
  :deep(.vxe-textarea) {
    width: 100%;
  }
  
  :deep(.vxe-tree--indent) {
    width: 16px;
  }
}
</style>
