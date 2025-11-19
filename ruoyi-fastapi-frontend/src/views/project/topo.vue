<template>
  <ZxContentWrap class="home">
    <XflowDAG
      ref="dagRef"
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
        <!-- <zx-button
          size="small"
          type="warning"
          :disabled="!canPauseSimulation"
          @click="handlePauseSimulation"
        >
          暂停
        </zx-button>
        <zx-button
          size="small"
          type="info"
          :disabled="!canResumeSimulation"
          @click="handleResumeSimulation"
        >
          继续
        </zx-button> -->
        <!-- <zx-button size="small" :disabled="!canResetSimulation" @click="handleResetSimulation">
          重置
        </zx-button> -->
        <zx-button size="small" type="primary" :disabled="loading" @click="handleSaveTopo">
          保存
        </zx-button>
      </template>
    </XflowDAG>

    <!-- 仿真状态面板 -->
    <zx-floating-panel
      v-if="simulationNarration"
      title="仿真进度"
      :position="{ top: '90px', left: '17%' }"
      :size="{ width: '360px', maxHeight: '240px' }"
      :collapsed-size="{ width: '48px', height: '48px' }"
      :default-collapsed="false"
    >
      <template #header>
        <div class="simulation-floating-panel__header">
          <el-tag :type="simulationNarration.badge === '完成' ? 'success' : 'primary'" size="small">
            {{ simulationNarration.badge }}
          </el-tag>
          <span class="simulation-floating-panel__header-title">仿真进度</span>
        </div>
      </template>
      <div class="simulation-floating-panel__content">
        <p class="simulation-floating-panel__title">{{ simulationNarration.title }}</p>
        <p class="simulation-floating-panel__desc">
          {{ simulationNarration.description }}
        </p>
        <p v-if="simulationNarration.busType" class="simulation-floating-panel__meta">
          <el-tag size="small" effect="plain">{{ simulationNarration.busType }}</el-tag>
        </p>
      </div>
    </zx-floating-panel>

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
import { listDevice } from '@/api/device/device';
import { saveProjectTopology, getProjectTopology } from '@/api/project/topology';
import { ElMessage } from 'element-plus';
import { getPortColor } from '@/constants/portColor';

const version = ref('3.9.0');
const simulationLoading = ref(false);
const simulationStatus = ref('idle');
const simulationSteps = ref([]);
const simulationPointer = ref(0);
const simulationRunner = {
  currentStepResolver: null,
  activeController: null,
  runningPromise: null,
};
const simulationResultPayload = ref(null);
const simulationNarration = ref(null);
const simulationTimelinePhases = ref([]);
const simulationArtifacts = {
  tokens: new Set(),
  animations: new Set(),
};
const edgeOriginalStyles = new Map();
const BUS_TYPES = ['RS422', 'RS485', 'CAN', 'LAN', '1553B'];

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
const layoutMode = ref('horizontal'); // 'vertical' | 'horizontal'

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

const nodeStateStyles = {
  idle: {
    borderColor: '#cbd5f5',
    backgroundColor: '#ffffff',
    boxShadow: '',
    opacity: 1,
  },
  active: {
    borderColor: '#16a34a',
    backgroundColor: '#f0fdf4',
    boxShadow: '0 0 8px rgba(22,163,74,0.45)',
    opacity: 1,
  },
  processing: {
    borderColor: '#f59e0b',
    backgroundColor: '#fffbeb',
    boxShadow: '0 0 8px rgba(245,158,11,0.5)',
    opacity: 1,
  },
  done: {
    borderColor: '#0ea5e9',
    backgroundColor: '#f0f9ff',
    boxShadow: '',
    opacity: 0.95,
  },
  error: {
    borderColor: '#dc2626',
    backgroundColor: '#fee2e2',
    boxShadow: '0 0 8px rgba(220,38,38,0.45)',
    opacity: 1,
  },
  sending: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
    boxShadow: '0 0 10px rgba(37,99,235,0.45)',
    opacity: 1,
  },
  receiving: {
    borderColor: '#7c3aed',
    backgroundColor: '#f5f3ff',
    boxShadow: '0 0 10px rgba(124,58,237,0.35)',
    opacity: 1,
  },
  synchronizing: {
    borderColor: '#14b8a6',
    backgroundColor: '#ecfeff',
    boxShadow: '0 0 10px rgba(20,184,166,0.4)',
    opacity: 1,
  },
};

const edgeHighlightStyles = {
  queued: {
    stroke: '#94a3b8',
    strokeWidth: 2,
    strokeDasharray: 6,
  },
  current: {
    stroke: '#22c55e',
    strokeWidth: 3,
    strokeDasharray: 0,
  },
};

const SIMULATION_STEP_DURATION = 950;
const SIMULATION_TOKEN_SIZE = 12;
const EDGE_PHASE_SEQUENCE = [
  {
    key: 'handshake',
    label: '建立握手',
    badge: '握手请求',
    direction: 'forward',
    sourceState: 'active',
    targetState: 'processing',
    postSourceState: 'processing',
    postTargetState: 'active',
    timelineTag: 'info',
    description: (sourceName, targetName, busType) =>
      `${sourceName} 通过 ${busType} 通道向 ${targetName} 发起握手，请求建立通信链路`,
  },
  {
    key: 'handshakeAck',
    label: '握手确认',
    badge: '握手确认',
    direction: 'reverse',
    sourceState: 'processing',
    targetState: 'active',
    postSourceState: 'active',
    postTargetState: 'processing',
    timelineTag: 'success',
    description: (sourceName, targetName) =>
      `${sourceName} 确认收到握手，返回确认信号，${targetName} 准备发送业务数据`,
  },
  {
    key: 'dataTransfer',
    label: '数据传输',
    badge: '数据传输',
    direction: 'forward',
    sourceState: 'sending',
    targetState: 'receiving',
    postSourceState: 'receiving',
    postTargetState: 'sending',
    timelineTag: 'primary',
    description: (sourceName, targetName, busType) =>
      `${sourceName} 正以 ${busType} 总线向 ${targetName} 推送任务数据包`,
  },
  {
    key: 'resultConfirm',
    label: '结果确认',
    badge: '结果确认',
    direction: 'reverse',
    sourceState: 'receiving',
    targetState: 'sending',
    postSourceState: 'done',
    postTargetState: 'done',
    timelineTag: 'warning',
    description: (sourceName, targetName) =>
      `${sourceName} 返回处理确认，${targetName} 完成闭环校验`,
  },
];
const EDGE_PHASE_META = EDGE_PHASE_SEQUENCE.reduce((acc, phase) => {
  acc[phase.key] = phase;
  return acc;
}, {});

function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

function clearGraphContent(graphInstance) {
  const graph = graphInstance || getGraphInstance();
  if (graph && typeof graph.clearCells === 'function') {
    graph.clearCells();
  }
}

function isSimulationToken(node) {
  const data = typeof node?.getData === 'function' ? node.getData() : node?.data;
  return Boolean(data?.isSimToken);
}

function mergeNodeStyle(currentStyle, preset) {
  const nextStyle = { ...(currentStyle || {}) };
  if (preset.borderColor) {
    nextStyle.borderColor = preset.borderColor;
  } else if (nextStyle.borderColor) {
    delete nextStyle.borderColor;
  }
  if (preset.backgroundColor) {
    nextStyle.backgroundColor = preset.backgroundColor;
  } else if (nextStyle.backgroundColor) {
    delete nextStyle.backgroundColor;
  }
  if (preset.boxShadow !== undefined) {
    nextStyle.boxShadow = preset.boxShadow;
  } else if (nextStyle.boxShadow) {
    delete nextStyle.boxShadow;
  }
  if (preset.opacity !== undefined) {
    nextStyle.opacity = preset.opacity;
  } else if (nextStyle.opacity) {
    delete nextStyle.opacity;
  }
  return nextStyle;
}

function applyNodeState(node, state) {
  if (!node || isSimulationToken(node)) {
    return;
  }
  const data = node.getData?.() || {};
  const preset = nodeStateStyles[state] || nodeStateStyles.idle;
  const nextStyle = mergeNodeStyle(data.style, preset);
  node.setData(
    {
      ...data,
      simState: state,
      style: nextStyle,
    },
    { overwrite: false }
  );
}

function getEdgeOriginalStyle(edge) {
  if (!edge) {
    return null;
  }
  if (!edgeOriginalStyles.has(edge.id)) {
    const attrs = edge.getAttrs?.() || {};
    const line = attrs.line || {};
    edgeOriginalStyles.set(edge.id, {
      stroke: line.stroke,
      strokeWidth: line.strokeWidth,
      strokeDasharray: line.strokeDasharray,
      targetMarker: line.targetMarker,
    });
  }
  return edgeOriginalStyles.get(edge.id);
}

function applyEdgeStyle(edge, overrides = {}) {
  if (!edge) {
    return;
  }
  const original = getEdgeOriginalStyle(edge) || {};
  let resolvedMarker;
  if (overrides.targetMarker === null) {
    resolvedMarker = null;
  } else if (overrides.targetMarker !== undefined) {
    resolvedMarker = overrides.targetMarker;
  } else {
    resolvedMarker = original.targetMarker;
  }
  edge.attr({
    line: {
      stroke: overrides.stroke ?? original.stroke ?? '#c2c8d5',
      strokeWidth: overrides.strokeWidth ?? original.strokeWidth ?? 1.6,
      strokeDasharray: overrides.strokeDasharray ?? original.strokeDasharray ?? 0,
      targetMarker: resolvedMarker || null,
    },
  });
}

function restoreEdgeStyle(edge) {
  const original = getEdgeOriginalStyle(edge);
  if (!original) {
    return;
  }
  edge.attr({
    line: {
      stroke: original.stroke ?? '#c2c8d5',
      strokeWidth: original.strokeWidth ?? 1.6,
      strokeDasharray: original.strokeDasharray ?? 0,
      targetMarker: original.targetMarker || null,
    },
  });
}

function highlightEdge(edge, mode) {
  if (!edge) {
    return;
  }
  if (!mode || mode === 'idle' || mode === 'completed') {
    restoreEdgeStyle(edge);
    return;
  }
  const preset = edgeHighlightStyles[mode];
  if (!preset) {
    restoreEdgeStyle(edge);
    return;
  }
  applyEdgeStyle(edge, preset);
}

function deriveNodeName(node) {
  if (!node) {
    return '未命名节点';
  }
  const data = node.getData?.() || {};
  return data.name || data.label || data.deviceName || node.id || '未命名节点';
}

function deriveEdgeBusType(edge) {
  if (!edge) {
    return 'BUS';
  }
  const data = edge.getData?.() || {};
  const candidate =
    data.busType || data.interfaceType || data.protocolType || edge.attrs?.line?.busType;
  return candidate || 'BUS';
}

function buildPhaseTimeline(steps) {
  if (!Array.isArray(steps) || !steps.length) {
    return [];
  }
  return steps.map((step, index) => {
    const meta = EDGE_PHASE_META[step.phase] || {};
    return {
      id: `${step.id}-${step.phase}-${index}`,
      title: `${meta.label || '阶段'}｜${step.sourceName} → ${step.targetName}`,
      description: step.description,
      timestamp: `${((index + 1) * 0.8).toFixed(1)} s`,
      busTypeTag: meta.timelineTag || 'info',
    };
  });
}

function updateSimulationNarration(step) {
  const meta = EDGE_PHASE_META[step?.phase];
  if (!meta) {
    return;
  }
  simulationNarration.value = {
    badge: meta.badge,
    title: `${meta.label}｜${step.sourceName} → ${step.targetName}`,
    description: step.description,
    busType: step.busType,
  };
}

function resetSimulationNarration() {
  simulationNarration.value = null;
}

function announceSimulationSchedule(steps) {
  if (!Array.isArray(steps) || !steps.length) {
    return;
  }
  const edgeCount = new Set(steps.map((item) => item.id)).size;
  simulationNarration.value = {
    badge: '排程',
    title: '仿真路径已生成',
    description: `检测到 ${edgeCount} 条链路，共 ${steps.length} 个阶段，将展示握手、数据传输与确认全过程`,
    busType: '',
  };
}

function resetGraphSimulationState(graph) {
  if (!graph) {
    return;
  }
  const nodes = graph.getNodes?.() || [];
  nodes.forEach((node) => {
    if (isSimulationToken(node)) {
      node.remove?.();
      return;
    }
    applyNodeState(node, 'idle');
  });
  const edges = graph.getEdges?.() || [];
  edges.forEach((edge) => {
    highlightEdge(edge, 'idle');
  });
}

function registerSimulationToken(token) {
  if (token) {
    simulationArtifacts.tokens.add(token);
  }
}

function disposeSimulationToken(token) {
  if (token) {
    token.remove?.();
    simulationArtifacts.tokens.delete(token);
  }
}

function disposeAllSimulationTokens() {
  simulationArtifacts.tokens.forEach((token) => {
    token.remove?.();
  });
  simulationArtifacts.tokens.clear();
}

function disposeSimulationAnimations() {
  simulationArtifacts.animations.forEach((controller) => {
    if (typeof controller?.cancel === 'function') {
      controller.cancel();
    }
  });
  simulationArtifacts.animations.clear();
}

function createSimulationToken(graph, startPoint) {
  if (!graph || !startPoint) {
    return null;
  }
  const halfSize = SIMULATION_TOKEN_SIZE / 2;
  const token = graph.addNode({
    shape: 'circle',
    width: SIMULATION_TOKEN_SIZE,
    height: SIMULATION_TOKEN_SIZE,
    x: startPoint.x - halfSize,
    y: startPoint.y - halfSize,
    zIndex: 1000,
    attrs: {
      body: {
        fill: '#f97316',
        stroke: '#ffffff',
        strokeWidth: 2,
      },
    },
    data: {
      isSimToken: true,
    },
    rotatable: false,
    draggable: false,
    resizable: false,
  });
  registerSimulationToken(token);
  return token;
}

function animateEdgeToken(
  edge,
  direction = 'forward',
  duration = SIMULATION_STEP_DURATION,
  callbacks = {}
) {
  const graph = getGraphInstance();
  if (!graph || !edge) {
    if (callbacks.onCancelled) {
      callbacks.onCancelled();
    }
    return null;
  }
  const edgeView = graph.findViewByCell?.(edge);
  const pathElement =
    edgeView?.container?.querySelector?.('path[data-edge-path="1"]') ||
    edgeView?.container?.querySelector?.('path');
  const pathTotalLength =
    typeof pathElement?.getTotalLength === 'function' ? pathElement.getTotalLength() : 0;
  const sourcePoint = edge.getSourcePoint?.();
  const targetPoint = edge.getTargetPoint?.();
  if (!pathElement && (!sourcePoint || !targetPoint)) {
    if (callbacks.onCancelled) {
      callbacks.onCancelled();
    }
    return null;
  }
  const startPoint = direction === 'forward' ? sourcePoint : targetPoint;
  const token = createSimulationToken(graph, startPoint);
  if (!token) {
    if (callbacks.onCancelled) {
      callbacks.onCancelled();
    }
    return null;
  }
  const state = {
    rafId: 0,
    cancelled: false,
    startTs: 0,
  };
  const controller = {
    cancel() {
      if (state.cancelled) {
        return;
      }
      state.cancelled = true;
      if (state.rafId) {
        cancelAnimationFrame(state.rafId);
      }
      disposeSimulationToken(token);
      simulationArtifacts.animations.delete(controller);
      if (callbacks.onCancelled) {
        callbacks.onCancelled();
      }
    },
  };
  const stepFrame = (timestamp) => {
    if (state.cancelled) {
      return;
    }
    if (!state.startTs) {
      state.startTs = timestamp;
    }
    const progress = Math.min((timestamp - state.startTs) / duration, 1);
    const travelProgress = direction === 'forward' ? progress : 1 - progress;
    const halfSize = SIMULATION_TOKEN_SIZE / 2;
    let x = 0;
    let y = 0;
    if (pathElement && pathTotalLength > 0) {
      const point = pathElement.getPointAtLength(pathTotalLength * travelProgress);
      x = point.x - halfSize;
      y = point.y - halfSize;
    } else if (sourcePoint && targetPoint) {
      if (direction === 'forward') {
        x = sourcePoint.x + (targetPoint.x - sourcePoint.x) * progress - halfSize;
        y = sourcePoint.y + (targetPoint.y - sourcePoint.y) * progress - halfSize;
      } else {
        x = targetPoint.x + (sourcePoint.x - targetPoint.x) * progress - halfSize;
        y = targetPoint.y + (sourcePoint.y - targetPoint.y) * progress - halfSize;
      }
    }
    token.position(x, y);
    if (progress >= 1) {
      disposeSimulationToken(token);
      simulationArtifacts.animations.delete(controller);
      if (callbacks.onCompleted) {
        callbacks.onCompleted();
      }
      return;
    }
    state.rafId = requestAnimationFrame(stepFrame);
  };
  state.rafId = requestAnimationFrame(stepFrame);
  simulationArtifacts.animations.add(controller);
  return controller;
}

function buildSimulationSteps(graph) {
  const edges = graph?.getEdges?.() || [];
  const orderedSteps = edges
    .map((edge, index) => {
      const sourceId = edge.getSourceCellId?.();
      const targetId = edge.getTargetCellId?.();
      if (!sourceId || !targetId) {
        return null;
      }
      const sourceNode = graph.getCellById?.(sourceId);
      const targetNode = graph.getCellById?.(targetId);
      if (
        !sourceNode ||
        !targetNode ||
        isSimulationToken(sourceNode) ||
        isSimulationToken(targetNode)
      ) {
        return null;
      }
      const order = edge.getData?.()?.simOrder ?? index;
      return {
        id: edge.id,
        edge,
        sourceNode,
        targetNode,
        order,
        sourceName: deriveNodeName(sourceNode),
        targetName: deriveNodeName(targetNode),
        busType: deriveEdgeBusType(edge),
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.order - b.order);

  const expandedSteps = [];
  orderedSteps.forEach((connection) => {
    EDGE_PHASE_SEQUENCE.forEach((phase) => {
      const isForward = phase.direction === 'forward';
      const actualSourceNode = isForward ? connection.sourceNode : connection.targetNode;
      const actualTargetNode = isForward ? connection.targetNode : connection.sourceNode;
      const sourceName = isForward ? connection.sourceName : connection.targetName;
      const targetName = isForward ? connection.targetName : connection.sourceName;
      const description = phase.description
        ? phase.description(sourceName, targetName, connection.busType)
        : `${sourceName} → ${targetName}`;
      expandedSteps.push({
        id: connection.id,
        edge: connection.edge,
        sourceNode: actualSourceNode,
        targetNode: actualTargetNode,
        sourceName,
        targetName,
        order: connection.order,
        direction: isForward ? 'forward' : 'reverse',
        phase: phase.key,
        description,
        busType: connection.busType,
        badge: phase.badge,
        timelineTag: phase.timelineTag,
      });
    });
  });
  return expandedSteps;
}

function markQueuedEdges(steps) {
  const markedEdges = new Set();
  steps.forEach((step) => {
    if (!markedEdges.has(step.id)) {
      highlightEdge(step.edge, 'queued');
      markedEdges.add(step.id);
    }
  });
  const firstStep = steps[0];
  if (firstStep) {
    applyNodeState(firstStep.sourceNode, 'active');
  }
}

function queueSimulationResult(payload) {
  simulationResultPayload.value = payload;
}

function presentSimulationResult() {
  if (!simulationResultPayload.value) {
    return;
  }
  simulationDialogRef.value?.open(simulationResultPayload.value);
}

function handleReopenSimulationDialog() {
  if (!simulationResultPayload.value) {
    ElMessage.warning('暂无仿真结果，请先执行仿真');
    return;
  }
  simulationDialogRef.value?.open(simulationResultPayload.value);
}

function playSimulationStep(step) {
  return new Promise((resolve) => {
    if (!step?.edge) {
      resolve({ interrupted: true });
      return;
    }
    let settled = false;
    const finish = (payload) => {
      if (settled) {
        return;
      }
      settled = true;
      simulationRunner.currentStepResolver = null;
      simulationRunner.activeController = null;
      resolve(payload);
    };
    simulationRunner.currentStepResolver = finish;
    const phaseMeta = EDGE_PHASE_META[step.phase] || {};
    updateSimulationNarration(step);
    highlightEdge(step.edge, 'current');
    if (phaseMeta.sourceState) {
      applyNodeState(step.sourceNode, phaseMeta.sourceState);
    }
    if (phaseMeta.targetState) {
      applyNodeState(step.targetNode, phaseMeta.targetState);
    }
    const controller = animateEdgeToken(step.edge, step.direction, SIMULATION_STEP_DURATION, {
      onCompleted: () => {
        highlightEdge(step.edge, 'completed');
        if (phaseMeta.postSourceState) {
          applyNodeState(step.sourceNode, phaseMeta.postSourceState);
        }
        if (phaseMeta.postTargetState) {
          applyNodeState(step.targetNode, phaseMeta.postTargetState);
        }
        finish({ interrupted: false });
      },
      onCancelled: () => {
        highlightEdge(step.edge, 'queued');
        applyNodeState(step.sourceNode, 'processing');
        finish({ interrupted: true });
      },
    });
    simulationRunner.activeController = controller;
    if (!controller) {
      finish({ interrupted: true });
    }
  });
}

function runSimulationFlow() {
  if (simulationRunner.runningPromise) {
    return simulationRunner.runningPromise;
  }
  const runnerTask = (async () => {
    while (simulationPointer.value < simulationSteps.value.length) {
      if (simulationStatus.value !== 'running') {
        return;
      }
      const step = simulationSteps.value[simulationPointer.value];
      const result = await playSimulationStep(step);
      if (result?.interrupted) {
        return;
      }
      simulationPointer.value += 1;
      if (simulationPointer.value >= simulationSteps.value.length) {
        applyNodeState(step.targetNode, 'done');
      }
    }
    finalizeSimulation();
    simulationStatus.value = 'completed';
  })();
  simulationRunner.runningPromise = runnerTask.finally(() => {
    simulationRunner.runningPromise = null;
  });
  return simulationRunner.runningPromise;
}

function finalizeSimulation() {
  const graph = getGraphInstance();
  if (!graph) {
    return;
  }
  disposeSimulationAnimations();
  disposeAllSimulationTokens();
  const nodes = graph.getNodes?.() || [];
  nodes.forEach((node) => {
    if (isSimulationToken(node)) {
      return;
    }
    applyNodeState(node, 'done');
  });
  const edges = graph.getEdges?.() || [];
  edges.forEach((edge) => {
    highlightEdge(edge, 'completed');
  });
  simulationNarration.value = {
    badge: '完成',
    title: '仿真结束',
    description: '所有链路已完成握手、数据传输与结果确认，正在生成报表',
    busType: '',
  };
  presentSimulationResult();
}

function stopSimulationRunner(nextStatus) {
  if (simulationRunner.activeController?.cancel) {
    simulationRunner.activeController.cancel();
  }
  if (typeof simulationRunner.currentStepResolver === 'function') {
    simulationRunner.currentStepResolver({ interrupted: true });
  }
  simulationRunner.activeController = null;
  simulationRunner.currentStepResolver = null;
  simulationRunner.runningPromise = null;
  if (nextStatus) {
    simulationStatus.value = nextStatus;
  }
  if (nextStatus === 'idle') {
    resetSimulationNarration();
  }
}

/**
 * 解析端口方向，兼容中英文配置
 * @param {Object} intf - 接口数据
 * @returns {String} 方向标识
 */
function resolvePortDirection(intf) {
  const source = intf?.direction || intf?.params?.direction;
  const text = String(source || '').toLowerCase();
  if (text.includes('入') || text === 'input' || text === 'in') {
    return 'input';
  }
  if (text.includes('出') || text === 'output' || text === 'out') {
    return 'output';
  }
  return 'bidirectional';
}

function normalizeBusType(type) {
  if (!type) return '';
  return String(type).toUpperCase();
}

function inferConnectionBusType(sourcePort, targetPort, index) {
  const candidate = normalizeBusType(
    sourcePort?.busType ||
      sourcePort?.interfaceType ||
      sourcePort?.protocolType ||
      targetPort?.busType ||
      targetPort?.interfaceType ||
      targetPort?.protocolType
  );
  if (candidate && BUS_TYPES.includes(candidate)) {
    return candidate;
  }
  return BUS_TYPES[index % BUS_TYPES.length];
}

function ensurePortSummary(portId, ports, fallbackName, index, assignedBusType) {
  const port = Array.isArray(ports) ? ports.find((item) => item.id === portId) : null;
  if (port) {
    const declaredType =
      normalizeBusType(port.busType || port.interfaceType || port.protocolType) || assignedBusType;
    return {
      id: port.id || portId,
      name: port.interfaceName || port.interfaceLabel || `端口${index + 1}`,
      busType: declaredType || BUS_TYPES[index % BUS_TYPES.length],
    };
  }
  return {
    id: portId || `virtual-${index}`,
    name: fallbackName,
    busType: assignedBusType || BUS_TYPES[index % BUS_TYPES.length],
  };
}

function buildSimulationSummary(nodes, edges) {
  const coverage = new Set();
  edges.forEach((edge) => {
    if (edge.busType) {
      coverage.add(edge.busType);
    }
  });
  return {
    deviceCount: nodes.length,
    connectionCount: edges.length,
    busCoverage: BUS_TYPES.map((type) => ({
      name: type,
      active: coverage.has(type),
    })),
    generatedAt: new Date().toLocaleString(),
  };
}

function generateDesignFilePayload(projectName, versionName, nodes, edges) {
  const header = [
    '# === Bus Communication Design File ===',
    `# Project: ${projectName || '-'}`,
    `# Version: ${versionName || version.value}`,
    `# Generated: ${new Date().toISOString()}`,
    '',
    'BUS_ID,LINK_NAME,SOURCE_DEVICE,SOURCE_PORT,TARGET_DEVICE,TARGET_PORT,BUS_TYPE,DATA_RATE,REMARK',
  ];

  const lines = edges.map((edge, index) => {
    return [
      `BUS-${index + 1}`,
      `${edge.sourceDevice}-${edge.targetDevice}`,
      edge.sourceDevice,
      edge.sourcePort.name,
      edge.targetDevice,
      edge.targetPort.name,
      edge.busType,
      edge.dataRate,
      edge.remark,
    ].join(',');
  });

  return header.concat(lines).join('\n');
}

function generateIcdFilePayload(projectName, versionName, nodes, edges) {
  const header = [
    '# === Interface Control Document ===',
    `# Project: ${projectName || '-'}`,
    `# Version: ${versionName || version.value}`,
    `# Generated: ${new Date().toISOString()}`,
    '',
    'DEVICE,PORT_ID,PORT_NAME,BUS_TYPE,PEER_DEVICE,PEER_PORT,PROTOCOL,DATA_RATE',
  ];

  const lines = edges.flatMap((edge) => {
    return [
      [
        edge.sourceDevice,
        edge.sourcePort.id,
        edge.sourcePort.name,
        edge.busType,
        edge.targetDevice,
        edge.targetPort.name,
        edge.protocolType,
        edge.dataRate,
      ].join(','),
      [
        edge.targetDevice,
        edge.targetPort.id,
        edge.targetPort.name,
        edge.busType,
        edge.sourceDevice,
        edge.sourcePort.name,
        edge.protocolType,
        edge.dataRate,
      ].join(','),
    ];
  });

  return header.concat(lines).join('\n');
}

function generateSimulationTimeline(edges) {
  return edges.map((edge, index) => {
    const delayMs = (index + 1) * 0.6;
    const color = ['primary', 'success', 'warning', 'danger', 'info'][index % 5];
    return {
      id: edge.id,
      title: `${edge.sourceDevice} → ${edge.targetDevice}`,
      description: `${edge.busType} 链路通过 ${edge.protocolType || '自定义协议'} 完成数据握手，速率 ${edge.dataRate}`,
      timestamp: `${delayMs.toFixed(1)} s`,
      busTypeTag: color,
    };
  });
}

function buildSimulationPayload() {
  const graph = getGraphInstance();
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const nodes = (graph.getNodes?.() || [])
    .filter((node) => !isSimulationToken(node))
    .map((node, index) => {
      const data = node.getData?.() || {};
      return {
        id: node.id,
        name: data.name || data.label || `节点${index + 1}`,
        type: data.deviceType || data.nodeType || 'device',
        ports: data.ports || [],
      };
    });

  const edges = (graph.getEdges?.() || [])
    .map((edge, index) => {
      const sourceId = edge.getSourceCellId?.();
      const targetId = edge.getTargetCellId?.();
      const sourcePortId = edge.getSourcePortId?.();
      const targetPortId = edge.getTargetPortId?.();

      const sourceNode = nodes.find((node) => node.id === sourceId);
      const targetNode = nodes.find((node) => node.id === targetId);

      if (!sourceNode || !targetNode) {
        return null;
      }

      const sourcePortRaw = sourceNode.ports?.find((item) => item.id === sourcePortId);
      const targetPortRaw = targetNode.ports?.find((item) => item.id === targetPortId);

      const assignedBusType = inferConnectionBusType(sourcePortRaw, targetPortRaw, index);

      const sourcePort = ensurePortSummary(
        sourcePortId,
        sourceNode.ports,
        `端口${index + 1}`,
        index,
        assignedBusType
      );
      const targetPort = ensurePortSummary(
        targetPortId,
        targetNode.ports,
        `端口${index + 1}`,
        index,
        assignedBusType
      );

      return {
        id: edge.id,
        sourceId,
        targetId,
        sourceDevice: sourceNode.name,
        targetDevice: targetNode.name,
        sourcePort,
        targetPort,
        busType: assignedBusType,
        protocolType: sourcePortRaw?.protocolType || targetPortRaw?.protocolType || '自定义协议',
        dataRate: sourcePortRaw?.dataRate || targetPortRaw?.dataRate || '32Mbps',
        remark: '仿真示例链路',
      };
    })
    .filter(Boolean);

  return { nodes, edges };
}

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

  const { nodes: nodePayload, edges: edgePayload } = buildSimulationPayload();
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

  disposeSimulationAnimations();
  disposeAllSimulationTokens();
  resetGraphSimulationState(graph);
  markQueuedEdges(steps);
  simulationSteps.value = steps;
  simulationTimelinePhases.value = buildPhaseTimeline(steps);
  announceSimulationSchedule(steps);
  simulationPointer.value = 0;
  simulationStatus.value = 'running';

  const summary = buildSimulationSummary(nodePayload, edgePayload);
  const designContent = generateDesignFilePayload(
    '多总线仿真工程',
    version.value,
    nodePayload,
    edgePayload
  );
  const icdContent = generateIcdFilePayload(
    '多总线仿真工程',
    version.value,
    nodePayload,
    edgePayload
  );
  const timeline =
    simulationTimelinePhases.value?.length > 0
      ? simulationTimelinePhases.value
      : generateSimulationTimeline(edgePayload);

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
  runSimulationFlow();
}

/**
 * 转换设备接口数据为端口格式
 * @param {Array} interfaces - 接口列表
 * @returns {Array} 端口列表
 */
function convertInterfacesToPorts(interfaces) {
  if (!interfaces || !Array.isArray(interfaces)) {
    return [];
  }

  return interfaces.map((intf, index) => {
    // 总线类型用于展示和配色
    const busType = intf.interfaceType || intf.busType || 'RS422';

    // 使用接口自身的布局位置，保持与设备配置一致
    const position = String(intf.position || '').toLowerCase();
    const validGroups = ['left', 'right', 'top', 'bottom'];
    const group = validGroups.includes(position) ? position : 'right';

    const rawProtocol = intf.protocolConfig || intf.messageConfig || null;
    const protocolConfig = rawProtocol ? JSON.parse(JSON.stringify(rawProtocol)) : {};
    const protocolType =
      intf.protocolType || protocolConfig.protocolType || protocolConfig.type || '';
    const dataRate = intf.dataRate || intf.params?.dataRate || protocolConfig.dataRate || '';

    return {
      id: `port-${intf.interfaceId || index}`,
      interfaceId: intf.interfaceId,
      interfaceName: intf.interfaceName || `端口${index + 1}`,
      interfaceType: busType, // 与设备管理保持一致
      busType: busType,
      direction: resolvePortDirection(intf),
      group: group,
      description: intf.description || intf.remark || '',
      color: getPortColor(busType),
      dataRate,
      protocolType,
      protocolConfig,
      messageConfig: protocolConfig,
      params: intf.params || {},
    };
  });
}

/**
 * 从后端加载设备列表数据
 */
async function loadDeviceList() {
  loading.value = true;
  try {
    // 从后端获取设备列表
    const response = await listDevice({});
    const devices = response?.rows || [];

    if (devices.length === 0) {
      operators.value = [];
      return;
    }
    // 确保端口数据存在，若列表未返回则补充查询详情
    const devicesWithPorts = devices.map((device) => {
      const interfaces = Array.isArray(device.interfaces) ? device.interfaces : [];
      const ports = convertInterfacesToPorts(interfaces);

      return {
        // DAG组件需要的字段
        name: device.deviceName,
        value: device.remark || device.deviceDesc || '设备',
        category: device.categoryName || device.category || '未分类',

        // 设备原始数据（用于节点创建时使用）
        deviceId: device.deviceId,
        deviceType: device.deviceType,
        busType: device.busType,
        manufacturer: device.manufacturer,
        model: device.model,
        version: device.version,

        // 端口信息（用于连接桩）
        ports,

        // 节点类型标识
        nodeType: 'device-port-node',
      };
    });

    operators.value = devicesWithPorts;
  } catch (error) {
    void error;
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 根据当前节点构建端口到对端设备名的映射
 * @param {Object} node - 当前节点（X6 节点实例或其 JSON）
 * @returns {Record<string, string>} key 为端口 ID，value 为对端设备名称
 */
function buildPeerDeviceNameByPort(node) {
  const graph = dagRef.value?.getGraph();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];

  edges.forEach((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    if (!sourceId || !targetId) {
      return;
    }

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

    if (!localPortId || !peerNodeId) {
      return;
    }

    const peerNode = graph.getCellById(peerNodeId);
    const data = peerNode?.getData?.() || {};
    const deviceName = data.name || data.label || data.deviceName || '';

    if (deviceName) {
      result[localPortId] = deviceName;
    }
  });

  return result;
}

/**
 * 处理节点双击事件
 * @param {Object} params - 包含 node, event, type
 */
function handleNodeDblclick({ node }) {
  // 计算当前节点各端口对应的对端设备名称
  const peerDeviceNameByPort = buildPeerDeviceNameByPort(node);

  // 转为普通 JSON，确保包含 data / ports 等字段
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;

  // 保存当前节点数据（附加端口到对端设备名的映射）
  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
  };

  // 打开抽屉
  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 * @param {Object} params - 包含 nodeId, node, name, ports
 */
function handleNodeUpdate({ nodeId, name, ports }) {
  // 获取图实例
  const graph = dagRef.value?.getGraph();
  if (!graph) {
    ElMessage.error('更新失败：图实例不存在');
    return;
  }

  // 通过节点ID获取节点实例
  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) {
    ElMessage.error('更新失败：节点不存在');
    return;
  }

  // 获取当前节点数据
  const currentData = cellNode.getData() || {};

  // 更新节点数据（包含 label、name 和 ports 字段）
  const updatedData = {
    ...currentData,
    name: name,
    label: name,
    ports: ports || currentData.ports, // 更新端口信息（包含协议配置）
  };

  // 如果存在 properties.content 结构，也更新里面的 label
  if (currentData.properties?.content) {
    updatedData.properties = {
      ...currentData.properties,
      content: {
        ...currentData.properties.content,
        label: name,
      },
    };
  }

  // 使用 setData 方法更新节点数据
  // 节点组件会通过 watch 监听数据变化并自动重新渲染
  cellNode.setData(updatedData, { overwrite: false });

  // 如果需要更新到后端，可以在这里调用 API
  // await updateNodeName(nodeId, name)
  // await updateNodePorts(nodeId, ports)
}

/**
 * 构建设计保存用的拓扑数据 payload
 */
function buildTopologySavePayload() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('保存失败：图实例不存在');
    return null;
  }

  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    ElMessage.error('保存失败：缺少工程ID');
    return null;
  }

  const nodes = (graph.getNodes?.() || []).filter((node) => !isSimulationToken(node));
  const edges = graph.getEdges?.() || [];

  if (!nodes.length) {
    ElMessage.warning('请先在画布中放置设备节点');
    return null;
  }

  const graphJson = typeof graph.toJSON === 'function' ? graph.toJSON() : null;
  if (graphJson && Array.isArray(graphJson.cells)) {
    graphJson.cells = graphJson.cells.filter((cell) => !cell?.data?.isSimToken);
  }

  const nodeSummaries = nodes.map((node) => {
    const data = node.getData?.() || {};
    return {
      id: node.id,
      data,
    };
  });

  const edgeSummaries = edges.map((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    const sourcePortId = edge.getSourcePortId?.();
    const targetPortId = edge.getTargetPortId?.();
    return {
      id: edge.id,
      sourceId,
      targetId,
      sourcePortId,
      targetPortId,
    };
  });

  return {
    projectId: currentProjectId,
    versionId: getVersionIdNumber(),
    topologyData: {
      version: version.value,
      savedAt: new Date().toISOString(),
      graph: graphJson,
      nodes: nodeSummaries,
      edges: edgeSummaries,
    },
  };
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

  const payload = buildTopologySavePayload();
  if (!payload) {
    return;
  }

  saveProjectTopology(payload)
    .then(() => {
      ElMessage.success('拓扑保存成功');
      router.push(`/project/project-detail/index/${currentProjectId}`);
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

  const currentVersionId = getVersionIdNumber();

  const tryRestore = () => {
    const graph = dagRef.value?.getGraph?.();
    if (!graph) {
      setTimeout(tryRestore, 200);
      return;
    }

    clearGraphContent(graph);

    getProjectTopology(currentProjectId, currentVersionId)
      .then((res) => {
        const topo = res?.data;
        const topoData = topo?.topologyData;
        const graphJson = topoData?.graph;
        if (graphJson) {
          graph.fromJSON(graphJson);
        }
      })
      .catch(() => {});
  };

  tryRestore();
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
  disposeSimulationAnimations();
  disposeAllSimulationTokens();
});
</script>

<style lang="less">
.home {
  height: calc(100vh - 84px);
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

.simulation-floating-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.simulation-floating-panel__header-title {
  font-weight: 600;
  font-size: 14px;
}

.simulation-floating-panel__content {
  padding: 12px 0;
}

.simulation-floating-panel__title {
  font-weight: 600;
  margin: 0 0 8px;
  font-size: 14px;
  color: #1f2937;
}

.simulation-floating-panel__desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.simulation-floating-panel__meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
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
