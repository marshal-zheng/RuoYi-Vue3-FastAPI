/**
 * 图形样式管理 Composable
 * 负责节点和边的样式控制、状态管理
 */
import { ref } from 'vue';

export function useGraphStyle() {
  const edgeOriginalStyles = new Map();

  // 节点状态样式配置
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

  // 边高亮样式配置
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

  /**
   * 判断是否为仿真令牌节点
   */
  function isSimulationToken(node) {
    const data = typeof node?.getData === 'function' ? node.getData() : node?.data;
    return Boolean(data?.isSimToken);
  }

  /**
   * 合并节点样式
   */
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

  /**
   * 应用节点状态
   */
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

  /**
   * 获取边的原始样式
   */
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

  /**
   * 应用边样式
   */
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

  /**
   * 恢复边的原始样式
   */
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

  /**
   * 高亮边
   */
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

  /**
   * 重置图的仿真状态
   */
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

  /**
   * 标记队列中的边
   */
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

  return {
    isSimulationToken,
    applyNodeState,
    highlightEdge,
    resetGraphSimulationState,
    markQueuedEdges,
  };
}
