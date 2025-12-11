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
export function useTopologyAnimation(dagRef, speedSource = null) {
  // 动画状态
  const isAnimating = ref(false)
  const activeNodes = ref(new Set())
  const activeEdges = ref(new Set())
  const errorEdges = ref(new Set())

  // 动画定时器
  const animationTimers = ref(new Map())

  // 节流配置
  const THROTTLE_INTERVAL = 100 // 基准 100ms 节流

  // 上次动画触发时间
  const lastAnimationTime = ref(new Map())

  /**
   * 当前速度倍率
   */
  function getSpeedFactor() {
    const val =
      typeof speedSource === 'function'
        ? speedSource()
        : speedSource && typeof speedSource === 'object' && 'value' in speedSource
          ? speedSource.value
          : speedSource
    const num = Number(val) || 1
    return Math.max(0.5, Math.min(num, 4))
  }

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
    const factor = getSpeedFactor()
    const interval = Math.max(20, THROTTLE_INTERVAL / factor)
    const lastTime = lastAnimationTime.value.get(key) || 0
    
    if (now - lastTime < interval) {
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
      // 通过 findViewByCell 获取节点视图
      const nodeView = graph.findViewByCell(node)
      if (nodeView && nodeView.container) {
        nodeView.container.classList.remove('node-breathing', 'node-error')
        // 重置 SVG 元素样式
        const svgEl = nodeView.container.querySelector('rect, circle, ellipse, path')
        if (svgEl) {
          svgEl.style.stroke = ''
          svgEl.style.strokeWidth = ''
          svgEl.style.filter = ''
        }
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
    const factor = getSpeedFactor()
    const adjustedDuration = Math.max(200, duration / factor)

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
    }, adjustedDuration)

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
    const factor = getSpeedFactor()
    const adjustedDuration = Math.max(300, duration / factor)

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
    }, adjustedDuration)

    animationTimers.value.set(`error-${edgeId}`, timerId)
  }

  /**
   * 设置节点活跃状态（呼吸灯效果）
   * @param {string} nodeId - 节点ID
   * @param {boolean} active - 是否活跃
   * @param {boolean} force - 是否强制设置（忽略 isAnimating 状态）
   */
  function setNodeActive(nodeId, active = true, force = false) {
    // 如果不是强制模式且动画未启动，则跳过
    if (!force && !isAnimating.value && active) return

    const graph = getGraph()
    if (!graph) return

    const node = graph.getCellById(nodeId)
    if (!node) return

    // 通过 findViewByCell 获取节点视图
    const nodeView = graph.findViewByCell(node)
    if (!nodeView || !nodeView.container) return

    if (active) {
      activeNodes.value.add(nodeId)
      nodeView.container.classList.add('node-breathing')
    } else {
      activeNodes.value.delete(nodeId)
      nodeView.container.classList.remove('node-breathing')
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

    const node = graph.getCellById(nodeId)
    if (!node) return

    // 方式1: 通过 findViewByCell 获取节点视图的容器元素并添加 CSS 类
    const nodeView = graph.findViewByCell(node)
    if (nodeView && nodeView.container) {
      if (hasError) {
        nodeView.container.classList.add('node-error')
        // 同时给 SVG 元素添加红色边框效果
        const svgEl = nodeView.container.querySelector('rect, circle, ellipse, path')
        if (svgEl) {
          svgEl.style.stroke = '#ef4444'
          svgEl.style.strokeWidth = '3px'
          svgEl.style.filter = 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.9))'
        }
      } else {
        nodeView.container.classList.remove('node-error')
        const svgEl = nodeView.container.querySelector('rect, circle, ellipse, path')
        if (svgEl) {
          svgEl.style.stroke = ''
          svgEl.style.strokeWidth = ''
          svgEl.style.filter = ''
        }
      }
    }

    // 方式2: 通过 X6 的 attr API 设置样式（兼容不同节点类型）
    // 尝试多个可能的形状属性名
    const shapeAttrs = ['body', 'rect', 'circle', 'ellipse', 'path', 'polygon']
    
    if (hasError) {
      // 保存原始样式
      const originalStyles = {}
      shapeAttrs.forEach(shape => {
        const stroke = node.attr(`${shape}/stroke`)
        const strokeWidth = node.attr(`${shape}/strokeWidth`)
        if (stroke !== undefined) {
          originalStyles[shape] = { stroke, strokeWidth }
        }
      })
      node.setData({ _originalStyles: originalStyles }, { silent: true })
      
      // 设置错误样式 - 尝试所有可能的形状
      shapeAttrs.forEach(shape => {
        node.attr(`${shape}/stroke`, '#ef4444', { silent: true })
        node.attr(`${shape}/strokeWidth`, 3, { silent: true })
      })
    } else {
      // 恢复原始样式
      const data = node.getData() || {}
      const originalStyles = data._originalStyles || {}
      
      shapeAttrs.forEach(shape => {
        const original = originalStyles[shape]
        if (original) {
          node.attr(`${shape}/stroke`, original.stroke || '#e2e8f0', { silent: true })
          node.attr(`${shape}/strokeWidth`, original.strokeWidth || 1, { silent: true })
        } else {
          node.attr(`${shape}/stroke`, '#e2e8f0', { silent: true })
          node.attr(`${shape}/strokeWidth`, 1, { silent: true })
        }
      })
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
