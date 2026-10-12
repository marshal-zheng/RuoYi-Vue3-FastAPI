<template>
  <div class="pro-card-body">
    <!-- 仪表盘视图 -->
    <div v-if="!showTrend" class="flex flex-wrap gap-4">
      <div
        v-for="item in groupedBandwidth"
        :key="item.protocol"
        class="flex-1 min-w-24 max-w-36 text-center cursor-pointer transition-all duration-300 hover:scale-105 p-3 rounded-lg border border-transparent hover:border-zx-border-default/50 hover:bg-zx-surface-card-fill/30"
        @click="$emit('port-click', item)"
      >
        <!-- 仪表环 -->
        <div class="relative w-20 h-20 mx-auto">
          <svg viewBox="0 0 100 100" class="-rotate-90">
            <circle cx="50" cy="50" r="45" fill="none" stroke-width="6" class="stroke-zx-border-default" />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke-width="6"
              :stroke-dasharray="getStrokeDasharray(item.loadPercent)"
              :class="getStrokeClass(item.loadPercent)"
              class="transition-all duration-500 drop-shadow-[0_0_4px_currentColor]"
              stroke-linecap="round"
            />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-lg font-bold text-zx-text-primary tabular-nums"
              >{{ Math.round(item.loadPercent) }}%</span
            >
            <span class="text-[10px] text-zx-text-secondary uppercase tracking-wider font-medium mt-0.5">{{
              item.protocol
            }}</span>
          </div>
        </div>
        <!-- 信息 -->
        <div class="mt-3 space-y-1">
          <div class="text-xs font-medium text-zx-text-secondary">
            {{ formatBandwidth(item.bandwidthMbps) }}
          </div>
          <div class="text-[10px] text-zx-text-secondary">{{ item.messageCount }} 报文</div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="groupedBandwidth.length === 0" class="w-full text-center py-10 text-zx-text-secondary">
        <el-icon class="text-4xl mb-3 text-zx-text-disabled"><DataLine /></el-icon>
        <div class="text-sm font-medium">暂无带宽数据</div>
        <div class="text-xs text-zx-text-disabled mt-1">等待仿真开始</div>
      </div>
    </div>

    <!-- 趋势图视图 -->
    <div v-else class="w-full h-48 relative">
      <div
        v-if="bandwidthData.length === 0"
        class="absolute inset-0 flex flex-col items-center justify-center text-zx-text-secondary"
      >
        <el-icon class="text-4xl mb-3 text-zx-text-disabled"><DataLine /></el-icon>
        <div class="text-sm font-medium">暂无带宽数据</div>
        <div class="text-xs text-zx-text-disabled mt-1">等待仿真开始</div>
      </div>
      <div ref="chartRef" class="w-full h-full"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { DataLine } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { useChartTheme } from '@/theme/useChartTheme';

const { theme: chartTheme } = useChartTheme();

const props = defineProps({
  bandwidthData: {
    type: Array,
    default: () => [],
  },
  isRunning: {
    type: Boolean,
    default: false,
  },
  showTrend: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['port-click', 'update:showTrend']);

const showTrend = computed({
  get: () => props.showTrend,
  set: (val) => emit('update:showTrend', val),
});
const chartRef = ref(null);
let chartInstance = null;
let resizeObserver = null;

const groupedBandwidth = computed(() => {
  const grouped = {};

  props.bandwidthData.forEach((item) => {
    const protocol = item.protocolType || 'unknown';
    const load = Number((item.loadPercent || 0).toFixed(2));
    const bw = Number((item.bandwidthMbps || 0).toFixed(3));
    if (!grouped[protocol]) {
      grouped[protocol] = {
        protocol,
        bandwidthMbps: 0,
        loadPercent: 0,
        messageCount: 0,
        ports: [],
      };
    }
    grouped[protocol].bandwidthMbps += bw;
    grouped[protocol].loadPercent = Math.max(grouped[protocol].loadPercent, load);
    grouped[protocol].messageCount += item.messageCount || 0;
    grouped[protocol].ports.push(item);
  });

  return Object.values(grouped);
});

function getStrokeClass(loadPercent) {
  if (loadPercent > 95) return 'stroke-red-500';
  if (loadPercent > 80) return 'stroke-amber-500';
  return 'stroke-emerald-500';
}

function getStrokeDasharray(percent) {
  const circumference = 2 * Math.PI * 45;
  const progress = (percent / 100) * circumference;
  return `${progress} ${circumference}`;
}

function formatBandwidth(mbps) {
  const safe = Number(mbps || 0);
  if (safe >= 1000) {
    return `${(safe / 1000).toFixed(2)} Gbps`;
  }
  return `${safe.toFixed(2)} Mbps`;
}

function initChart() {
  if (!chartRef.value || !chartTheme.value) return;
  chartInstance?.dispose();
  chartInstance = echarts.init(chartRef.value, chartTheme.value);

  const option = {
    backgroundColor: 'transparent',
    grid: {
      top: 30,
      right: 5,
      bottom: 20,
      left: 30,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: chartTheme.value.backgroundColor,
      borderColor: chartTheme.value.tooltip.borderColor,
      borderWidth: 1,
      textStyle: { color: chartTheme.value.textStyle.color, fontSize: 12 },
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: chartTheme.value.backgroundColor,
        },
      },
      formatter: (params) => {
        let result = `<div style="margin-bottom: 4px; font-weight: 600;">${params[0].axisValue}</div>`;
        params.forEach((param) => {
          const val = Number(param.value?.[1] ?? 0).toFixed(2);
          result += `<div style="margin: 2px 0;">
            <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 6px;"></span>
            ${param.seriesName}: <span style="font-weight: 600; color: ${param.color};">${val}%</span>
          </div>`;
        });
        return result;
      },
    },
    legend: {
      data: [],
      top: 0,
      textStyle: { color: chartTheme.value.legend.inactiveColor, fontSize: 11 },
      itemWidth: 12,
      itemHeight: 8,
      itemGap: 15,
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLine: {
        lineStyle: { color: chartTheme.value.valueAxis.axisLine.lineStyle.color, width: 1 },
      },
      axisLabel: {
        color: chartTheme.value.legend.inactiveColor,
        fontSize: 10,
        rotate: 0,
        formatter: (value) => {
          const date = new Date(value);
          const hours = date.getHours().toString().padStart(2, '0');
          const minutes = date.getMinutes().toString().padStart(2, '0');
          const seconds = date.getSeconds().toString().padStart(2, '0');
          return `${hours}:${minutes}:${seconds}`;
        },
      },
      splitLine: {
        show: true,
        lineStyle: { color: chartTheme.value.valueAxis.splitLine.lineStyle.color, type: 'dashed' },
      },
      axisPointer: {
        label: {
          formatter: (params) => {
            const date = new Date(params.value);
            return `${date.toLocaleTimeString('zh-CN', { hour12: false })}`;
          },
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '负载率 (%)',
      nameTextStyle: { color: chartTheme.value.legend.inactiveColor, fontSize: 11 },
      min: 0,
      max: 100,
      axisLine: {
        lineStyle: { color: chartTheme.value.valueAxis.axisLine.lineStyle.color, width: 1 },
      },
      axisLabel: {
        color: chartTheme.value.legend.inactiveColor,
        fontSize: 10,
        formatter: '{value}%',
      },
      splitLine: {
        show: true,
        lineStyle: { color: chartTheme.value.valueAxis.splitLine.lineStyle.color, type: 'dashed' },
      },
    },
    series: [],
  };

  chartInstance.setOption(option);
}

function updateChart() {
  if (!chartInstance || !chartTheme.value) return;

  if (!props.bandwidthData || props.bandwidthData.length === 0) {
    chartInstance.setOption({
      series: [],
      legend: { data: [] },
    });
    return;
  }

  // 按协议类型分组数据
  const seriesData = {};
  const protocolColors = {
    '1553B': '#3b82f6', // 蓝色
    CAN: '#10b981', // 绿色
    RS422: '#f59e0b', // 橙色
    LAN: '#8b5cf6', // 紫色
    unknown: '#64748b', // 灰色
  };

  // 渐变色配置
  const gradientColors = {
    '1553B': ['rgba(59, 130, 246, 0.4)', 'rgba(59, 130, 246, 0.05)'],
    CAN: ['rgba(16, 185, 129, 0.4)', 'rgba(16, 185, 129, 0.05)'],
    RS422: ['rgba(245, 158, 11, 0.4)', 'rgba(245, 158, 11, 0.05)'],
    LAN: ['rgba(139, 92, 246, 0.4)', 'rgba(139, 92, 246, 0.05)'],
    unknown: ['rgba(100, 116, 139, 0.4)', 'rgba(100, 116, 139, 0.05)'],
  };

  // 处理数据：按时间戳排序，按协议分组
  const sortedData = [...props.bandwidthData].sort((a, b) => {
    const timeA = (a.timestamp || 0) * 1000;
    const timeB = (b.timestamp || 0) * 1000;
    return timeA - timeB;
  });

  sortedData.forEach((item) => {
    const protocol = item.protocolType || 'unknown';
    if (!seriesData[protocol]) {
      seriesData[protocol] = [];
    }
    const timestamp = (item.timestamp || 0) * 1000;
    const loadPercent = Number((item.loadPercent || 0).toFixed(2));
    seriesData[protocol].push([timestamp, loadPercent]);
  });

  // 生成系列配置
  const series = Object.entries(seriesData)
    .filter(([_, data]) => data.length > 0)
    .map(([name, data], index) => {
      const color = protocolColors[name] || `hsl(${(index * 60) % 360}, 70%, 60%)`;
      const gradients = gradientColors[name] || [`${color}40`, `${color}05`];

      return {
        name,
        type: 'line',
        smooth: 0.4,
        symbol: 'circle',
        symbolSize: data.length < 30 ? 5 : 0, // 数据点少时显示符号
        showSymbol: false,
        data,
        lineStyle: {
          width: 2.5,
          color,
          shadowBlur: 4,
          shadowColor: color,
          shadowOffsetY: 2,
        },
        itemStyle: {
          color,
          borderColor: chartTheme.value.backgroundColor,
          borderWidth: 1,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: gradients[0] },
              { offset: 1, color: gradients[1] },
            ],
          },
        },
        emphasis: {
          focus: 'series',
          lineStyle: {
            width: 3.5,
          },
          itemStyle: {
            symbolSize: 7,
            borderWidth: 2,
          },
        },
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut',
      };
    });

  // 更新图表
  chartInstance.setOption(
    {
      legend: {
        data: Object.keys(seriesData).filter((key) => seriesData[key].length > 0),
        selected: Object.keys(seriesData).reduce((acc, key) => {
          acc[key] = true;
          return acc;
        }, {}),
      },
      series,
    },
    { notMerge: false }
  );

  // 自适应调整Y轴范围
  if (series.length > 0) {
    const allValues = series.flatMap((s) => s.data.map((d) => d[1]));
    const maxValue = Math.max(...allValues, 0);
    const minValue = Math.min(...allValues, 0);

    chartInstance.setOption({
      yAxis: {
        min: Math.max(0, Math.floor(minValue / 10) * 10 - 5),
        max: Math.min(100, Math.ceil(maxValue / 10) * 10 + 5),
      },
    });
  }
}

// Apply only presentation, preserving the current series data and legend selection.
watch(chartTheme, (theme) => {
  if (!theme || !showTrend.value) return;
  if (!chartInstance) {
    nextTick(() => { initChart(); updateChart(); });
    return;
  }
  chartInstance.setOption({
    textStyle: theme.textStyle,
    tooltip: { ...theme.tooltip, axisPointer: { label: { backgroundColor: theme.backgroundColor } } },
    legend: { textStyle: theme.legend.textStyle, inactiveColor: theme.legend.inactiveColor },
    xAxis: theme.valueAxis,
    yAxis: { ...theme.valueAxis, nameTextStyle: theme.legend.textStyle },
    series: (chartInstance.getOption().series || []).map(() => ({
      itemStyle: { borderColor: theme.backgroundColor },
    })),
  });
}, { flush: 'post' });

watch(() => props.bandwidthData, updateChart, { deep: true, immediate: true });

watch(showTrend, (show) => {
  if (show) {
    nextTick(() => {
      setTimeout(() => {
        initChart();
        updateChart();
      }, 100);
    });
  } else {
    if (chartInstance) {
      chartInstance.dispose();
      chartInstance = null;
    }
  }
});

onMounted(() => {
  if (showTrend.value) {
    nextTick(() => {
      setTimeout(() => {
        initChart();
        updateChart();
      }, 100);
    });
  }

  // 监听容器大小变化
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (chartInstance) {
        chartInstance.resize();
      }
    });
    resizeObserver.observe(chartRef.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
/* 自定义 Switch 样式 */
:deep(.custom-switch .el-switch__label) {
  color: var(--zx-semantic-text-secondary) !important;
  font-size: 11px;
}

:deep(.custom-switch .el-switch__label.is-active) {
  color: var(--zx-semantic-text-secondary) !important;
}
</style>
