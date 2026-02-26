/**
 * 告警处理 Composable
 *
 * 管理告警的解析、定位和高亮显示
 */

interface AlarmReasonConfig {
  label: string;
  color: string;
}

interface Alarm {
  alarmType?: string;
  targetId?: string;
  targetEdgeId?: string;
  targetNodeId?: string;
  edgeId?: string;
  edgeIds?: string[];
  affectedNodes?: string[];
  affected_nodes?: string[];
  affectedNodeIds?: string[];
  details?: Record<string, any>;
  severity?: string;
}

interface AlarmTargets {
  nodeIds: string[];
  edgeIds: string[];
}

interface TopologyAnimation {
  highlightEdges: (edgeIds: string[], color: string) => void;
  clearEdgeHighlight: (edgeIds: string[]) => void;
  triggerErrorAnimation: (edgeId: string, duration: number) => void;
  setNodeError: (nodeId: string, isError: boolean) => void;
  setNodeActive: (nodeId: string, isActive: boolean, force?: boolean) => void;
}

interface UseAlarmHandlerOptions {
  getGraphInstance: () => any;
  topologyAnimation: TopologyAnimation;
}

/**
 * 告警类型映射配置
 */
export const ALARM_REASON_MAP: Record<string, AlarmReasonConfig> = {
  collision: { label: '冲突', color: '#ef4444' },
  multi_connection: { label: '冲突', color: '#ef4444' },
  packet_loss: { label: '丢包', color: '#f97316' },
  bandwidth_exceed: { label: '超载', color: '#f59e0b' },
  bandwidth_overflow: { label: '超载', color: '#f59e0b' },
  congestion: { label: '超载', color: '#f59e0b' },
  value_overflow: { label: '超载', color: '#f59e0b' },
  disconnect: { label: '链路断开', color: '#60a5fa' },
  link_down: { label: '链路断开', color: '#60a5fa' },
  device_failure: { label: '链路断开', color: '#60a5fa' },
};

// 告警高亮持续时间
export const ALARM_HIGHLIGHT_DURATION = 2800;

/**
 * 告警处理 Composable
 * @param {Object} options 配置选项
 * @param {Function} options.getGraphInstance - 获取图实例的函数
 * @param {Object} options.topologyAnimation - 拓扑动画对象
 */
export function useAlarmHandler(options: UseAlarmHandlerOptions) {
  const { getGraphInstance, topologyAnimation } = options;
  const { highlightEdges, clearEdgeHighlight, triggerErrorAnimation, setNodeError, setNodeActive } =
    topologyAnimation;

  /**
   * 获取告警原因配置
   * @param {string} alarmType - 告警类型
   * @returns {Object} 告警配置
   */
  function getAlarmReason(alarmType?: string): AlarmReasonConfig {
    const key = (alarmType || '').toLowerCase();
    return ALARM_REASON_MAP[key] || { label: '告警', color: '#94a3b8' };
  }

  /**
   * 收集告警关联的目标（节点和边）
   * @param {Object} alarm - 告警对象
   * @returns {Object} { nodeIds: string[], edgeIds: string[] }
   */
  function collectAlarmTargets(alarm: Alarm): AlarmTargets {
    const graph = getGraphInstance();
    const nodeIds = new Set<string>();
    const edgeIds = new Set<string>();

    if (!graph || !alarm) {
      return { nodeIds: [], edgeIds: [] };
    }

    const addByCell = (cellId?: string) => {
      if (!cellId) return;
      const cell = graph.getCellById(cellId);
      if (!cell) return;
      if (cell.isEdge?.()) {
        edgeIds.add(cellId);
      } else {
        nodeIds.add(cellId);
      }
    };

    addByCell(alarm.targetId);
    addByCell(alarm.targetEdgeId);
    addByCell(alarm.targetNodeId);

    if (alarm.edgeId) {
      edgeIds.add(alarm.edgeId);
    }
    if (Array.isArray(alarm.edgeIds)) {
      alarm.edgeIds.forEach((id) => id && edgeIds.add(id));
    }

    // 兼容驼峰和下划线两种格式
    const affectedNodesList = alarm.affectedNodes || alarm.affected_nodes || [];
    if (Array.isArray(affectedNodesList)) {
      affectedNodesList.forEach((id) => id && nodeIds.add(id));
    }
    if (Array.isArray(alarm.affectedNodeIds)) {
      alarm.affectedNodeIds.forEach((id) => id && nodeIds.add(id));
    }

    const details = alarm.details || {};
    addByCell(details.edgeId || details.edge_id);

    // 优先处理 details 中的 nodeId
    const detailNodeId = details.nodeId || details.node_id;
    if (detailNodeId) {
      nodeIds.add(detailNodeId);
    }

    if (Array.isArray(details.connections)) {
      details.connections.forEach((conn: any) => {
        const connEdgeId = conn?.edgeId || conn?.edge_id;
        if (connEdgeId) {
          edgeIds.add(connEdgeId);
        }
      });
    }

    // 通过端口ID查找关联的节点和边
    const portId = details.portId || details.port_id;
    if (portId) {
      const edges = graph.getEdges?.() || [];
      edges.forEach((edge: any) => {
        const sourcePortId = edge.getSourcePortId?.();
        const targetPortId = edge.getTargetPortId?.();
        if (sourcePortId === portId || targetPortId === portId) {
          edgeIds.add(edge.id);
        }
      });
      // 如果还没有找到节点，通过端口遍历节点查找
      if (nodeIds.size === 0) {
        const nodes = graph.getNodes?.() || [];
        nodes.forEach((node: any) => {
          const data = node.getData?.() || {};
          const ports = data.ports || [];
          const hit = ports.some((p: any) => p.id === portId);
          if (hit) {
            nodeIds.add(node.id);
          }
        });
      }
    }

    // 如果有节点但没有边，补充与节点相关的边
    if (nodeIds.size > 0 && edgeIds.size === 0) {
      const edges = graph.getEdges?.() || [];
      edges.forEach((edge: any) => {
        const sourceId = edge.getSourceCellId?.();
        const targetId = edge.getTargetCellId?.();
        if (nodeIds.has(sourceId) || nodeIds.has(targetId)) {
          edgeIds.add(edge.id);
        }
      });
    }

    // 如果有多个节点，补充节点之间的边
    if (nodeIds.size >= 2) {
      const edges = graph.getEdges?.() || [];
      edges.forEach((edge: any) => {
        const sourceId = edge.getSourceCellId?.();
        const targetId = edge.getTargetCellId?.();
        if (nodeIds.has(sourceId) && nodeIds.has(targetId)) {
          edgeIds.add(edge.id);
        }
      });
    }

    return {
      nodeIds: Array.from(nodeIds),
      edgeIds: Array.from(edgeIds),
    };
  }

  /**
   * 处理告警点击
   * @param {Object} alarm - 告警对象
   */
  function handleAlarmClick(alarm: Alarm) {
    const graph = getGraphInstance();
    if (!graph) return;

    const reason = getAlarmReason(alarm?.alarmType);
    const { nodeIds, edgeIds } = collectAlarmTargets(alarm);

    // 优先聚焦到节点（告警通常关联到设备）
    const focusId = nodeIds[0] || edgeIds[0] || alarm?.targetId;

    if (focusId) {
      const cell = graph.getCellById(focusId);
      if (cell) {
        graph.centerCell(cell);
      }
    }

    // 高亮边（如果有）
    if (edgeIds.length > 0) {
      highlightEdges(edgeIds, reason.color);
      setTimeout(() => clearEdgeHighlight(edgeIds), ALARM_HIGHLIGHT_DURATION);
      if (alarm?.severity === 'error' || alarm?.severity === 'critical') {
        edgeIds.forEach((edgeId) => triggerErrorAnimation(edgeId, ALARM_HIGHLIGHT_DURATION));
      }
    }

    // 高亮节点（始终执行，即使没有边）
    if (nodeIds.length > 0) {
      nodeIds.forEach((nodeId) => {
        setNodeError(nodeId, true);
        // 同时设置节点为活跃状态增强视觉效果（force=true 强制生效）
        setNodeActive(nodeId, true, true);
      });
      setTimeout(() => {
        nodeIds.forEach((nodeId) => {
          setNodeError(nodeId, false);
          setNodeActive(nodeId, false, true);
        });
      }, ALARM_HIGHLIGHT_DURATION);
    }
  }

  /**
   * 处理告警过滤变化
   * @param {Object} filter - 过滤条件
   */
  function handleAlarmFilterChange(filter: Record<string, any>) {
    // 告警过滤逻辑（预留扩展）
  }

  return {
    // 常量
    ALARM_REASON_MAP,
    ALARM_HIGHLIGHT_DURATION,

    // 方法
    getAlarmReason,
    collectAlarmTargets,
    handleAlarmClick,
    handleAlarmFilterChange,
  };
}

export default useAlarmHandler;
