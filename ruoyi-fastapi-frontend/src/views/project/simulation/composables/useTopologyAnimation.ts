/**
 * 拓扑动画 Composable
 *
 * 管理拓扑图上的动画效果：
 * - 链路光点动画（数据传输）
 * - 链路错误闪烁
 * - 节点呼吸灯效果
 */
import { ref, onUnmounted, type Ref } from 'vue';
import type { Graph } from '@antv/x6';
import type { SimulationNodeData } from './topology-types';

/**
 * 协议类型到颜色的映射
 */
export const PROTOCOL_COLORS: Record<string, string> = {
  '1553B': '#f97316', // 橙色
  'MIL-STD-1553B': '#f97316',
  CAN: '#3b82f6', // 蓝色
  RS422: '#22c55e', // 绿色
  RS485: '#22c55e', // 绿色
  LAN: '#e2e8f0', // 白色
  Ethernet: '#e2e8f0', // 白色
  default: '#94a3b8', // 灰色
};

/**
 * 获取协议对应的颜色
 * @param protocolType - 协议类型
 * @returns 颜色值
 */
export function getProtocolColor(protocolType: string): string {
  if (!protocolType) {
    return PROTOCOL_COLORS.default;
  }

  const normalizedType = protocolType.toUpperCase().replace(/[-_\s]/g, '');

  // 精确匹配
  if (PROTOCOL_COLORS[protocolType]) {
    return PROTOCOL_COLORS[protocolType];
  }

  // 模糊匹配
  if (normalizedType.includes('1553')) {
    return PROTOCOL_COLORS['1553B'];
  }
  if (normalizedType.includes('CAN')) {
    return PROTOCOL_COLORS['CAN'];
  }
  if (normalizedType.includes('RS422') || normalizedType.includes('RS485')) {
    return PROTOCOL_COLORS['RS422'];
  }
  if (normalizedType.includes('LAN') || normalizedType.includes('ETHERNET')) {
    return PROTOCOL_COLORS['LAN'];
  }

  return PROTOCOL_COLORS.default;
}

/**
 * 验证协议颜色映射的完整性
 * @param protocolTypes - 协议类型列表
 * @returns 是否所有协议都有对应颜色
 */
export function validateProtocolColors(protocolTypes: string[]): boolean {
  const colors = new Set<string>();

  for (const type of protocolTypes) {
    const color = getProtocolColor(type);
    if (color === PROTOCOL_COLORS.default) {
      return false;
    }
    colors.add(color);
  }

  // 确保不同协议映射到不同颜色
  return colors.size === protocolTypes.length;
}

/**
 * DAG 图实例接口（简化版）
 */
export type DagGraph = Pick<Graph, 'getCellById' | 'getEdges' | 'getNodes' | 'findViewByCell'>;

/**
 * DAG 组件引用接口
 */
export interface DagRef {
  getGraph?: () => DagGraph | null;
}

/**
 * 速度源类型
 */
export type SpeedSource = number | Ref<number> | (() => number) | { value: number } | null;

/**
 * 拓扑动画返回类型
 */
export interface UseTopologyAnimationReturn {
  isAnimating: Ref<boolean>;
  activeNodes: Ref<Set<string>>;
  activeEdges: Ref<Set<string>>;
  errorEdges: Ref<Set<string>>;
  startAnimation: () => void;
  stopAnimation: () => void;
  triggerTrafficAnimation: (edgeId: string, protocolType: string, duration?: number) => void;
  triggerErrorAnimation: (edgeId: string, duration?: number) => void;
  setNodeActive: (nodeId: string, active?: boolean, force?: boolean) => void;
  setNodeError: (nodeId: string, hasError?: boolean) => void;
  highlightEdges: (edgeIds: string[], color?: string) => void;
  clearEdgeHighlight: (edgeIds: string[]) => void;
  getProtocolColor: (protocolType: string) => string;
}

/**
 * 拓扑动画 Composable
 * @param dagRef - DAG 组件引用
 * @param speedSource - 速度倍率源
 * @returns 动画控制方法
 */
export function useTopologyAnimation(
  dagRef: Ref<DagRef | null>,
  speedSource: SpeedSource = null
): UseTopologyAnimationReturn {
  // 动画状态
  const isAnimating = ref<boolean>(false);
  const activeNodes = ref<Set<string>>(new Set());
  const activeEdges = ref<Set<string>>(new Set());
  const errorEdges = ref<Set<string>>(new Set());

  // 动画定时器
  const animationTimers = ref<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // 节流配置
  const THROTTLE_INTERVAL = 100; // 基准 100ms 节流

  // 上次动画触发时间
  const lastAnimationTime = ref<Map<string, number>>(new Map());

  /**
   * 当前速度倍率
   */
  function getSpeedFactor(): number {
    const val =
      typeof speedSource === 'function'
        ? speedSource()
        : speedSource && typeof speedSource === 'object' && 'value' in speedSource
          ? speedSource.value
          : speedSource;
    const num = Number(val) || 1;
    return Math.max(0.5, Math.min(num, 4));
  }

  /**
   * 获取图实例
   */
  function getGraph(): DagGraph | null {
    return dagRef.value?.getGraph?.() || null;
  }

  /**
   * 节流检查
   */
  function shouldThrottle(key: string): boolean {
    const now = Date.now();
    const factor = getSpeedFactor();
    const interval = Math.max(20, THROTTLE_INTERVAL / factor);
    const lastTime = lastAnimationTime.value.get(key) || 0;

    if (now - lastTime < interval) {
      return true;
    }

    lastAnimationTime.value.set(key, now);
    return false;
  }

  /**
   * 启动全局动画
   */
  function startAnimation(): void {
    isAnimating.value = true;
  }

  /**
   * 停止全局动画
   */
  function stopAnimation(): void {
    isAnimating.value = false;

    // 清除所有动画定时器
    animationTimers.value.forEach((timer) => clearTimeout(timer));
    animationTimers.value.clear();

    // 重置所有状态
    activeNodes.value.clear();
    activeEdges.value.clear();
    errorEdges.value.clear();

    // 重置图形样式
    const graph = getGraph();
    if (graph) {
      resetGraphStyles(graph);
    }
  }

  /**
   * 重置图形样式
   */
  function resetGraphStyles(graph: DagGraph): void {
    const edges = graph.getEdges?.() || [];
    const nodes = graph.getNodes?.() || [];

    edges.forEach((edge) => {
      edge.attr('line/stroke', '#b1b1b7');
      edge.attr('line/strokeWidth', 2);
      edge.attr('line/strokeDasharray', null);
    });

    nodes.forEach((node) => {
      // 通过 findViewByCell 获取节点视图
      const nodeView = graph.findViewByCell(node);
      if (nodeView && nodeView.container) {
        nodeView.container.classList.remove('node-breathing', 'node-error');
        // 重置 SVG 元素样式
        const svgEl = nodeView.container.querySelector<SVGElement>('rect, circle, ellipse, path');
        if (svgEl) {
          svgEl.style.stroke = '';
          svgEl.style.strokeWidth = '';
          svgEl.style.filter = '';
        }
      }
    });
  }

  /**
   * 触发链路流量动画
   * @param edgeId - 边ID
   * @param protocolType - 协议类型
   * @param duration - 动画持续时间（毫秒）
   */
  function triggerTrafficAnimation(
    edgeId: string,
    protocolType: string,
    duration: number = 1000
  ): void {
    if (!isAnimating.value) return;
    if (shouldThrottle(`traffic-${edgeId}`)) return;

    const graph = getGraph();
    if (!graph) return;

    const edge = graph.getCellById(edgeId);
    if (!edge) return;

    const color = getProtocolColor(protocolType);

    // 设置边的动画样式
    edge.attr('line/stroke', color);
    edge.attr('line/strokeWidth', 3);
    edge.attr('line/strokeDasharray', '5 5');

    // 添加到活跃边集合
    activeEdges.value.add(edgeId);

    // 创建光点动画（使用 CSS 动画）
    const edgeView = graph.findViewByCell(edge);
    if (edgeView) {
      const pathEl = edgeView.findOne('path');
      if (pathEl instanceof SVGElement) {
        pathEl.classList.add('edge-traffic-animation');
        pathEl.style.setProperty('--traffic-color', color);
      }
    }

    // 设置定时器恢复样式
    const factor = getSpeedFactor();
    const adjustedDuration = Math.max(200, duration / factor);

    const timerId = setTimeout(() => {
      edge.attr('line/stroke', '#b1b1b7');
      edge.attr('line/strokeWidth', 2);
      edge.attr('line/strokeDasharray', null);
      activeEdges.value.delete(edgeId);

      if (edgeView) {
        const pathEl = edgeView.findOne('path');
        if (pathEl) {
          pathEl.classList.remove('edge-traffic-animation');
        }
      }

      animationTimers.value.delete(edgeId);
    }, adjustedDuration);

    animationTimers.value.set(edgeId, timerId);
  }

  /**
   * 触发链路错误动画
   * @param edgeId - 边ID
   * @param duration - 动画持续时间（毫秒）
   */
  function triggerErrorAnimation(edgeId: string, duration: number = 2000): void {
    if (shouldThrottle(`error-${edgeId}`)) return;

    const graph = getGraph();
    if (!graph) return;

    const edge = graph.getCellById(edgeId);
    if (!edge) return;

    // 设置错误样式
    edge.attr('line/stroke', '#ef4444');
    edge.attr('line/strokeWidth', 4);

    // 添加到错误边集合
    errorEdges.value.add(edgeId);

    // 创建闪烁动画
    const edgeView = graph.findViewByCell(edge);
    if (edgeView) {
      const pathEl = edgeView.findOne('path');
      if (pathEl) {
        pathEl.classList.add('edge-error-animation');
      }
    }

    // 设置定时器恢复样式
    const factor = getSpeedFactor();
    const adjustedDuration = Math.max(300, duration / factor);

    const timerId = setTimeout(() => {
      edge.attr('line/stroke', '#b1b1b7');
      edge.attr('line/strokeWidth', 2);
      errorEdges.value.delete(edgeId);

      if (edgeView) {
        const pathEl = edgeView.findOne('path');
        if (pathEl) {
          pathEl.classList.remove('edge-error-animation');
        }
      }

      animationTimers.value.delete(`error-${edgeId}`);
    }, adjustedDuration);

    animationTimers.value.set(`error-${edgeId}`, timerId);
  }

  /**
   * 设置节点活跃状态（呼吸灯效果）
   * @param nodeId - 节点ID
   * @param active - 是否活跃
   * @param force - 是否强制设置（忽略 isAnimating 状态）
   */
  function setNodeActive(nodeId: string, active: boolean = true, force: boolean = false): void {
    // 如果不是强制模式且动画未启动，则跳过
    if (!force && !isAnimating.value && active) return;

    const graph = getGraph();
    if (!graph) return;

    const node = graph.getCellById(nodeId);
    if (!node) return;

    // 通过 findViewByCell 获取节点视图
    const nodeView = graph.findViewByCell(node);
    if (!nodeView || !nodeView.container) return;

    if (active) {
      activeNodes.value.add(nodeId);
      nodeView.container.classList.add('node-breathing');
    } else {
      activeNodes.value.delete(nodeId);
      nodeView.container.classList.remove('node-breathing');
    }
  }

  /**
   * 设置节点错误状态
   * @param nodeId - 节点ID
   * @param hasError - 是否有错误
   */
  function setNodeError(nodeId: string, hasError: boolean = true): void {
    const graph = getGraph();
    if (!graph) return;

    const node = graph.getCellById(nodeId);
    if (!node) return;

    // 方式1: 通过 findViewByCell 获取节点视图的容器元素并添加 CSS 类
    const nodeView = graph.findViewByCell(node);
    if (nodeView && nodeView.container) {
      if (hasError) {
        nodeView.container.classList.add('node-error');
        // 同时给 SVG 元素添加红色边框效果
        const svgEl = nodeView.container.querySelector<SVGElement>('rect, circle, ellipse, path');
        if (svgEl) {
          svgEl.style.stroke = '#ef4444';
          svgEl.style.strokeWidth = '3px';
          svgEl.style.filter = 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.9))';
        }
      } else {
        nodeView.container.classList.remove('node-error');
        const svgEl = nodeView.container.querySelector<SVGElement>('rect, circle, ellipse, path');
        if (svgEl) {
          svgEl.style.stroke = '';
          svgEl.style.strokeWidth = '';
          svgEl.style.filter = '';
        }
      }
    }

    // 方式2: 通过 X6 的 attr API 设置样式（兼容不同节点类型）
    // 尝试多个可能的形状属性名
    const shapeAttrs = ['body', 'rect', 'circle', 'ellipse', 'path', 'polygon'];

    if (hasError) {
      // 保存原始样式
      const originalStyles: NonNullable<SimulationNodeData['_originalStyles']> = {};
      const currentAttrs = node.getAttrs();
      shapeAttrs.forEach((shape) => {
        const stroke = currentAttrs[shape]?.stroke;
        const strokeWidth = currentAttrs[shape]?.strokeWidth;
        if (stroke !== undefined) {
          originalStyles[shape] = { stroke, strokeWidth };
        }
      });
      node.setData({ _originalStyles: originalStyles }, { silent: true });

      // 设置错误样式 - 尝试所有可能的形状
      shapeAttrs.forEach((shape) => {
        node.attr(`${shape}/stroke`, '#ef4444', { silent: true });
        node.attr(`${shape}/strokeWidth`, 3, { silent: true });
      });
    } else {
      // 恢复原始样式
      const data = node.getData<SimulationNodeData>() || {};
      const originalStyles = data._originalStyles || {};

      shapeAttrs.forEach((shape) => {
        const original = originalStyles[shape];
        if (original) {
          node.attr(`${shape}/stroke`, original.stroke || '#e2e8f0', { silent: true });
          node.attr(`${shape}/strokeWidth`, original.strokeWidth || 1, { silent: true });
        } else {
          node.attr(`${shape}/stroke`, '#e2e8f0', { silent: true });
          node.attr(`${shape}/strokeWidth`, 1, { silent: true });
        }
      });
    }
  }

  /**
   * 高亮指定的边
   * @param edgeIds - 边ID列表
   * @param color - 高亮颜色
   */
  function highlightEdges(edgeIds: string[], color: string = '#3b82f6'): void {
    const graph = getGraph();
    if (!graph) return;

    edgeIds.forEach((edgeId) => {
      const edge = graph.getCellById(edgeId);
      if (edge) {
        edge.attr('line/stroke', color);
        edge.attr('line/strokeWidth', 3);
      }
    });
  }

  /**
   * 清除边高亮
   * @param edgeIds - 边ID列表
   */
  function clearEdgeHighlight(edgeIds: string[]): void {
    const graph = getGraph();
    if (!graph) return;

    edgeIds.forEach((edgeId) => {
      const edge = graph.getCellById(edgeId);
      if (edge) {
        edge.attr('line/stroke', '#b1b1b7');
        edge.attr('line/strokeWidth', 2);
      }
    });
  }

  // 清理
  onUnmounted(() => {
    stopAnimation();
  });

  return {
    // 状态
    isAnimating,
    activeNodes,
    activeEdges,
    errorEdges,

    // 方法
    startAnimation,
    stopAnimation,
    triggerTrafficAnimation,
    triggerErrorAnimation,
    setNodeActive,
    setNodeError,
    highlightEdges,
    clearEdgeHighlight,
    getProtocolColor,
  };
}

export default useTopologyAnimation;
