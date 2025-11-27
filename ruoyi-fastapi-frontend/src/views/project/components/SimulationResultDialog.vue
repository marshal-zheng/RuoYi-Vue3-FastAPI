<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <template #header>
      <div class="simulation-dialog__header">
        <span>多总线仿真结果</span>
        <el-tag type="success" size="small">示意仿真</el-tag>
      </div>
    </template>

    <template #footer>
      <div class="simulation-dialog__footer">
        <el-button type="primary" @click="dialog.close()">关闭</el-button>
      </div>
    </template>

    <div v-if="simulationResult" class="simulation-summary">
      <el-descriptions :column="2" size="small" border>
        <el-descriptions-item label="设备数量">
          {{ simulationResult.summary.deviceCount }}
        </el-descriptions-item>
        <el-descriptions-item label="连线数量">
          {{ simulationResult.summary.connectionCount }}
        </el-descriptions-item>
        <el-descriptions-item label="覆盖总线">
          <el-space wrap>
            <el-tag
              v-for="bus in simulationResult.summary.busCoverage"
              :key="bus.name"
              size="small"
              :type="bus.active ? 'success' : 'info'"
              :effect="bus.active ? 'dark' : 'plain'"
            >
              {{ bus.name }}<span v-if="!bus.active">（未使用）</span>
            </el-tag>
          </el-space>
        </el-descriptions-item>
        <el-descriptions-item label="仿真时间">
          {{ simulationResult.summary.generatedAt }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-tabs v-model="simulationTab" class="simulation-tabs">
      <el-tab-pane label="仿真过程" name="timeline">
        <el-empty v-if="!simulationResult?.timeline?.length" description="暂无仿真数据" />
        <el-timeline class="p-4" v-else>
          <el-timeline-item
            v-for="item in simulationResult.timeline"
            :key="item.id"
            :timestamp="item.timestamp"
            :type="item.busTypeTag"
          >
            <p class="simulation-timeline__title">{{ item.title }}</p>
            <p class="simulation-timeline__desc">{{ item.description }}</p>
          </el-timeline-item>
        </el-timeline>
      </el-tab-pane>

      <!-- 数据图表 Tab -->
      <el-tab-pane label="数据图表" name="charts">
        <div class="charts-container">
          <!-- 带宽趋势图 -->
          <div class="chart-section">
            <div class="chart-title">带宽趋势</div>
            <div ref="bandwidthChartRef" class="chart-box"></div>
          </div>
          <!-- 协议分布图 -->
          <div class="chart-section">
            <div class="chart-title">协议分布</div>
            <div ref="protocolChartRef" class="chart-box"></div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="总线通信设计文件" name="design">
        <div class="simulation-file__header">
          <el-button
            type="primary"
            link
            @click="
              downloadSimulationFile(
                simulationResult.designFile.name,
                simulationResult.designFile.content
              )
            "
          >
            下载设计文件
          </el-button>
        </div>
        <pre class="simulation-file__viewer">{{ simulationResult.designFile.content }}</pre>
      </el-tab-pane>
      <el-tab-pane label="接口控制文件" name="icd">
        <div class="simulation-file__header">
          <el-button
            type="primary"
            link
            @click="
              downloadSimulationFile(
                simulationResult.icdFile.name,
                simulationResult.icdFile.content
              )
            "
          >
            下载接口控制文件
          </el-button>
        </div>
        <pre class="simulation-file__viewer">{{ simulationResult.icdFile.content }}</pre>
      </el-tab-pane>
    </el-tabs>
  </ZxDialog>
</template>

<script setup name="SimulationResultDialog">
import { ref, watch, nextTick, onUnmounted } from 'vue';
import { useDialog } from '@zxio/zxui';
import * as echarts from 'echarts';

defineEmits(['reopen']);

const simulationResult = ref(null);
const simulationTab = ref('timeline');

// 图表 DOM 引用
const bandwidthChartRef = ref(null);
const protocolChartRef = ref(null);

// echarts 实例
let bandwidthChart = null;
let protocolChart = null;

const dialog = useDialog({
  title: '多总线仿真结果',
  width: '75%',
  height: '80%',
  showCancel: false,
  okText: '关闭',
  footer: false,
});

// 监听 tab 切换，当切换到图表 tab 时初始化图表
watch(simulationTab, (newTab) => {
  if (newTab === 'charts') {
    nextTick(() => {
      initCharts();
    });
  }
});

// 初始化图表
function initCharts() {
  initBandwidthChart();
  initProtocolChart();
}

// 带宽趋势图
function initBandwidthChart() {
  if (!bandwidthChartRef.value) return;

  if (bandwidthChart) {
    bandwidthChart.dispose();
  }

  bandwidthChart = echarts.init(bandwidthChartRef.value);

  // 使用真实的带宽数据
  const rawBandwidthData = simulationResult.value?.bandwidthData || [];
  const timeData = [];
  const bandwidthValues = [];

  // 获取基准时间戳（第一个数据点的时间）
  const baseTimestamp = rawBandwidthData.length > 0 ? rawBandwidthData[0].timestamp || 0 : 0;

  // 计算最大带宽值，决定使用 Kbps 还是 Mbps
  // 注意：数据字段名是 bandwidthMbps
  let maxBandwidth = 0;
  rawBandwidthData.forEach((item) => {
    const bw = item.bandwidthMbps || item.bandwidth || 0;
    if (bw > maxBandwidth) maxBandwidth = bw;
  });

  // 如果最大值小于 1 Mbps，使用 Kbps 作为单位
  const useKbps = maxBandwidth < 1;
  const unit = useKbps ? 'Kbps' : 'Mbps';
  const multiplier = useKbps ? 1000 : 1;

  if (rawBandwidthData.length > 0) {
    rawBandwidthData.forEach((item) => {
      // X轴使用相对时间（从0开始）
      const relativeTime = (item.timestamp || 0) - baseTimestamp;
      timeData.push(`${relativeTime.toFixed(1)}s`);
      // 带宽值根据单位转换，保持两位小数（字段名是 bandwidthMbps）
      const rawValue = item.bandwidthMbps || item.bandwidth || 0;
      const value = rawValue * multiplier;
      bandwidthValues.push(parseFloat(value.toFixed(2)));
    });
  } else {
    // 没有数据时显示空状态
    for (let i = 0; i < 10; i++) {
      timeData.push(`${i}s`);
      bandwidthValues.push(0);
    }
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: (params) => {
        const data = params[0];
        return `${data.axisValue}<br/><span style="color:#3b82f6">●</span> 带宽: ${data.value.toFixed(2)} ${unit}`;
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timeData,
      axisLine: { lineStyle: { color: '#64748b' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      name: unit,
      nameTextStyle: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#64748b' } },
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => value.toFixed(2),
      },
      splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
    },
    series: [
      {
        name: '带宽',
        type: 'line',
        smooth: true,
        symbol: 'none',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
          ]),
        },
        lineStyle: { color: '#3b82f6', width: 2 },
        data: bandwidthValues,
      },
    ],
  };

  bandwidthChart.setOption(option);
}

// 协议分布饼图
function initProtocolChart() {
  if (!protocolChartRef.value) return;

  if (protocolChart) {
    protocolChart.dispose();
  }

  protocolChart = echarts.init(protocolChartRef.value);

  // 从真实报文数据统计协议分布
  const messageData = simulationResult.value?.messageData || [];
  const protocolCount = {};

  messageData.forEach((msg) => {
    const protocol = msg.protocolType || '未知';
    protocolCount[protocol] = (protocolCount[protocol] || 0) + 1;
  });

  // 转换为图表数据格式
  let chartData = Object.entries(protocolCount).map(([name, value]) => ({
    name,
    value,
  }));

  // 如果没有报文数据，使用 summary 中的总线覆盖信息
  if (chartData.length === 0) {
    const busCoverage = simulationResult.value?.summary?.busCoverage || [];
    chartData = busCoverage
      .filter((bus) => bus.active)
      .map((bus) => ({
        name: bus.name,
        value: bus.count || 1,
      }));
  }

  // 如果仍然没有数据，显示空状态
  if (chartData.length === 0) {
    chartData = [{ name: '暂无数据', value: 1 }];
  }

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: '{b}: {c} 条报文 ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#64748b' },
    },
    series: [
      {
        name: '协议分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        labelLine: { show: false },
        data: chartData,
      },
    ],
    color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
  };

  protocolChart.setOption(option);
}

function open(payload) {
  simulationResult.value = payload || null;
  simulationTab.value = 'timeline';
  dialog.open();
}

function close() {
  dialog.close();
}

function downloadSimulationFile(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || 'simulation.txt';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// 清理 echarts 实例
onUnmounted(() => {
  if (bandwidthChart) {
    bandwidthChart.dispose();
    bandwidthChart = null;
  }
  if (protocolChart) {
    protocolChart.dispose();
    protocolChart = null;
  }
});

defineExpose({
  open,
  close,
});
</script>

<style scoped lang="less">
.simulation-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.simulation-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.simulation-summary {
  margin-bottom: 16px;
}

.simulation-tabs {
  .el-tab-pane {
    min-height: 240px;
  }
}

.simulation-file__header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.simulation-file__viewer {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  max-height: 280px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.simulation-timeline__title {
  font-weight: 600;
  margin-bottom: 4px;
}

.simulation-timeline__desc {
  color: #606266;
  margin: 0;
  font-size: 12px;
}

/* 图表容器样式 */
.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 16px;
}

.chart-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #3b82f6;
}

.chart-box {
  height: 260px;
  background: #fff;
  border-radius: 8px;
}
</style>
