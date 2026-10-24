<template>
  <section class="simulation-widget-content">
    <header class="simulation-widget-toolbar">
      <div class="flex items-center gap-2 flex-1">
        <el-tag v-if="isRunning" type="success" size="small" effect="dark" class="live-tag">
          <span class="live-dot"></span>
          实时
        </el-tag>
        <el-tag v-else-if="isWaiting" type="info" size="small" effect="plain"> 待机 </el-tag>

        <div class="flex items-center gap-2 ml-auto">
          <el-segmented v-model="viewMode" :options="viewOptions" size="small" />
          <el-select
            v-if="viewMode === 'port'"
            v-model="selectedPort"
            placeholder="选择端口"
            size="small"
            style="width: 120px"
            clearable
            popper-class="sim-popper-dark"
          >
            <el-option v-for="port in portList" :key="port" :label="port" :value="port" />
          </el-select>
        </div>
      </div>
    </header>

    <div class="bandwidth-chart-panel monitor-panel" :style="chartStyle">
      <!-- 实时图表区域 -->
      <div
        class="chart-wrapper"
        @mousemove="handleChartMouseMove"
        @mouseleave="handleChartMouseLeave"
      >
        <!-- 示波器风格背景 -->
        <div class="oscilloscope-bg">
          <div class="grid-lines"></div>
          <div v-if="hasData" class="scanline" :style="{ left: scanlinePosition }"></div>
        </div>

        <!-- Canvas 图表 -->
        <canvas ref="canvasRef" class="chart-canvas"></canvas>

        <!-- 当前值显示 -->
        <div class="current-value-display">
          <div class="label">实时带宽</div>
          <div class="value" :class="bandwidthLevelClass">
            {{ displayBandwidth.value }}
            <span class="unit">{{ displayBandwidth.unit }}</span>
          </div>
        </div>

        <!-- 状态指示 -->
        <div class="status-indicator">
          <span class="status-dot" :class="statusClass"></span>
          <span class="status-text">{{ statusText }}</span>
        </div>

        <!-- Y轴刻度 -->
        <div class="y-axis-labels">
          <span>{{ yAxisLabels.max }}</span>
          <span>{{ yAxisLabels.mid }}</span>
          <span>0</span>
        </div>

        <!-- 垂直指示线 -->
        <div
          v-if="chartTooltip.visible"
          class="chart-crosshair"
          :style="{ left: chartTooltip.lineX + 'px' }"
        ></div>

        <!-- 数据点高亮 -->
        <div
          v-if="chartTooltip.visible"
          class="chart-highlight-dot"
          :style="{
            left: chartTooltip.dotX + 'px',
            top: chartTooltip.dotY + 'px',
          }"
        ></div>
      </div>

      <!-- Tooltip 浮层 (fixed定位，避免被截断) -->
      <Teleport v-if="chartPortalTarget" :to="chartPortalTarget">
        <div
          v-if="chartTooltip.visible"
          class="chart-tooltip-fixed bandwidth"
          :style="{
            ...chartStyle,
            left: chartTooltip.tooltipX + 'px',
            top: chartTooltip.tooltipY + 'px',
          }"
        >
          <div class="tooltip-header">
            <span class="tooltip-time">{{ chartTooltip.time }}</span>
            <span class="tooltip-index">#{{ chartTooltip.index + 1 }}</span>
          </div>
          <div class="tooltip-main-value">
            <span class="main-value">
              {{ chartTooltip.value }}
              <span class="unit">{{ chartTooltip.unit }}</span>
            </span>
          </div>
        </div>
      </Teleport>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon avg"></div>
          <div class="stat-content">
            <span class="stat-label">平均</span>
            <span class="stat-value">{{ stats.avg }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon peak"></div>
          <div class="stat-content">
            <span class="stat-label">峰值</span>
            <span class="stat-value highlight">{{ stats.peak }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon min"></div>
          <div class="stat-content">
            <span class="stat-label">最小</span>
            <span class="stat-value">{{ stats.min }}</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon count"></div>
          <div class="stat-content">
            <span class="stat-label">报文</span>
            <span class="stat-value">{{ stats.msgCount }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRequiredThemePortalBinding } from '@zxio/zxui';
import { useChartTheme } from '@/theme/useChartTheme';

const { theme: chartTheme } = useChartTheme();
const portal = useRequiredThemePortalBinding();
const chartPortalTarget = computed(() =>
  portal.ok ? portal.value.binding.value?.target : undefined
);
const chartStyle = computed(() =>
  chartTheme.value
    ? {
        '--simulation-chart-surface': chartTheme.value.backgroundColor,
        '--simulation-chart-text': chartTheme.value.textStyle.color,
        '--simulation-chart-muted': chartTheme.value.legend.inactiveColor,
        '--simulation-chart-grid': chartTheme.value.valueAxis.splitLine.lineStyle.color,
      }
    : {}
);

const props = defineProps({
  bandwidthData: {
    type: Array,
    default: () => [],
  },
  running: {
    type: Boolean,
    default: undefined,
  },
  speed: {
    type: Number,
    default: 1,
  },
  resetOnStop: {
    type: Boolean,
    default: false,
  },
});

// DOM引用
const canvasRef = ref(null);

// 状态
const viewMode = ref('total');
const selectedPort = ref(null);
const viewOptions = [
  { label: '汇总', value: 'total' },
  { label: '按端口', value: 'port' },
];
const hasData = ref(false);

// 带宽数值格式化，自动在 Mbps/Kbps 之间切换，避免小数被四舍五入成 0
const formatBandwidth = (valueMbps) => {
  const safeVal = Number(valueMbps) || 0;
  if (safeVal <= 0) {
    return { value: '0.00', unit: 'Mbps', text: '0.00 Mbps' };
  }
  if (safeVal < 1) {
    const kbps = safeVal * 1000;
    const digits = kbps >= 10 ? 1 : 2;
    const value = kbps.toFixed(digits);
    return { value, unit: 'Kbps', text: `${value} Kbps` };
  }
  const digits = safeVal >= 100 ? 1 : 2;
  const value = safeVal.toFixed(digits);
  return { value, unit: 'Mbps', text: `${value} Mbps` };
};

// 实时数据缓冲区（固定600个点，表示10分钟按1秒采样）
const MAX_POINTS = 600;
const dataBuffer = ref(new Array(MAX_POINTS).fill(0));
const currentBandwidth = ref(0);
const scanlineOffset = ref(0);
const STEP_OFFSET = 100 / MAX_POINTS;

// 动画相关
let animationFrameId = null;
let lastUpdateTime = 0;
const UPDATE_INTERVAL = 1000; // 每秒更新一次数据点
const MIN_SPEED = 0.25;

// Tooltip 状态
const chartTooltip = ref({
  visible: false,
  lineX: 0,
  dotX: 0,
  dotY: 0,
  tooltipX: 0,
  tooltipY: 0,
  index: 0,
  time: '',
  value: '',
  unit: '',
});

// 图表布局参数（供鼠标事件使用）
const chartLayout = ref({
  padding: { top: 10, right: 10, bottom: 20, left: 40 },
  width: 0,
  height: 0,
  chartWidth: 0,
  chartHeight: 0,
});

// 是否正在运行
const isRunning = computed(() => {
  if (props.running !== undefined && props.running !== null) {
    return props.running;
  }
  if (props.bandwidthData.length === 0) return false;
  const latestTime = Math.max(...props.bandwidthData.map((d) => d.timestamp || 0));
  const now = Date.now() / 1000;
  return now - latestTime < 5;
});

// 是否待机
const isWaiting = computed(() => true && props.bandwidthData.length === 0);

// 状态文字
const statusText = computed(() => {
  if (isRunning.value) return '采集中';
  if (props.bandwidthData.length > 0) return '已暂停';
  return '等待数据';
});

// 状态样式
const statusClass = computed(() => {
  if (isRunning.value) return 'running';
  if (props.bandwidthData.length > 0) return 'paused';
  return 'waiting';
});

// 扫描线位置
const scanlinePosition = computed(() => {
  return `${scanlineOffset.value % 100}%`;
});

// 端口列表
const portList = computed(() => {
  const ports = new Set();
  props.bandwidthData.forEach((item) => {
    if (item.portId) {
      ports.add(item.portId);
    }
  });
  return Array.from(ports);
});

// Y轴最大值（动态调整）
const yAxisMax = computed(() => {
  const maxVal = Math.max(...dataBuffer.value, 0);
  if (maxVal <= 0) return 1;
  if (maxVal < 0.01) return 0.01;
  if (maxVal < 0.1) return 0.1;
  if (maxVal < 1) return Math.ceil(maxVal * 10) / 10;
  if (maxVal <= 10) return Math.ceil(maxVal);
  if (maxVal <= 50) return 50;
  if (maxVal <= 100) return 100;
  return Math.ceil(maxVal / 50) * 50;
});

const yAxisLabels = computed(() => {
  const formatAxisValue = (val) => {
    if (val >= 10) return val.toFixed(0);
    if (val >= 1) return val.toFixed(1);
    return val.toFixed(3);
  };
  return {
    max: formatAxisValue(yAxisMax.value),
    mid: formatAxisValue(yAxisMax.value / 2),
  };
});

// 格式化带宽显示
const displayBandwidth = computed(() => formatBandwidth(currentBandwidth.value));

// 带宽级别样式
const bandwidthLevelClass = computed(() => {
  const val = currentBandwidth.value;
  if (val > 50) return 'critical';
  if (val > 20) return 'warning';
  return 'normal';
});

// 统计数据
const stats = computed(() => {
  const validData = dataBuffer.value.filter((v) => v > 0);
  if (validData.length === 0) {
    const zero = formatBandwidth(0);
    return { avg: zero.text, peak: zero.text, min: zero.text, msgCount: 0 };
  }

  const sum = validData.reduce((a, b) => a + b, 0);
  const avg = sum / validData.length;
  const peak = Math.max(...validData);
  const min = Math.min(...validData);

  // 计算报文总数
  const msgCount = props.bandwidthData.reduce((acc, item) => acc + (item.messageCount || 0), 0);

  return {
    avg: formatBandwidth(avg).text,
    peak: formatBandwidth(peak).text,
    min: formatBandwidth(min).text,
    msgCount,
  };
});

// 播放速率，最低 0.25x，防止 0
const playSpeed = computed(() => {
  const val = Number(props.speed) || 1;
  return Math.max(val, MIN_SPEED);
});

// 动画间隔随速度缩放
const intervalMs = computed(() => UPDATE_INTERVAL / playSpeed.value);

// 自动选择第一个端口
watch(
  portList,
  (newList) => {
    if (newList.length > 0 && !selectedPort.value) {
      selectedPort.value = newList[0];
    }
  },
  { immediate: true }
);

// 监听数据变化，更新缓冲区
watch(
  () => props.bandwidthData,
  (newData) => {
    hasData.value = Array.isArray(newData) && newData.length > 0;
    if (!newData || newData.length === 0) return;

    // 根据视图模式过滤数据
    let filteredData = newData;
    if (viewMode.value === 'port' && selectedPort.value) {
      filteredData = newData.filter((item) => item.portId === selectedPort.value);
    }

    // 汇总模式：合并同一时间戳的数据
    if (viewMode.value === 'total') {
      const timeMap = new Map();
      filteredData.forEach((item) => {
        const ts = Math.floor(item.timestamp || 0);
        if (!timeMap.has(ts)) {
          timeMap.set(ts, { bandwidth: 0, count: 0 });
        }
        const entry = timeMap.get(ts);
        entry.bandwidth += item.bandwidthMbps || 0;
        entry.count += item.messageCount || 0;
      });

      // 获取最新的带宽值
      const sortedTimes = Array.from(timeMap.keys()).sort((a, b) => b - a);
      if (sortedTimes.length > 0) {
        const latestEntry = timeMap.get(sortedTimes[0]);
        currentBandwidth.value = latestEntry.bandwidth;
      }
    } else {
      // 端口模式：取最新值
      const sorted = [...filteredData].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
      if (sorted.length > 0) {
        currentBandwidth.value = sorted[0].bandwidthMbps || 0;
      }
    }
  },
  { deep: true, immediate: true }
);

// 绘制图表
function drawChart() {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  // 设置画布尺寸
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 10, right: 10, bottom: 20, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // 保存布局供鼠标事件使用
  chartLayout.value = { padding, width, height, chartWidth, chartHeight };

  // 清空画布
  ctx.clearRect(0, 0, width, height);

  // 绘制波形
  const data = dataBuffer.value;
  const maxY = Math.max(yAxisMax.value, 0.001);
  const pointWidth = chartWidth / (MAX_POINTS - 1);

  // 创建渐变
  const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  gradient.addColorStop(0, 'rgba(0, 255, 136, 0.4)');
  gradient.addColorStop(1, 'rgba(0, 255, 136, 0)');

  // 绘制填充区域
  ctx.beginPath();
  ctx.moveTo(padding.left, height - padding.bottom);

  for (let i = 0; i < data.length; i++) {
    const x = padding.left + i * pointWidth;
    const y = height - padding.bottom - (data[i] / maxY) * chartHeight;
    if (i === 0) {
      ctx.lineTo(x, y);
    } else {
      // 使用贝塞尔曲线使线条更平滑
      const prevX = padding.left + (i - 1) * pointWidth;
      const prevY = height - padding.bottom - (data[i - 1] / maxY) * chartHeight;
      const cpX = (prevX + x) / 2;
      ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
      if (i === data.length - 1) {
        ctx.lineTo(x, y);
      }
    }
  }

  ctx.lineTo(padding.left + (data.length - 1) * pointWidth, height - padding.bottom);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // 绘制线条
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = padding.left + i * pointWidth;
    const y = height - padding.bottom - (data[i] / maxY) * chartHeight;
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      const prevX = padding.left + (i - 1) * pointWidth;
      const prevY = height - padding.bottom - (data[i - 1] / maxY) * chartHeight;
      const cpX = (prevX + x) / 2;
      ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + y) / 2);
      if (i === data.length - 1) {
        ctx.lineTo(x, y);
      }
    }
  }

  ctx.strokeStyle = '#00ff88';
  ctx.lineWidth = 2;
  ctx.shadowColor = '#00ff88';
  ctx.shadowBlur = 8;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // 绘制最新数据点发光效果
  if (data.length > 0) {
    const lastX = padding.left + (data.length - 1) * pointWidth;
    const lastY = height - padding.bottom - (data[data.length - 1] / maxY) * chartHeight;

    // 外发光
    ctx.beginPath();
    ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 255, 136, 0.3)';
    ctx.fill();

    // 内核
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#00ff88';
    ctx.fill();
  }
}

// 鼠标移动处理
function handleChartMouseMove(event) {
  const canvas = canvasRef.value;
  if (!canvas || dataBuffer.value.length === 0) {
    chartTooltip.value.visible = false;
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;

  const { padding, chartWidth, chartHeight, height } = chartLayout.value;
  const data = dataBuffer.value;
  const pointWidth = chartWidth / (MAX_POINTS - 1);

  // 找到最近的数据点
  const relativeX = mouseX - padding.left;

  // 检查是否在图表区域内
  if (relativeX < 0 || relativeX > chartWidth) {
    chartTooltip.value.visible = false;
    return;
  }

  const index = Math.round(relativeX / pointWidth);

  if (index >= 0 && index < data.length) {
    const value = data[index];
    const maxY = Math.max(yAxisMax.value, 0.001);

    // 计算数据点的实际位置（相对于canvas）
    const pointX = padding.left + index * pointWidth;
    const pointY = height - padding.bottom - (value / maxY) * chartHeight;

    // 计算tooltip位置（使用视口绝对坐标，因为 tooltip 通过主题 Portal 挂载）
    const tooltipWidth = 140;
    const tooltipHeight = 70;
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

    // 格式化带宽值
    const formatted = formatBandwidth(value);

    // 计算时间（假设每个点代表1秒，从当前时间往前推）
    const secondsAgo = data.length - 1 - index;
    const time = secondsAgo === 0 ? '现在' : `-${secondsAgo}s`;

    chartTooltip.value = {
      visible: true,
      lineX: pointX,
      dotX: pointX - 6,
      dotY: pointY - 6,
      tooltipX,
      tooltipY,
      index,
      time,
      value: formatted.value,
      unit: formatted.unit,
    };
  } else {
    chartTooltip.value.visible = false;
  }
}

// 鼠标离开处理
function handleChartMouseLeave() {
  chartTooltip.value.visible = false;
}

// 动画循环
function animate(timestamp) {
  if (!isRunning.value) {
    stopAnimation();
    return;
  }

  scanlineOffset.value += 0.5 * playSpeed.value;

  // 每秒更新一次数据点
  if (timestamp - lastUpdateTime >= intervalMs.value) {
    lastUpdateTime = timestamp;

    // 将数据向左移动，添加新数据到右侧
    const newBuffer = [...dataBuffer.value.slice(1), currentBandwidth.value];
    dataBuffer.value = newBuffer;

    // 重绘图表
    drawChart();
  }

  animationFrameId = requestAnimationFrame(animate);
}

// 单步推进扫描线
function stepScanline() {
  scanlineOffset.value += STEP_OFFSET;
  drawChart();
}

// 启动动画
function startAnimation() {
  if (animationFrameId) return;
  lastUpdateTime = performance.now();
  animationFrameId = requestAnimationFrame(animate);
}

// 停止动画
function stopAnimation() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

// 初始化画布
async function initCanvas() {
  await nextTick();
  if (canvasRef.value) {
    drawChart();
  }
}

watch(isRunning, (running) => {
  if (running) {
    startAnimation();
  } else {
    stopAnimation();
    if (props.resetOnStop) {
      dataBuffer.value = new Array(MAX_POINTS).fill(0);
      currentBandwidth.value = 0;
      drawChart();
    }
  }
});

// 监听视图模式变化
watch([viewMode, selectedPort], () => {
  // 重置缓冲区
  dataBuffer.value = new Array(MAX_POINTS).fill(0);
  currentBandwidth.value = 0;
});

onMounted(() => {
  initCanvas();
  if (isRunning.value) startAnimation();
});

onUnmounted(() => {
  stopAnimation();
});

defineExpose({
  stepScanline,
});
</script>

<style scoped lang="less">
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

.monitor-panel {
  padding: 12px;
  background: var(--simulation-chart-surface, var(--zx-semantic-surface-canvas-fill));
  border-radius: 8px;
}

.chart-wrapper {
  position: relative;
  height: 180px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--simulation-chart-surface, var(--zx-semantic-surface-canvas-fill));
  border: 1px solid var(--simulation-chart-grid, var(--zx-semantic-border-subtle));
  cursor: crosshair;
}

.oscilloscope-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;

  .grid-lines {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(
        to right,
        var(--simulation-chart-grid, var(--zx-semantic-border-subtle)) 1px,
        transparent 1px
      ),
      linear-gradient(
        to bottom,
        var(--simulation-chart-grid, var(--zx-semantic-border-subtle)) 1px,
        transparent 1px
      );
    background-size: 20px 20px;
  }

  .scanline {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(
      to bottom,
      transparent,
      rgba(0, 255, 136, 0.6),
      rgba(0, 255, 136, 0.8),
      rgba(0, 255, 136, 0.6),
      transparent
    );
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
    opacity: 0.7;
  }
}

.chart-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

// 垂直指示线
.chart-crosshair {
  position: absolute;
  top: 10px;
  bottom: 20px;
  width: 1px;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0, 255, 136, 0.8) 10%,
    rgba(0, 255, 136, 0.8) 90%,
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
    background: #00ff88;
    border-radius: 50%;
  }
}

// 数据点高亮
.chart-highlight-dot {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(circle, #00ff88 0%, rgba(0, 255, 136, 0.4) 50%, transparent 70%);
  pointer-events: none;
  z-index: 21;
  animation: pulse-highlight 1.5s ease-in-out infinite;
}

@keyframes pulse-highlight {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.7;
  }
}

.current-value-display {
  position: absolute;
  top: 8px;
  right: 8px;
  text-align: right;
  z-index: 10;

  .label {
    font-size: 10px;
    color: var(--simulation-chart-muted, var(--zx-semantic-text-secondary));
    margin-bottom: 2px;
  }

  .value {
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.5px;
    text-shadow: 0 0 20px currentColor;

    &.normal {
      color: var(--zx-semantic-status-success-on-surface);
    }
    &.warning {
      color: var(--zx-semantic-status-warning-on-surface);
    }
    &.critical {
      color: var(--zx-semantic-status-danger-on-surface);
      animation: pulse-critical 1s ease-in-out infinite;
    }

    .unit {
      font-size: 10px;
      font-weight: 400;
      opacity: 0.7;
    }
  }
}

@keyframes pulse-critical {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.status-indicator {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 10;

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;

    &.running {
      background: #00ff88;
      box-shadow: 0 0 8px #00ff88;
      animation: pulse-dot 1.5s ease-in-out infinite;
    }
    &.paused {
      background: #fbbf24;
    }
    &.waiting {
      background: var(--zx-semantic-text-disabled);
      animation: pulse-dot 2s ease-in-out infinite;
    }
  }

  .status-text {
    font-size: 10px;
    color: var(--simulation-chart-muted, var(--zx-semantic-text-secondary));
  }
}

.y-axis-labels {
  position: absolute;
  left: 4px;
  top: 10px;
  bottom: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  z-index: 10;

  span {
    font-size: 9px;
    color: var(--simulation-chart-muted, var(--zx-semantic-text-secondary));
    font-family: monospace;
  }
}

.stats-grid {
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
  background: var(--zx-semantic-surface-card-fill);
  border-radius: 6px;
  border: 1px solid var(--simulation-chart-grid, var(--zx-semantic-border-subtle));

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
    &.peak {
      background: linear-gradient(135deg, #f59e0b, #d97706);
    }
    &.min {
      background: linear-gradient(135deg, #10b981, #059669);
    }
    &.count {
      background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    }

    &::before {
      content: '';
      width: 8px;
      height: 8px;
      background: var(--zx-semantic-surface-card-fill);
      border-radius: 2px;
    }
  }

  .stat-content {
    display: flex;
    flex-direction: column;
    min-width: 0;

    .stat-label {
      font-size: 9px;
      color: var(--simulation-chart-muted, var(--zx-semantic-text-secondary));
    }

    .stat-value {
      font-size: 12px;
      font-weight: 600;
      color: var(--simulation-chart-text, var(--zx-semantic-text-primary));
      font-family: monospace;

      &.highlight {
        color: var(--zx-semantic-status-warning-on-surface);
      }
    }
  }
}
</style>

<style lang="less">
@import '../styles/aviation-dark-theme.less';
@import '../styles/chart-tooltip.less';
</style>
