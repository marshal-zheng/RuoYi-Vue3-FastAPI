/**
 * 仿真核心逻辑 Composable
 * 负责仿真流程控制、步骤管理、状态机
 */
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

// 边阶段序列配置
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

const SIMULATION_STEP_DURATION = 950;
const SIMULATION_LOOP_DELAY = 800; // 循环间隔延时

export function useSimulationCore({ graphStyleUtils, animationUtils }) {
  const simulationStatus = ref('idle');
  const simulationSteps = ref([]);
  const simulationPointer = ref(0);
  const simulationLoading = ref(false);
  const simulationNarration = ref(null);
  const simulationTimelinePhases = ref([]);
  const simulationResultPayload = ref(null);
  const simulationLoopCount = ref(0); // 仿真循环次数
  const simulationContinuousMode = ref(true); // 持续仿真模式

  const simulationRunner = {
    currentStepResolver: null,
    activeController: null,
    runningPromise: null,
  };

  /**
   * 导出节点名称
   */
  function deriveNodeName(node) {
    if (!node) {
      return '未命名节点';
    }
    const data = node.getData?.() || {};
    return data.name || data.label || data.deviceName || node.id || '未命名节点';
  }

  /**
   * 导出边总线类型
   */
  function deriveEdgeBusType(edge) {
    if (!edge) {
      return 'BUS';
    }
    const data = edge.getData?.() || {};
    const candidate =
      data.busType || data.interfaceType || data.protocolType || edge.attrs?.line?.busType;
    return candidate || 'BUS';
  }

  /**
   * 构建仿真步骤
   */
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
          graphStyleUtils.isSimulationToken(sourceNode) ||
          graphStyleUtils.isSimulationToken(targetNode)
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

  /**
   * 构建阶段时间线
   */
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

  /**
   * 更新仿真旁白
   */
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

  /**
   * 重置仿真旁白
   */
  function resetSimulationNarration() {
    simulationNarration.value = null;
  }

  /**
   * 宣布仿真调度
   */
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

  /**
   * 播放单个仿真步骤
   */
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
      graphStyleUtils.highlightEdge(step.edge, 'current');
      if (phaseMeta.sourceState) {
        graphStyleUtils.applyNodeState(step.sourceNode, phaseMeta.sourceState);
      }
      if (phaseMeta.targetState) {
        graphStyleUtils.applyNodeState(step.targetNode, phaseMeta.targetState);
      }
      const controller = animationUtils.animateEdgeToken(
        step.edge,
        step.direction,
        SIMULATION_STEP_DURATION,
        {
          onCompleted: () => {
            graphStyleUtils.highlightEdge(step.edge, 'completed');
            if (phaseMeta.postSourceState) {
              graphStyleUtils.applyNodeState(step.sourceNode, phaseMeta.postSourceState);
            }
            if (phaseMeta.postTargetState) {
              graphStyleUtils.applyNodeState(step.targetNode, phaseMeta.postTargetState);
            }
            finish({ interrupted: false });
          },
          onCancelled: () => {
            graphStyleUtils.highlightEdge(step.edge, 'queued');
            graphStyleUtils.applyNodeState(step.sourceNode, 'processing');
            finish({ interrupted: true });
          },
        },
        step.busType // 传递总线类型以显示不同颜色
      );
      simulationRunner.activeController = controller;
      if (!controller) {
        finish({ interrupted: true });
      }
    });
  }

  /**
   * 延时工具函数
   */
  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * 运行仿真流程（支持持续循环模式）
   */
  function runSimulationFlow() {
    if (simulationRunner.runningPromise) {
      return simulationRunner.runningPromise;
    }
    const runnerTask = (async () => {
      // 持续循环运行
      while (simulationStatus.value === 'running') {
        // 执行一轮完整的仿真步骤
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
        }

        // 一轮完成
        simulationLoopCount.value += 1;

        // 如果是持续模式，重置指针并继续循环
        if (simulationContinuousMode.value && simulationStatus.value === 'running') {
          // 更新旁白显示循环信息
          simulationNarration.value = {
            badge: `第${simulationLoopCount.value}轮`,
            title: '仿真持续运行中',
            description: `已完成 ${simulationLoopCount.value} 轮仿真，正在准备下一轮...`,
            busType: '',
          };

          // 重置图形状态，准备下一轮
          const graph = simulationSteps.value[0]?.edge?.model?.graph;
          if (graph) {
            graphStyleUtils.resetGraphSimulationState(graph);
            graphStyleUtils.markQueuedEdges(simulationSteps.value);
          }

          // 重置指针
          simulationPointer.value = 0;

          // 短暂延时后开始下一轮
          await delay(SIMULATION_LOOP_DELAY);
        } else {
          // 非持续模式，正常结束
          finalizeSimulation();
          simulationStatus.value = 'completed';
          return;
        }
      }
    })();
    simulationRunner.runningPromise = runnerTask.finally(() => {
      simulationRunner.runningPromise = null;
    });
    return simulationRunner.runningPromise;
  }

  /**
   * 完成仿真
   */
  function finalizeSimulation() {
    animationUtils.disposeSimulationAnimations();
    animationUtils.disposeAllSimulationTokens();
    simulationNarration.value = {
      badge: '完成',
      title: '仿真结束',
      description: '所有链路已完成握手、数据传输与结果确认，正在生成报表',
      busType: '',
    };
  }

  /**
   * 停止仿真运行器
   */
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
   * 队列仿真结果
   */
  function queueSimulationResult(payload) {
    simulationResultPayload.value = payload;
  }

  /**
   * 设置持续仿真模式
   */
  function setContinuousMode(enabled) {
    simulationContinuousMode.value = enabled;
  }

  /**
   * 重置仿真状态（用于重新开始）
   */
  function resetSimulationState() {
    simulationLoopCount.value = 0;
    simulationPointer.value = 0;
  }

  return {
    simulationStatus,
    simulationSteps,
    simulationPointer,
    simulationLoading,
    simulationNarration,
    simulationTimelinePhases,
    simulationResultPayload,
    simulationLoopCount,
    simulationContinuousMode,
    buildSimulationSteps,
    buildPhaseTimeline,
    announceSimulationSchedule,
    runSimulationFlow,
    stopSimulationRunner,
    queueSimulationResult,
    resetSimulationNarration,
    setContinuousMode,
    resetSimulationState,
  };
}
