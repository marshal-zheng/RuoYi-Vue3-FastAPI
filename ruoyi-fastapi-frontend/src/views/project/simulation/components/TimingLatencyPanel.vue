<template>
  <transition name="fade-slide">
    <zx-floating-panel
      v-if="visible"
      :position="position"
      :size="size"
      :collapsed-size="collapsedSize"
      :default-collapsed="defaultCollapsed"
      theme="dark"
      class="timing-latency-panel"
    >
      <template #header>
        <div class="flex items-center gap-2 flex-1">
          <span class="font-semibold text-sm">时序/延迟分析</span>
          <el-tag v-if="isRunning" type="success" size="small" effect="dark" class="live-tag">
            <span class="live-dot"></span>
            实时
          </el-tag>
          <el-tag v-else-if="!hasData" type="info" size="small" effect="plain">待机</el-tag>

          <div class="flex items-center gap-2 ml-auto">
            <el-segmented v-model="viewMode" :options="viewOptions" size="small" />
          </div>
        </div>
      </template>

      <div class="timing-panel-content">
        <!-- 时序视图模式 -->
        <div v-if="viewMode === 'timing'" class="timing-view">
          <!-- 时序图表区域 -->
          <div 
            class="timing-chart-wrapper"
            @mousemove="handleTimingMouseMove"
            @mouseleave="handleTimingMouseLeave"
          >
            <div class="oscilloscope-bg">
              <div class="grid-lines"></div>
            </div>
            <canvas ref="timingCanvasRef" class="timing-canvas"></canvas>

            <!-- Y轴刻度 (延迟) -->
            <div class="y-axis-labels">
              <span>{{ latencyAxisLabels.max }}</span>
              <span>{{ latencyAxisLabels.mid }}</span>
              <span>{{ latencyAxisLabels.min }}</span>
            </div>

            <!-- 图例 -->
            <div class="chart-legend">
              <span class="legend-item">
                <span class="legend-line latency"></span>时延
              </span>
            </div>

            <!-- 垂直指示线 -->
            <div 
              v-if="timingTooltip.visible" 
              class="chart-crosshair"
              :style="{ left: timingTooltip.lineX + 'px' }"
            ></div>

            <!-- 数据点高亮 -->
            <div 
              v-if="timingTooltip.visible" 
              class="chart-highlight-dot"
              :style="{ left: timingTooltip.dotX + 'px', top: timingTooltip.dotY + 'px' }"
            ></div>

          </div>

          <!-- Tooltip 浮层 (fixed定位，避免被截断) -->
          <Teleport to="body">
            <div 
              v-if="timingTooltip.visible" 
              class="chart-tooltip-fixed timing"
              :style="{ left: timingTooltip.tooltipX + 'px', top: timingTooltip.tooltipY + 'px' }"
            >
              <div class="tooltip-header">
                <span class="tooltip-index">#{{ timingTooltip.index + 1 }}</span>
                <span class="tooltip-protocol">{{ timingTooltip.protocol }}</span>
              </div>
              <div class="tooltip-body">
                <div class="tooltip-row main latency">
                  <span class="tooltip-dot latency"></span>
                  <span class="tooltip-label">时延</span>
                  <span class="tooltip-value align-right">{{ timingTooltip.latency }}</span>
                </div>
                <div class="tooltip-row">
                  <span class="tooltip-dot send"></span>
                  <span class="tooltip-label">发送</span>
                  <span class="tooltip-value">{{ timingTooltip.sender }}</span>
                </div>
                <div class="tooltip-row">
                  <span class="tooltip-dot receive"></span>
                  <span class="tooltip-label">接收</span>
                  <span class="tooltip-value">{{ timingTooltip.receiver }}</span>
                </div>
              </div>
            </div>
          </Teleport>

          <!-- 时延统计卡片 -->
          <div class="latency-stats-grid">
            <div class="stat-card">
              <div class="stat-icon avg"></div>
              <div class="stat-content">
                <span class="stat-label">平均时延</span>
                <span class="stat-value">{{ latencyStats.avg }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon max"></div>
              <div class="stat-content">
                <span class="stat-label">最大时延</span>
                <span class="stat-value highlight-warning">{{ latencyStats.max }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon min"></div>
              <div class="stat-content">
                <span class="stat-label">最小时延</span>
                <span class="stat-value highlight-success">{{ latencyStats.min }}</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon jitter"></div>
              <div class="stat-content">
                <span class="stat-label">抖动</span>
                <span class="stat-value">{{ latencyStats.jitter }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 带宽分组视图模式 -->
        <div v-else-if="viewMode === 'bandwidth'" class="bandwidth-grouped-view">
          <!-- 分组选择器 -->
          <div class="group-selector">
            <el-radio-group v-model="groupBy" size="small">
              <el-radio-button value="protocol">按协议</el-radio-button>
              <el-radio-button value="port">按端口</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 分组带宽图表 -->
          <div 
            class="grouped-chart-wrapper"
            @mousemove="handleBandwidthMouseMove"
            @mouseleave="handleBandwidthMouseLeave"
          >
            <div class="oscilloscope-bg">
              <div class="grid-lines"></div>
            </div>
            <canvas ref="bandwidthCanvasRef" class="bandwidth-canvas"></canvas>

            <!-- Y轴刻度 -->
            <div class="y-axis-labels">
              <span>{{ bandwidthAxisLabels.max }}</span>
              <span>{{ bandwidthAxisLabels.mid }}</span>
              <span>0</span>
            </div>

            <!-- 动态图例 -->
            <div class="chart-legend grouped-legend">
              <span
                v-for="(group, index) in groupedBandwidthLegend"
                :key="group.key"
                class="legend-item"
              >
                <span class="legend-line" :style="{ background: getGroupColor(index) }"></span>
                {{ group.label }}
              </span>
            </div>

            <!-- 垂直指示线 -->
            <div 
              v-if="bandwidthTooltip.visible" 
              class="chart-crosshair bandwidth"
              :style="{ left: bandwidthTooltip.lineX + 'px' }"
            ></div>

          </div>

          <!-- Tooltip 浮层 (fixed定位，避免被截断) -->
          <Teleport to="body">
            <div 
              v-if="bandwidthTooltip.visible && bandwidthTooltip.groups.length > 0" 
              class="chart-tooltip-fixed bandwidth"
              :style="{ left: bandwidthTooltip.tooltipX + 'px', top: bandwidthTooltip.tooltipY + 'px' }"
            >
              <div class="tooltip-header">
                <span class="tooltip-time">{{ bandwidthTooltip.time }}</span>
              </div>
              <div class="tooltip-body">
                <div 
                  v-for="(item, idx) in bandwidthTooltip.groups" 
                  :key="item.key"
                  class="tooltip-row"
                >
                  <span class="tooltip-dot" :style="{ background: getGroupColor(idx) }"></span>
                  <span class="tooltip-label">{{ item.label }}</span>
                  <span class="tooltip-value">{{ item.value }}</span>
                </div>
              </div>
            </div>
          </Teleport>

          <!-- 分组统计表格 -->
          <div class="grouped-stats-table">
            <div class="stats-header">
              <span>{{ groupBy === 'protocol' ? '协议' : '端口' }}</span>
              <span>当前</span>
              <span>平均</span>
              <span>峰值</span>
            </div>
            <div
              v-for="(group, index) in groupedBandwidthStats"
              :key="group.key"
              class="stats-row"
            >
              <span class="group-name">
                <span class="color-dot" :style="{ background: getGroupColor(index) }"></span>
                {{ group.label }}
              </span>
              <span class="stat-current">{{ group.current }}</span>
              <span class="stat-avg">{{ group.avg }}</span>
              <span class="stat-peak">{{ group.peak }}</span>
            </div>
            <div v-if="groupedBandwidthStats.length === 0" class="stats-empty">
              暂无数据
            </div>
          </div>
        </div>
      </div>
    </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  bandwidthData: {
    type: Array,
    default: () => [],
  },
  visible: {
    type: Boolean,
    default: false,
  },
  position: {
    type: Object,
    default: () => ({ bottom: '96px', left: '28px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '560px', maxHeight: '480px' }),
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

// DOM引用
const timingCanvasRef = ref(null);
const bandwidthCanvasRef = ref(null);

// 状态
const viewMode = ref('timing');
const groupBy = ref('protocol');
const viewOptions = [
  { label: '时序', value: 'timing' },
  { label: '带宽分组', value: 'bandwidth' },
];

// 数据缓冲区
const MAX_TIMING_POINTS = 60;
const timingBuffer = ref([]);
const bandwidthGroupBuffer = ref(new Map());

// Tooltip状态
const timingTooltip = ref({
  visible: false,
  lineX: 0,      // 垂直指示线位置
  dotX: 0,       // 高亮点X
  dotY: 0,       // 高亮点Y
  tooltipX: 0,   // tooltip X
  tooltipY: 0,   // tooltip Y
  index: 0,
  latency: '',
  protocol: '',
  sender: '',
  receiver: '',
});

const bandwidthTooltip = ref({
  visible: false,
  lineX: 0,
  tooltipX: 0,
  tooltipY: 0,
  groups: [],    // 多条线的数据
});

// 动画相关
let animationFrameId = null;
let lastUpdateTime = 0;
const UPDATE_INTERVAL = 1000;

// 颜色配置
const GROUP_COLORS = [
  '#00ff88', // 绿色
  '#3b82f6', // 蓝色
  '#f59e0b', // 橙色
  '#ef4444', // 红色
  '#8b5cf6', // 紫色
  '#06b6d4', // 青色
  '#f97316', // 深橙色
  '#ec4899', // 粉色
];

// 是否有数据
const hasData = computed(() => {
  return props.messages.length > 0 || props.bandwidthData.length > 0;
});

// 是否正在运行
const isRunning = computed(() => {
  if (!hasData.value) return false;
  const latestMsgTime = Math.max(...props.messages.map((m) => m.receiveTimestamp || m.sendTimestamp || 0), 0);
  const latestBwTime = Math.max(...props.bandwidthData.map((d) => d.timestamp || 0), 0);
  const latestTime = Math.max(latestMsgTime, latestBwTime);
  const now = Date.now() / 1000;
  return now - latestTime < 5;
});

// 获取分组颜色
function getGroupColor(index) {
  return GROUP_COLORS[index % GROUP_COLORS.length];
}

// ==================== 时序视图相关 ====================

// 时延单位：自动选择 μs 或 ms
const latencyUnit = computed(() => {
  const latencies = timingBuffer.value.map((t) => t.latency).filter((l) => l > 0);
  if (latencies.length === 0) return 'ms';
  const maxVal = Math.max(...latencies);
  // 如果最大值小于 1ms，使用微秒显示
  return maxVal < 1 ? 'μs' : 'ms';
});

// 时延转换因子（用于图表绘制）
const latencyScale = computed(() => {
  return latencyUnit.value === 'μs' ? 1000 : 1;
});

// Y轴范围（使用 min-max 范围来放大细微波动）
const latencyAxisRange = computed(() => {
  const latencies = timingBuffer.value.map((t) => t.latency * latencyScale.value).filter((l) => l > 0);
  
  if (latencies.length === 0) {
    return { min: 0, max: latencyUnit.value === 'μs' ? 100 : 10 };
  }
  
  const dataMin = Math.min(...latencies);
  const dataMax = Math.max(...latencies);
  const range = dataMax - dataMin;
  
  // 如果波动范围太小，扩展范围以显示细微变化
  // 至少保证有 20% 的数据范围作为显示范围
  const minRange = dataMax * 0.2 || 1;
  const effectiveRange = Math.max(range, minRange);
  
  // 在数据范围基础上增加 10% 的边距
  const padding = effectiveRange * 0.1;
  let axisMin = Math.max(0, dataMin - padding);
  let axisMax = dataMax + padding;
  
  // 如果数据变化很小（< 5%），使用居中显示
  if (range < dataMax * 0.05 && dataMax > 0) {
    const center = (dataMin + dataMax) / 2;
    const halfRange = Math.max(center * 0.15, 1); // 至少显示中心值 ±15%
    axisMin = Math.max(0, center - halfRange);
    axisMax = center + halfRange;
  }
  
  // 美化刻度值
  const niceMax = niceNumber(axisMax);
  const niceMin = axisMin > 0 ? Math.floor(axisMin / (niceMax * 0.1)) * (niceMax * 0.1) : 0;
  
  return { min: niceMin, max: niceMax };
});

// 美化数字（用于Y轴刻度）
function niceNumber(value) {
  if (value <= 0) return 1;
  const exp = Math.floor(Math.log10(value));
  const frac = value / Math.pow(10, exp);
  let nice;
  if (frac <= 1) nice = 1;
  else if (frac <= 2) nice = 2;
  else if (frac <= 5) nice = 5;
  else nice = 10;
  return nice * Math.pow(10, exp);
}

const latencyAxisLabels = computed(() => {
  const unit = latencyUnit.value;
  const { min, max } = latencyAxisRange.value;
  const mid = (min + max) / 2;
  
  const formatVal = (val) => {
    if (val >= 100) return val.toFixed(0);
    if (val >= 10) return val.toFixed(0);
    if (val >= 1) return val.toFixed(1);
    return val.toFixed(2);
  };
  
  return {
    max: `${formatVal(max)} ${unit}`,
    mid: `${formatVal(mid)} ${unit}`,
    min: min > 0 ? `${formatVal(min)} ${unit}` : '0',
  };
});

// 时延统计
const latencyStats = computed(() => {
  const latencies = timingBuffer.value.map((t) => t.latency).filter((l) => l > 0);
  if (latencies.length === 0) {
    return { avg: '-', max: '-', min: '-', jitter: '-' };
  }

  const sum = latencies.reduce((a, b) => a + b, 0);
  const avg = sum / latencies.length;
  const max = Math.max(...latencies);
  const min = Math.min(...latencies);

  // 计算抖动（标准差的近似）
  const squaredDiffs = latencies.map((l) => Math.pow(l - avg, 2));
  const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / latencies.length;
  const jitter = Math.sqrt(avgSquaredDiff);

  return {
    avg: formatLatency(avg),
    max: formatLatency(max),
    min: formatLatency(min),
    jitter: formatLatency(jitter),
  };
});

function formatLatency(ms) {
  if (ms <= 0) return '0';
  // 小于 0.001ms (1μs) 
  if (ms < 0.001) return `${(ms * 1000000).toFixed(1)} ns`;
  // 小于 1ms，用微秒
  if (ms < 1) return `${(ms * 1000).toFixed(1)} μs`;
  // 小于 10ms
  if (ms < 10) return `${ms.toFixed(2)} ms`;
  // 小于 100ms
  if (ms < 100) return `${ms.toFixed(1)} ms`;
  return `${Math.round(ms)} ms`;
}

// 更新时序数据
function updateTimingData() {
  if (!props.messages || props.messages.length === 0) return;

  // 从消息中提取时序数据
  const newTimingPoints = props.messages.slice(-MAX_TIMING_POINTS).map((msg) => {
    const sendTime = msg.sendTimestamp || msg.timestamp || 0;
    const receiveTime = msg.receiveTimestamp || sendTime;
    const latency = Math.max(0, (receiveTime - sendTime) * 1000); // 转换为毫秒
    return {
      messageId: msg.messageId,
      sendTime,
      receiveTime,
      latency,
      protocolType: msg.protocolType,
      // 优先使用名称，没有则使用ID
      senderNode: msg.senderNodeName || msg.senderNodeId,
      receiverNode: msg.receiverNodeName || msg.receiverNodeId,
    };
  });

  timingBuffer.value = newTimingPoints;
}

// 图表布局参数（供鼠标事件使用）
const chartLayout = ref({
  padding: { top: 15, right: 15, bottom: 25, left: 55 },
  width: 0,
  height: 0,
  chartWidth: 0,
  chartHeight: 0,
});

// 绘制时序图
function drawTimingChart() {
  const canvas = timingCanvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 15, right: 15, bottom: 25, left: 55 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // 保存布局供鼠标事件使用
  chartLayout.value = { padding, width, height, chartWidth, chartHeight };

  ctx.clearRect(0, 0, width, height);

  const data = timingBuffer.value;
  if (data.length === 0) return;

  // 使用转换后的单位进行绘制
  const scale = latencyScale.value;
  const { min: axisMin, max: axisMax } = latencyAxisRange.value;
  const axisRange = axisMax - axisMin;
  const pointWidth = chartWidth / Math.max(data.length - 1, 1);

  // 转换数据为当前单位
  const scaledData = data.map((d) => ({
    ...d,
    scaledLatency: d.latency * scale,
  }));

  // 计算Y坐标的辅助函数（考虑min-max范围）
  const getY = (value) => {
    const normalized = (value - axisMin) / axisRange;
    return height - padding.bottom - normalized * chartHeight;
  };

  // 绘制时延区域填充
  const gradientLatency = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradientLatency.addColorStop(0, 'rgba(251, 191, 36, 0.3)');
  gradientLatency.addColorStop(1, 'rgba(251, 191, 36, 0)');

  ctx.beginPath();
  ctx.moveTo(padding.left, height - padding.bottom);

  for (let i = 0; i < scaledData.length; i++) {
    const x = padding.left + i * pointWidth;
    const y = getY(scaledData[i].scaledLatency);
    if (i === 0) {
      ctx.lineTo(x, y);
    } else {
      const prevX = padding.left + (i - 1) * pointWidth;
      const prevY = getY(scaledData[i - 1].scaledLatency);
      const cpX = (prevX + x) / 2;
      ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
      if (i === scaledData.length - 1) ctx.lineTo(x, y);
    }
  }

  ctx.lineTo(padding.left + (scaledData.length - 1) * pointWidth, height - padding.bottom);
  ctx.closePath();
  ctx.fillStyle = gradientLatency;
  ctx.fill();

  // 绘制时延曲线
  ctx.beginPath();
  for (let i = 0; i < scaledData.length; i++) {
    const x = padding.left + i * pointWidth;
    const y = getY(scaledData[i].scaledLatency);
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      const prevX = padding.left + (i - 1) * pointWidth;
      const prevY = getY(scaledData[i - 1].scaledLatency);
      const cpX = (prevX + x) / 2;
      ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
      if (i === scaledData.length - 1) ctx.lineTo(x, y);
    }
  }
  ctx.strokeStyle = '#fbbf24';
  ctx.lineWidth = 2;
  ctx.shadowColor = '#fbbf24';
  ctx.shadowBlur = 6;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // 绘制数据点
  for (let i = 0; i < scaledData.length; i++) {
    const x = padding.left + i * pointWidth;
    const latencyY = getY(scaledData[i].scaledLatency);

    // 数据点（黄色小点）
    ctx.beginPath();
    ctx.arc(x, latencyY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = '#fbbf24';
    ctx.fill();
  }

  // 绘制最新数据点高亮
  if (scaledData.length > 0) {
    const lastX = padding.left + (scaledData.length - 1) * pointWidth;
    const lastY = getY(scaledData[scaledData.length - 1].scaledLatency);

    // 外发光
    ctx.beginPath();
    ctx.arc(lastX, lastY, 8, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(251, 191, 36, 0.3)';
    ctx.fill();

    // 内核
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#fbbf24';
    ctx.fill();
  }
}

// 时序图鼠标移动处理
function handleTimingMouseMove(event) {
  const canvas = timingCanvasRef.value;
  if (!canvas || timingBuffer.value.length === 0) {
    timingTooltip.value.visible = false;
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;

  const { padding, chartWidth, chartHeight, height } = chartLayout.value;
  const data = timingBuffer.value;
  const pointWidth = chartWidth / Math.max(data.length - 1, 1);

  // 找到最近的数据点
  const relativeX = mouseX - padding.left;
  
  // 检查是否在图表区域内
  if (relativeX < 0 || relativeX > chartWidth) {
    timingTooltip.value.visible = false;
    return;
  }

  const index = Math.round(relativeX / pointWidth);

  if (index >= 0 && index < data.length) {
    const point = data[index];
    const scale = latencyScale.value;
    const { min: axisMin, max: axisMax } = latencyAxisRange.value;
    const axisRange = axisMax - axisMin;
    
    // 计算数据点的实际位置（相对于canvas）
    const pointX = padding.left + index * pointWidth;
    const scaledLatency = point.latency * scale;
    const normalized = (scaledLatency - axisMin) / axisRange;
    const pointY = height - padding.bottom - normalized * chartHeight;

    // 计算tooltip位置（使用视口绝对坐标，因为tooltip通过Teleport放到body）
    const tooltipWidth = 180;
    const tooltipHeight = 100;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // 转换为视口坐标
    let tooltipX = rect.left + pointX + 12;
    let tooltipY = rect.top + pointY - tooltipHeight / 2;

    // 如果tooltip会超出右边界，显示在左边
    if (tooltipX + tooltipWidth > viewportWidth - 10) {
      tooltipX = rect.left + pointX - tooltipWidth - 12;
    }
    // 如果超出左边界，贴左边显示
    if (tooltipX < 10) {
      tooltipX = 10;
    }
    // 确保不超出上下边界
    tooltipY = Math.max(10, Math.min(tooltipY, viewportHeight - tooltipHeight - 10));

    timingTooltip.value = {
      visible: true,
      lineX: pointX,
      dotX: pointX - 6,  // 调整为圆点中心
      dotY: pointY - 6,
      tooltipX,
      tooltipY,
      index,
      latency: formatLatency(point.latency),
      protocol: point.protocolType || '-',
      sender: point.senderNode || '-',
      receiver: point.receiverNode || '-',
    };
  } else {
    timingTooltip.value.visible = false;
  }
}

// 时序图鼠标离开处理
function handleTimingMouseLeave() {
  timingTooltip.value.visible = false;
}

// ==================== 带宽分组视图相关 ====================

// 按协议/端口分组的带宽数据
const groupedBandwidth = computed(() => {
  const groups = new Map();

  props.bandwidthData.forEach((item) => {
    const key = groupBy.value === 'protocol' 
      ? (item.protocolType || item.protocol_type || 'unknown')
      : (item.portId || item.port_id || 'unknown');
    
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(item);
  });

  return groups;
});

// 图例数据
const groupedBandwidthLegend = computed(() => {
  const groups = groupedBandwidth.value;
  return Array.from(groups.keys()).map((key) => ({
    key,
    label: key,
  }));
});

// 分组统计数据
const groupedBandwidthStats = computed(() => {
  const groups = groupedBandwidth.value;
  const stats = [];

  groups.forEach((items, key) => {
    if (items.length === 0) return;

    const bandwidths = items.map((item) => item.bandwidthMbps || item.bandwidth_mbps || 0);
    const sum = bandwidths.reduce((a, b) => a + b, 0);
    const avg = sum / bandwidths.length;
    const peak = Math.max(...bandwidths);
    const current = bandwidths[bandwidths.length - 1] || 0;

    stats.push({
      key,
      label: key,
      current: formatBandwidth(current),
      avg: formatBandwidth(avg),
      peak: formatBandwidth(peak),
    });
  });

  return stats;
});

// Y轴最大带宽值
const bandwidthAxisMax = computed(() => {
  const allBandwidths = props.bandwidthData.map((d) => d.bandwidthMbps || d.bandwidth_mbps || 0);
  if (allBandwidths.length === 0) return 1;
  const maxVal = Math.max(...allBandwidths);
  if (maxVal <= 0) return 1;
  if (maxVal < 0.1) return 0.1;
  if (maxVal < 1) return 1;
  if (maxVal <= 10) return Math.ceil(maxVal);
  if (maxVal <= 50) return 50;
  if (maxVal <= 100) return 100;
  return Math.ceil(maxVal / 50) * 50;
});

const bandwidthAxisLabels = computed(() => {
  const max = bandwidthAxisMax.value;
  const formatVal = (val) => {
    if (val < 1) return `${(val * 1000).toFixed(0)} K`;
    return `${val.toFixed(val >= 10 ? 0 : 1)} M`;
  };
  return {
    max: formatVal(max),
    mid: formatVal(max / 2),
  };
});

function formatBandwidth(mbps) {
  if (mbps <= 0) return '0';
  if (mbps < 0.001) return '< 1 Kbps';
  if (mbps < 1) return `${(mbps * 1000).toFixed(1)} Kbps`;
  return `${mbps.toFixed(2)} Mbps`;
}

// 带宽图表布局参数
const bandwidthChartLayout = ref({
  padding: { top: 15, right: 15, bottom: 25, left: 45 },
  width: 0,
  height: 0,
  chartWidth: 0,
  chartHeight: 0,
});

// 绘制分组带宽图
function drawBandwidthChart() {
  const canvas = bandwidthCanvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 15, right: 15, bottom: 25, left: 45 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // 保存布局
  bandwidthChartLayout.value = { padding, width, height, chartWidth, chartHeight };

  ctx.clearRect(0, 0, width, height);

  const groups = groupedBandwidth.value;
  if (groups.size === 0) return;

  const maxBandwidth = Math.max(bandwidthAxisMax.value, 0.001);

  // 为每个分组绘制曲线
  let colorIndex = 0;
  groups.forEach((items, key) => {
    if (items.length === 0) return;

    const color = getGroupColor(colorIndex);
    colorIndex++;

    // 按时间排序并取最近60个点
    const sortedItems = [...items]
      .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
      .slice(-60);

    if (sortedItems.length === 0) return;

    const pointWidth = chartWidth / Math.max(sortedItems.length - 1, 1);

    // 绘制填充区域
    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, color.replace(')', ', 0.2)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, color.replace(')', ', 0)').replace('rgb', 'rgba'));

    ctx.beginPath();
    ctx.moveTo(padding.left, height - padding.bottom);

    for (let i = 0; i < sortedItems.length; i++) {
      const x = padding.left + i * pointWidth;
      const bandwidth = sortedItems[i].bandwidthMbps || sortedItems[i].bandwidth_mbps || 0;
      const y = height - padding.bottom - (bandwidth / maxBandwidth) * chartHeight;

      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = padding.left + (i - 1) * pointWidth;
        const prevBw = sortedItems[i - 1].bandwidthMbps || sortedItems[i - 1].bandwidth_mbps || 0;
        const prevY = height - padding.bottom - (prevBw / maxBandwidth) * chartHeight;
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
        if (i === sortedItems.length - 1) ctx.lineTo(x, y);
      }
    }

    ctx.lineTo(padding.left + (sortedItems.length - 1) * pointWidth, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // 绘制曲线
    ctx.beginPath();
    for (let i = 0; i < sortedItems.length; i++) {
      const x = padding.left + i * pointWidth;
      const bandwidth = sortedItems[i].bandwidthMbps || sortedItems[i].bandwidth_mbps || 0;
      const y = height - padding.bottom - (bandwidth / maxBandwidth) * chartHeight;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        const prevX = padding.left + (i - 1) * pointWidth;
        const prevBw = sortedItems[i - 1].bandwidthMbps || sortedItems[i - 1].bandwidth_mbps || 0;
        const prevY = height - padding.bottom - (prevBw / maxBandwidth) * chartHeight;
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
        if (i === sortedItems.length - 1) ctx.lineTo(x, y);
      }
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowColor = color;
    ctx.shadowBlur = 4;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // 绘制最新点
    if (sortedItems.length > 0) {
      const lastX = padding.left + (sortedItems.length - 1) * pointWidth;
      const lastBw = sortedItems[sortedItems.length - 1].bandwidthMbps || sortedItems[sortedItems.length - 1].bandwidth_mbps || 0;
      const lastY = height - padding.bottom - (lastBw / maxBandwidth) * chartHeight;

      ctx.beginPath();
      ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    }
  });
}

// 带宽图鼠标移动处理
function handleBandwidthMouseMove(event) {
  const canvas = bandwidthCanvasRef.value;
  const groups = groupedBandwidth.value;
  
  if (!canvas || groups.size === 0) {
    bandwidthTooltip.value.visible = false;
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;

  const { padding, chartWidth, height } = bandwidthChartLayout.value;

  // 检查是否在图表区域内
  const relativeX = mouseX - padding.left;
  if (relativeX < 0 || relativeX > chartWidth) {
    bandwidthTooltip.value.visible = false;
    return;
  }

  // 收集所有分组在该位置的数据
  const tooltipGroups = [];
  let maxDataLength = 0;

  groups.forEach((items, key) => {
    const sortedItems = [...items]
      .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
      .slice(-60);
    
    if (sortedItems.length > maxDataLength) {
      maxDataLength = sortedItems.length;
    }
  });

  if (maxDataLength === 0) {
    bandwidthTooltip.value.visible = false;
    return;
  }

  const pointWidth = chartWidth / Math.max(maxDataLength - 1, 1);
  const index = Math.round(relativeX / pointWidth);
  const pointX = padding.left + index * pointWidth;

  let timestamp = null;

  groups.forEach((items, key) => {
    const sortedItems = [...items]
      .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
      .slice(-60);
    
    if (index >= 0 && index < sortedItems.length) {
      const item = sortedItems[index];
      const bandwidth = item.bandwidthMbps || item.bandwidth_mbps || 0;
      
      if (!timestamp && item.timestamp) {
        timestamp = item.timestamp;
      }
      
      tooltipGroups.push({
        key,
        label: key,
        value: formatBandwidth(bandwidth),
      });
    }
  });

  if (tooltipGroups.length === 0) {
    bandwidthTooltip.value.visible = false;
    return;
  }

  // 格式化时间
  const formatTime = (ts) => {
    if (!ts) return '-';
    const date = new Date(ts * 1000);
    const h = date.getHours().toString().padStart(2, '0');
    const m = date.getMinutes().toString().padStart(2, '0');
    const s = date.getSeconds().toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  // 计算tooltip位置（使用视口绝对坐标，因为tooltip通过Teleport放到body）
  const tooltipWidth = 160;
  const tooltipHeight = 30 + tooltipGroups.length * 26;
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  
  // 转换为视口坐标
  let tooltipX = rect.left + pointX + 12;
  let tooltipY = rect.top + 20;

  // 如果tooltip会超出右边界，显示在左边
  if (tooltipX + tooltipWidth > viewportWidth - 10) {
    tooltipX = rect.left + pointX - tooltipWidth - 12;
  }
  // 如果超出左边界，贴左边显示
  if (tooltipX < 10) {
    tooltipX = 10;
  }
  // 确保不超出下边界
  tooltipY = Math.min(tooltipY, viewportHeight - tooltipHeight - 10);

  bandwidthTooltip.value = {
    visible: true,
    lineX: pointX,
    tooltipX,
    tooltipY,
    time: formatTime(timestamp),
    groups: tooltipGroups,
  };
}

// 带宽图鼠标离开处理
function handleBandwidthMouseLeave() {
  bandwidthTooltip.value.visible = false;
}

// ==================== 动画和生命周期 ====================

function animate(timestamp) {
  if (timestamp - lastUpdateTime >= UPDATE_INTERVAL) {
    lastUpdateTime = timestamp;

    if (viewMode.value === 'timing') {
      updateTimingData();
      drawTimingChart();
    } else {
      drawBandwidthChart();
    }
  }

  animationFrameId = requestAnimationFrame(animate);
}

function startAnimation() {
  if (animationFrameId) return;
  lastUpdateTime = performance.now();
  animationFrameId = requestAnimationFrame(animate);
}

function stopAnimation() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

async function initCanvas() {
  await nextTick();
  if (viewMode.value === 'timing' && timingCanvasRef.value) {
    updateTimingData();
    drawTimingChart();
  } else if (viewMode.value === 'bandwidth' && bandwidthCanvasRef.value) {
    drawBandwidthChart();
  }
}

// 监听可见性变化
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      nextTick(() => {
        initCanvas();
        startAnimation();
      });
    } else {
      stopAnimation();
    }
  },
  { immediate: true }
);

// 监听视图模式变化
watch(viewMode, () => {
  nextTick(() => {
    initCanvas();
  });
});

// 监听分组方式变化
watch(groupBy, () => {
  nextTick(() => {
    if (viewMode.value === 'bandwidth') {
      drawBandwidthChart();
    }
  });
});

// 监听消息数据变化
watch(
  () => props.messages,
  () => {
    if (viewMode.value === 'timing' && props.visible) {
      updateTimingData();
    }
  },
  { deep: true }
);

// 监听带宽数据变化
watch(
  () => props.bandwidthData,
  () => {
    if (viewMode.value === 'bandwidth' && props.visible) {
      drawBandwidthChart();
    }
  },
  { deep: true }
);

onMounted(() => {
  if (props.visible) {
    initCanvas();
    startAnimation();
  }
});

onUnmounted(() => {
  stopAnimation();
});
</script>

<style scoped lang="less">
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.live-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;

  .live-dot {
    width: 6px;
    height: 6px;
    background: #fff;
    border-radius: 50%;
    animation: pulse-dot 1.5s ease-in-out infinite;
  }
}

@keyframes pulse-dot {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.timing-panel-content {
  padding: 12px;
  background: linear-gradient(180deg, #0a0f1a 0%, #0d1320 100%);
  border-radius: 8px;
}

:deep(.el-segmented) {
  --el-segmented-bg-color: rgba(255, 255, 255, 0.05);
  --el-segmented-item-hover-bg-color: rgba(255, 255, 255, 0.1);
  --el-segmented-item-selected-bg-color: #10b981;
}

:deep(.el-radio-group) {
  --el-radio-button-checked-bg-color: #10b981;
  --el-radio-button-checked-border-color: #10b981;
}

// 时序视图
.timing-view {
  .timing-chart-wrapper {
    position: relative;
    height: 200px;
    border-radius: 6px;
    overflow: hidden;
    background: #0a0f18;
    border: 1px solid rgba(251, 191, 36, 0.15);
    cursor: crosshair;
  }

  .timing-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  // 垂直指示线
  .chart-crosshair {
    position: absolute;
    top: 15px;
    bottom: 25px;
    width: 1px;
    background: linear-gradient(
      to bottom,
      transparent 0%,
      rgba(251, 191, 36, 0.8) 10%,
      rgba(251, 191, 36, 0.8) 90%,
      transparent 100%
    );
    pointer-events: none;
    z-index: 20;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -2px;
      width: 5px;
      height: 5px;
      background: #fbbf24;
      border-radius: 50%;
    }
  }

  // 数据点高亮
  .chart-highlight-dot {
    position: absolute;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: radial-gradient(circle, #fbbf24 0%, rgba(251, 191, 36, 0.4) 50%, transparent 70%);
    pointer-events: none;
    z-index: 21;
    animation: pulse-highlight 1.5s ease-in-out infinite;
  }

  @keyframes pulse-highlight {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.7;
    }
  }
}

// 带宽分组视图
.bandwidth-grouped-view {
  .group-selector {
    margin-bottom: 12px;
  }

  .grouped-chart-wrapper {
    position: relative;
    height: 160px;
    border-radius: 6px;
    overflow: hidden;
    background: #0a0f18;
    border: 1px solid rgba(0, 255, 136, 0.15);
  }

  .bandwidth-canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }
}

// 通用样式
.oscilloscope-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;

  .grid-lines {
    position: absolute;
    inset: 0;
    background-image: linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 20px 20px;
  }
}

.y-axis-labels {
  position: absolute;
  left: 4px;
  top: 15px;
  bottom: 25px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  z-index: 10;

  span {
    font-size: 9px;
    color: rgba(255, 255, 255, 0.4);
    font-family: monospace;
  }
}

.chart-legend {
  position: absolute;
  top: 6px;
  right: 10px;
  display: flex;
  gap: 12px;
  z-index: 10;

  .legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.6);
  }

  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;

    &.send {
      background: #10b981;
    }
    &.receive {
      background: #3b82f6;
    }
  }

  .legend-line {
    width: 16px;
    height: 2px;
    border-radius: 1px;

    &.latency {
      background: #fbbf24;
    }
  }

  &.grouped-legend {
    flex-wrap: wrap;
    max-width: 200px;
    gap: 8px;

    .legend-line {
      width: 12px;
      height: 3px;
    }
  }
}

// 统计卡片
.latency-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);

  .stat-icon {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;

    &.avg {
      background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    }
    &.max {
      background: linear-gradient(135deg, #f59e0b, #d97706);
    }
    &.min {
      background: linear-gradient(135deg, #10b981, #059669);
    }
    &.jitter {
      background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    }

    &::before {
      content: '';
      width: 8px;
      height: 8px;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 2px;
    }
  }

  .stat-content {
    display: flex;
    flex-direction: column;
    min-width: 0;

    .stat-label {
      font-size: 9px;
      color: rgba(255, 255, 255, 0.4);
    }

    .stat-value {
      font-size: 12px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.9);
      font-family: monospace;

      &.highlight-warning {
        color: #fbbf24;
      }
      &.highlight-success {
        color: #10b981;
      }
    }
  }
}

// 分组统计表格
.grouped-stats-table {
  margin-top: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;

  .stats-header,
  .stats-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 8px;
    padding: 8px 12px;

    span {
      font-size: 11px;
      font-family: monospace;
    }
  }

  .stats-header {
    background: rgba(255, 255, 255, 0.03);
    color: rgba(255, 255, 255, 0.5);
    font-weight: 500;
  }

  .stats-row {
    color: rgba(255, 255, 255, 0.8);
    border-top: 1px solid rgba(255, 255, 255, 0.03);

    &:hover {
      background: rgba(255, 255, 255, 0.03);
    }

    .group-name {
      display: flex;
      align-items: center;
      gap: 6px;

      .color-dot {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        flex-shrink: 0;
      }
    }

    .stat-current {
      color: #00ff88;
    }

    .stat-peak {
      color: #fbbf24;
    }
  }

  .stats-empty {
    padding: 20px;
    text-align: center;
    color: rgba(255, 255, 255, 0.3);
    font-size: 12px;
  }
}
</style>

<style lang="less">
@import '../styles/aviation-dark-theme.less';
@import '../styles/chart-tooltip.less';
</style>
