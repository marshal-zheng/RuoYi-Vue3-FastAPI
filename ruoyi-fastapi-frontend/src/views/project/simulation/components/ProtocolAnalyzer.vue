<template>
  <div class="flex flex-col h-full text-slate-300">
    <!-- 工具栏 -->
    <div class="pro-card-header flex justify-between items-center">
      <div class="flex gap-3 items-center">
        <el-select
          v-model="localFilter.protocolType"
          placeholder="协议类型"
          clearable
          size="small"
          class="w-28 sim-select-dark"
          @change="handleFilterChange"
        >
          <el-option label="1553B" value="1553B" />
          <el-option label="CAN" value="CAN" />
          <el-option label="RS422" value="RS422" />
          <el-option label="LAN" value="LAN" />
        </el-select>
        <el-input
          v-model="localFilter.keyword"
          placeholder="搜索关键字"
          clearable
          size="small"
          class="w-36 sim-input-dark"
          @input="handleFilterChange"
        />
        <el-checkbox v-model="localFilter.errorOnly" size="small" @change="handleFilterChange">
          仅显示错误
        </el-checkbox>
      </div>
      <div class="flex gap-3 items-center">
        <el-checkbox v-model="localAutoScroll" size="small" @change="$emit('auto-scroll-change', $event)">
          自动滚动
        </el-checkbox>
        <el-dropdown @command="handleExport">
          <el-button size="small" class="sim-btn-dark">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <span class="text-xs text-slate-500">共 {{ messages.length }} 条</span>
      </div>
    </div>

    <!-- 报文列表 -->
    <div class="flex-1 overflow-hidden" ref="listRef">
      <!-- 表头 -->
      <div class="pro-table-header flex px-4 py-2 border-b border-slate-700/50">
        <span class="w-24">时间</span>
        <span class="w-28">源节点</span>
        <span class="w-28">目标节点</span>
        <span class="w-20">协议</span>
        <span class="w-16">大小</span>
        <span class="flex-1">数据</span>
      </div>
      <!-- 数据行 -->
      <el-table-v2
        v-if="messages.length > 0"
        ref="tableRef"
        :columns="tableColumns"
        :data="messages"
        :width="tableWidth"
        :height="tableHeight"
        :row-height="36"
        :row-class="getRowClass"
        @row-click="handleRowClick"
      />
      <div v-else class="flex flex-col items-center justify-center h-full text-slate-500">
        <el-icon class="text-5xl mb-3"><Document /></el-icon>
        <span class="text-sm">暂无报文数据</span>
      </div>
    </div>

    <!-- 报文详情 -->
    <div v-if="selectedMessage" class="border-t border-slate-700/50 max-h-28 overflow-y-auto bg-slate-900/50">
      <div class="pro-card-header flex justify-between items-center text-xs font-semibold text-slate-300">
        <span>报文详情</span>
        <el-button :icon="Close" circle size="small" @click="selectedMessage = null" />
      </div>
      <div class="p-3">
        <div class="flex flex-wrap gap-1 mb-3">
          <span
            v-for="(byte, index) in parseHex(selectedMessage.payloadHex)"
            :key="index"
            class="px-1 py-0.5 bg-slate-800 rounded text-xs font-mono text-slate-300"
          >
            {{ byte }}
          </span>
        </div>
        <div v-if="selectedMessage.fieldValues" class="flex flex-wrap gap-4">
          <div v-for="(value, key) in selectedMessage.fieldValues" :key="key" class="text-xs">
            <span class="text-slate-500 mr-1">{{ key }}:</span>
            <span class="text-primary-400 font-medium">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { ArrowDown, Document, Close } from '@element-plus/icons-vue'
import { formatTimestamp } from '../utils/timeFormatter'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  isRunning: {
    type: Boolean,
    default: false,
  },
  autoScroll: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['message-select', 'filter-change', 'export', 'auto-scroll-change'])

const tableRef = ref(null)
const listRef = ref(null)
const tableWidth = ref(800)
const tableHeight = ref(200)

const tableColumns = [
  {
    key: 'timestamp',
    dataKey: 'timestamp',
    title: '时间',
    width: 100,
    cellRenderer: ({ cellData }) => formatTime(cellData),
  },
  { key: 'senderNodeName', dataKey: 'senderNodeName', title: '源节点', width: 120 },
  { key: 'receiverNodeName', dataKey: 'receiverNodeName', title: '目标节点', width: 120 },
  { key: 'protocolType', dataKey: 'protocolType', title: '协议', width: 80 },
  {
    key: 'sizeBytes',
    dataKey: 'sizeBytes',
    title: '大小',
    width: 60,
    cellRenderer: ({ cellData }) => `${cellData}B`,
  },
  {
    key: 'payloadHex',
    dataKey: 'payloadHex',
    title: '数据',
    width: 200,
    cellRenderer: ({ cellData }) => truncateHex(cellData),
  },
]

function getRowClass({ rowData }) {
  const classes = []
  if (rowData.isError) classes.push('protocol-analyzer__row--error')
  if (selectedId.value === rowData.messageId) classes.push('protocol-analyzer__row--selected')
  return classes.join(' ')
}

function handleRowClick({ rowData }) {
  handleSelect(rowData)
}

const selectedId = ref(null)
const selectedMessage = ref(null)
const localAutoScroll = ref(props.autoScroll)

const localFilter = ref({
  protocolType: '',
  keyword: '',
  errorOnly: false,
})

function formatTime(timestamp) {
  return formatTimestamp(timestamp)
}

function truncateHex(hex) {
  if (!hex) return ''
  if (hex.length > 32) {
    return hex.substring(0, 32) + '...'
  }
  return hex
}

function parseHex(hex) {
  if (!hex) return []
  const bytes = []
  for (let i = 0; i < hex.length; i += 2) {
    bytes.push(hex.substring(i, i + 2).toUpperCase())
  }
  return bytes
}

function handleSelect(message) {
  selectedId.value = message.messageId
  selectedMessage.value = message
  emit('message-select', message)
}

function handleFilterChange() {
  emit('filter-change', { ...localFilter.value })
}

function handleExport(format) {
  emit('export', format)
}

function scrollToBottom() {
  if (tableRef.value && localAutoScroll.value) {
    nextTick(() => {
      tableRef.value.scrollToBottom?.()
    })
  }
}

watch(
  () => props.messages.length,
  () => {
    if (localAutoScroll.value) {
      scrollToBottom()
    }
  }
)

watch(
  () => props.autoScroll,
  (val) => {
    localAutoScroll.value = val
  }
)

function exportData(format) {
  const data = props.messages

  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    downloadBlob(blob, 'messages.json')
  } else if (format === 'csv') {
    const headers = ['时间', '源节点', '目标节点', '协议', '大小', '数据']
    const rows = data.map((m) => [
      formatTime(m.timestamp),
      m.senderNodeName || m.senderNodeId,
      m.receiverNodeName || m.receiverNodeId,
      m.protocolType,
      m.sizeBytes,
      m.payloadHex,
    ])
    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    downloadBlob(blob, 'messages.csv')
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

defineExpose({ exportData })
</script>

<style scoped>
/* 虚拟表格行样式 - 深色主题 */
:deep(.el-table-v2__row) {
  font-size: 12px;
  font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Courier New', monospace;
  cursor: pointer;
  color: #cbd5e1;
  background-color: transparent;
  transition: all 0.15s ease;
}

:deep(.el-table-v2__row:hover) {
  background-color: rgba(51, 65, 85, 0.4);
}

:deep(.protocol-analyzer__row--selected) {
  background-color: rgba(0, 82, 217, 0.12);
  border-left: 2px solid #0052d9;
}

:deep(.protocol-analyzer__row--error) {
  background-color: rgba(239, 68, 68, 0.08);
  color: #fca5a5;
  border-left: 2px solid #f56c6c;
}

/* 表单控件已通过全局 simulation-dark 类统一样式 */
/* 这里保留组件特定的微调 */

:deep(.el-checkbox__label) {
  color: #94a3b8 !important;
  font-size: 13px;
}
</style>
