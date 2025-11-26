<template>
  <transition name="fade-slide">
    <zx-floating-panel
      v-if="visible"
      title="实时带宽监控"
      :position="position"
      :size="size"
      :collapsed-size="collapsedSize"
      :default-collapsed="defaultCollapsed"
    >
      <template #header>
        <div class="flex items-center gap-2">
          <span class="font-semibold text-sm">带宽使用情况</span>
          <el-tag v-if="isRunning" type="success" size="small" effect="dark" class="animate-pulse">
            实时
          </el-tag>
          <el-tag v-else-if="isWaiting" type="warning" size="small" effect="plain"> 待机 </el-tag>
        </div>
      </template>

      <div class="py-3">
        <!-- 视图切换 & 端口选择 -->
        <div class="flex items-center gap-2 mb-3">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="total">汇总</el-radio-button>
            <el-radio-button value="port">按端口</el-radio-button>
          </el-radio-group>
          <el-select
            v-if="viewMode === 'port'"
            v-model="selectedPort"
            placeholder="选择端口"
            size="small"
            class="flex-1"
            clearable
          >
            <el-option v-for="port in portList" :key="port" :label="port" :value="port" />
          </el-select>
        </div>

        <!-- 图表 - 始终显示心电图效果 -->
        <div
          class="chart-container min-h-[220px] bg-slate-900 rounded-lg p-2 relative overflow-hidden"
        >
          <!-- 扫描线动画 -->
          <div v-if="isRunning || isWaiting" class="scan-line"></div>
          <!-- 网格背景 -->
          <div class="grid-bg"></div>

          <ZxChart
            v-if="chartOptions"
            ref="chartRef"
            :options="chartOptions"
            height="200px"
            :auto-resize="true"
          />

          <!-- 当前值显示 -->
          <!-- <div class="absolute top-2 right-2 text-right z-10">
            <div class="text-xs text-slate-400">当前带宽</div>
            <div class="text-lg font-mono font-bold" :class="bandwidthColorClass">
              {{ currentBandwidth }} <span class="text-xs">Mbps</span>
            </div>
          </div> -->

          <!-- 状态指示器 -->
          <div class="absolute bottom-2 left-2 flex items-center gap-1.5 z-10">
            <span class="status-dot" :class="statusDotClass"></span>
            <span class="text-xs text-slate-500">{{ statusText }}</span>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="grid grid-cols-4 gap-2 mt-3 text-center">
          <div class="bg-slate-50 rounded px-2 py-1.5">
            <div class="text-xs text-gray-400">平均</div>
            <div class="text-sm font-semibold text-gray-700">{{ stats?.avg || '0.00' }}</div>
          </div>
          <div class="bg-slate-50 rounded px-2 py-1.5">
            <div class="text-xs text-gray-400">峰值</div>
            <div class="text-sm font-semibold text-amber-600">{{ stats?.peak || '0.00' }}</div>
          </div>
          <div class="bg-slate-50 rounded px-2 py-1.5">
            <div class="text-xs text-gray-400">最小</div>
            <div class="text-sm font-semibold text-gray-700">{{ stats?.min || '0.00' }}</div>
          </div>
          <div class="bg-slate-50 rounded px-2 py-1.5">
            <div class="text-xs text-gray-400">报文数</div>
            <div class="text-sm font-semibold text-blue-600">{{ stats?.msgCount || 0 }}</div>
          </div>
        </div>
      </div>
    </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
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
    default: () => ({ top: '100px', right: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '420px', maxHeight: '450px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: false,
  },
});

const chartRef = ref(null);
const viewMode = ref('total');
const selectedPort = ref(null);
const heartbeatTick = ref(0); // 用于触发心跳动画更新

// 心跳定时器
let heartbeatTimer = null;

onMounted(() => {
  // 启动心跳动画（每200ms更新一次）
  heartbeatTimer = setInterval(() => {
    heartbeatTick.value++;
  }, 200);
});

onUnmounted(() => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
  }
});

// 是否有真实数据
const hasRealData = computed(() => props.bandwidthData.length > 0);

// 是否正在运行（最近5秒内有数据更新）
const isRunning = computed(() => {
  if (props.bandwidthData.length === 0) return false;
  const latestTime = Math.max(...props.bandwidthData.map((d) => d.timestamp || 0));
  const now = Date.now() / 1000;
  return now - latestTime < 5;
});

// 是否待机状态（面板可见但无数据）
const isWaiting = computed(() => props.visible && !hasRealData.value);

// 状态文字
const statusText = computed(() => {
  if (isRunning.value) return '数据采集中';
  if (hasRealData.value) return '已暂停';
  return '等待数据';
});

// 状态指示点样式
const statusDotClass = computed(() => {
  if (isRunning.value) return 'bg-green-500 animate-pulse';
  if (hasRealData.value) return 'bg-yellow-500';
  return 'bg-slate-500 animate-pulse';
});

// 带宽值颜色
const bandwidthColorClass = computed(() => {
  const val = parseFloat(currentBandwidth.value);
  if (val > 50) return 'text-red-400';
  if (val > 20) return 'text-amber-400';
  return 'text-green-400';
});

// 从数据中提取端口列表
const portList = computed(() => {
  const ports = new Set();
  props.bandwidthData.forEach((item) => {
    if (item.portId) {
      ports.add(item.portId);
    }
  });
  return Array.from(ports);
});

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

// 获取显示数据（根据视图模式）
const displayData = computed(() => {
  let data = props.bandwidthData;

  if (viewMode.value === 'port' && selectedPort.value) {
    data = data.filter((item) => item.portId === selectedPort.value);
  }

  // 按时间戳排序
  data = [...data].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

  // 如果是汇总模式，合并同一时间戳的数据
  if (viewMode.value === 'total' && data.length > 0) {
    const timeMap = new Map();
    data.forEach((item) => {
      const rawTs = item.timestamp || 0;
      const ts = Number(rawTs.toFixed(2));
      if (!timeMap.has(ts)) {
        timeMap.set(ts, { timestamp: ts, bandwidthMbps: 0, messageCount: 0 });
      }
      const existing = timeMap.get(ts);
      existing.bandwidthMbps += item.bandwidthMbps || 0;
      existing.messageCount += item.messageCount || 0;
    });
    data = Array.from(timeMap.values()).sort((a, b) => a.timestamp - b.timestamp);
  }

  // 保留最近60个数据点
  return data.slice(-60);
});

// 计算仿真开始时间
const startTime = computed(() => {
  if (props.bandwidthData.length === 0) return 0;
  return Math.min(...props.bandwidthData.map((d) => d.timestamp || 0));
});

// 当前带宽值
const currentBandwidth = computed(() => {
  const data = displayData.value;
  if (data.length === 0) return '0.00';
  return (data[data.length - 1].bandwidthMbps || 0).toFixed(2);
});

/**
 * 生成心电图风格的基线数据
 * 模拟网络心跳 - 周期性的小脉冲，表示系统在线但无数据传输
 */
const generateHeartbeatData = (pointCount = 60) => {
  // 依赖tick触发重新计算，实现动态心跳效果
  void heartbeatTick.value;
  const data = [];
  const now = Date.now() / 1000;

  for (let i = 0; i < pointCount; i++) {
    const t = i / pointCount;
    let value = 0;

    // 每隔一段时间产生一个心跳脉冲（模拟网络探测/心跳包）
    const beatPhase = (t * 5 + now * 0.5) % 1; // 5个周期，动态偏移

    if (beatPhase < 0.08) {
      // 快速上升
      value = (beatPhase / 0.08) * 2.5;
    } else if (beatPhase < 0.15) {
      // 主峰
      const peakPhase = (beatPhase - 0.08) / 0.07;
      value = 2.5 + Math.sin(peakPhase * Math.PI) * 1.5;
    } else if (beatPhase < 0.22) {
      // 快速下降
      value = 2.5 * (1 - (beatPhase - 0.15) / 0.07);
    } else if (beatPhase < 0.28) {
      // 小反弹
      const reboundPhase = (beatPhase - 0.22) / 0.06;
      value = Math.sin(reboundPhase * Math.PI) * 0.8;
    } else {
      // 基线 + 微小噪声
      value = (Math.random() - 0.5) * 0.15;
    }

    // 确保值为正
    value = Math.max(0, value);

    data.push({
      timestamp: now - (pointCount - i) * 0.5,
      bandwidthMbps: value,
      isHeartbeat: true,
    });
  }

  return data;
};

/**
 * 增强真实数据，添加视觉效果
 * 在真实数据基础上添加微小波动，使图表更生动
 */
const enhanceRealData = (data) => {
  if (data.length === 0) return data;

  // 如果数据点太少，插值扩展
  if (data.length < 10) {
    const enhanced = [];
    for (let i = 0; i < data.length; i++) {
      enhanced.push(data[i]);
      // 在两点之间插入过渡点
      if (i < data.length - 1) {
        const curr = data[i];
        const next = data[i + 1];
        const steps = 3;
        for (let j = 1; j <= steps; j++) {
          const t = j / (steps + 1);
          const interpValue = curr.bandwidthMbps + (next.bandwidthMbps - curr.bandwidthMbps) * t;
          // 添加微小波动
          const noise = (Math.random() - 0.5) * 0.1 * Math.max(interpValue, 0.5);
          enhanced.push({
            timestamp: curr.timestamp + (next.timestamp - curr.timestamp) * t,
            bandwidthMbps: Math.max(0, interpValue + noise),
            messageCount: Math.round(
              curr.messageCount + (next.messageCount - curr.messageCount) * t
            ),
          });
        }
      }
    }
    return enhanced.slice(-60);
  }

  // 数据足够多时，只添加微小波动使曲线更自然
  return data.map((item) => ({
    ...item,
    bandwidthMbps: Math.max(0, item.bandwidthMbps + (Math.random() - 0.5) * 0.05),
  }));
};

// 格式化图表数据 - 融合真实数据和心跳效果
const chartData = computed(() => {
  let data = displayData.value;

  // 无真实数据时显示心跳效果
  if (data.length === 0) {
    data = generateHeartbeatData(60);
    const xData = data.map((_, i) => i);
    const yData = data.map((item) => item.bandwidthMbps.toFixed(2));
    return { xData, yData, isHeartbeat: true };
  }

  // 有真实数据时增强显示
  data = enhanceRealData(data);
  const start = startTime.value;

  const xData = data.map((item) => {
    const elapsed = (item.timestamp || 0) - start;
    return Number(elapsed.toFixed(2));
  });

  const yData = data.map((item) => (item.bandwidthMbps || 0).toFixed(2));

  return { xData, yData, isHeartbeat: false };
});

// 图表配置 - 心电图/示波器风格
const chartOptions = computed(() => {
  const { xData, yData, isHeartbeat } = chartData.value;
  if (xData.length === 0) return null;

  // 计算Y轴范围
  const numericYData = yData.map(Number);
  const maxY = Math.max(...numericYData, isHeartbeat ? 5 : 10);
  const yMax = isHeartbeat ? 6 : Math.ceil(maxY / 10) * 10 + 10;

  // 根据是否是心跳模式选择颜色
  const lineColor = isHeartbeat ? '#06b6d4' : '#22c55e'; // 心跳用青色，真实数据用绿色
  const glowColor = isHeartbeat ? 'rgba(6, 182, 212, 0.6)' : 'rgba(34, 197, 94, 0.6)';

  return {
    animation: true,
    animationDuration: isHeartbeat ? 0 : 300,
    animationDurationUpdate: isHeartbeat ? 0 : 300,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut',
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.85)',
      borderColor: lineColor,
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params) => {
        const param = params[0];
        if (isHeartbeat) {
          return `<div class="text-xs">
            <div class="text-cyan-400">系统心跳</div>
            <div class="text-slate-400">等待数据传输...</div>
          </div>`;
        }
        return `<div class="text-xs">
          <div>时间: ${param.name}s</div>
          <div>带宽: <span style="color: ${lineColor}; font-weight: bold;">${param.value}</span> Mbps</div>
        </div>`;
      },
    },
    grid: {
      left: 45,
      right: 15,
      bottom: 30,
      top: 20,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      name: isHeartbeat ? '' : '时间(秒)',
      nameLocation: 'center',
      nameGap: 20,
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      axisLabel: {
        show: !isHeartbeat,
        color: '#64748b',
        fontSize: 10,
        interval: 'auto',
        formatter: (val) => `${val}`,
      },
      axisLine: { lineStyle: { color: '#334155' } },
      axisTick: { show: !isHeartbeat, lineStyle: { color: '#334155' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: isHeartbeat ? '' : 'Mbps',
      nameTextStyle: { color: '#64748b', fontSize: 10 },
      min: 0,
      max: yMax,
      axisLabel: {
        show: !isHeartbeat,
        color: '#64748b',
        fontSize: 10,
        formatter: '{value}',
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { color: '#1e293b', type: 'dashed' },
      },
    },
    series: [
      {
        name: isHeartbeat ? '心跳' : '带宽',
        type: 'line',
        smooth: isHeartbeat ? 0.3 : 0.2, // 轻微平滑
        symbol: 'none', // 不显示数据点，更流畅
        lineStyle: {
          width: isHeartbeat ? 1.5 : 2,
          color: lineColor,
          shadowColor: glowColor,
          shadowBlur: isHeartbeat ? 8 : 10,
          shadowOffsetY: 0,
        },
        itemStyle: {
          color: lineColor,
        },
        areaStyle: {
          opacity: isHeartbeat ? 0.1 : 0.25,
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: lineColor },
              { offset: 1, color: 'transparent' },
            ],
          },
        },
        data: yData,
      },
    ],
  };
});

// 统计信息
const stats = computed(() => {
  const data = displayData.value;
  if (data.length === 0) return null;

  const bandwidths = data.map((item) => item.bandwidthMbps || 0);
  const sum = bandwidths.reduce((acc, val) => acc + val, 0);
  const max = Math.max(...bandwidths);
  const min = Math.min(...bandwidths);
  const msgCount = data.reduce((acc, item) => acc + (item.messageCount || 0), 0);

  return {
    avg: (sum / data.length).toFixed(2),
    peak: max.toFixed(2),
    min: min.toFixed(2),
    msgCount,
  };
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

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 图表容器 */
.chart-container {
  position: relative;
}

/* 网格背景 - 示波器效果 */
.grid-bg {
  position: absolute;
  inset: 8px;
  pointer-events: none;
  opacity: 0.15;
  background-image:
    linear-gradient(to right, #334155 1px, transparent 1px),
    linear-gradient(to bottom, #334155 1px, transparent 1px);
  background-size: 20px 20px;
  border-radius: 6px;
}

/* 扫描线动画 */
.scan-line {
  position: absolute;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(to bottom, transparent, rgba(34, 197, 94, 0.8), transparent);
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.6);
  animation: scan 4s linear infinite;
  pointer-events: none;
  z-index: 5;
}

@keyframes scan {
  0% {
    left: 8px;
    opacity: 0;
  }
  5% {
    opacity: 1;
  }
  95% {
    opacity: 1;
  }
  100% {
    left: calc(100% - 10px);
    opacity: 0;
  }
}

/* 状态指示点 */
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
</style>
