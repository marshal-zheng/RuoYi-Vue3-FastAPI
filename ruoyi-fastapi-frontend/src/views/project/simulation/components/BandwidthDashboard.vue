<template>
  <div class="pro-card-body">
    <!-- 头部 -->
    <div class="flex justify-between items-center mb-4 pb-3 border-b border-slate-700/30">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 bg-primary-500 rounded-full"></div>
        <span class="text-sm font-semibold text-slate-200 tracking-wide">带宽监控</span>
      </div>
      <el-switch 
        v-model="showTrend" 
        active-text="趋势" 
        inactive-text="仪表" 
        size="small"
        class="custom-switch"
      />
    </div>

    <!-- 仪表盘视图 -->
    <div v-if="!showTrend" class="flex flex-wrap gap-4">
      <div
        v-for="item in groupedBandwidth"
        :key="item.protocol"
        class="flex-1 min-w-24 max-w-36 text-center cursor-pointer transition-all duration-300 hover:scale-105 p-3 rounded-lg border border-transparent hover:border-slate-700/50 hover:bg-slate-800/30"
        @click="$emit('port-click', item)"
      >
        <!-- 仪表环 -->
        <div class="relative w-20 h-20 mx-auto">
          <svg viewBox="0 0 100 100" class="-rotate-90">
            <circle cx="50" cy="50" r="45" fill="none" stroke-width="6" class="stroke-slate-800" />
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
            <span class="text-lg font-bold text-slate-100 tabular-nums">{{ Math.round(item.loadPercent) }}%</span>
            <span class="text-[10px] text-slate-500 uppercase tracking-wider font-medium mt-0.5">{{ item.protocol }}</span>
          </div>
        </div>
        <!-- 信息 -->
        <div class="mt-3 space-y-1">
          <div class="text-xs font-medium text-slate-300">{{ formatBandwidth(item.bandwidthMbps) }}</div>
          <div class="text-[10px] text-slate-500">{{ item.messageCount }} 报文</div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="groupedBandwidth.length === 0" class="w-full text-center py-10 text-slate-500">
        <el-icon class="text-4xl mb-3 text-slate-600"><DataLine /></el-icon>
        <div class="text-sm font-medium">暂无带宽数据</div>
        <div class="text-xs text-slate-600 mt-1">等待仿真开始</div>
      </div>
    </div>

    <!-- 趋势图视图 -->
    <div v-else ref="chartRef" class="w-full h-48"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { DataLine } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps({
  bandwidthData: {
    type: Array,
    default: () => [],
  },
  isRunning: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['port-click'])

const showTrend = ref(false)
const chartRef = ref(null)
let chartInstance = null

const groupedBandwidth = computed(() => {
  const grouped = {}

  props.bandwidthData.forEach((item) => {
    const protocol = item.protocolType || 'unknown'
    if (!grouped[protocol]) {
      grouped[protocol] = {
        protocol,
        bandwidthMbps: 0,
        loadPercent: 0,
        messageCount: 0,
        ports: [],
      }
    }
    grouped[protocol].bandwidthMbps += item.bandwidthMbps || 0
    grouped[protocol].loadPercent = Math.max(grouped[protocol].loadPercent, item.loadPercent || 0)
    grouped[protocol].messageCount += item.messageCount || 0
    grouped[protocol].ports.push(item)
  })

  return Object.values(grouped)
})

function getStrokeClass(loadPercent) {
  if (loadPercent > 95) return 'stroke-red-500'
  if (loadPercent > 80) return 'stroke-amber-500'
  return 'stroke-emerald-500'
}

function getStrokeDasharray(percent) {
  const circumference = 2 * Math.PI * 45
  const progress = (percent / 100) * circumference
  return `${progress} ${circumference}`
}

function formatBandwidth(mbps) {
  if (mbps >= 1000) {
    return `${(mbps / 1000).toFixed(2)} Gbps`
  }
  return `${mbps.toFixed(2)} Mbps`
}

function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option = {
    backgroundColor: 'transparent',
    grid: {
      top: 30,
      right: 20,
      bottom: 30,
      left: 50,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(51, 65, 85, 0.5)',
      textStyle: { color: '#e2e8f0' },
    },
    legend: {
      data: [],
      textStyle: { color: '#94a3b8' },
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      name: '负载率(%)',
      nameTextStyle: { color: '#94a3b8' },
      max: 100,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
    },
    series: [],
  }

  chartInstance.setOption(option)
}

function updateChart() {
  if (!chartInstance) return

  const seriesData = {}

  props.bandwidthData.forEach((item) => {
    const protocol = item.protocolType || 'unknown'
    if (!seriesData[protocol]) {
      seriesData[protocol] = []
    }
    seriesData[protocol].push([item.timestamp * 1000, item.loadPercent || 0])
  })

  const series = Object.entries(seriesData).map(([name, data]) => ({
    name,
    type: 'line',
    smooth: true,
    data,
    areaStyle: { opacity: 0.1 },
  }))

  chartInstance.setOption({
    legend: { data: Object.keys(seriesData) },
    series,
  })
}

watch(() => props.bandwidthData, updateChart, { deep: true })

watch(showTrend, (show) => {
  if (show) {
    setTimeout(initChart, 100)
  }
})

onMounted(() => {
  if (showTrend.value) {
    initChart()
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
/* 自定义 Switch 样式 */
:deep(.custom-switch .el-switch__label) {
  color: #94a3b8 !important;
  font-size: 11px;
}

:deep(.custom-switch .el-switch__label.is-active) {
  color: #cbd5e1 !important;
}
</style>
