<template>
  <div
    class="simulation-dark simulation-shell flex h-full bg-slate-950"
    :class="{ 'fault-injection-mode': isFaultInjectionMode }"
  >
    <!-- 故障注入模式提示条 -->
    <Transition name="mode-banner">
      <div v-if="isFaultInjectionMode" class="fault-mode-banner">
        <div class="banner-content">
          <div class="banner-icon">
            <el-icon class="pulse-icon"><Warning /></el-icon>
          </div>
          <div class="banner-text">
            <span class="banner-title">故障注入</span>
            <span class="banner-hint">
              <template v-if="!selectedEdge"
                >点击拓扑图中的 <strong>链路</strong> 选择目标</template
              >
              <template v-else
                >已锁定
                <strong class="text-cyan-400">{{
                  getSelectedEdgeId()
                }}</strong></template
              >
            </span>
          </div>
          <div class="banner-actions">
            <el-button
              v-if="selectedEdge"
              class="cancel-select-btn"
              size="small"
              @click="clearSelectedEdge"
            >
              取消
            </el-button>
            <el-button
              class="exit-mode-btn"
              size="small"
              @click="exitFaultMode"
            >
              关闭
            </el-button>
          </div>
        </div>
        <div class="banner-progress"></div>
      </div>
    </Transition>

    <!-- 左侧主区域：header + main + footer -->
    <div class="flex flex-col flex-1 min-w-0 h-full">
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
          @health-check="handleHealthCheck"
          @show-events="handleShowEvents"
          @show-report="handleShowReport"
        />
      </header>

      <!-- 主内容区域 -->
      <main class="flex flex-1 min-h-0 p-3 relative">
        <!-- 拓扑画布 -->
        <section
          class="sim-canvas pro-card flex-1 relative"
          :class="{ 'fault-target-canvas': isFaultInjectionMode }"
        >
          <!-- 故障注入模式下的选中链路高亮层 -->
          <div
            v-if="isFaultInjectionMode && selectedEdge"
            class="selected-edge-indicator"
          >
            <div class="indicator-ring"></div>
            <span class="indicator-text">已锁定目标链路</span>
          </div>
          <XflowDAG
            ref="dagRef"
            :showToolbar="false"
            :showSidebar="false"
            :operators="operators"
            :operators-loading="loading"
            :layout="layoutMode"
            :dnd-config="dndConfig"
            :show-graph-control="false"
            theme="dark"
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

        <!-- 带宽面板（封装组件，内部含浮动容器） -->
        <BandwidthChartPanel
          ref="bandwidthChartRef"
          v-if="dockState.bandwidth"
          :visible="dockState.bandwidth"
          :bandwidth-data="bandwidthData"
          :running="isRunning"
          :speed="simulationState.speed"
          :reset-on-stop="true"
          :position="{ top: '14px', left: '14px' }"
          :size="{ width: '520px', maxHeight: '430px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
        />

        <!-- 告警面板（封装组件，内部含浮动容器） -->
        <AlarmPanelFloating
          v-if="dockState.alarm"
          :alarms="alarmData"
          :position="{ top: '14px', right: '14px' }"
          :size="{ width: '520px', maxHeight: '420px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
          @alarm-click="handleAlarmClick"
          @filter-change="handleAlarmFilterChange"
        />

        <!-- 时序/延迟分析面板 -->
        <TimingLatencyPanel
          v-if="dockState.timing"
          :visible="dockState.timing"
          :messages="filteredMessages"
          :bandwidth-data="bandwidthData"
          :position="{ top: '420px', left: '14px' }"
          :size="{ width: '520px', maxHeight: '430px' }"
          :collapsed-size="{ width: '46px', height: '46px' }"
          :default-collapsed="false"
        />
      </main>

      <!-- 底部：协议分析器 -->
      <footer class="shrink-0 h-64 mx-3 mb-3 pro-card">
        <ProtocolAnalyzer
          ref="protocolAnalyzerRef"
          :messages="filteredMessages"
          :is-running="isRunning"
          :auto-scroll="autoScroll"
          :speed="simulationState.speed"
          @message-select="handleMessageSelect"
          @filter-change="handleMessageFilterChange"
          @export="handleExportMessages"
          @auto-scroll-change="autoScroll = $event"
        />
      </footer>
    </div>

    <!-- 故障板浮层 -->
    <FaultBoardFloating
      v-if="dockState.fault"
      :visible="dockState.fault"
      :faults="faults"
      :loading="faultsLoading"
      :selected-edge="selectedEdge"
      :hovered-edge="hoveredEdge"
      :is-running="isRunning"
      :position="{ top: '58px', right: '92px' }"
      @apply-template="handleFaultTemplate"
      @clear="handleFaultClear"
      @clear-all="handleClearAllFaults"
      @refresh="refreshFaults"
      @close="exitFaultMode"
    />

    <!-- 数据注入策略面板 -->
    <DataInjectionPanel
      ref="injectionPanelRef"
      :visible="dockState.injection"
      :position="{ bottom: '280px', left: '14px' }"
      :default-collapsed="false"
      @apply="handleInjectionStrategyApply"
    />

    <!-- 右侧通顶侧边栏 - 航空暗黑系 -->
    <aside class="sim-side-dock-aside">
      <SimulationSideDock
        :items="dockItems"
        :active-keys="activeDockKeys"
        :badges="dockBadges"
        :disabled-items="dockDisabledItems"
        :all-collapsed="allDockPanelsCollapsed"
        @toggle="handleDockToggle"
        @toggle-all="handleToggleAllPanels"
      />
    </aside>

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer
      ref="nodeEditDrawerRef"
      :node-data="currentNode"
      @submit="handleNodeUpdate"
    />

    <!-- 事件触发面板 -->
    <EventTriggerPanel
      v-model:visible="showEventPanel"
      :events="eventList"
      :nodes="topologyNodes"
      @create="handleEventCreate"
      @edit="handleEventEdit"
      @delete="handleEventDelete"
      @trigger="handleEventTrigger"
    />

    <!-- 仿真报告对话框 -->
    <SimulationReportDialog ref="reportDialogRef" />

    <!-- 健康自检对话框 -->
    <HealthCheckDialog
      ref="healthCheckDialogRef"
      @recheck="handleHealthCheck"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from "vue";
import { throttle } from "lodash-es";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Warning } from "@element-plus/icons-vue";

// 组件导入
import XflowDAG from "@/components/business/Dag/index.vue";
import SimulationHeader from "./components/SimulationHeader.vue";
import BandwidthChartPanel from "./components/BandwidthChartPanel.vue";
import AlarmPanelFloating from "./components/AlarmPanelFloating.vue";
import SimulationSideDock from "./components/SimulationSideDock.vue";
import ProtocolAnalyzer from "./components/ProtocolAnalyzer.vue";
import EdgeTooltip from "./components/EdgeTooltip.vue";
import FaultBoardFloating from "./components/FaultBoardFloating.vue";
import EventTriggerPanel from "./components/EventTriggerPanel.vue";
import SimulationReportDialog from "./components/SimulationReportDialog.vue";
import HealthCheckDialog from "./components/HealthCheckDialog.vue";
import TimingLatencyPanel from "./components/TimingLatencyPanel.vue";
import DataInjectionPanel from "./components/DataInjectionPanel.vue";
import { NodeEditDrawer } from "../components";

// Composables 导入
import { useSimulationControl } from "./composables/useSimulationControl";
import { useSimulationData } from "./composables/useSimulationData";
import { useTopologyAnimation } from "./composables/useTopologyAnimation";
import { useFaultInjection } from "./composables/useFaultInjection";
import { useFaultInjectionUI } from "./composables/useFaultInjectionUI";
import { useAlarmHandler } from "./composables/useAlarmHandler";
import { useSimulationReport } from "./composables/useSimulationReport";
import { useEventTrigger } from "./composables/useEventTrigger";
import { useHealthCheck } from "./composables/useHealthCheck";
import useAppStore from "@/store/modules/app";

// 样式导入 - 注意：simulation-theme.css 已内部导入 variables.css
import "./styles/simulation-theme.css";
import "./styles/global-popper-dark.css"; // 全局 Popper 深色样式（Teleport到body的元素）
import "./styles/fault-injection-mode.less";
import "./styles/aviation-dark-theme.less";
import "./styles/simulation-dialog-theme.less";

// API 导入
import { listDevice } from "@/api/device/device";
import { getProject } from "@/api/project/project";
import { getProjectTopology } from "@/api/project/topology";

defineOptions({ name: "SimulationConsole" });

// 路由
const route = useRoute();
const router = useRouter();
const projectId = computed(() => Number(route.params.projectId));
const versionId = computed(() =>
  route.query.versionId ? Number(route.query.versionId) : undefined,
);
const appStore = useAppStore();

// 项目信息
const projectName = ref("");

// DAG 组件
const dagRef = ref(null);
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref("horizontal");
const dndConfig = {
  title: "设备库",
  searchPlaceholder: "搜索设备...",
  textConfig: {
    loadingText: "正在加载设备库...",
    emptySearchText: "没有找到匹配的设备",
    emptySearchDesc: "请尝试使用其他关键词搜索",
    emptyDataText: "暂无可用设备",
    emptyDataDesc: "请先添加设备数据",
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
  syncStatus,
} = useSimulationControl(projectId, versionId);
let stepLock = false;

// 仿真数据
const {
  bandwidthData,
  messageData,
  alarmData,
  statusData,
  filteredMessages,
  filteredAlarms,
  messageFilter,
  alarmFilter,
  setMessageFilter,
  setAlarmFilter,
  clearData,
  faultEventData,
  getNewFaultEvents,
} = useSimulationData(sessionId);

watch(statusData, (status) => {
  if (!status) return;
  syncStatus(status);
});

// 拓扑动画
const {
  startAnimation,
  stopAnimation,
  triggerTrafficAnimation,
  triggerErrorAnimation,
  setNodeActive,
  setNodeError,
  highlightEdges,
  clearEdgeHighlight,
} = useTopologyAnimation(dagRef, () => simulationState.speed);

const { runHealthCheck } = useHealthCheck();
const healthReport = ref(null);

// 故障注入
const faultInjection = useFaultInjection(sessionId);
const {
  faults,
  injectFault,
  ingestFaultEvents,
  loading: faultsLoading,
} = faultInjection;

// 事件触发
const {
  eventList,
  loadEvents,
  createEvent,
  updateEvent,
  deleteEvent,
  triggerEvent,
} = useEventTrigger(sessionId);

// 获取拓扑节点列表（用于事件触发面板的设备选择）
const topologyNodes = ref([]);

// 更新拓扑节点列表
function updateTopologyNodes() {
  const graph = dagRef.value?.getGraph?.();
  if (!graph) return;
  const nodes = graph.getNodes?.() || [];
  topologyNodes.value = nodes.map((node) => ({
    id: node.id,
    data: node.getData?.() || node.data || {},
    label: node.getData?.()?.label || node.data?.label || node.id,
  }));
}

// UI 状态
const currentNode = ref(null);
const hoveredEdge = ref(null);
const tooltipPosition = ref({ x: 0, y: 0 });
const autoScroll = ref(true);
const dashboardShowTrend = ref(false);
const showEventPanel = ref(false);
const simulationSummary = ref(null);

// 数据注入策略配置
const injectionStrategy = ref({
  strategy: "random",
  params: {
    valueRange: "0~255",
    startValue: 0,
    step: 1,
    fixedValue: "0",
    presetValues: "0,1,2,3,4,5",
    amplitude: 100,
    offset: 0,
    frequency: 1,
    phase: 0,
  },
});
const dockState = reactive({
  bandwidth: false,
  alarm: false,
  timing: false,
  fault: false,
  injection: false,
});

const dockItems = [
  { key: "bandwidth", label: "带宽", icon: "ri:activity-line" },
  { key: "alarm", label: "告警", icon: "ri:alarm-warning-line" },
  { key: "timing", label: "时序", icon: "ri:bar-chart-2-line" },
  { key: "fault", label: "故障", icon: "ri:bug-line" },
  { key: "injection", label: "注入", icon: "ri:settings-3-line" },
];
const activeDockKeys = computed(() => {
  const keys = [];
  if (dockState.bandwidth) keys.push("bandwidth");
  if (dockState.alarm) keys.push("alarm");
  if (dockState.timing) keys.push("timing");
  if (dockState.fault) keys.push("fault");
  if (dockState.injection) keys.push("injection");
  return keys;
});
const dockBadges = computed(() => {
  const uniqueAlarmCount = alarmData.value?.length
    ? new Set(alarmData.value.map((item) => item.alarmId)).size
    : 0;
  const activeFaultCount =
    faults.value?.filter?.((f) => f.status === "active").length || 0;
  return {
    alarm: uniqueAlarmCount || "",
    fault: activeFaultCount || "",
  };
});

// 侧边栏按钮禁用配置
const dockDisabledItems = computed(() => {
  const disabled = {};
  // 仿真未运行时禁用故障注入
  if (!isRunning.value) {
    disabled.fault = "请先启动仿真后再进行故障注入";
  }
  return disabled;
});
const allDockPanelsCollapsed = computed(() => {
  return (
    !dockState.bandwidth &&
    !dockState.alarm &&
    !dockState.timing &&
    !dockState.fault &&
    !dockState.injection
  );
});

// 组件引用
const nodeEditDrawerRef = ref(null);
const protocolAnalyzerRef = ref(null);
const reportDialogRef = ref(null);
const healthCheckDialogRef = ref(null);
const bandwidthChartRef = ref(null);
const injectionPanelRef = ref(null);

// 获取图实例
function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

/**
 * 构建端口到对端设备名的映射
 * @param {Object} node - 当前节点
 * @returns {Record<string, string[]>} key 为端口 ID，value 为对端设备名称数组
 */
function buildPeerDeviceNameByPort(node) {
  const graph = getGraphInstance();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];

  const registerPeer = (portId, peerName) => {
    if (!portId || !peerName) return;
    const key = String(portId);
    const keys = [key];
    if (key.startsWith("port-")) {
      keys.push(key.replace(/^port-/, ""));
    }

    keys.forEach((k) => {
      if (!result[k]) {
        result[k] = [];
      }
      const list = Array.isArray(result[k]) ? result[k] : [result[k]];
      if (!list.includes(peerName)) {
        result[k] = list.concat(peerName);
      } else {
        result[k] = list;
      }
    });
  };

  edges.forEach((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    if (!sourceId || !targetId) return;

    let localPortId;
    let peerNodeId;

    if (sourceId === nodeId) {
      localPortId = edge.getSourcePortId?.();
      peerNodeId = targetId;
    } else if (targetId === nodeId) {
      localPortId = edge.getTargetPortId?.();
      peerNodeId = sourceId;
    } else {
      return;
    }

    if (!localPortId || !peerNodeId) return;

    const peerNode = graph.getCellById(peerNodeId);
    const data = peerNode?.getData?.() || {};
    const deviceName = data.name || data.label || data.deviceName || "";

    registerPeer(localPortId, deviceName);
  });

  return result;
}

// 故障注入 UI 交互
const {
  selectedEdge,
  isFaultInjectionMode,
  getSelectedEdgeId,
  setupEdgeEvents,
  clearSelectedEdge,
  exitFaultMode: _exitFaultMode,
  handleFaultClear,
  handleClearAllFaults,
  handleFaultTemplate: _handleFaultTemplate,
  refreshFaults,
} = useFaultInjectionUI({
  getGraphInstance,
  dockState,
  faultInjection,
});

// 退出故障模式（包装函数，额外清除图上的高亮状态）
async function exitFaultMode() {
  const graph = getGraphInstance();
  if (graph) {
    // 清除所有边的高亮
    const edgeIds = graph.getEdges().map((e) => e.id);
    clearEdgeHighlight(edgeIds);
    // 清除所有节点的错误状态
    graph.getNodes().forEach((node) => {
      setNodeError(node.id, false);
      setNodeActive(node.id, false, true);
    });
  }
  await _exitFaultMode();
}

// 告警处理
const { handleAlarmClick, handleAlarmFilterChange } = useAlarmHandler({
  getGraphInstance,
  topologyAnimation: {
    highlightEdges,
    clearEdgeHighlight,
    triggerErrorAnimation,
    setNodeError,
    setNodeActive,
  },
});

// 仿真报告
const { buildSimulationSummary } = useSimulationReport({
  messageData,
  alarmData,
  bandwidthData,
  simulationState,
});

// 加载项目信息
async function loadProjectInfo() {
  const res = await getProject(projectId.value);
  projectName.value = res.data?.projectName || "未命名工程";
}

// 加载设备列表
async function loadDeviceList() {
  loading.value = true;
  const response = await listDevice({});
  const devices = response?.rows || [];
  operators.value = devices.map((device) => ({
    name: device.deviceName,
    value: device.remark || device.deviceDesc || "设备",
    category: device.categoryName || device.category || "未分类",
    deviceId: device.deviceId,
    deviceType: device.deviceType,
    busType: device.busType,
    ports: device.interfaces || [],
    nodeType: "device-port-node",
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

    // 设置边的事件监听
    setupEdgeEvents(graph);
    setupEdgeHoverEvents(graph);

    getProjectTopology(projectId.value, versionId.value)
      .then((res) => {
        const topo = res?.data;
        const topoData = topo?.topologyData;
        const graphJson = topoData?.graph;
        if (graphJson) {
          graph.fromJSON(graphJson);
          // 拓扑加载完成后，更新节点列表
          updateTopologyNodes();
        }
      })
      .catch(() => {});
  };

  tryRestore();
}

// 设置边的鼠标事件（hover 提示）
function setupEdgeHoverEvents(graph) {
  if (!graph) return;

  graph.on("edge:mouseenter", ({ edge, e }) => {
    hoveredEdge.value = edge;
    tooltipPosition.value = { x: e.clientX, y: e.clientY };
  });

  graph.on("edge:mouseleave", () => {
    hoveredEdge.value = null;
  });
}

// 仿真控制处理
async function handleStart() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error("图实例不存在");
    return;
  }

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning("请至少放置两个设备节点");
    return;
  }

  if (!edges.length) {
    ElMessage.warning("请先建立设备之间的连接");
    return;
  }

  const passed = await runPreflightCheck(graph);
  if (!passed) return;

  // 构建数据注入策略参数
  const strategyConfig =
    injectionPanelRef.value?.getConfig?.() || injectionStrategy.value;
  const startOptions = {
    injection_strategy: strategyConfig.strategy,
    injection_params: strategyConfig.params,
  };

  await start(startOptions);
  startAnimation();
  ElMessage.success("仿真已启动");
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
  reportDialogRef.value?.open({
    sessionId: sessionId.value,
    summary: simulationSummary.value,
  });
}

const handleStep = throttle(
  () => {
    if (stepLock) return;
    stepLock = true;
    step()
      .then(() => {
        bandwidthChartRef.value?.stepScanline();
      })
      .catch((err) => {
        const message = err?.message || "单步执行失败";
        ElMessage.error(message);
      })
      .finally(() => {
        stepLock = false;
      });
  },
  500,
  { trailing: false },
);

function handleSpeedChange(speed) {
  setSpeed(speed);
}

function handleBack() {
  router.push(`/project/project-detail/index/${projectId.value}`);
}

// 节点事件处理
function handleNodeClick({ node }) {
  // 点击节点时取消链路选中
  selectedEdge.value = null;
}

function handleNodeDblclick({ node }) {
  // 构建端口到对端设备名的映射
  const peerDeviceNameByPort = buildPeerDeviceNameByPort(node);
  // 转为普通 JSON
  const jsonNode = typeof node?.toJSON === "function" ? node.toJSON() : node;
  // 附加映射数据
  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
  };
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
    { overwrite: false },
  );
}

// 链路事件处理 (这些函数现在由 setupEdgeEvents 中的图实例事件监听处理)
function handleEdgeClick({ edge, e }) {
  // 由 setupEdgeEvents 处理
}

function handleEdgeMouseEnter({ edge, e }) {
  // 由 setupEdgeEvents 处理
}

function handleEdgeMouseLeave() {
  // 由 setupEdgeEvents 处理
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
          (sourceId === message.senderNodeId &&
            targetId === message.receiverNodeId) ||
          (sourceId === message.receiverNodeId &&
            targetId === message.senderNodeId)
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

function handleDockToggle(key) {
  dockState[key] = !dockState[key];
}

function handleToggleAllPanels() {
  const allCollapsed =
    !dockState.bandwidth &&
    !dockState.alarm &&
    !dockState.timing &&
    !dockState.fault &&
    !dockState.injection;
  Object.keys(dockState).forEach((key) => {
    dockState[key] = allCollapsed;
  });
}

function handleExportMessages(format) {
  protocolAnalyzerRef.value?.exportData(format);
}

// 故障模板应用（包装 composable 方法，传入 hoveredEdge）
function handleFaultTemplate(tpl) {
  _handleFaultTemplate(tpl, hoveredEdge);
}

// 数据注入策略应用
function handleInjectionStrategyApply(config) {
  injectionStrategy.value = config;
}

// 事件触发处理
async function handleEventCreate(config) {
  if (!sessionId.value) {
    ElMessage.warning("请先启动仿真会话后再添加事件");
    return;
  }
  try {
    await createEvent(config);
    ElMessage.success("事件创建成功");
  } catch (err) {
    console.error("创建事件失败", err);
    ElMessage.error(err?.message || "创建事件失败");
  }
}

async function handleEventEdit(eventId, config) {
  if (!sessionId.value) {
    ElMessage.warning("当前无仿真会话，无法更新事件");
    return;
  }
  try {
    await updateEvent(eventId, config);
    ElMessage.success("事件更新成功");
  } catch (err) {
    console.error("更新事件失败", err);
    ElMessage.error(err?.message || "更新事件失败");
  }
}

async function handleEventDelete(eventId) {
  if (!sessionId.value) {
    ElMessage.warning("当前无仿真会话，无法删除事件");
    return;
  }
  try {
    await deleteEvent(eventId);
    ElMessage.success("事件删除成功");
  } catch (err) {
    console.error("删除事件失败", err);
    ElMessage.error(err?.message || "删除事件失败");
  }
}

async function handleEventTrigger(eventId) {
  if (!sessionId.value) {
    ElMessage.warning("当前无仿真会话，无法触发事件");
    return;
  }
  try {
    await triggerEvent(eventId);
    ElMessage.success("事件已触发");
  } catch (err) {
    console.error("触发事件失败", err);
    ElMessage.error(err?.message || "触发事件失败");
  }
}

// 健康自检
function handleHealthCheck() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error("图实例不存在");
    return;
  }
  const report = runHealthCheck(graph);
  healthReport.value = report;
  healthCheckDialogRef.value?.open(report);
}

// 显示事件面板
function handleShowEvents() {
  showEventPanel.value = true;
}

// 显示仿真报告
function handleShowReport() {
  if (!sessionId.value) {
    ElMessage.warning("当前无仿真会话，无法生成报告");
    return;
  }
  simulationSummary.value = buildSimulationSummary();
  reportDialogRef.value?.open({
    sessionId: sessionId.value,
    summary: simulationSummary.value,
  });
}

async function runPreflightCheck(graph) {
  const report = runHealthCheck(graph);
  healthReport.value = report;
  if (!report.canSimulate || report.errorChecks > 0) {
    healthCheckDialogRef.value?.open(report);
    ElMessage.error("拓扑检查未通过，无法启动仿真");
    return false;
  }
  if (report.warningChecks > 0) {
    healthCheckDialogRef.value?.open(report);
    ElMessage.warning("存在警告，请确认后继续");
  }
  return true;
}

watch(faultEventData, () => {
  const events = getNewFaultEvents();
  if (events && events.length) {
    ingestFaultEvents(events);
  }
});

watch(
  sessionId,
  (id) => {
    if (id) {
      refreshFaults();
      loadEvents();
    } else {
      console.log('eventList.valuesss', eventList.value)
      eventList.value = [];
    }
  },
  { immediate: true },
);

// 监听故障面板打开，自动获取故障列表
watch(
  () => dockState.fault,
  (opened) => {
    if (opened && sessionId.value) {
      refreshFaults();
    }
  },
);

// 生命周期
onMounted(async () => {
  // 进入页面时自动收起全局侧边栏
  appStore.closeSideBar({ withoutAnimation: true });
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
@import "./styles/animation.css";

/* 拓扑画布网格背景 - 深色主题优化 */
.sim-canvas {
  background-color: #0a0f1a;
  background-image:
    linear-gradient(rgba(77, 125, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(77, 125, 255, 0.03) 1px, transparent 1px),
    radial-gradient(
      circle at 50% 50%,
      rgba(77, 125, 255, 0.02) 0%,
      transparent 50%
    );
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

/* 仿真页面 DAG 暗黑主题覆盖 */
.sim-canvas :deep(.zx-dag-page) {
  background: transparent;
}

.sim-canvas :deep(.dag-center) {
  background: transparent !important;
}

.sim-canvas :deep(.dag-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.xflow-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.x6-graph) {
  background: transparent !important;
}

.sim-canvas :deep(.x6-graph-svg) {
  background: transparent !important;
}

.simulation-shell {
  background:
    radial-gradient(
      circle at 20% 20%,
      rgba(59, 130, 246, 0.07),
      transparent 30%
    ),
    radial-gradient(
      circle at 80% 0%,
      rgba(52, 211, 153, 0.05),
      transparent 25%
    ),
    #0b1220;
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

/* 右侧通顶侧边栏 - 航空暗黑系 */
.sim-side-dock-aside {
  position: relative;
  flex-shrink: 0;
  width: 80px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 10px;
  background: linear-gradient(
    180deg,
    rgba(12, 22, 40, 0.98) 0%,
    rgba(8, 14, 26, 1) 30%,
    rgba(6, 10, 18, 1) 70%,
    rgba(10, 18, 32, 0.98) 100%
  );
  border-left: 1px solid rgba(34, 211, 238, 0.12);
  box-shadow:
    -6px 0 32px rgba(0, 0, 0, 0.5),
    -2px 0 8px rgba(0, 0, 0, 0.3),
    inset 1px 0 0 rgba(34, 211, 238, 0.06);
}

/* 侧边栏顶部光晕 */
.sim-side-dock-aside::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: radial-gradient(
    ellipse 100% 100% at 50% -20%,
    rgba(34, 211, 238, 0.08) 0%,
    transparent 70%
  );
  pointer-events: none;
}

/* 侧边栏底部光晕 */
.sim-side-dock-aside::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: radial-gradient(
    ellipse 100% 100% at 50% 120%,
    rgba(34, 211, 238, 0.05) 0%,
    transparent 70%
  );
  pointer-events: none;
}
</style>
