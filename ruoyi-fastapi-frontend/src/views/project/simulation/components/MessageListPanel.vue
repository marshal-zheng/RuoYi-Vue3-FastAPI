<template>
  <transition name="fade-slide">
    <zx-floating-panel
      ref="panelRef"
      v-if="visible"
      title="报文追踪"
      :position="position"
      :size="size"
      :collapsed-size="collapsedSize"
      :default-collapsed="defaultCollapsed"
    >
      <template #header>
        <div class="flex items-center justify-between">
          <div>
            <span class="font-semibold text-sm">报文追踪</span>
            <transition name="badge-bounce">
              <el-badge
                :value="localMessages.length"
                :max="999"
                type="primary"
                :key="localMessages.length"
              />
            </transition>
          </div>
          <el-button
            type="primary"
            size="small"
            icon="Download"
            class="mr-4"
            :disabled="!localMessages || localMessages.length === 0"
            @click="handleExport"
          >
            导出
          </el-button>
        </div>
      </template>

      <ZxGridList
        ref="gridListRef"
        :load-data="loadMessageData"
        :initial-state="initialState"
        class="zx-grid-list--simple"
      >
        <template #form="{ query, loading, refresh: handleRefresh, updateState }">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <el-input
                v-model="query.keyword"
                placeholder="搜索节点或端口"
                clearable
                size="small"
                style="width: 180px"
                @keyup.enter="() => onSearch({ handleRefresh, updateState })"
              />
              <el-select
                v-model="query.protocolType"
                placeholder="协议类型"
                clearable
                size="small"
                style="width: 140px"
                popper-class="sim-popper-dark"
                @change="(v) => onFilterChange('protocolType', v, { handleRefresh, updateState })"
              >
                <el-option label="全部" value="" />
                <el-option label="LAN" value="LAN" />
                <el-option label="RS422" value="RS422" />
                <el-option label="RS485" value="RS485" />
                <el-option label="CAN" value="CAN" />
                <el-option label="1553B" value="1553B" />
              </el-select>
            </div>
            <div>
              <ZxSearch
                v-model="query.search"
                placeholder="搜索报文"
                size="small"
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
              empty-text="暂无报文数据"
              v-loading="grid.loading"
              :data="grid.list || []"
              height="220px"
              size="small"
              :row-class-name="getRowClassName"
              key="table"
            >
              <el-table-column label="序号" type="index" width="55" align="center" />

              <!-- 信息流转 -->
              <el-table-column label="信息流转" min-width="200">
                <template #default="scope">
                  <div class="flex items-center gap-1 text-xs">
                    <span class="font-medium text-blue-600">{{ scope.row.senderNodeId }}</span>
                    <el-icon class="text-gray-400"><Right /></el-icon>
                    <span class="font-medium text-green-600">{{ scope.row.receiverNodeId }}</span>
                  </div>
                  <div class="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                    <span>{{ scope.row.senderPortId }}</span>
                    <el-icon :size="10"><Right /></el-icon>
                    <span>{{ scope.row.receiverPortId }}</span>
                  </div>
                </template>
              </el-table-column>

              <!-- 协议 -->
              <el-table-column label="协议" width="90" align="center">
                <template #default="scope">
                  <el-tag size="small" :type="getProtocolTagType(scope.row.protocolType)">
                    {{ scope.row.protocolType || '-' }}
                  </el-tag>
                </template>
              </el-table-column>

              <!-- 时延特性 -->
              <el-table-column label="时延特性" width="180">
                <template #default="scope">
                  <div class="text-xs space-y-0.5">
                    <div class="flex items-center gap-1">
                      <span class="text-gray-500 w-10">发送:</span>
                      <span class="font-mono">{{ formatTime(scope.row.sendTimestamp) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <span class="text-gray-500 w-10">接收:</span>
                      <span class="font-mono">{{ formatTime(scope.row.receiveTimestamp) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <span class="text-gray-500 w-10">时延:</span>
                      <span class="font-mono font-semibold" :class="getLatencyClass(scope.row)">
                        {{ calculateLatency(scope.row) }}
                      </span>
                    </div>
                  </div>
                </template>
              </el-table-column>

              <!-- 大小 -->
              <el-table-column label="大小" width="80" align="center">
                <template #default="scope">
                  <span class="text-xs">{{ scope.row.sizeBytes }} B</span>
                </template>
              </el-table-column>

              <!-- 报文内容 -->
              <el-table-column label="报文内容" width="180">
                <template #default="scope">
                  <el-popover
                    v-if="scope.row.payloadHex"
                    placement="top"
                    :width="300"
                    trigger="hover"
                  >
                    <template #reference>
                      <div class="payload-preview text-xs font-mono text-gray-600 cursor-pointer">
                        {{ formatPayloadPreview(scope.row.payloadHex) }}
                      </div>
                    </template>
                    <div class="payload-detail">
                      <div class="text-xs text-gray-500 mb-2">完整报文内容 (HEX)</div>
                      <div class="font-mono text-xs bg-gray-100 p-2 rounded break-all">
                        {{ formatPayloadHex(scope.row.payloadHex) }}
                      </div>
                      <div v-if="scope.row.fillStrategy" class="mt-2 text-xs">
                        <span class="text-gray-500">填充策略：</span>
                        <el-tag size="small" type="info">
                          {{ getStrategyLabel(scope.row.fillStrategy) }}
                        </el-tag>
                      </div>
                    </div>
                  </el-popover>
                  <span v-else class="text-xs text-gray-400">-</span>
                </template>
              </el-table-column>

              <!-- 传输状态 -->
              <el-table-column label="传输状态" width="100" align="center">
                <template #default="scope">
                  <div class="flex flex-col items-center gap-1">
                    <el-tag :type="getTransmissionStatusType(scope.row)" size="small" effect="dark">
                      {{ getTransmissionStatus(scope.row) }}
                    </el-tag>
                    <span
                      v-if="scope.row.packetLoss"
                      class="text-xs text-red-500 flex items-center gap-0.5"
                    >
                      <el-icon><Warning /></el-icon>
                      丢包
                    </span>
                  </div>
                </template>
              </el-table-column>

              <!-- 网段 -->
              <el-table-column label="网段检测" width="110">
                <template #default="scope">
                  <div class="text-xs">
                    <div v-if="scope.row.crossSegment" class="space-y-0.5">
                      <div class="flex items-center gap-1 text-orange-600">
                        <el-icon><Connection /></el-icon>
                        <span>跨网段</span>
                      </div>
                      <div class="text-gray-400">
                        {{ scope.row.sourceSegment }} → {{ scope.row.targetSegment }}
                      </div>
                      <div v-if="scope.row.routingHops" class="text-gray-500">
                        {{ scope.row.routingHops }} 跳
                      </div>
                    </div>
                    <div v-else class="text-gray-400 flex items-center gap-1">
                      <el-icon><Link /></el-icon>
                      <span>同网段</span>
                    </div>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </transition>
        </template>
      </ZxGridList>
    </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Right, Warning, Connection, Link } from '@element-plus/icons-vue';
import SkeletonLoader from './SkeletonLoader.vue';

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  visible: {
    type: Boolean,
    default: false,
  },
  position: {
    type: Object,
    default: () => ({ bottom: '20px', right: '20px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '780px', maxHeight: '350px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: true,
  },
  // 数据注入策略配置
  injectionStrategy: {
    type: Object,
    default: () => ({ strategy: 'random', params: {} }),
  },
});

const emit = defineEmits(['export']);

const gridListRef = ref();
const panelRef = ref();
const localMessages = ref([]);
const isLoading = ref(false);
const enhancedMessagesCache = new Map(); // 缓存增强后的数据

const initialState = {
  query: {
    keyword: '',
    protocolType: '',
    search: '',
  },
  pager: {
    page: 1,
    size: 50,
  },
};

// 监听外部数据变化并进行增强处理（优化：仅处理新增数据）
watch(
  () => props.messages,
  (newMessages) => {
    if (!newMessages) return;

    // 只处理新增的消息
    const newEnhanced = [];
    newMessages.forEach((msg) => {
      const id = msg.messageId;
      if (!enhancedMessagesCache.has(id)) {
        const enhanced = enhanceMessage(msg);
        enhancedMessagesCache.set(id, enhanced);
        newEnhanced.push(enhanced);
      }
    });

    if (newEnhanced.length > 0 || localMessages.value.length !== newMessages.length) {
      // 重建列表（从缓存中获取）
      localMessages.value = newMessages.map(
        (msg) => enhancedMessagesCache.get(msg.messageId) || enhanceMessage(msg)
      );

      // 清理缓存（保持最近200条）
      if (enhancedMessagesCache.size > 200) {
        const toKeep = new Set(localMessages.value.map((m) => m.messageId));
        enhancedMessagesCache.forEach((_, key) => {
          if (!toKeep.has(key)) {
            enhancedMessagesCache.delete(key);
          }
        });
      }

      // 刷新表格数据（nextTick 确保 gridListRef 已就绪）
      nextTick(() => {
        gridListRef.value?.refresh?.();
      });
    }
  },
  { immediate: true, deep: true }
);

// 监听策略变化，清除缓存并重新计算
watch(
  () => props.injectionStrategy,
  () => {
    // 清除缓存，强制重新计算报文内容
    enhancedMessagesCache.clear();
    // 重置计数器
    incrementCounter = 0;
    cycleIndex = 0;
    // 重新增强所有消息
    if (props.messages && props.messages.length > 0) {
      localMessages.value = props.messages.map((msg) => {
        const enhanced = enhanceMessage(msg);
        enhancedMessagesCache.set(msg.messageId, enhanced);
        return enhanced;
      });
      nextTick(() => {
        gridListRef.value?.refresh?.();
      });
    }
  },
  { deep: true }
);

// 网段缓存（优化：避免重复计算）
const segmentCache = new Map();

/**
 * 增强报文数据 - 添加网段检测、丢包检测、报文内容模拟等
 */
function enhanceMessage(msg) {
  const enhanced = { ...msg };

  // 模拟网段检测（使用缓存）
  const sourceSegment = extractSegment(msg.senderNodeId);
  const targetSegment = extractSegment(msg.receiverNodeId);
  enhanced.sourceSegment = sourceSegment;
  enhanced.targetSegment = targetSegment;
  enhanced.crossSegment = sourceSegment !== targetSegment;

  // 跨网段时计算路由跳数（固定值，避免随机）
  if (enhanced.crossSegment) {
    const hopKey = `${sourceSegment}-${targetSegment}`;
    if (!segmentCache.has(hopKey)) {
      const hash = hopKey.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      segmentCache.set(hopKey, (hash % 3) + 1); // 1-3跳
    }
    enhanced.routingHops = segmentCache.get(hopKey);
  }

  // 丢包检测（基于时延异常或协议特性）
  const latency = (msg.receiveTimestamp - msg.sendTimestamp) * 1000;
  enhanced.packetLoss = detectPacketLoss(msg, latency, enhanced.crossSegment);

  // 传输状态
  enhanced.transmissionStatus = getTransmissionStatusValue(enhanced.packetLoss, latency);

  // payloadHex 由后端真实生成，前端不再模拟
  // 如果后端没有返回 payloadHex，显示空值而非假数据
  if (!enhanced.payloadHex) {
    enhanced.payloadHex = '';
    enhanced.fillStrategy = msg.fillStrategy || 'unknown';
  }

  return enhanced;
}

/**
 * 提取网段信息（使用缓存）
 */
function extractSegment(nodeId) {
  if (!nodeId) return 'unknown';

  if (segmentCache.has(nodeId)) {
    return segmentCache.get(nodeId);
  }

  // 尝试从节点ID提取网段信息
  const match = nodeId.match(/(\d+\.\d+\.\d+)\./);
  if (match) {
    segmentCache.set(nodeId, match[1]);
    return match[1];
  }

  // 基于节点名称的hash（固定计算）
  const hash = nodeId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const segment = `192.168.${hash % 256}`;
  segmentCache.set(nodeId, segment);
  return segment;
}

/**
 * 检测丢包（优化：减少随机性，基于确定性规则）
 */
function detectPacketLoss(msg, latency, crossSegment) {
  // 丢包条件（确定性）：
  // 1. 跨网段且时延过高（>100ms）
  // 2. 报文大小超过MTU（>1500B）
  if (crossSegment && latency > 100) return true;
  if (msg.sizeBytes > 1500) return true;
  return false;
}

/**
 * 获取传输状态值
 */
function getTransmissionStatusValue(packetLoss, latency) {
  if (packetLoss) return 'lost';
  if (latency < 1) return 'excellent';
  if (latency < 10) return 'good';
  if (latency < 50) return 'normal';
  return 'slow';
}

/**
 * 加载报文数据
 */
async function loadMessageData(params) {
  const { query = {}, pager = {} } = params || {};
  const { keyword, protocolType, search } = query;
  const { page: pageNum = 1, size: pageSize = 50 } = pager;

  let filteredData = [...localMessages.value];

  // 按关键字过滤
  if (keyword) {
    const kw = keyword.toLowerCase();
    filteredData = filteredData.filter(
      (msg) =>
        msg.senderNodeId?.toLowerCase().includes(kw) ||
        msg.senderPortId?.toLowerCase().includes(kw) ||
        msg.receiverNodeId?.toLowerCase().includes(kw) ||
        msg.receiverPortId?.toLowerCase().includes(kw)
    );
  }

  // 按协议类型过滤
  if (protocolType) {
    filteredData = filteredData.filter((msg) => msg.protocolType === protocolType);
  }

  // 按搜索词过滤
  if (search) {
    const s = search.toLowerCase();
    filteredData = filteredData.filter((msg) => JSON.stringify(msg).toLowerCase().includes(s));
  }

  // 客户端分页
  const total = filteredData.length;
  const start = (pageNum - 1) * pageSize;
  const end = start + pageSize;
  const list = filteredData.slice(start, end);

  return { list, total };
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}

/**
 * 格式化报文内容预览（只显示前几个字节）
 */
function formatPayloadPreview(hex) {
  if (!hex) return '-';
  // 每2个字符是一个字节，显示前8个字节
  const preview = hex.substring(0, 16).toUpperCase();
  const formatted = preview.match(/.{2}/g)?.join(' ') || preview;
  return hex.length > 16 ? `${formatted}...` : formatted;
}

/**
 * 格式化完整报文内容
 */
function formatPayloadHex(hex) {
  if (!hex) return '-';
  // 每2个字符用空格分隔
  return hex.toUpperCase().match(/.{2}/g)?.join(' ') || hex;
}

/**
 * 获取策略标签
 */
function getStrategyLabel(strategy) {
  const labels = {
    random: '随机值',
    increment: '序列递增',
    fixed: '固定值',
    cycle: '循环模式',
    sine_wave: '正弦波',
  };
  return labels[strategy] || strategy || '随机值';
}

/**
 * 格式化时间
 */
function formatTime(timestamp) {
  if (!timestamp) return '-';
  return timestamp.toFixed(3) + 's';
}

/**
 * 计算时延
 */
function calculateLatency(row) {
  if (!row.receiveTimestamp || !row.sendTimestamp) return '-';
  const latency = (row.receiveTimestamp - row.sendTimestamp) * 1000;
  return latency.toFixed(2) + ' ms';
}

/**
 * 获取时延样式类
 */
function getLatencyClass(row) {
  if (!row.receiveTimestamp || !row.sendTimestamp) return '';
  const latency = (row.receiveTimestamp - row.sendTimestamp) * 1000;
  if (latency < 1) return 'text-green-600';
  if (latency < 10) return 'text-blue-600';
  if (latency < 50) return 'text-orange-500';
  return 'text-red-600';
}

/**
 * 获取协议标签类型
 */
function getProtocolTagType(protocolType) {
  const typeMap = {
    LAN: 'primary',
    RS422: 'success',
    RS485: 'success',
    CAN: 'warning',
    '1553B': 'danger',
  };
  return typeMap[protocolType] || 'info';
}

/**
 * 获取传输状态
 */
function getTransmissionStatus(row) {
  if (row.packetLoss) return '丢包';
  const latency = (row.receiveTimestamp - row.sendTimestamp) * 1000;
  if (latency < 1) return '优秀';
  if (latency < 10) return '良好';
  if (latency < 50) return '正常';
  return '较慢';
}

/**
 * 获取传输状态类型
 */
function getTransmissionStatusType(row) {
  if (row.packetLoss) return 'danger';
  const latency = (row.receiveTimestamp - row.sendTimestamp) * 1000;
  if (latency < 1) return 'success';
  if (latency < 10) return 'primary';
  if (latency < 50) return 'warning';
  return 'info';
}

/**
 * 行样式
 */
function getRowClassName({ row }) {
  if (row.packetLoss) return 'bg-red-50';
  if (row.crossSegment) return 'bg-orange-50';
  return '';
}

/**
 * 导出报文数据
 */
function handleExport() {
  if (!localMessages.value || localMessages.value.length === 0) {
    ElMessage.warning('暂无报文数据可导出');
    return;
  }

  const headers = [
    '时间戳',
    '发送节点',
    '发送端口',
    '接收节点',
    '接收端口',
    '协议类型',
    '大小(B)',
    '发送时间',
    '接收时间',
    '时延(ms)',
    '跨网段',
    '源网段',
    '目标网段',
    '路由跳数',
    '传输状态',
    '丢包',
  ];

  const rows = localMessages.value.map((msg) => [
    msg.sendTimestamp?.toFixed(3) || '-',
    msg.senderNodeId || '-',
    msg.senderPortId || '-',
    msg.receiverNodeId || '-',
    msg.receiverPortId || '-',
    msg.protocolType || '-',
    msg.sizeBytes || 0,
    formatTime(msg.sendTimestamp),
    formatTime(msg.receiveTimestamp),
    calculateLatency(msg),
    msg.crossSegment ? '是' : '否',
    msg.sourceSegment || '-',
    msg.targetSegment || '-',
    msg.routingHops || '-',
    getTransmissionStatus(msg),
    msg.packetLoss ? '是' : '否',
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
  ].join('\n');

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `simulation_messages_${new Date().getTime()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  ElMessage.success('导出成功');
  emit('export', csvContent);
}

function refresh() {
  gridListRef.value?.refresh?.();
}

defineExpose({
  refresh,
  handleExport,
});
</script>

<style scoped>
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

.payload-preview {
  background: var(--sim-fill-light, rgba(30, 41, 59, 0.8));
  padding: 2px 6px;
  border-radius: 4px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: background 0.2s;
  color: var(--sim-text-regular, #e2e8f0);
}

.payload-preview:hover {
  background: var(--sim-accent-bg, rgba(34, 211, 238, 0.1));
}
</style>
