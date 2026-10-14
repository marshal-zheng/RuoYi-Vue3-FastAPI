<template>
  <zx-floating-panel
    v-if="visible"
    class="fault-floating simbus-floating-panel"
    :position="position"
    :size="size"
    :showCollapseBtn="false"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
    @close="$emit('close')"
  >
    <template #header>
      <div class="header">
        <div>
          <div class="title">故障板</div>
          <div class="sub">活跃 {{ activeCount }} / 共 {{ faults.length }}</div>
        </div>
        <div class="actions">
          <el-button class="refresh-btn" size="small" :loading="loading" @click="$emit('refresh')">
            <el-icon><Refresh /></el-icon>
            <span>刷新</span>
          </el-button>
          <el-button class="clear-all-btn" size="small" @click="$emit('clear-all')">
            <el-icon><Delete /></el-icon>
            <span>清除全部</span>
          </el-button>
          <el-button size="small" text @click="$emit('close')">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </template>

    <!-- 仿真未运行提示（边界情况：仿真在中途停止） -->
    <div v-if="!isRunning" class="not-running-hint">
      <el-icon class="mr-2"><Warning /></el-icon>
      <span>仿真已停止，故障注入功能暂不可用</span>
    </div>

    <section class="mb-3">
      <div class="flex items-center justify-between mb-2">
        <div class="text-xs text-zx-text-secondary">快捷模板</div>
        <div v-if="selectedEdge" class="selected-edge-hint">
          <el-icon class="mr-1"><Link /></el-icon>
          <span>{{ getSelectedEdgeInfo() }}</span>
        </div>
      </div>
      <div v-if="!edgeAvailable" class="edge-hint">请选择或悬停一条链路后再应用模板</div>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="tpl in templates"
          :key="tpl.name"
          type="button"
          class="tpl-btn"
          :class="{ 'tpl-btn-disabled': !edgeAvailable }"
          :disabled="!edgeAvailable"
          @click="edgeAvailable && $emit('apply-template', tpl)"
        >
          <div
            class="text-xs font-semibold"
            :class="edgeAvailable ? 'text-zx-text-primary' : 'text-zx-text-secondary'"
          >
            {{ tpl.label }}
          </div>
          <div class="text-[11px] text-zx-text-secondary">{{ tpl.tip }}</div>
        </button>
      </div>
    </section>

    <section class="fault-list">
      <div class="text-xs text-zx-text-secondary mb-2">故障列表</div>
      <div v-if="!faults.length" class="empty">
        <div class="empty-content">
          <div class="empty-icon">📋</div>
          <div class="empty-text">暂无活跃故障</div>
          <div class="empty-hint">选中链路后应用模板即可注入故障</div>
        </div>
      </div>
      <div
        v-else
        v-for="fault in orderedFaults"
        :key="fault.faultId"
        class="fault-item"
        :class="statusClass(fault)"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="tag">{{ faultLabel(fault.faultType) }}</span>
              <span class="text-[11px] text-zx-text-secondary truncate">
                {{ fault.targetType === 'edge' ? '链路' : fault.targetType }}：{{
                  faultTargetLabel(fault)
                }}
              </span>
            </div>
            <div class="text-[11px] text-zx-text-secondary mt-0.5 truncate">
              {{ briefParams(fault.params) }}
            </div>
            <div class="text-[10px] text-zx-text-secondary mt-0.5">
              {{ statusText(fault.status) }}
            </div>
          </div>
          <el-button size="small" text type="primary" @click="$emit('clear', fault.faultId)"
            >清除</el-button
          >
        </div>
      </div>
    </section>
  </zx-floating-panel>
</template>

<script setup>
import { computed } from 'vue';
import { Close, Refresh, Delete, Link, Warning } from '@element-plus/icons-vue';
import { FAULT_TYPE_CONFIG } from '../composables/useFaultInjection';

const props = defineProps({
  visible: { type: Boolean, default: false },
  faults: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  selectedEdge: { type: Object, default: null }, // 选中的链路
  hoveredEdge: { type: Object, default: null }, // 悬停的链路（备用选中）
  isRunning: { type: Boolean, default: false }, // 仿真是否运行中
  position: {
    type: Object,
    default: () => ({ top: '12px', right: '92px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '420px', maxHeight: '620px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '46px', height: '46px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['apply-template', 'clear', 'clear-all', 'refresh', 'close']);

const templates = [
  { name: 'disconnect', label: '断链', tip: '立即断开链路', payload: { type: 'disconnect' } },
  {
    name: 'loss10',
    label: '丢包10%',
    tip: '10%概率丢弃',
    payload: { type: 'packet_loss', params: { lossRate: 10 } },
  },
  {
    name: 'delay50',
    label: '延时50ms',
    tip: '固定延时+抖动',
    payload: { type: 'delay', params: { delayMs: 50, jitterMs: 10 } },
  },
  {
    name: 'limit',
    label: '限速QPS20',
    tip: '节流窗口',
    payload: { type: 'bandwidth_limit', params: { messagesPerSecond: 20 } },
  },
  {
    name: 'bitflip',
    label: 'bit flip',
    tip: '随机篡改payload',
    payload: { type: 'payload_corrupt', params: { bitFlipCount: 2 } },
  },
  {
    name: 'noise',
    label: '噪声帧',
    tip: '随机无效帧',
    payload: { type: 'noise_frame', params: { length: 16 } },
  },
];

const orderedFaults = computed(() => {
  return [...props.faults].sort((a, b) => {
    const pa = Number(a?.priority || 0);
    const pb = Number(b?.priority || 0);
    if (pa !== pb) return pb - pa;
    return (b?.startAt || 0) - (a?.startAt || 0);
  });
});

const activeCount = computed(() => props.faults.filter((f) => f.status === 'active').length);
const edgeAvailable = computed(() => props.selectedEdge || props.hoveredEdge);

function statusClass(fault) {
  if (fault.status === 'active') return 'is-active';
  if (fault.status === 'pending') return 'is-pending';
  return 'is-ended';
}

function statusText(status) {
  if (status === 'active') return '生效中';
  if (status === 'pending') return '等待生效';
  if (status === 'expired') return '已到期';
  if (status === 'cleared') return '已清除';
  return status || '未知';
}

function shortId(id) {
  if (!id) return '未知链路';
  const str = String(id);
  if (str.length <= 12) return str;
  return `${str.slice(0, 6)}...${str.slice(-4)}`;
}

function faultTargetLabel(fault) {
  const label = fault.targetName || fault.target_name || fault.targetLabel || fault.targetAlias;
  const id = fault.targetId || fault.targetKey;
  return label || shortId(id);
}

function briefParams(params = {}) {
  const parts = [];
  if (params.lossRate !== undefined)
    parts.push(`丢包${Math.round(params.lossRate * 100 || params.lossRate)}%`);
  if (params.delayMs !== undefined) parts.push(`延时${params.delayMs}ms`);
  if (params.jitterMs) parts.push(`抖动±${params.jitterMs}ms`);
  if (params.messagesPerSecond) parts.push(`QPS<=${params.messagesPerSecond}`);
  if (params.bitFlipCount) parts.push(`bitFlip=${params.bitFlipCount}`);
  if (params.durationMs) parts.push(`持续${Math.round(params.durationMs / 1000)}s`);
  if (params.startAfterMs) parts.push(`延迟${params.startAfterMs}ms`);
  return parts.join(' · ') || '默认参数';
}

function faultLabel(type) {
  return FAULT_TYPE_CONFIG[type]?.label || type;
}

function getSelectedEdgeInfo() {
  if (!props.selectedEdge) return '';
  const edge = props.selectedEdge;
  const data = edge?.getData?.() || {};
  const edgeId = edge?.id || edge?.getID?.() || data.id || data.edgeId || '未知';

  const sourceNode = edge?.getSourceNode?.();
  const targetNode = edge?.getTargetNode?.();
  const sourceData = sourceNode?.getData?.() || {};
  const targetData = targetNode?.getData?.() || {};

  const srcName = sourceData.name || sourceData.label || sourceData.deviceName;
  const dstName = targetData.name || targetData.label || targetData.deviceName;
  const srcPort = data.sourcePortName || data.sourcePort || sourceData.portName;
  const dstPort = data.targetPortName || data.targetPort || targetData.portName;
  const alias = data.alias || data.label || data.name || data.title;

  if (srcName || dstName) {
    const left = srcName || '源设备';
    const right = dstName || '目标设备';
    const leftPort = srcPort ? `(${srcPort})` : '';
    const rightPort = dstPort ? `(${dstPort})` : '';
    return `已选: ${left}${leftPort} → ${right}${rightPort}`;
  }

  return alias ? `已选: ${alias}` : `已选: ${shortId(edgeId)}`;
}
</script>

<style scoped>
.fault-floating {
  border: 1px solid rgba(239, 68, 68, 0.3);
  box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15);
}

/* 仿真未运行提示 */
.not-running-hint {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.12), rgba(245, 158, 11, 0.15));
  border: 1px solid rgba(251, 191, 36, 0.4);
  border-radius: 10px;
  color: #fbbf24;
  font-size: 12px;
  font-weight: 500;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.title {
  font-weight: 700;
  color: var(--sim-danger, #ef4444);
}
.sub {
  font-size: 12px;
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
}
.actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tpl-btn {
  text-align: left;
  padding: 10px 12px;
  border-radius: var(--sim-radius-lg, 10px);
  border: 1px solid
    var(--sim-border-light, color-mix(in srgb, var(--zx-semantic-accent-base) 8%, transparent));
  background: var(--sim-fill-lighter, var(--zx-semantic-surface-card-fill));
  transition: all 0.2s ease;
  cursor: pointer;
}
.tpl-btn:hover:not(.tpl-btn-disabled) {
  border-color: var(
    --sim-border-accent,
    color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent)
  );
  box-shadow: var(
    --sim-shadow-glow,
    0 8px 16px color-mix(in srgb, var(--zx-semantic-accent-base) 12%, transparent)
  );
  transform: translateY(-1px);
}
.tpl-btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: var(--sim-border-light, rgba(100, 116, 139, 0.2));
}
.edge-hint {
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
}
.fault-list {
  /* 自适应高度，保证在小屏和面板缩放时也能滚动 */
  max-height: clamp(320px, calc(100vh - 260px), 540px);
  overflow-y: auto;
  padding-right: 4px;
  padding-bottom: 8px; /* 防止最后一项被截断 */
  /* 允许在 flex 列布局中收缩，避免被父级撑开导致无法滚动 */
  min-height: 0;
}
.fault-list::-webkit-scrollbar {
  width: 6px;
}
.fault-list::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--zx-semantic-border-default) 35%, transparent);
  border-radius: 999px;
}
.fault-item {
  padding: 10px 12px;
  border: 1px solid
    var(--sim-border-base, color-mix(in srgb, var(--zx-semantic-border-default) 18%, transparent));
  border-radius: var(--sim-radius-lg, 10px);
  background: var(--sim-fill-lighter, var(--zx-semantic-surface-card-fill));
  margin-bottom: 8px;
}
.fault-item.is-active {
  border-color: var(
    --sim-border-focus,
    color-mix(in srgb, var(--zx-semantic-accent-base) 50%, transparent)
  );
  box-shadow: var(
    --sim-shadow-glow,
    0 6px 20px color-mix(in srgb, var(--zx-semantic-accent-base) 15%, transparent)
  );
}
.fault-item.is-pending {
  border-color: var(--sim-warning-border, rgba(250, 204, 21, 0.4));
}
.fault-item.is-ended {
  opacity: 0.7;
}
.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 6px;
  background: var(
    --sim-accent-bg,
    color-mix(in srgb, var(--zx-semantic-accent-base) 12%, transparent)
  );
  color: var(--sim-accent, #22d3ee);
  font-size: 11px;
  font-weight: 700;
}
.empty {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed color-mix(in srgb, var(--zx-semantic-border-default) 20%, transparent);
  border-radius: 10px;
  padding: 20px;
}
.empty-content {
  text-align: center;
}
.empty-icon {
  font-size: 28px;
  margin-bottom: 8px;
  opacity: 0.6;
}
.empty-text {
  font-size: 13px;
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
  font-weight: 500;
  margin-bottom: 4px;
}
.empty-hint {
  font-size: 11px;
  color: var(--sim-text-disabled, var(--zx-semantic-text-disabled));
}

/* 刷新按钮样式 - 使用CSS变量 */
.refresh-btn {
  background: linear-gradient(
    135deg,
    var(--sim-accent-bg, color-mix(in srgb, var(--zx-semantic-accent-base) 15%, transparent)),
    color-mix(in srgb, var(--zx-semantic-accent-base) 15%, transparent)
  ) !important;
  border: 1px solid
    var(--sim-border-accent, color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent)) !important;
  color: var(--sim-accent, #22d3ee) !important;
  font-weight: 600;
  transition: all var(--sim-transition-normal, 0.3s ease);
}
.refresh-btn:hover {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--zx-semantic-accent-base) 25%, transparent),
    color-mix(in srgb, var(--zx-semantic-accent-base) 25%, transparent)
  ) !important;
  border-color: var(
    --sim-accent-light,
    color-mix(in srgb, var(--zx-semantic-accent-base) 60%, transparent)
  ) !important;
  box-shadow: var(
    --sim-shadow-glow-accent,
    0 4px 12px color-mix(in srgb, var(--zx-semantic-accent-base) 20%, transparent)
  );
  transform: translateY(-1px);
}
.refresh-btn .el-icon {
  margin-right: 4px;
}

/* 清除全部按钮样式 - 使用CSS变量 */
.clear-all-btn {
  background: linear-gradient(
    135deg,
    var(--sim-danger-bg, rgba(239, 68, 68, 0.15)),
    rgba(220, 38, 38, 0.15)
  ) !important;
  border: 1px solid var(--sim-danger-border, rgba(239, 68, 68, 0.4)) !important;
  color: var(--sim-danger, #ef4444) !important;
  font-weight: 600;
  transition: all var(--sim-transition-normal, 0.3s ease);
}
.clear-all-btn:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(220, 38, 38, 0.25)) !important;
  border-color: var(--sim-danger, rgba(239, 68, 68, 0.6)) !important;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
  transform: translateY(-1px);
}
.clear-all-btn .el-icon {
  margin-right: 4px;
}

/* 选中链路提示样式 - 使用CSS变量 */
.selected-edge-hint {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(
    --sim-accent-bg,
    color-mix(in srgb, var(--zx-semantic-accent-base) 15%, transparent)
  );
  border: 1px solid
    var(--sim-border-accent, color-mix(in srgb, var(--zx-semantic-accent-base) 30%, transparent));
  color: var(--sim-accent, #22d3ee);
  font-size: 11px;
  font-weight: 600;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%,
  100% {
    box-shadow: 0 0 8px color-mix(in srgb, var(--zx-semantic-accent-base) 20%, transparent);
  }
  50% {
    box-shadow: 0 0 12px color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent);
  }
}
</style>
