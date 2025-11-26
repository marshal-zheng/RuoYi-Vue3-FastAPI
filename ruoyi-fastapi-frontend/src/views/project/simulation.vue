<template>
  <ZxContentWrap class="simulation-page">
    <!-- header-right插槽添加 '仿真'操作 -->
    <template #header-right>
      <zx-button type="primary" icon="VideoPlay" @click="handleRunSimulation"> 执行仿真 </zx-button>
      <zx-button type="success" icon="GoodsFilled" @click="handleSaveTopo"> 健康自检 </zx-button>
    </template>
    <XflowDAG
      ref="dagRef"
      :showToolbar="false"
      :showSidebar="false"
      :operators="operators"
      :operators-loading="loading"
      :layout="layoutMode"
      :dnd-config="dndConfig"
      :show-graph-control="false"
      @node-dblclick="handleNodeDblclick"
    >
      <template #right>
        <zx-button
          size="small"
          type="success"
          :loading="simulationLoading"
          :disabled="loading || simulationLoading || simulationStatus === 'running'"
          @click="handleRunSimulation"
        >
          执行仿真
        </zx-button>
        <zx-button size="small" type="primary" :disabled="loading" @click="handleSaveTopo">
          保存
        </zx-button>
      </template>
    </XflowDAG>

    <!-- 仿真状态面板 -->
    <SimulationStatusPanel :narration="simulationNarration" />

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />

    <!-- 仿真结果对话框 -->
    <SimulationResultDialog ref="simulationDialogRef" @reopen="handleReopenSimulationDialog" />
  </ZxContentWrap>
</template>

<script setup name="Index">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import XflowDAG from '@/components/business/Dag/index.vue';
import { NodeEditDrawer } from './components';
import SimulationResultDialog from './components/SimulationResultDialog.vue';
import SimulationStatusPanel from './components/SimulationStatusPanel.vue';
import { listDevice } from '@/api/device/device';
import { ElMessage } from 'element-plus';

// 引入拆分的 composables
import { useGraphStyle } from './composables/useGraphStyle';
import { useSimulationAnimation } from './composables/useSimulationAnimation';
import { useSimulationCore } from './composables/useSimulationCore';
import { useDataTransform } from './composables/useDataTransform';
import { useSimulationFiles } from './composables/useSimulationFiles';
import { useTopology } from './composables/useTopology';

// 版本号
const version = ref('3.9.0');

// 路由参数
const route = useRoute();
const router = useRouter();
const projectId = computed(() => route.params.projectId);
const versionId = computed(() => route.query.versionId);

function getProjectIdNumber() {
  const id = projectId.value;
  return id ? Number(id) : null;
}

function getVersionIdNumber() {
  const id = versionId.value;
  return id ? Number(id) : undefined;
}

// DAG 组件配置 - 设备列表（从后端获取）
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal');

// DAG 组件引用
const dagRef = ref(null);

// 节点编辑抽屉
const nodeEditDrawerRef = ref(null);
const currentNode = ref(null);
const simulationDialogRef = ref(null);

// 可配置的文案和设置
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

// 获取图实例
function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

// 清除图内容
function clearGraphContent(graphInstance) {
  const graph = graphInstance || getGraphInstance();
  if (graph && typeof graph.clearCells === 'function') {
    graph.clearCells();
  }
}

// 初始化 composables
const graphStyleUtils = useGraphStyle();
const animationUtils = useSimulationAnimation();
const simulationCore = useSimulationCore({
  graphStyleUtils,
  animationUtils,
});
const dataTransform = useDataTransform();
const simulationFiles = useSimulationFiles(version);
const topologyUtils = useTopology(
  version,
  getGraphInstance,
  clearGraphContent,
  graphStyleUtils.isSimulationToken
);

// 解构 simulationCore 导出的状态和方法
const {
  simulationStatus,
  simulationSteps,
  simulationPointer,
  simulationLoading,
  simulationNarration,
  simulationTimelinePhases,
  simulationResultPayload,
  buildSimulationSteps,
  buildPhaseTimeline,
  announceSimulationSchedule,
  runSimulationFlow,
  stopSimulationRunner,
  queueSimulationResult,
  resetSimulationNarration,
} = simulationCore;

/**
 * 队列仿真结果并展示
 */
function presentSimulationResult() {
  if (!simulationResultPayload.value) {
    return;
  }
  simulationDialogRef.value?.open(simulationResultPayload.value);
}

/**
 * 重新打开仿真对话框
 */
function handleReopenSimulationDialog() {
  if (!simulationResultPayload.value) {
    ElMessage.warning('暂无仿真结果，请先执行仿真');
    return;
  }
  simulationDialogRef.value?.open(simulationResultPayload.value);
}

/**
 * 执行仿真
 */
function handleRunSimulation() {
  if (simulationLoading.value) {
    return;
  }
  if (simulationStatus.value === 'running') {
    ElMessage.warning('仿真正在执行，请稍后');
    return;
  }

  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('仿真失败：图实例不存在');
    return;
  }
  resetSimulationNarration();

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning('请至少放置两个设备节点后再生成仿真');
    return;
  }

  if (!edges.length) {
    ElMessage.warning('请先建立设备之间的接口连线');
    return;
  }

  stopSimulationRunner('idle');
  simulationResultPayload.value = null;
  simulationSteps.value = [];
  simulationPointer.value = 0;
  simulationLoading.value = true;

  const { nodes: nodePayload, edges: edgePayload } = dataTransform.buildSimulationPayload(
    graph,
    graphStyleUtils.isSimulationToken
  );
  if (!edgePayload.length) {
    ElMessage.warning('暂未检测到有效连线');
    simulationLoading.value = false;
    return;
  }

  const steps = buildSimulationSteps(graph);
  if (!steps.length) {
    ElMessage.warning('当前拓扑缺少可执行路径');
    simulationLoading.value = false;
    return;
  }

  animationUtils.disposeSimulationAnimations();
  animationUtils.disposeAllSimulationTokens();
  graphStyleUtils.resetGraphSimulationState(graph);
  graphStyleUtils.markQueuedEdges(steps);
  simulationSteps.value = steps;
  simulationTimelinePhases.value = buildPhaseTimeline(steps);
  announceSimulationSchedule(steps);
  simulationPointer.value = 0;
  simulationStatus.value = 'running';

  const summary = simulationFiles.buildSimulationSummary(
    nodePayload,
    edgePayload,
    dataTransform.BUS_TYPES
  );
  const designContent = simulationFiles.generateDesignFilePayload(
    '多总线仿真工程',
    version.value,
    nodePayload,
    edgePayload
  );
  const icdContent = simulationFiles.generateIcdFilePayload(
    '多总线仿真工程',
    version.value,
    nodePayload,
    edgePayload
  );
  const timeline =
    simulationTimelinePhases.value?.length > 0
      ? simulationTimelinePhases.value
      : simulationFiles.generateSimulationTimeline(edgePayload);

  queueSimulationResult({
    summary,
    timeline,
    designFile: {
      name: 'bus_design.csv',
      content: designContent,
    },
    icdFile: {
      name: 'interface_control.csv',
      content: icdContent,
    },
  });

  simulationLoading.value = false;

  // 运行仿真流程，完成后展示结果
  runSimulationFlow().then(() => {
    if (simulationStatus.value === 'completed') {
      presentSimulationResult();
    }
  });
}

/**
 * 从后端加载设备列表数据
 */
async function loadDeviceList() {
  loading.value = true;
  try {
    const response = await listDevice({});
    const devices = response?.rows || [];

    if (devices.length === 0) {
      operators.value = [];
      return;
    }

    operators.value = dataTransform.convertDevicesToOperators(devices);
  } catch (error) {
    void error;
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 处理节点双击事件
 */
function handleNodeDblclick({ node }) {
  const graph = dagRef.value?.getGraph();
  const peerDeviceNameByPort = topologyUtils.buildPeerDeviceNameByPort(node, graph);
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;

  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
  };

  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 */
function handleNodeUpdate({ nodeId, name, ports }) {
  const graph = dagRef.value?.getGraph();
  if (!graph) {
    ElMessage.error('更新失败：图实例不存在');
    return;
  }

  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) {
    ElMessage.error('更新失败：节点不存在');
    return;
  }

  const currentData = cellNode.getData() || {};

  const updatedData = {
    ...currentData,
    name: name,
    label: name,
    ports: ports || currentData.ports,
  };

  if (currentData.properties?.content) {
    updatedData.properties = {
      ...currentData.properties,
      content: {
        ...currentData.properties.content,
        label: name,
      },
    };
  }

  cellNode.setData(updatedData, { overwrite: false });
}

/**
 * 保存工程拓扑
 */
function handleSaveTopo() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    ElMessage.error('保存失败：缺少工程ID');
    return;
  }

  topologyUtils
    .saveTopo(currentProjectId, getVersionIdNumber())
    .then((success) => {
      if (success) {
        router.push(`/project/project-detail/index/${currentProjectId}`);
      }
    })
    .catch(() => {
      ElMessage.error('拓扑保存失败，请稍后重试');
    });
}

/**
 * 从后端加载并回显已保存的拓扑数据
 */
function restoreSavedTopology() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    return;
  }
  topologyUtils.restoreSavedTopology(currentProjectId, getVersionIdNumber(), dagRef);
}

watch(
  () => [projectId.value, versionId.value],
  () => {
    restoreSavedTopology();
  }
);

// 页面加载时获取设备列表并尝试回显拓扑
onMounted(() => {
  loadDeviceList();
  restoreSavedTopology();
});

onUnmounted(() => {
  stopSimulationRunner('idle');
  animationUtils.disposeSimulationAnimations();
  animationUtils.disposeAllSimulationTokens();
});
</script>

<style lang="less">
.simulation-page {
  height: calc(100vh - 130px);
  display: flex;
  flex-direction: column;
  &.zx-content-wrap .el-card__body {
    height: 100%;
    .zx-content-wrap__content {
      height: 100%;
    }
  }
}

.simulation-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
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
</style>
