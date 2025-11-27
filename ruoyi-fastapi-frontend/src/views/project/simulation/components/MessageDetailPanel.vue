<template>
  <zx-floating-panel
    v-if="visible && latestMessage"
    title="报文详情"
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="false"
  >
    <template #header>
      <div class="panel-header">
        <el-icon class="pulse-icon"><Connection /></el-icon>
        <span class="panel-title">报文详情</span>
        <el-tag size="small" type="success" effect="dark">实时</el-tag>
      </div>
    </template>

    <div class="panel-content">
      <!-- 发送接收信息 -->
      <div class="info-card">
        <div class="info-row">
          <div class="info-item">
            <span class="info-label">发送方</span>
            <span class="info-value device-name">{{ senderName }}</span>
          </div>
          <el-icon class="arrow-icon"><Right /></el-icon>
          <div class="info-item">
            <span class="info-label">接收方</span>
            <span class="info-value device-name">{{ receiverName }}</span>
          </div>
        </div>
        <div class="info-row meta-row">
          <el-tag size="small" effect="plain">{{ latestMessage.protocolType }}</el-tag>
          <span class="meta-text">{{ latestMessage.sizeBytes }} 字节</span>
          <span class="meta-text">{{ formatTimestamp(latestMessage.sendTimestamp) }}</span>
        </div>
      </div>

      <!-- 字段值域 -->
      <div class="section">
        <div class="section-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>字段值域</span>
        </div>
        <div class="field-grid">
          <div v-for="(field, idx) in fieldValues" :key="idx" class="field-card">
            <div class="field-name">{{ field.name }}</div>
            <div class="field-value-row">
              <span class="field-value" :class="field.valueClass">{{ field.displayValue }}</span>
              <span v-if="field.unit" class="field-unit">{{ field.unit }}</span>
            </div>
            <div class="field-hex">{{ field.hexValue }}</div>
          </div>
        </div>
      </div>

      <!-- 报文内容 -->
      <div class="section">
        <div class="section-header">
          <el-icon><Document /></el-icon>
          <span>报文内容</span>
          <el-tag v-if="latestMessage.fillStrategy" size="small" type="info">
            {{ getStrategyLabel(latestMessage.fillStrategy) }}
          </el-tag>
        </div>
        <div class="payload-box">
          <code>{{ formatPayloadHex(latestMessage.payloadHex) }}</code>
        </div>
      </div>
    </div>
  </zx-floating-panel>
</template>

<script setup name="MessageDetailPanel">
import { computed } from 'vue';
import { Connection, Right, DataAnalysis, Document } from '@element-plus/icons-vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  latestMessage: {
    type: Object,
    default: null,
  },
  // 节点ID到名称的映射
  nodeNameMap: {
    type: Object,
    default: () => ({}),
  },
  // 数据注入策略
  injectionStrategy: {
    type: Object,
    default: () => ({ strategy: 'random', params: {} }),
  },
  position: {
    type: Object,
    default: () => ({ top: '230px', left: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '380px', height: '420px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
});

// 获取发送方设备名称
const senderName = computed(() => {
  const nodeId = props.latestMessage?.senderNodeId;
  if (!nodeId) return '-';
  return props.nodeNameMap[nodeId] || formatNodeId(nodeId);
});

// 获取接收方设备名称
const receiverName = computed(() => {
  const nodeId = props.latestMessage?.receiverNodeId;
  if (!nodeId) return '-';
  return props.nodeNameMap[nodeId] || formatNodeId(nodeId);
});

// 解析字段值域
const fieldValues = computed(() => {
  if (!props.latestMessage?.payloadHex) return [];

  const strategy = props.injectionStrategy?.strategy || 'random';
  const params = props.injectionStrategy?.params || {};
  const hex = props.latestMessage.payloadHex;
  const bytes = hex.match(/.{2}/g) || [];
  const fields = [];

  if (bytes.length >= 1) {
    const value = parseInt(bytes[0], 16);
    fields.push({
      name: '状态字',
      value,
      displayValue: value.toString(),
      hexValue: `0x${bytes[0].toUpperCase()}`,
      unit: '',
      valueClass: getValueClass(value),
    });
  }

  if (bytes.length >= 3) {
    const value = parseInt(bytes[1] + bytes[2], 16);
    let displayValue = value.toString();
    let unit = '';

    if (strategy === 'sine_wave') {
      const amplitude = params.amplitude || 100;
      const offset = params.offset || 127;
      const physicalValue = ((value - offset) / amplitude) * 100;
      displayValue = physicalValue.toFixed(1);
      unit = '%';
    } else if (strategy === 'increment') {
      unit = '计数';
    }

    fields.push({
      name: '模拟量',
      value,
      displayValue,
      hexValue: `0x${(bytes[1] + bytes[2]).toUpperCase()}`,
      unit,
      valueClass: getValueClass(value),
    });
  }

  if (bytes.length >= 5) {
    const value = parseInt(bytes[3] + bytes[4], 16);
    const tempValue = (value / 100).toFixed(1);
    fields.push({
      name: '温度',
      value,
      displayValue: tempValue,
      hexValue: `0x${(bytes[3] + bytes[4]).toUpperCase()}`,
      unit: '°C',
      valueClass: '',
    });
  }

  if (bytes.length >= 7) {
    const value = parseInt(bytes[5] + bytes[6], 16);
    fields.push({
      name: '压力',
      value,
      displayValue: (value / 10).toFixed(1),
      hexValue: `0x${(bytes[5] + bytes[6]).toUpperCase()}`,
      unit: 'kPa',
      valueClass: '',
    });
  }

  return fields;
});

function formatNodeId(nodeId) {
  if (!nodeId) return '-';
  if (nodeId.length > 10) {
    return nodeId.substring(0, 8) + '...';
  }
  return nodeId;
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '-';
  return timestamp.toFixed(3) + 's';
}

function formatPayloadHex(hex) {
  if (!hex) return '-';
  const preview = hex.substring(0, 48).toUpperCase();
  const formatted = preview.match(/.{2}/g)?.join(' ') || preview;
  return hex.length > 48 ? `${formatted} ...` : formatted;
}

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

function getValueClass(value) {
  if (value > 200) return 'value-high';
  if (value < 50) return 'value-low';
  return '';
}
</script>

<style lang="less" scoped>
.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pulse-icon {
  color: #10b981;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
}

.panel-content {
  padding: 8px 0;
  min-height: 240px;
}

.info-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.info-item {
  flex: 1;
  text-align: center;
}

.info-label {
  display: block;
  font-size: 10px;
  color: #64748b;
  margin-bottom: 2px;
}

.info-value {
  font-size: 13px;
  font-weight: 600;
  color: #1e40af;

  &.device-name {
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  }
}

.arrow-icon {
  color: #3b82f6;
  font-size: 16px;
  flex-shrink: 0;
}

.meta-row {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #bfdbfe;
  justify-content: center;
  gap: 12px;
}

.meta-text {
  font-size: 11px;
  color: #64748b;
}

.section {
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.field-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
  padding: 8px 10px;
  color: #fff;
}

.field-name {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2px;
}

.field-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.field-value {
  font-size: 16px;
  font-weight: 700;
  font-family: 'Monaco', 'Consolas', monospace;

  &.value-high {
    color: #fbbf24;
  }

  &.value-low {
    color: #60a5fa;
  }
}

.field-unit {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
}

.field-hex {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-family: 'Monaco', 'Consolas', monospace;
  margin-top: 2px;
}

.payload-box {
  background: #1e293b;
  border-radius: 6px;
  padding: 10px;

  code {
    color: #4ade80;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 11px;
    letter-spacing: 0.5px;
    word-break: break-all;
    line-height: 1.6;
  }
}
</style>
