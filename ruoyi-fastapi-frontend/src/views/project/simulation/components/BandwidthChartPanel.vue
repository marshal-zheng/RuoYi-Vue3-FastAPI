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
        <div class="bandwidth-panel__header">
          <span class="bandwidth-panel__title">实时带宽监控</span>
          <transition name="fade">
            <el-tag v-if="selectedPort" type="primary" size="small">
              {{ selectedPort }}
            </el-tag>
          </transition>
        </div>
      </template>

      <div class="bandwidth-panel__content">
        <div class="bandwidth-panel__selector">
          <el-select
            v-model="selectedPort"
            placeholder="选择端口"
            size="small"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="port in portList"
              :key="port"
              :label="port"
              :value="port"
            />
          </el-select>
        </div>

        <div class="bandwidth-panel__chart">
          <ZxChart
            v-if="chartOptions && portList.length > 0"
            ref="chartRef"
            :options="chartOptions"
            height="200px"
            :auto-resize="true"
          />
          <el-empty v-else description="暂无带宽数据" :image-size="60" />
        </div>

        <div v-if="portStats" class="bandwidth-panel__stats">
          <div class="stat-item">
            <span class="stat-label">平均</span>
            <span class="stat-value">{{ portStats.averageBandwidth }} Mbps</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">峰值</span>
            <span class="stat-value">{{ portStats.peakBandwidth }} Mbps</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">报文</span>
            <span class="stat-value">{{ portStats.messageCount }}</span>
          </div>
        </div>
      </div>
    </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  bandwidthData: {
    type: Array,
    default: () => []
  },
  visible: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({ top: '100px', right: '30px' })
  },
  size: {
    type: Object,
    default: () => ({ width: '400px', maxHeight: '450px' })
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' })
  },
  defaultCollapsed: {
    type: Boolean,
    default: false
  }
})

const chartRef = ref(null)
const selectedPort = ref(null)

// 从数据中提取端口列表
const portList = computed(() => {
  const ports = new Set()
  props.bandwidthData.forEach(item => {
    if (item.portId) {
      ports.add(item.portId)
    }
  })
  return Array.from(ports)
})

// 自动选择第一个端口
watch(portList, (newList) => {
  if (newList.length > 0 && !selectedPort.value) {
    selectedPort.value = newList[0]
  }
}, { immediate: true })

// 获取选中端口的数据
const selectedPortData = computed(() => {
  if (!selectedPort.value) return []
  return props.bandwidthData
    .filter(item => item.portId === selectedPort.value)
    .sort((a, b) => a.timestamp - b.timestamp)
})

// 格式化图表数据
const chartData = computed(() => {
  const data = selectedPortData.value
  // 只显示最近30个数据点，避免图表过于密集
  const recentData = data.slice(-30)
  
  const xData = recentData.map(item => {
    const date = new Date(item.timestamp * 1000)
    const min = String(date.getMinutes()).padStart(2, '0')
    const sec = String(date.getSeconds()).padStart(2, '0')
    return `${min}:${sec}`
  })
  
  const yData = recentData.map(item => item.bandwidthMbps || 0)
  
  return { xData, yData }
})

// 图表配置 - 示波器风格
const chartOptions = computed(() => {
  if (!selectedPort.value) return null
  
  const { xData, yData } = chartData.value
  if (xData.length === 0) return null

  return {
    animation: true,
    animationDuration: 300,
    animationDurationUpdate: 300,
    animationEasing: 'linear',
    animationEasingUpdate: 'linear',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const param = params[0]
        return `${param.name}<br/>带宽: ${param.value} Mbps`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLabel: {
        fontSize: 10,
        interval: 'auto'
      },
      axisLine: {
        lineStyle: { color: '#e0e0e0' }
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'Mbps',
      nameTextStyle: { fontSize: 10, color: '#909399' },
      axisLabel: { formatter: '{value}', fontSize: 10 },
      axisLine: { show: false },
      splitLine: {
        lineStyle: { color: '#f0f0f0', type: 'dashed' }
      }
    },
    series: [{
      name: '带宽',
      type: 'line',
      smooth: 0.3,
      symbol: 'none',
      lineStyle: { width: 2, color: '#409eff' },
      areaStyle: {
        opacity: 0.15,
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#409eff' },
            { offset: 1, color: 'rgba(64, 158, 255, 0)' }
          ]
        }
      },
      data: yData
    }]
  }
})

// 端口统计
const portStats = computed(() => {
  const data = selectedPortData.value
  if (data.length === 0) return null

  const bandwidths = data.map(item => item.bandwidthMbps || 0)
  const sum = bandwidths.reduce((acc, val) => acc + val, 0)
  const max = Math.max(...bandwidths)
  const messageCount = data.reduce((acc, item) => acc + (item.messageCount || 0), 0)

  return {
    averageBandwidth: (sum / data.length).toFixed(2),
    peakBandwidth: max.toFixed(2),
    messageCount
  }
})
</script>

<style lang="less" scoped>
.bandwidth-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bandwidth-panel__title {
  font-weight: 600;
  font-size: 14px;
}

.bandwidth-panel__content {
  padding: 12px 0;
}

.bandwidth-panel__selector {
  margin-bottom: 12px;
}

.bandwidth-panel__chart {
  margin-bottom: 12px;
  min-height: 200px;
}

.bandwidth-panel__stats {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
}

.stat-label {
  font-size: 11px;
  color: #909399;
}

.stat-value {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
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
</style>
