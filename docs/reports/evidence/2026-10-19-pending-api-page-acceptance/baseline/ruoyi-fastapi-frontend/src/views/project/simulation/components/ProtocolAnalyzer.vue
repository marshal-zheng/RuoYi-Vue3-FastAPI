<template>
  <div class="flex flex-col h-full text-zx-text-secondary">
    <!-- 工具栏 -->
    <div class="pro-card-header flex items-center gap-2 px-3 py-2 flex-nowrap overflow-x-auto">
      <ProtocolTypeSelector
        v-model="localFilter.protocolType"
        placeholder="协议"
        clearable
        size="small"
        class="!w-20 sim-select-dark flex-shrink-0"
        popper-class="sim-popper-dark"
        @change="handleFilterChange"
      />
      <el-select
        v-model="localFilter.senderNode"
        placeholder="源节点"
        clearable
        filterable
        size="small"
        class="!w-24 sim-select-dark flex-shrink-0"
        popper-class="sim-popper-dark"
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
        popper-class="sim-popper-dark"
        @change="handleFilterChange"
      >
        <el-option
          v-for="node in receiverNodeOptions"
          :key="node.value"
          :label="node.label"
          :value="node.value"
        />
      </el-select>
      <PortPairSelector
        v-model="localFilter.portPair"
        :options="portPairOptions"
        placeholder="源端口 → 目标端口"
        size="small"
        class="!w-40 sim-select-dark flex-shrink-0"
        popper-class="sim-popper-dark"
        clearable
        filterable
        @change="handleFilterChange"
      />
      <!-- <el-input
        v-model="localFilter.keyword"
        placeholder="关键字"
        clearable
        size="small"
        class="!w-24 sim-input-dark flex-shrink-0"
        @input="handleFilterChange"
      /> -->
      <el-popover
        v-model:visible="showAdvanced"
        placement="bottom-start"
        :width="520"
        trigger="click"
      >
        <div class="advanced-search__panel">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-zx-text-secondary">报文/字段多条件检索</span>
            <el-select
              v-model="conditionLogic"
              size="small"
              class="!w-32 sim-select-dark"
              popper-class="sim-popper-dark"
              @change="handleAdvancedChange"
            >
              <el-option label="满足全部(AND)" value="and" />
              <el-option label="满足任一(OR)" value="or" />
            </el-select>
          </div>
          <div class="space-y-2 max-h-60 overflow-y-auto pr-1">
            <div v-for="cond in advancedConditions" :key="cond.id" class="flex items-center gap-2">
              <el-select
                v-model="cond.type"
                placeholder="条件类型"
                size="small"
                class="!w-28 sim-select-dark"
                popper-class="sim-popper-dark"
                @change="handleAdvancedChange"
              >
                <el-option label="报文HEX包含" value="payload" />
                <el-option label="字段键/值" value="field" />
                <el-option label="节点/端口" value="node" />
                <el-option label="协议匹配" value="protocol" />
                <el-option label="大小范围" value="size" />
                <el-option label="时延范围" value="latency" />
              </el-select>

              <template v-if="cond.type === 'node'">
                <el-select
                  v-model="cond.field"
                  placeholder="字段"
                  size="small"
                  class="!w-32 sim-select-dark"
                  popper-class="sim-popper-dark"
                  @change="handleAdvancedChange"
                >
                  <el-option label="源节点" value="senderNodeId" />
                  <el-option label="源端口" value="senderPortId" />
                  <el-option label="目标节点" value="receiverNodeId" />
                  <el-option label="目标端口" value="receiverPortId" />
                </el-select>
                <el-input
                  v-model="cond.value"
                  size="small"
                  placeholder="请输入值"
                  class="!w-36 sim-input-dark"
                  @input="handleAdvancedChange"
                />
              </template>

              <template v-else-if="cond.type === 'field'">
                <el-input
                  v-model="cond.key"
                  size="small"
                  placeholder="字段名(可选)"
                  class="!w-32 sim-input-dark"
                  @input="handleAdvancedChange"
                />
                <el-input
                  v-model="cond.value"
                  size="small"
                  placeholder="字段值"
                  class="!w-36 sim-input-dark"
                  @input="handleAdvancedChange"
                />
              </template>

              <template v-else-if="cond.type === 'size' || cond.type === 'latency'">
                <el-input
                  v-model.number="cond.min"
                  size="small"
                  placeholder="最小"
                  class="!w-24 sim-input-dark"
                  @input="handleAdvancedChange"
                />
                <span class="text-xs text-zx-text-secondary">~</span>
                <el-input
                  v-model.number="cond.max"
                  size="small"
                  placeholder="最大"
                  class="!w-24 sim-input-dark"
                  @input="handleAdvancedChange"
                />
                <span class="text-xs text-zx-text-secondary">{{
                  cond.type === 'size' ? 'B' : 'ms'
                }}</span>
              </template>

              <template v-else>
                <el-input
                  v-model="cond.value"
                  size="small"
                  placeholder="请输入值"
                  class="!w-48 sim-input-dark"
                  @input="handleAdvancedChange"
                />
              </template>

              <el-button
                circle
                size="small"
                class="sim-btn-dark !border-zx-border-default"
                @click="removeCondition(cond.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs text-zx-text-secondary">
              <el-button text size="small" type="primary" @click="addCondition">
                新增条件
              </el-button>
              <span>当前 {{ activeConditionCount }} 条</span>
            </div>
            <el-button size="small" type="primary" @click="applyAdvancedSearch">
              应用检索
            </el-button>
          </div>
        </div>
        <!-- <template #reference>
        <el-button
          size="small"
          class="sim-btn-dark flex-shrink-0"
          :type="activeConditionCount ? 'primary' : 'default'"
        >
          多条件检索
          <span v-if="activeConditionCount" class="ml-1 text-zx-accent-on-surface">
            ({{ activeConditionCount }})
          </span>
        </el-button>
      </template> -->
      </el-popover>
      <el-checkbox
        v-model="localFilter.errorOnly"
        size="small"
        class="flex-shrink-0"
        @change="handleFilterChange"
      >
        错误
      </el-checkbox>
      <el-checkbox
        v-model="localAutoScroll"
        size="small"
        class="flex-shrink-0"
        @change="handleAutoScrollChange"
      >
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
      <span class="text-xs text-zx-text-secondary flex-shrink-0 ml-auto"
        >共 {{ filteredMessages.length }} 条</span
      >
    </div>
    <div v-if="activeConditionCount" class="px-3 pb-2 flex flex-wrap gap-2">
      <el-tag
        v-for="cond in normalizedConditions"
        :key="cond.id"
        closable
        size="small"
        type="info"
        effect="dark"
        @close="removeCondition(cond.id)"
      >
        {{ describeCondition(cond) }}
      </el-tag>
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
      <div v-else class="flex flex-col items-center justify-center h-full text-zx-text-secondary">
        <el-icon class="text-5xl mb-3"><Document /></el-icon>
        <span class="text-sm">暂无报文数据</span>
      </div>
    </div>

    <!-- 报文详情 -->
    <div
      v-if="selectedMessage"
      class="border-t border-zx-border-default/50 max-h-28 overflow-y-auto bg-zx-surface-canvas-fill/50"
    >
      <div
        class="pro-card-header flex justify-between items-center text-xs font-semibold text-zx-text-secondary"
      >
        <span>报文详情</span>
        <el-button :icon="Close" circle size="small" @click="selectedMessage = null" />
      </div>
      <div class="p-3">
        <div class="flex flex-wrap gap-1 mb-3">
          <span
            v-for="(byte, index) in parseHex(selectedMessage.payloadHex)"
            :key="index"
            class="px-1 py-0.5 bg-zx-surface-card-fill rounded text-xs font-mono text-zx-text-secondary"
          >
            {{ byte }}
          </span>
        </div>
        <div v-if="selectedMessage.fieldValues" class="flex flex-wrap gap-4">
          <div v-for="(value, key) in selectedMessage.fieldValues" :key="key" class="text-xs">
            <span class="text-zx-text-secondary mr-1">{{ key }}:</span>
            <span class="text-zx-accent-on-surface font-medium">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed, h } from 'vue';
import { ArrowDown, Document, Close } from '@element-plus/icons-vue';
import { formatTimestamp } from '../utils/timeFormatter';
import { PortPairSelector, ProtocolTypeSelector } from './selector';

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
  speed: {
    type: Number,
    default: 1,
  },
});

const emit = defineEmits(['message-select', 'filter-change', 'export', 'auto-scroll-change']);

const tableRef = ref(null);
const listRef = ref(null);
const tableWidth = ref(0);
const tableHeight = ref(200);
const resizeObserver = ref(null);

const selectedId = ref(null);
const selectedMessage = ref(null);
const localAutoScroll = ref(props.autoScroll);
const safeMessages = computed(() => (Array.isArray(props.messages) ? props.messages : []));
const playSpeed = computed(() => Math.max(0.5, Math.min(Number(props.speed) || 1, 4)));

let conditionUid = 0;
const showAdvanced = ref(false);
const advancedConditions = ref([createCondition('payload')]);
const conditionLogic = ref('and');

const localFilter = ref({
  protocolType: '',
  senderNode: '',
  receiverNode: '',
  portPair: '',
  keyword: '',
  errorOnly: false,
});

const normalizedConditions = computed(() =>
  advancedConditions.value
    .map((cond) => ({
      ...cond,
      type: cond?.type || 'payload',
    }))
    .filter((cond) => {
      if (cond.type === 'size' || cond.type === 'latency') {
        return cond.min !== undefined || cond.max !== undefined;
      }
      return Boolean(String(cond.value || cond.key || '').trim());
    })
);

const activeConditionCount = computed(() => normalizedConditions.value.length);

const keywordTokens = computed(() =>
  localFilter.value.keyword ? [localFilter.value.keyword] : []
);
const payloadTokens = computed(() =>
  normalizedConditions.value.filter((c) => c.type === 'payload' && c.value).map((c) => c.value)
);
const nodeTokens = computed(() =>
  normalizedConditions.value.filter((c) => c.type === 'node' && c.value).map((c) => c.value)
);

const protocolTokens = computed(() => {
  const tokens = [];
  if (localFilter.value.protocolType) tokens.push(localFilter.value.protocolType);
  normalizedConditions.value
    .filter((c) => c.type === 'protocol' && c.value)
    .forEach((c) => tokens.push(c.value));
  return tokens;
});

// 上层已按同样条件过滤过，这里直接透传，避免重复全量遍历
const filteredMessages = computed(() => safeMessages.value);

function createCondition(type = 'payload') {
  return {
    id: `cond-${Date.now()}-${conditionUid++}`,
    type,
    value: '',
    key: '',
    field: 'senderNodeId',
    min: null,
    max: null,
  };
}

function addCondition() {
  advancedConditions.value.push(createCondition('payload'));
  handleAdvancedChange();
}

function removeCondition(id) {
  advancedConditions.value = advancedConditions.value.filter((c) => c.id !== id);
  handleAdvancedChange();
}

function handleAdvancedChange() {
  emitFilterChange();
}

function applyAdvancedSearch() {
  showAdvanced.value = false;
  emitFilterChange();
}

function emitFilterChange() {
  emit('filter-change', {
    ...localFilter.value,
    conditionLogic: conditionLogic.value,
    conditions: normalizedConditions.value,
  });
}

// 增量累积节点/端口对选项，避免每次全量遍历 5w 条窗口
const senderNodeOptions = ref([]);
const receiverNodeOptions = ref([]);
const portPairOptions = ref([]);
const senderNodeMap = ref(new Map());
const receiverNodeMap = ref(new Map());
const portPairMap = ref(new Map());
const lastProcessedCount = ref(0);

const buildPortPairKey = (msg) => {
  const sNode = msg?.senderNodeId || msg?.senderNodeName || '';
  const sPort = msg?.senderPortId || msg?.senderPortName || '';
  const rNode = msg?.receiverNodeId || msg?.receiverNodeName || '';
  const rPort = msg?.receiverPortId || msg?.receiverPortName || '';
  if (!sPort && !rPort) return '';
  return [sNode, sPort, rNode, rPort].join('||');
};

const buildPortPairLabel = (msg) => {
  const senderNode = msg?.senderNodeName || msg?.senderNodeId || '源节点';
  const senderPort = msg?.senderPortName || msg?.senderPortId || '-';
  const receiverNode = msg?.receiverNodeName || msg?.receiverNodeId || '目标节点';
  const receiverPort = msg?.receiverPortName || msg?.receiverPortId || '-';
  return `${senderNode}/${senderPort} → ${receiverNode}/${receiverPort}`;
};

watch(
  safeMessages,
  (list) => {
    // 如果过滤重置导致数量变少，整体重建一次
    if (!Array.isArray(list) || list.length < lastProcessedCount.value) {
      senderNodeMap.value = new Map();
      receiverNodeMap.value = new Map();
      portPairMap.value = new Map();
      lastProcessedCount.value = 0;
    }

    const delta = list.slice(lastProcessedCount.value);
    delta.forEach((m) => {
      const senderId = m?.senderNodeId || m?.senderNodeName;
      const senderLabel = m?.senderNodeName || m?.senderNodeId;
      if (senderId && !senderNodeMap.value.has(senderId)) {
        senderNodeMap.value.set(senderId, senderLabel);
      }

      const receiverId = m?.receiverNodeId || m?.receiverNodeName;
      const receiverLabel = m?.receiverNodeName || m?.receiverNodeId;
      if (receiverId && !receiverNodeMap.value.has(receiverId)) {
        receiverNodeMap.value.set(receiverId, receiverLabel);
      }

      const pairKey = buildPortPairKey(m);
      if (pairKey && !portPairMap.value.has(pairKey)) {
        portPairMap.value.set(pairKey, {
          value: pairKey,
          label: buildPortPairLabel(m),
        });
      }
    });

    lastProcessedCount.value = list.length;
    senderNodeOptions.value = Array.from(senderNodeMap.value.entries()).map(([value, label]) => ({
      value,
      label,
    }));
    receiverNodeOptions.value = Array.from(receiverNodeMap.value.entries()).map(
      ([value, label]) => ({
        value,
        label,
      })
    );
    portPairOptions.value = Array.from(portPairMap.value.values());
  },
  { immediate: true }
);

function formatTime(timestamp) {
  return formatTimestamp(timestamp);
}

function truncateHex(hex) {
  if (!hex) return '';
  if (hex.length > 32) {
    return hex.substring(0, 32) + '...';
  }
  return hex;
}

function highlightText(text, tokens) {
  const value = String(text || '');
  if (!tokens || tokens.length === 0) return value;
  const lower = value.toLowerCase();
  const targetTokens = [
    ...new Set(tokens.map((t) => String(t || '').toLowerCase()).filter(Boolean)),
  ].filter((t) => lower.includes(t));
  if (!targetTokens.length) return value;

  const segments = [];
  let cursor = 0;

  const findNext = () => {
    let pos = -1;
    let tok = '';
    targetTokens.forEach((t) => {
      const idx = lower.indexOf(t, cursor);
      if (idx !== -1 && (pos === -1 || idx < pos)) {
        pos = idx;
        tok = t;
      }
    });
    return { pos, tok };
  };

  while (cursor < value.length) {
    const { pos, tok } = findNext();
    if (pos === -1) {
      segments.push(value.slice(cursor));
      break;
    }
    if (pos > cursor) {
      segments.push(value.slice(cursor, pos));
    }
    segments.push(h('span', { class: 'highlight-token' }, value.slice(pos, pos + tok.length)));
    cursor = pos + tok.length;
  }

  return segments;
}

function parseHex(hex) {
  if (!hex) return [];
  const bytes = [];
  for (let i = 0; i < hex.length; i += 2) {
    bytes.push(hex.substring(i, i + 2).toUpperCase());
  }
  return bytes;
}

function formatLatency(message) {
  const send = message?.sendTimestamp ?? message?.timestamp;
  const recv = message?.receiveTimestamp;
  if (!send || !recv) return '-';
  const diffMs = Math.max(0, (recv - send) * 1000);
  return `${diffMs.toFixed(2)} ms`;
}

function handleSelect(message) {
  selectedId.value = message.messageId;
  selectedMessage.value = message;
  emit('message-select', message);
}

function handleFilterChange() {
  emitFilterChange();
}

function handleExport(format) {
  emit('export', format);
}

function handleAutoScrollChange(val) {
  localAutoScroll.value = val;
  emit('auto-scroll-change', val);
  if (val) {
    scrollToBottom();
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
    cellRenderer: ({ rowData }) =>
      highlightText(rowData?.senderNodeName || rowData?.senderNodeId || '-', [
        ...nodeTokens.value,
        ...keywordTokens.value,
      ]),
  },
  {
    key: 'senderPort',
    dataKey: 'senderPortId',
    title: '源端口',
    minWidth: 120,
    cellRenderer: ({ rowData }) =>
      highlightText(rowData?.senderPortName || rowData?.senderPortId || '-', [
        ...nodeTokens.value,
        ...keywordTokens.value,
      ]),
  },
  {
    key: 'receiverNode',
    dataKey: 'receiverNodeId',
    title: '目标节点',
    minWidth: 140,
    cellRenderer: ({ rowData }) =>
      highlightText(rowData?.receiverNodeName || rowData?.receiverNodeId || '-', [
        ...nodeTokens.value,
        ...keywordTokens.value,
      ]),
  },
  {
    key: 'receiverPort',
    dataKey: 'receiverPortId',
    title: '目标端口',
    minWidth: 120,
    cellRenderer: ({ rowData }) =>
      highlightText(rowData?.receiverPortName || rowData?.receiverPortId || '-', [
        ...nodeTokens.value,
        ...keywordTokens.value,
      ]),
  },
  {
    key: 'latency',
    dataKey: 'receiveTimestamp',
    title: '时延',
    minWidth: 100,
    cellRenderer: ({ rowData }) => formatLatency(rowData),
  },
  {
    key: 'protocolType',
    dataKey: 'protocolType',
    title: '协议',
    minWidth: 80,
    cellRenderer: ({ cellData }) =>
      highlightText(cellData || '-', [...protocolTokens.value, ...keywordTokens.value]),
  },
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
    cellRenderer: ({ cellData }) =>
      highlightText(truncateHex(cellData), [...payloadTokens.value, ...keywordTokens.value]),
  },
];

const tableColumns = computed(() => {
  const perColWidth = Math.max(Math.floor(tableWidth.value / baseColumns.length), 120);
  return baseColumns.map((col) => ({
    ...col,
    width: Math.max(perColWidth, col.minWidth || 0),
    flexGrow: 1,
  }));
});

function getRowClass({ rowData }) {
  const classes = [];
  if (rowData.isError) classes.push('protocol-analyzer__row--error');
  if (selectedId.value === rowData.messageId) classes.push('protocol-analyzer__row--selected');
  return classes.join(' ');
}

function handleRowClick({ rowData }) {
  handleSelect(rowData);
}

function scrollToBottom() {
  if (!tableRef.value || !localAutoScroll.value || filteredMessages.value.length === 0) return;

  const duration = Math.max(80, 320 / playSpeed.value);

  const smoothScroll = (container, target) => {
    const start = container.scrollTop;
    const change = target - start;
    const startTime = performance.now();
    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

    const step = (now) => {
      if (!localAutoScroll.value || !tableRef.value) return;
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = easeOutCubic(progress);
      container.scrollTop = start + change * eased;
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };
    requestAnimationFrame(step);
  };

  nextTick(() => {
    if (!localAutoScroll.value) return;
    const tableEl = tableRef.value?.$el;
    const scrollContainer =
      tableEl?.querySelector('.el-table-v2__body') || tableEl?.querySelector('.el-scrollbar__wrap');

    if (scrollContainer) {
      smoothScroll(scrollContainer, scrollContainer.scrollHeight);
    }
  });
}

watch(
  () => filteredMessages.value.length,
  () => {
    scrollToBottom();
  },
  { flush: 'post' }
);

watch(
  () => props.autoScroll,
  (val) => {
    localAutoScroll.value = val;
    if (val) {
      scrollToBottom();
    }
  }
);

function exportData(format) {
  const data = filteredMessages.value;

  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'messages.json');
  } else if (format === 'csv') {
    const headers = ['时间', '源节点', '目标节点', '协议', '大小', '数据'];
    const rows = data.map((m) => [
      formatTime(m.sendTimestamp || m.timestamp || m.receiveTimestamp),
      m.senderNodeName || m.senderNodeId,
      m.receiverNodeName || m.receiverNodeId,
      m.protocolType,
      m.sizeBytes,
      m.payloadHex,
    ]);
    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, 'messages.csv');
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

defineExpose({ exportData });

function updateTableSize() {
  if (!listRef.value) return;
  const { clientWidth, clientHeight } = listRef.value;
  tableWidth.value = clientWidth;
  tableHeight.value = Math.max(clientHeight, 160);
}

onMounted(() => {
  nextTick(() => {
    updateTableSize();
    if (listRef.value) {
      resizeObserver.value = new ResizeObserver(updateTableSize);
      resizeObserver.value.observe(listRef.value);
    }
    if (localAutoScroll.value && props.messages.length > 0) {
      scrollToBottom();
    }
  });
});

onBeforeUnmount(() => {
  resizeObserver.value?.disconnect();
});
</script>

<style scoped>
:deep(.el-table-v2__header) {
  background-color: var(--sim-fill-light, var(--zx-semantic-surface-panel-fill));
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
}

:deep(.el-table-v2__row) {
  font-size: 12px;
  font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Courier New', monospace;
  cursor: pointer;
  color: var(--sim-text-secondary, var(--zx-semantic-text-secondary));
  background-color: transparent;
  transition: background 0.15s ease;
}

:deep(.el-table-v2__row:hover) {
  background-color: var(
    --sim-bg-hover,
    color-mix(in srgb, var(--zx-semantic-border-default) 35%, transparent)
  );
}

:deep(.protocol-analyzer__row--selected) {
  background-color: var(
    --sim-accent-bg,
    color-mix(in srgb, var(--zx-semantic-accent-base) 12%, transparent)
  );
  border-left: 2px solid var(--sim-accent, #22d3ee);
}

:deep(.protocol-analyzer__row--error) {
  background-color: var(--sim-danger-bg, rgba(239, 68, 68, 0.12));
  color: var(--zx-semantic-status-danger-on-surface);
  border-left: 2px solid var(--sim-danger, #ef4444);
}

/* Native control appearance is owned by the Host Element Plus adapter. */

.pro-card-header {
  color: var(--sim-text-regular, var(--zx-semantic-text-primary));
}

:deep(.sim-input-dark .el-input__inner),
:deep(.sim-select-dark .el-select__placeholder),
:deep(.sim-select-dark .el-select__selected-item) {
  color: var(--sim-text-regular, var(--zx-semantic-text-primary));
}

:deep(.sim-input-dark input::placeholder) {
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
}

.highlight-token {
  background: var(
    --sim-accent-bg,
    color-mix(in srgb, var(--zx-semantic-accent-base) 18%, transparent)
  );
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));
  padding: 0 2px;
  border-radius: 2px;
}
</style>
