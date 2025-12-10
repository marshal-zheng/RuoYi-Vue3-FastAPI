<template>
  <div class="flex flex-col h-full text-slate-300">
    <!-- 工具栏 -->
    <div class="pro-card-header flex items-center gap-2 px-3 py-2 flex-nowrap overflow-x-auto">
      <el-select
        v-model="localFilter.protocolType"
        placeholder="协议"
        clearable
        size="small"
        class="!w-20 sim-select-dark flex-shrink-0"
        @change="handleFilterChange"
      >
        <el-option label="1553B" value="1553B" />
        <el-option label="CAN" value="CAN" />
        <el-option label="RS422" value="RS422" />
        <el-option label="LAN" value="LAN" />
      </el-select>
      <el-select
        v-model="localFilter.senderNode"
        placeholder="源节点"
        clearable
        filterable
        size="small"
        class="!w-24 sim-select-dark flex-shrink-0"
        @change="handleFilterChange"
      >
        <el-option
          v-for="node in senderNodeOptions"
          :key="node.value"
          :label="node.label"
          :value="node.value"
        />
      </el-select>
      <el-select
        v-model="localFilter.receiverNode"
        placeholder="目标节点"
        clearable
        filterable
        size="small"
        class="!w-24 sim-select-dark flex-shrink-0"
        @change="handleFilterChange"
      >
        <el-option
          v-for="node in receiverNodeOptions"
          :key="node.value"
          :label="node.label"
          :value="node.value"
        />
      </el-select>
      <el-input
        v-model="localFilter.keyword"
        placeholder="关键字"
        clearable
        size="small"
        class="!w-24 sim-input-dark flex-shrink-0"
        @input="handleFilterChange"
      />
      <el-checkbox v-model="localFilter.errorOnly" size="small" class="flex-shrink-0" @change="handleFilterChange">
        错误
      </el-checkbox>
      <el-checkbox v-model="localAutoScroll" size="small" class="flex-shrink-0" @change="handleAutoScrollChange">
        自动滚动
      </el-checkbox>
      <el-dropdown @command="handleExport" class="flex-shrink-0">
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
      <span class="text-xs text-slate-500 flex-shrink-0 ml-auto">共 {{ filteredMessages.length }} 条</span>
    </div>

    <!-- 报文列表 -->
    <div class="flex-1 overflow-hidden w-full" ref="listRef">
      <el-table-v2
        v-if="filteredMessages.length > 0"
        ref="tableRef"
        :columns="tableColumns"
        :data="filteredMessages"
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
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
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
const tableWidth = ref(0)
const tableHeight = ref(200)
const resizeObserver = ref(null)
const rowHeight = 36

const selectedId = ref(null)
const selectedMessage = ref(null)
const localAutoScroll = ref(props.autoScroll)
const safeMessages = computed(() => (Array.isArray(props.messages) ? props.messages : []))

const localFilter = ref({
  protocolType: '',
  senderNode: '',
  receiverNode: '',
  keyword: '',
  errorOnly: false,
})

const filteredMessages = computed(() => {
  const keyword = (localFilter.value.keyword || '').toLowerCase().trim()
  return safeMessages.value.filter((m) => {
    if (localFilter.value.protocolType && m.protocolType !== localFilter.value.protocolType) {
      return false
    }
    if (localFilter.value.senderNode) {
      const sender = m.senderNodeId || m.senderNodeName
      if (sender !== localFilter.value.senderNode) return false
    }
    if (localFilter.value.receiverNode) {
      const receiver = m.receiverNodeId || m.receiverNodeName
      if (receiver !== localFilter.value.receiverNode) return false
    }
    if (localFilter.value.errorOnly && !m.isError) {
      return false
    }
    if (keyword) {
      const text = [
        m.payloadHex,
        m.message,
        m.protocolType,
        m.senderNodeName,
        m.receiverNodeName,
        m.senderNodeId,
        m.receiverNodeId,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      if (!text.includes(keyword)) return false
    }
    return true
  })
})

const senderNodeOptions = computed(() => {
  const entries = new Map()
  safeMessages.value.forEach((m) => {
    const id = m?.senderNodeId || m?.senderNodeName
    if (!id) return
    entries.set(id, m?.senderNodeName || m?.senderNodeId)
  })
  return Array.from(entries.entries()).map(([value, label]) => ({ value, label }))
})

const receiverNodeOptions = computed(() => {
  const entries = new Map()
  safeMessages.value.forEach((m) => {
    const id = m?.receiverNodeId || m?.receiverNodeName
    if (!id) return
    entries.set(id, m?.receiverNodeName || m?.receiverNodeId)
  })
  return Array.from(entries.entries()).map(([value, label]) => ({ value, label }))
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

function formatLatency(message) {
  const send = message?.sendTimestamp ?? message?.timestamp
  const recv = message?.receiveTimestamp
  if (!send || !recv) return '-'
  const diffMs = Math.max(0, (recv - send) * 1000)
  return `${diffMs.toFixed(2)} ms`
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

function handleAutoScrollChange(val) {
  localAutoScroll.value = val
  emit('auto-scroll-change', val)
  if (val) {
    restartAutoScroll()
  } else {
    stopAutoScroll()
  }
}

const baseColumns = [
  {
    key: 'timestamp',
    dataKey: 'sendTimestamp',
    title: '时间',
    minWidth: 120,
    cellRenderer: ({ rowData }) =>
      formatTime(rowData?.sendTimestamp || rowData?.timestamp || rowData?.receiveTimestamp),
  },
  {
    key: 'senderNode',
    dataKey: 'senderNodeId',
    title: '源节点',
    minWidth: 140,
    cellRenderer: ({ rowData }) => rowData?.senderNodeName || rowData?.senderNodeId || '-',
  },
  {
    key: 'senderPort',
    dataKey: 'senderPortId',
    title: '源端口',
    minWidth: 120,
    cellRenderer: ({ rowData }) => rowData?.senderPortName || rowData?.senderPortId || '-',
  },
  {
    key: 'receiverNode',
    dataKey: 'receiverNodeId',
    title: '目标节点',
    minWidth: 140,
    cellRenderer: ({ rowData }) => rowData?.receiverNodeName || rowData?.receiverNodeId || '-',
  },
  {
    key: 'receiverPort',
    dataKey: 'receiverPortId',
    title: '目标端口',
    minWidth: 120,
    cellRenderer: ({ rowData }) => rowData?.receiverPortName || rowData?.receiverPortId || '-',
  },
  {
    key: 'latency',
    dataKey: 'receiveTimestamp',
    title: '时延',
    minWidth: 100,
    cellRenderer: ({ rowData }) => formatLatency(rowData),
  },
  { key: 'protocolType', dataKey: 'protocolType', title: '协议', minWidth: 80 },
  {
    key: 'sizeBytes',
    dataKey: 'sizeBytes',
    title: '大小',
    minWidth: 80,
    cellRenderer: ({ rowData }) => `${rowData?.sizeBytes ?? 0}B`,
  },
  {
    key: 'payloadHex',
    dataKey: 'payloadHex',
    title: '数据',
    minWidth: 240,
    cellRenderer: ({ cellData }) => truncateHex(cellData),
  },
]

const tableColumns = computed(() => {
  const perColWidth = Math.max(Math.floor(tableWidth.value / baseColumns.length), 120)
  return baseColumns.map((col) => ({
    ...col,
    width: Math.max(perColWidth, col.minWidth || 0),
    flexGrow: 1,
  }))
})

function getRowClass({ rowData }) {
  const classes = []
  if (rowData.isError) classes.push('protocol-analyzer__row--error')
  if (selectedId.value === rowData.messageId) classes.push('protocol-analyzer__row--selected')
  return classes.join(' ')
}

function handleRowClick({ rowData }) {
  handleSelect(rowData)
}

function scrollToBottom() {
  if (!tableRef.value || !localAutoScroll.value || filteredMessages.value.length === 0) return

  nextTick(() => {
    const lastIndex = filteredMessages.value.length - 1
    if (tableRef.value?.scrollToRow) {
      tableRef.value.scrollToRow(lastIndex, 'end')
      return
    }

    const tableEl = tableRef.value?.$el
    const scrollContainer =
      tableEl?.querySelector('.el-table-v2__body') ||
      tableEl?.querySelector('.el-scrollbar__wrap')

    if (scrollContainer) {
      scrollContainer.scrollTop = scrollContainer.scrollHeight
    }
  })
}

watch(
  () => filteredMessages.value.length,
  () => {
    scrollToBottom()
  },
  { flush: 'post' }
)

watch(
  () => props.autoScroll,
  (val) => {
    localAutoScroll.value = val
    if (val) {
      scrollToBottom()
    }
  }
)

function exportData(format) {
  const data = filteredMessages.value

  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    downloadBlob(blob, 'messages.json')
  } else if (format === 'csv') {
    const headers = ['时间', '源节点', '目标节点', '协议', '大小', '数据']
    const rows = data.map((m) => [
      formatTime(m.sendTimestamp || m.timestamp || m.receiveTimestamp),
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

function updateTableSize() {
  if (!listRef.value) return
  const { clientWidth, clientHeight } = listRef.value
  tableWidth.value = clientWidth
  tableHeight.value = Math.max(clientHeight, 160)
}

onMounted(() => {
  nextTick(() => {
    updateTableSize()
    if (listRef.value) {
      resizeObserver.value = new ResizeObserver(updateTableSize)
      resizeObserver.value.observe(listRef.value)
    }
    if (localAutoScroll.value && props.messages.length > 0) {
      scrollToBottom()
    }
  })
})

onBeforeUnmount(() => {
  resizeObserver.value?.disconnect()
})
</script>

<style scoped>
:deep(.el-table-v2__header) {
  background-color: rgba(30, 41, 59, 0.85);
  color: #94a3b8;
}

:deep(.el-table-v2__row) {
  font-size: 12px;
  font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Courier New', monospace;
  cursor: pointer;
  color: #cbd5e1;
  background-color: transparent;
  transition: background 0.15s ease;
}

:deep(.el-table-v2__row:hover) {
  background-color: rgba(51, 65, 85, 0.35);
}

:deep(.protocol-analyzer__row--selected) {
  background-color: rgba(0, 82, 217, 0.12);
  border-left: 2px solid #22d3ee;
}

:deep(.protocol-analyzer__row--error) {
  background-color: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
  border-left: 2px solid #f56c6c;
}

/* 表单控件已通过全局 simulation-dark 类统一样式 */
:deep(.el-checkbox__input) {
  border-color: #ffffff !important;
}

:deep(.el-checkbox__inner) {
  border-color: #ffffff !important;
  background-color: transparent !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner),
:deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  background-color: #ffffff !important;
  border-color: #ffffff !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner::after),
:deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner::after) {
  border-color: #0f172a !important;
}

:deep(.el-checkbox__label) {
  color: #ffffff !important;
  font-size: 13px;
}

.pro-card-header {
  color: #e2e8f0;
}

:deep(.sim-input-dark .el-input__inner),
:deep(.sim-select-dark .el-select__placeholder),
:deep(.sim-select-dark .el-select__selected-item) {
  color: #e2e8f0;
}

:deep(.sim-input-dark input::placeholder) {
  color: #cbd5e1;
}
</style>
