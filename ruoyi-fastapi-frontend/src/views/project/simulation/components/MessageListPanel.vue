<template>
  <transition name="fade-slide">
    <zx-floating-panel
      v-if="visible"
      title="报文记录"
      :position="position"
      :size="size"
      :collapsed-size="collapsedSize"
      :default-collapsed="defaultCollapsed"
    >
      <template #header>
        <div class="message-panel__header">
          <span class="message-panel__title">报文记录</span>
          <transition name="badge-bounce">
            <el-badge :value="localMessages.length" :max="999" type="primary" :key="localMessages.length" />
          </transition>
        </div>
      </template>

      <template #actions>
        <el-button
          type="primary"
          size="small"
          icon="Download"
          :disabled="!localMessages || localMessages.length === 0"
          @click="handleExport"
        >
          导出
        </el-button>
      </template>

      <div class="message-panel__content">
      <ZxGridList
      ref="gridListRef"
      :load-data="loadMessageData"
      :initial-state="initialState"
      class="zx-grid-list--simple"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.keyword"
              placeholder="搜索节点或端口"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.protocolType"
              placeholder="协议类型"
              clearable
              style="width: 160px; margin-left: 8px"
              @change="(v) => onFilterChange('protocolType', v, { handleRefresh, updateState })"
            >
              <el-option label="全部" value="" />
              <el-option label="以太网" value="ethernet" />
              <el-option label="RS422" value="rs422" />
              <el-option label="RS485" value="rs485" />
              <el-option label="CAN" value="can" />
              <el-option label="1553B" value="1553b" />
            </el-select>
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.search"
              placeholder="搜索报文"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <template #table="{ grid }">
        <transition name="fade" mode="out-in">
          <SkeletonLoader v-if="isLoading" type="table" :rows="5" :columns="8" key="loading" />
          <el-table
            v-else
            v-loading="grid.loading"
            :data="grid.list || []"
            height="250px"
            size="small"
            key="table"
          >
          <el-table-column label="序号" type="index" width="60" />
          <el-table-column label="时间戳" prop="sendTimestamp" width="100">
            <template #default="scope">
              <span>{{ formatTimestamp(scope.row.sendTimestamp) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="发送节点" prop="senderNodeId" width="120" show-overflow-tooltip />
          <el-table-column label="发送端口" prop="senderPortId" width="120" show-overflow-tooltip />
          <el-table-column label="接收节点" prop="receiverNodeId" width="120" show-overflow-tooltip />
          <el-table-column label="接收端口" prop="receiverPortId" width="120" show-overflow-tooltip />
          <el-table-column label="协议类型" prop="protocolType" width="100">
            <template #default="scope">
              <el-tag size="small" :type="getProtocolTagType(scope.row.protocolType)">
                {{ getProtocolLabel(scope.row.protocolType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="大小" prop="sizeBytes" width="100">
            <template #default="scope">
              <span>{{ scope.row.sizeBytes }} B</span>
            </template>
          </el-table-column>
          <el-table-column label="传输时间" prop="receiveTimestamp" width="100">
            <template #default="scope">
              <span v-if="scope.row.receiveTimestamp">
                {{ ((scope.row.receiveTimestamp - scope.row.sendTimestamp) * 1000).toFixed(2) }} ms
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        </transition>
      </template>
    </ZxGridList>
    </div>
  </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import SkeletonLoader from './SkeletonLoader.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  visible: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({ bottom: '30px', right: '30px' })
  },
  size: {
    type: Object,
    default: () => ({ width: '800px', maxHeight: '400px' })
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' })
  },
  defaultCollapsed: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['export'])

const gridListRef = ref()
const localMessages = ref([])
const isLoading = ref(false)

const initialState = {
  query: {
    keyword: '',
    protocolType: '',
    search: ''
  },
  pager: {
    page: 1,
    size: 50
  }
}

// 监听外部数据变化
watch(() => props.messages, (newMessages) => {
  if (newMessages) {
    isLoading.value = true
    // 模拟数据处理延迟，提供平滑过渡
    setTimeout(() => {
      localMessages.value = [...newMessages]
      // 刷新列表
      gridListRef.value?.refresh?.()
      isLoading.value = false
    }, 200)
  }
}, { immediate: true, deep: true })

/**
 * 加载报文数据（客户端分页和过滤）
 */
async function loadMessageData(params) {
  const { pageNum = 1, pageSize = 50, keyword, protocolType, search } = params || {}
  
  let filteredData = [...localMessages.value]

  // 按关键字过滤
  if (keyword) {
    const kw = keyword.toLowerCase()
    filteredData = filteredData.filter(msg =>
      msg.senderNodeId?.toLowerCase().includes(kw) ||
      msg.senderPortId?.toLowerCase().includes(kw) ||
      msg.receiverNodeId?.toLowerCase().includes(kw) ||
      msg.receiverPortId?.toLowerCase().includes(kw)
    )
  }

  // 按协议类型过滤
  if (protocolType) {
    filteredData = filteredData.filter(msg => msg.protocolType === protocolType)
  }

  // 按搜索词过滤
  if (search) {
    const s = search.toLowerCase()
    filteredData = filteredData.filter(msg =>
      JSON.stringify(msg).toLowerCase().includes(s)
    )
  }

  // 客户端分页
  const total = filteredData.length
  const start = (pageNum - 1) * pageSize
  const end = start + pageSize
  const list = filteredData.slice(start, end)

  return { list, total }
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value })
  handleRefresh()
}

function onSearch({ handleRefresh }) {
  handleRefresh()
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return '-'
  return timestamp.toFixed(3) + 's'
}

/**
 * 获取协议标签类型
 */
function getProtocolTagType(protocolType) {
  const typeMap = {
    ethernet: 'primary',
    rs422: 'success',
    rs485: 'success',
    can: 'warning',
    '1553b': 'danger'
  }
  return typeMap[protocolType] || 'info'
}

/**
 * 获取协议标签文本
 */
function getProtocolLabel(protocolType) {
  const labelMap = {
    ethernet: '以太网',
    rs422: 'RS422',
    rs485: 'RS485',
    can: 'CAN',
    '1553b': '1553B'
  }
  return labelMap[protocolType] || protocolType
}

/**
 * 导出报文数据
 */
function handleExport() {
  if (!localMessages.value || localMessages.value.length === 0) {
    ElMessage.warning('暂无报文数据可导出')
    return
  }

  // 生成CSV内容
  const headers = ['时间戳', '发送节点', '发送端口', '接收节点', '接收端口', '协议类型', '大小(B)', '传输时间(ms)']
  const rows = localMessages.value.map(msg => [
    msg.sendTimestamp?.toFixed(3) || '-',
    msg.senderNodeId || '-',
    msg.senderPortId || '-',
    msg.receiverNodeId || '-',
    msg.receiverPortId || '-',
    getProtocolLabel(msg.protocolType),
    msg.sizeBytes || 0,
    msg.receiveTimestamp 
      ? ((msg.receiveTimestamp - msg.sendTimestamp) * 1000).toFixed(2)
      : '-'
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // 下载文件
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `simulation_messages_${new Date().getTime()}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('导出成功')
  emit('export', csvContent)
}

/**
 * 刷新列表
 */
function refresh() {
  gridListRef.value?.refresh?.()
}

defineExpose({
  refresh,
  handleExport
})
</script>

<style lang="less" scoped>
.message-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-panel__title {
  font-weight: 600;
  font-size: 14px;
}

.message-panel__content {
  padding: 8px 0;
  
  :deep(.zx-grid-form-bar) {
    padding: 8px 0;
    background: transparent;
  }
  
  :deep(.zx-grid-form-bar__filters) {
    gap: 8px;
  }
}

/* Transition animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.badge-bounce-enter-active {
  animation: badge-bounce 0.5s ease;
}

@keyframes badge-bounce {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
