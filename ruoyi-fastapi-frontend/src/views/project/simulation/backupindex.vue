<template>
  <div class="simulation-dark simulation-shell flex flex-col h-full bg-slate-950">
    <!-- 顶部控制栏 -->
    <header class="shrink-0 z-50">
      <SimulationHeader
        :status="simulationState.status"
        :elapsed-time="simulationState.elapsedTime"
        :speed="simulationState.speed"
        :project-name="projectName"
        @start="handleStart"
        @pause="handlePause"
        @resume="handleResume"
        @stop="handleStop"
        @step="handleStep"
        @speed-change="handleSpeedChange"
        @back="handleBack"
      />
    </header>

    <!-- 主内容区域 -->
    <main class="flex flex-1 min-h-0 p-3 relative">
      <!-- 拓扑画布 -->
      <section class="sim-canvas pro-card flex-1 relative">
        <XflowDAG
          ref="dagRef"
          :showToolbar="false"
          :showSidebar="false"
          :operators="operators"
          :operators-loading="loading"
          :layout="layoutMode"
          :dnd-config="dndConfig"
          :show-graph-control="false"
          @node-click="handleNodeClick"
          @node-dblclick="handleNodeDblclick"
          @edge-click="handleEdgeClick"
          @edge-mouseenter="handleEdgeMouseEnter"
          @edge-mouseleave="handleEdgeMouseLeave"
        />

        <!-- 链路悬停信息提示 -->
        <EdgeTooltip
          v-if="hoveredEdge"
          :edge="hoveredEdge"
          :position="tooltipPosition"
          :bandwidth-data="getEdgeBandwidth(hoveredEdge)"
        />
      </section>

      <!-- 浮动监控/告警面板，不占用主布局 -->
      <zx-floating-panel
        :showCollapseBtn="false"
        :position="{ top: '90px', right: '28px' }"
        :size="{ width: '520px', maxHeight: '430px' }"
        :collapsed-size="{ width: '46px', height: '46px' }"
        :default-collapsed="false"
        class="floating-panel shadow-lg"
        theme="dark"
      >
        <template #header>
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-text">带宽监控</span>
              <span class="live-badge" v-if="isRunning">
                <span class="live-dot"></span>
                LIVE
              </span>
            </div>
            <div class="panel-actions">
              <div class="view-toggle">
                <span
                  class="toggle-item"
                  :class="{ active: !dashboardShowTrend }"
                  @click="dashboardShowTrend = false"
                  >仪表</span
                >
                <span class="toggle-divider">|</span>
                <span
                  class="toggle-item"
                  :class="{ active: dashboardShowTrend }"
                  @click="dashboardShowTrend = true"
                  >趋势</span
                >
              </div>
            </div>
          </div>
        </template>

        <BandwidthDashboard
          v-model:showTrend="dashboardShowTrend"
          :bandwidth-data="bandwidthData"
          :is-running="isRunning"
          @port-click="handlePortClick"
        />
      </zx-floating-panel>

      <zx-floating-panel
        :showCollapseBtn="false"
        title="告警信息"
        :position="{ top: '550px', right: '28px' }"
        :size="{ width: '320px', maxHeight: '420px' }"
        :collapsed-size="{ width: '46px', height: '46px' }"
        :default-collapsed="false"
        class="floating-panel shadow-lg"
        theme="dark"
      >
        <AlarmPanel
          :alarms="alarmData"
          @alarm-click="handleAlarmClick"
          @filter-change="handleAlarmFilterChange"
        />
      </zx-floating-panel>

      <zx-floating-panel
        v-if="selectedNode"
        title="设备详情"
        :position="{ bottom: '96px', right: '28px' }"
        :size="{ width: '340px', maxHeight: '460px' }"
        :collapsed-size="{ width: '46px', height: '46px' }"
        :default-collapsed="false"
        class="floating-panel shadow-lg"
        theme="dark"
      >
        <DeviceDetailPanel :node="selectedNode" @close="selectedNode = null" />
      </zx-floating-panel>
    </main>

    <!-- 底部：协议分析器 -->
    <footer class="shrink-0 h-64 mx-3 mb-3 pro-card">
      <ProtocolAnalyzer
        ref="protocolAnalyzerRef"
        :messages="filteredMessages"
        :is-running="isRunning"
        :auto-scroll="autoScroll"
        @message-select="handleMessageSelect"
        @filter-change="handleMessageFilterChange"
        @export="handleExportMessages"
        @auto-scroll-change="autoScroll = $event"
      />
    </footer>

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />

    <!-- 故障注入右键菜单 -->
    <FaultInjectorMenu ref="faultMenuRef" @inject="handleFaultInject" @clear="handleFaultClear" />

    <!-- 事件触发面板 -->
    <EventTriggerPanel
      v-model:visible="showEventPanel"
      :events="eventList"
      @create="handleEventCreate"
      @edit="handleEventEdit"
      @delete="handleEventDelete"
      @trigger="handleEventTrigger"
    />

    <!-- 仿真报告对话框 -->
    <SimulationReportDialog
      ref="reportDialogRef"
      :session-id="sessionId"
      :summary="simulationSummary"
    />

    <!-- 健康自检对话框 -->
    <HealthCheckDialog ref="healthCheckDialogRef" @recheck="handleHealthCheck" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

// 组件导入
import XflowDAG from '@/components/business/Dag/index.vue';
import SimulationHeader from './components/SimulationHeader.vue';
import BandwidthDashboard from './components/BandwidthDashboard.vue';
import AlarmPanel from './components/AlarmPanel.vue';
import ProtocolAnalyzer from './components/ProtocolAnalyzer.vue';
import DeviceDetailPanel from './components/DeviceDetailPanel.vue';
import EdgeTooltip from './components/EdgeTooltip.vue';
import FaultInjectorMenu from './components/FaultInjectorMenu.vue';
import EventTriggerPanel from './components/EventTriggerPanel.vue';
import SimulationReportDialog from './components/SimulationReportDialog.vue';
import HealthCheckDialog from './components/HealthCheckDialog.vue';
import { NodeEditDrawer } from '../components';

// Composables 导入
import { useSimulationControl } from './composables/useSimulationControl';
import { useSimulationData } from './composables/useSimulationData';

// 样式导入
import './styles/simulation-theme.css';
import { useTopologyAnimation } from './composables/useTopologyAnimation';
import { useFaultInjection } from './composables/useFaultInjection';
import { useEventTrigger } from './composables/useEventTrigger';

// API 导入
import { listDevice } from '@/api/device/device';
import { getProject } from '@/api/project/project';
import { getProjectTopology } from '@/api/project/topology';

defineOptions({ name: 'SimulationConsole' });

// 路由
const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.projectId));
const versionId = computed(() =>
  route.query.versionId ? Number(route.query.versionId) : undefined
);

// 项目信息
const projectName = ref('');

// DAG 组件
const dagRef = ref(null);
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal');
const dndConfig = {
  title: '设备库',
  searchPlaceholder: '搜索设备...',
  textConfig: {
    loadingText: '正在加载设备库...',
    emptySearchText: '没有找到匹配的设备',
    emptySearchDesc: '请尝试使用其他关键词搜索',
    emptyDataText: '暂无可用设备',
    emptyDataDesc: '请先添加设备数据',
  },
};

// 仿真控制
const {
  simulationState,
  sessionId,
  isRunning,
  isPaused,
  start,
  pause,
  resume,
  stop,
  step,
  setSpeed,
} = useSimulationControl(projectId, versionId);

// 仿真数据
const {
  bandwidthData,
  messageData,
  alarmData,
  filteredMessages,
  messageFilter,
  setMessageFilter,
  clearData,
} = useSimulationData(sessionId);

// 拓扑动画
const {
  startAnimation,
  stopAnimation,
  triggerTrafficAnimation,
  triggerErrorAnimation,
  setNodeActive,
} = useTopologyAnimation(dagRef, () => simulationState.speed);

// 故障注入
const { faults, injectFault, clearFault, clearAllFaults } = useFaultInjection(sessionId);

// 事件触发
const { eventList, createEvent, updateEvent, deleteEvent, triggerEvent } =
  useEventTrigger(sessionId);

// UI 状态
const selectedNode = ref(null);
const currentNode = ref(null);
const hoveredEdge = ref(null);
const tooltipPosition = ref({ x: 0, y: 0 });
const autoScroll = ref(true);
const dashboardShowTrend = ref(false);
const showEventPanel = ref(false);
const simulationSummary = ref(null);

// 组件引用
const nodeEditDrawerRef = ref(null);
const faultMenuRef = ref(null);
const protocolAnalyzerRef = ref(null);
const reportDialogRef = ref(null);
const healthCheckDialogRef = ref(null);

// 获取图实例
function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

// 加载项目信息
async function loadProjectInfo() {
  const res = await getProject(projectId.value);
  // http 客户端已解包 payload.data，直接访问字段
  projectName.value = res?.projectName || '未命名工程';
}

// 加载设备列表
async function loadDeviceList() {
  loading.value = true;
  const response = await listDevice({});
  const devices = response?.items || [];
  operators.value = devices.map((device) => ({
    name: device.deviceName,
    value: device.remark || device.deviceDesc || '设备',
    category: device.categoryName || device.category || '未分类',
    deviceId: device.deviceId,
    deviceType: device.deviceType,
    busType: device.busType,
    ports: device.interfaces || [],
    nodeType: 'device-port-node',
  }));
  loading.value = false;
}

// 从后端加载并回显已保存的拓扑数据
function restoreSavedTopology() {
  if (!projectId.value) return;

  const tryRestore = () => {
    const graph = dagRef.value?.getGraph?.();
    if (!graph) {
      setTimeout(tryRestore, 200);
      return;
    }

    getProjectTopology(projectId.value, versionId.value)
      .then((res) => {
        // http 客户端已解包 payload.data，res 直接是拓扑数据
        const topoData = res?.topologyData;
        const graphJson = topoData?.graph;
        if (graphJson) {
          graph.fromJSON(graphJson);
        }
      })
      .catch(() => {});
  };

  tryRestore();
}

// 仿真控制处理
async function handleStart() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('图实例不存在');
    return;
  }

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning('请至少放置两个设备节点');
    return;
  }

  if (!edges.length) {
    ElMessage.warning('请先建立设备之间的连接');
    return;
  }

  await start();
  startAnimation();
  ElMessage.success('仿真已启动');
}

function handlePause() {
  pause();
  stopAnimation();
}

function handleResume() {
  resume();
  startAnimation();
}

async function handleStop() {
  await stop();
  stopAnimation();
  simulationSummary.value = buildSimulationSummary();
  reportDialogRef.value?.open();
}

function handleStep() {
  step();
}

function handleSpeedChange(speed) {
  setSpeed(speed);
}

function handleBack() {
  router.push(`/project/project-detail/index/${projectId.value}`);
}

// 节点事件处理
function handleNodeClick({ node }) {
  const data = node.getData?.() || {};
  selectedNode.value = {
    id: node.id,
    ...data,
  };
}

function handleNodeDblclick({ node }) {
  currentNode.value = typeof node?.toJSON === 'function' ? node.toJSON() : node;
  nodeEditDrawerRef.value?.open();
}

function handleNodeUpdate({ nodeId, name, ports }) {
  const graph = getGraphInstance();
  if (!graph) return;

  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) return;

  const currentData = cellNode.getData() || {};
  cellNode.setData(
    {
      ...currentData,
      name,
      label: name,
      ports: ports || currentData.ports,
    },
    { overwrite: false }
  );
}

// 链路事件处理
function handleEdgeClick({ edge, e }) {
  if (e.button === 2) {
    faultMenuRef.value?.show(e, { type: 'edge', target: edge });
  }
}

function handleEdgeMouseEnter({ edge, e }) {
  hoveredEdge.value = edge;
  tooltipPosition.value = { x: e.clientX, y: e.clientY };
}

function handleEdgeMouseLeave() {
  hoveredEdge.value = null;
}

function getEdgeBandwidth(edge) {
  if (!edge) return null;
  const sourcePortId = edge.getSourcePortId?.();
  return bandwidthData.value.find((b) => b.portId === sourcePortId);
}

// 端口点击
function handlePortClick(portData) {
  const graph = getGraphInstance();
  if (!graph) return;

  const edges = graph.getEdges?.() || [];
  edges.forEach((edge) => {
    const sourcePortId = edge.getSourcePortId?.();
    const targetPortId = edge.getTargetPortId?.();
    if (sourcePortId === portData.portId || targetPortId === portData.portId) {
      triggerTrafficAnimation(edge.id, portData.protocolType);
    }
  });
}

// 告警处理
function handleAlarmClick(alarm) {
  if (alarm.targetId) {
    const graph = getGraphInstance();
    if (graph) {
      const cell = graph.getCellById(alarm.targetId);
      if (cell) {
        graph.centerCell(cell);
        triggerErrorAnimation(alarm.targetId);
      }
    }
  }
}

function handleAlarmFilterChange(filter) {
  // 告警过滤逻辑
}

// 报文处理
function handleMessageSelect(message) {
  if (message.senderNodeId && message.receiverNodeId) {
    const graph = getGraphInstance();
    if (graph) {
      const edges = graph.getEdges?.() || [];
      const edge = edges.find((e) => {
        const sourceId = e.getSourceCellId?.();
        const targetId = e.getTargetCellId?.();
        return (
          (sourceId === message.senderNodeId && targetId === message.receiverNodeId) ||
          (sourceId === message.receiverNodeId && targetId === message.senderNodeId)
        );
      });
      if (edge) {
        triggerTrafficAnimation(edge.id, message.protocolType);
      }
    }
  }
}

function handleMessageFilterChange(filter) {
  setMessageFilter(filter);
}

function formatDuration(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const parts = [];
  if (h > 0) parts.push(`${h}小时`);
  if (m > 0) parts.push(`${m}分`);
  parts.push(`${s}秒`);
  return parts.join('');
}

function buildSimulationSummary() {
  const messageCount = messageData.value.length;
  const alarmCount = alarmData.value.length;
  const duration = formatDuration(simulationState.elapsedTime);

  const bandwidthStatsMap = {};
  bandwidthData.value.forEach((item) => {
    const protocol = item.protocolType || item.protocol_type || '未知协议';
    if (!bandwidthStatsMap[protocol]) {
      bandwidthStatsMap[protocol] = {
        protocol,
        total: 0,
        max: 0,
        loadTotal: 0,
        count: 0,
      };
    }
    const stat = bandwidthStatsMap[protocol];
    const bw = Number(item.bandwidthMbps || item.bandwidth_mbps || 0);
    const load = Number(item.loadPercent || item.load_percent || 0);
    stat.total += bw;
    stat.loadTotal += load;
    stat.count += 1;
    stat.max = Math.max(stat.max, bw);
  });

  const bandwidthStats = Object.values(bandwidthStatsMap).map((item) => ({
    protocol: item.protocol,
    avgBandwidth: `${(item.total / item.count || 0).toFixed(3)} Mbps`,
    maxBandwidth: `${item.max.toFixed(3)} Mbps`,
    avgLoad: `${(item.loadTotal / item.count || 0).toFixed(1)}%`,
  }));

  const alarmStatsMap = {};
  alarmData.value.forEach((alarm) => {
    const type = alarm.alarmType || alarm.type || '未知类型';
    const level = alarm.severity || alarm.level || 'info';
    const key = `${type}-${level}`;
    if (!alarmStatsMap[key]) {
      alarmStatsMap[key] = { type, level, count: 0 };
    }
    alarmStatsMap[key].count += 1;
  });
  const alarmStats = Object.values(alarmStatsMap);

  return {
    duration,
    messageCount,
    alarmCount,
    bandwidthStats,
    alarmStats,
  };
}

function handleExportMessages(format) {
  protocolAnalyzerRef.value?.exportData(format);
}

// 故障注入处理
async function handleFaultInject(config) {
  await injectFault(config);
  ElMessage.success('故障注入成功');
}

async function handleFaultClear(faultId) {
  await clearFault(faultId);
  ElMessage.success('故障已清除');
}

// 事件触发处理
async function handleEventCreate(config) {
  await createEvent(config);
  ElMessage.success('事件创建成功');
}

async function handleEventEdit(eventId, config) {
  await updateEvent(eventId, config);
  ElMessage.success('事件更新成功');
}

async function handleEventDelete(eventId) {
  await deleteEvent(eventId);
  ElMessage.success('事件删除成功');
}

async function handleEventTrigger(eventId) {
  await triggerEvent(eventId);
  ElMessage.success('事件已触发');
}

// 健康自检
function handleHealthCheck() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('图实例不存在');
    return;
  }
  healthCheckDialogRef.value?.open(graph);
}

// 生命周期
onMounted(async () => {
  await Promise.all([loadProjectInfo(), loadDeviceList()]);
  restoreSavedTopology();
});

onUnmounted(() => {
  if (isRunning.value) {
    stop();
  }
  stopAnimation();
});

// 监听仿真状态变化
watch(isRunning, (running) => {
  if (running) {
    startAnimation();
  } else {
    stopAnimation();
  }
});
</script>

<style scoped>
@import './styles/animation.css';

/* 拓扑画布网格背景 - 深色主题优化 */
.sim-canvas {
  background-color: #0a0f1a;
  background-image:
    linear-gradient(rgba(77, 125, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(77, 125, 255, 0.03) 1px, transparent 1px),
    radial-gradient(circle at 50% 50%, rgba(77, 125, 255, 0.02) 0%, transparent 50%);
  background-size:
    20px 20px,
    20px 20px,
    100% 100%;
  background-position:
    0 0,
    0 0,
    center center;
}

.sim-canvas :deep(.xflow-dag),
.sim-canvas :deep(.xflow-dag-container) {
  width: 100% !important;
  height: 100% !important;
  position: relative;
  z-index: 1;
}

/* 设备详情面板滑入动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.simulation-shell {
  background:
    radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.07), transparent 30%),
    radial-gradient(circle at 80% 0%, rgba(52, 211, 153, 0.05), transparent 25%), #0b1220;
}

.floating-panel {
  position: absolute;
  z-index: 30;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.panel-title .title-text {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.panel-title .live-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 6px;
  border-radius: 3px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  font-size: 10px;
  font-weight: 600;
  color: #10b981;
  letter-spacing: 0.04em;
}

.panel-title .live-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10b981;
  animation: live-pulse 1.5s ease-in-out infinite;
}

@keyframes live-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.panel-actions {
  display: inline-flex;
  align-items: center;
}

.view-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.view-toggle .toggle-item {
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.15s ease;
  user-select: none;
}

.view-toggle .toggle-item:hover {
  color: #64748b;
}

.view-toggle .toggle-item.active {
  color: #2563eb;
  font-weight: 500;
}

.view-toggle .toggle-divider {
  color: #cbd5e1;
  font-weight: 300;
}
</style>
