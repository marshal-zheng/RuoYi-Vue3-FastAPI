/**
 * 拓扑动画 Composable
 * 
 * 管理拓扑图上的动画效果：
 * - 链路光点动画（数据传输）
 * - 链路错误闪烁
 * - 节点呼吸灯效果
 */
import { ref, onUnmounted } from 'vue'

/**
 * 协议类型到颜色的映射
 */
export const PROTOCOL_COLORS = {
  '1553B': '#f97316',    // 橙色
  'MIL-STD-1553B': '#f97316',
  'CAN': '#3b82f6',      // 蓝色
  'RS422': '#22c55e',    // 绿色
  'RS485': '#22c55e',    // 绿色
  'LAN': '#e2e8f0',      // 白色
  'Ethernet': '#e2e8f0', // 白色
  'default': '#94a3b8',  // 灰色
}

/**
 * 获取协议对应的颜色
 * @param {string} protocolType - 协议类型
 * @returns {string} 颜色值
 */
export function getProtocolColor(protocolType) {
  if (!protocolType) {
    return PROTOCOL_COLORS.default
  }

  const normalizedType = protocolType.toUpperCase().replace(/[-_\s]/g, '')
  
  // 精确匹配
  if (PROTOCOL_COLORS[protocolType]) {
    return PROTOCOL_COLORS[protocolType]
  }

  // 模糊匹配
  if (normalizedType.includes('1553')) {
    return PROTOCOL_COLORS['1553B']
  }
  if (normalizedType.includes('CAN')) {
    return PROTOCOL_COLORS['CAN']
  }
  if (normalizedType.includes('RS422') || normalizedType.includes('RS485')) {
    return PROTOCOL_COLORS['RS422']
  }
  if (normalizedType.includes('LAN') || normalizedType.includes('ETHERNET')) {
    return PROTOCOL_COLORS['LAN']
  }

  return PROTOCOL_COLORS.default
}

/**
 * 验证协议颜色映射的完整性
 * @param {string[]} protocolTypes - 协议类型列表
 * @returns {boolean} 是否所有协议都有对应颜色
 */
export function validateProtocolColors(protocolTypes) {
  const colors = new Set()
  
  for (const type of protocolTypes) {
    const color = getProtocolColor(type)
    if (color === PROTOCOL_COLORS.default) {
      return false
    }
    colors.add(color)
  }

  // 确保不同协议映射到不同颜色
  return colors.size === protocolTypes.length
}

/**
 * 拓扑动画 Composable
 * @param {Ref} dagRef - DAG 组件引用
 * @returns {Object} 动画控制方法
 */
export function useTopologyAnimation(dagRef) {
  // 动画状态
  const isAnimating = ref(false)
  const activeNodes = ref(new Set())
  const activeEdges = ref(new Set())
  const errorEdges = ref(new Set())

  // 动画定时器
  const animationTimers = ref(new Map())

  // 节流配置
  const THROTTLE_INTERVAL = 100 // 100ms 节流

  // 上次动画触发时间
  const lastAnimationTime = ref(new Map())

  /**
   * 获取图实例
   */
  function getGraph() {
    return dagRef.value?.getGraph?.() || null
  }

  /**
   * 节流检查
   */
  function shouldThrottle(key) {
    const now = Date.now()
    const lastTime = lastAnimationTime.value.get(key) || 0
    
    if (now - lastTime < THROTTLE_INTERVAL) {
      return true
    }

    lastAnimationTime.value.set(key, now)
    return false
  }

  /**
   * 启动全局动画
   */
  function startAnimation() {
    isAnimating.value = true
  }

  /**
   * 停止全局动画
   */
  function stopAnimation() {
    isAnimating.value = false
    
    // 清除所有动画定时器
    animationTimers.value.forEach(timer => clearTimeout(timer))
    animationTimers.value.clear()

    // 重置所有状态
    activeNodes.value.clear()
    activeEdges.value.clear()
    errorEdges.value.clear()

    // 重置图形样式
    const graph = getGraph()
    if (graph) {
      resetGraphStyles(graph)
    }
  }

  /**
   * 重置图形样式
   */
  function resetGraphStyles(graph) {
    const edges = graph.getEdges?.() || []
    const nodes = graph.getNodes?.() || []

    edges.forEach(edge => {
      edge.attr('line/stroke', '#b1b1b7')
      edge.attr('line/strokeWidth', 2)
      edge.attr('line/strokeDasharray', null)
    })

    nodes.forEach(node => {
      // 移除呼吸灯效果
      const nodeEl = document.querySelector(`[data-cell-id="${node.id}"]`)
      if (nodeEl) {
        nodeEl.classList.remove('node-breathing', 'node-error')
      }
    })
  }

  /**
   * 触发链路流量动画
   * @param {string} edgeId - 边ID
   * @param {string} protocolType - 协议类型
   * @param {number} duration - 动画持续时间（毫秒）
   */
  function triggerTrafficAnimation(edgeId, protocolType, duration = 1000) {
    if (!isAnimating.value) return
    if (shouldThrottle(`traffic-${edgeId}`)) return

    const graph = getGraph()
    if (!graph) return

    const edge = graph.getCellById(edgeId)
    if (!edge) return

    const color = getProtocolColor(protocolType)

    // 设置边的动画样式
    edge.attr('line/stroke', color)
    edge.attr('line/strokeWidth', 3)
    edge.attr('line/strokeDasharray', '5 5')

    // 添加到活跃边集合
    activeEdges.value.add(edgeId)

    // 创建光点动画（使用 CSS 动画）
    const edgeView = graph.findViewByCell(edge)
    if (edgeView) {
      const pathEl = edgeView.findOne('path')
      if (pathEl) {
        pathEl.classList.add('edge-traffic-animation')
        pathEl.style.setProperty('--traffic-color', color)
      }
    }

    // 设置定时器恢复样式
    const timerId = setTimeout(() => {
      edge.attr('line/stroke', '#b1b1b7')
      edge.attr('line/strokeWidth', 2)
      edge.attr('line/strokeDasharray', null)
      activeEdges.value.delete(edgeId)

      if (edgeView) {
        const pathEl = edgeView.findOne('path')
        if (pathEl) {
          pathEl.classList.remove('edge-traffic-animation')
        }
      }

      animationTimers.value.delete(edgeId)
    }, duration)

    animationTimers.value.set(edgeId, timerId)
  }

  /**
   * 触发链路错误动画
   * @param {string} edgeId - 边ID
   * @param {number} duration - 动画持续时间（毫秒）
   */
  function triggerErrorAnimation(edgeId, duration = 2000) {
    if (shouldThrottle(`error-${edgeId}`)) return

    const graph = getGraph()
    if (!graph) return

    const edge = graph.getCellById(edgeId)
    if (!edge) return

    // 设置错误样式
    edge.attr('line/stroke', '#ef4444')
    edge.attr('line/strokeWidth', 4)

    // 添加到错误边集合
    errorEdges.value.add(edgeId)

    // 创建闪烁动画
    const edgeView = graph.findViewByCell(edge)
    if (edgeView) {
      const pathEl = edgeView.findOne('path')
      if (pathEl) {
        pathEl.classList.add('edge-error-animation')
      }
    }

    // 设置定时器恢复样式
    const timerId = setTimeout(() => {
      edge.attr('line/stroke', '#b1b1b7')
      edge.attr('line/strokeWidth', 2)
      errorEdges.value.delete(edgeId)

      if (edgeView) {
        const pathEl = edgeView.findOne('path')
        if (pathEl) {
          pathEl.classList.remove('edge-error-animation')
        }
      }

      animationTimers.value.delete(`error-${edgeId}`)
    }, duration)

    animationTimers.value.set(`error-${edgeId}`, timerId)
  }

  /**
   * 设置节点活跃状态（呼吸灯效果）
   * @param {string} nodeId - 节点ID
   * @param {boolean} active - 是否活跃
   */
  function setNodeActive(nodeId, active = true) {
    if (!isAnimating.value && active) return

    const graph = getGraph()
    if (!graph) return

    const node = graph.getCellById(nodeId)
    if (!node) return

    const nodeEl = document.querySelector(`[data-cell-id="${nodeId}"]`)
    if (!nodeEl) return

    if (active) {
      activeNodes.value.add(nodeId)
      nodeEl.classList.add('node-breathing')
    } else {
      activeNodes.value.delete(nodeId)
      nodeEl.classList.remove('node-breathing')
    }
  }

  /**
   * 设置节点错误状态
   * @param {string} nodeId - 节点ID
   * @param {boolean} hasError - 是否有错误
   */
  function setNodeError(nodeId, hasError = true) {
    const graph = getGraph()
    if (!graph) return

    const nodeEl = document.querySelector(`[data-cell-id="${nodeId}"]`)
    if (!nodeEl) return

    if (hasError) {
      nodeEl.classList.add('node-error')
    } else {
      nodeEl.classList.remove('node-error')
    }
  }

  /**
   * 高亮指定的边
   * @param {string[]} edgeIds - 边ID列表
   * @param {string} color - 高亮颜色
   */
  function highlightEdges(edgeIds, color = '#3b82f6') {
    const graph = getGraph()
    if (!graph) return

    edgeIds.forEach(edgeId => {
      const edge = graph.getCellById(edgeId)
      if (edge) {
        edge.attr('line/stroke', color)
        edge.attr('line/strokeWidth', 3)
      }
    })
  }

  /**
   * 清除边高亮
   * @param {string[]} edgeIds - 边ID列表
   */
  function clearEdgeHighlight(edgeIds) {
    const graph = getGraph()
    if (!graph) return

    edgeIds.forEach(edgeId => {
      const edge = graph.getCellById(edgeId)
      if (edge) {
        edge.attr('line/stroke', '#b1b1b7')
        edge.attr('line/strokeWidth', 2)
      }
    })
  }

  // 清理
  onUnmounted(() => {
    stopAnimation()
  })

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
  }
}

export default useTopologyAnimation
