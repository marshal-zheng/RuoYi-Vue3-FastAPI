/**
 * 故障注入 UI 交互 Composable
 * 
 * 管理故障注入模式下的 UI 交互逻辑
 * - 边的选中与高亮
 * - 模式进入/退出
 * - 事件监听
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { ElMessage } from 'element-plus'

// 统一消息配置：短时长 + 合并同类
const msgOpts = { duration: 1500, grouping: true }

interface DockState {
  fault: boolean
  [key: string]: any
}

interface FaultInjection {
  faults: Ref<any[]>
  clearFault: (faultId: string) => Promise<void>
  clearAllFaults: () => Promise<void>
  injectFault: (payload: any) => Promise<any>
  fetchFaults: () => Promise<any[]>
}

interface FaultTemplate {
  label?: string
  payload: {
    type: string
    params?: Record<string, any>
  }
}

interface UseFaultInjectionUIOptions {
  getGraphInstance: () => any
  dockState: DockState
  faultInjection: FaultInjection
}

/**
 * 故障注入 UI 交互
 * @param {Object} options 配置选项
 * @param {Function} options.getGraphInstance - 获取图实例的函数
 * @param {Ref} options.dockState - dock 状态
 * @param {Object} options.faultInjection - useFaultInjection 返回的对象
 */
export function useFaultInjectionUI(options: UseFaultInjectionUIOptions) {
  const { getGraphInstance, dockState, faultInjection } = options
  
  // 选中的链路
  const selectedEdge: Ref<any> = ref(null)
  
  // 保存边的原始样式
  const edgeOriginalStyles = new Map<string, { stroke: string; strokeWidth: number }>()
  
  // 已注入故障的边 ID 集合
  const faultedEdges = new Set<string>()
  
  // 是否处于故障注入模式
  const isFaultInjectionMode: ComputedRef<boolean> = computed(() => dockState.fault)
  
  function shortId(id?: string): string {
    if (!id) return '未知链路'
    const str = String(id)
    if (str.length <= 12) return str
    return `${str.slice(0, 6)}...${str.slice(-4)}`
  }

  /**
   * 获取选中边的 ID
   */
  function getSelectedEdgeId(): string {
    if (!selectedEdge.value) return ''
    return formatEdgeLabel(selectedEdge.value)
  }
  
  /**
   * 设置边的事件监听
   * @param {Object} graph - 图实例
   */
  function setupEdgeEvents(graph: any) {
    if (!graph) return
    
    // 监听边点击事件
    graph.on('edge:click', ({ edge, e }: any) => {
      if (isFaultInjectionMode.value) {
        selectedEdge.value = edge
        highlightSelectedEdge(edge)
      }
    })
    
    // 监听空白区域点击，取消选中
    graph.on('blank:click', () => {
      if (isFaultInjectionMode.value && selectedEdge.value) {
        clearSelectedEdge()
      }
    })
  }
  
  /**
   * 高亮选中的边
   * @param {Object} edge - 边实例
   */
  function highlightSelectedEdge(edge: any) {
    const graph = getGraphInstance()
    if (!graph || !edge) return
    
    const selectedId = edge.id || edge.getID?.()
    
    graph.getEdges().forEach((e: any) => {
      const eId = e.id || e.getID?.()
      // 保存原始样式（如果还没保存）
      if (!edgeOriginalStyles.has(eId)) {
        edgeOriginalStyles.set(eId, {
          stroke: e.attr('line/stroke') || '#64748b',
          strokeWidth: e.attr('line/strokeWidth') || 2,
        })
      }
      
      if (eId === selectedId) {
        // 选中的边：红色、加粗（故障模式下锁定的边）
        e.attr('line/stroke', '#ef4444')
        e.attr('line/strokeWidth', 6)
      } else {
        // 其他边：恢复原始样式
        const original = edgeOriginalStyles.get(eId)
        if (original) {
          e.attr('line/stroke', original.stroke)
          e.attr('line/strokeWidth', original.strokeWidth)
        }
      }
    })
  }
  
  /**
   * 清除选中的边
   */
  function clearSelectedEdge() {
    selectedEdge.value = null
    const graph = getGraphInstance()
    if (!graph) return
    
    // 恢复所有边的原始样式（除了已注入故障的边）
    graph.getEdges().forEach((e: any) => {
      const eId = e.id || e.getID?.()
      if (faultedEdges.has(eId)) return // 保持故障边的红色
      const original = edgeOriginalStyles.get(eId)
      if (original) {
        e.attr('line/stroke', original.stroke)
        e.attr('line/strokeWidth', original.strokeWidth)
      }
    })
  }
  
  /**
   * 退出故障注入模式（清除所有故障和选中状态）
   */
  async function exitFaultMode() {
    clearSelectedEdge()
    clearAllFaultMarks()
    // 清除所有故障
    await faultInjection.clearAllFaults()
    dockState.fault = false
  }
  
  /**
   * 清除单个故障
   * @param {string} faultId - 故障ID
   */
  async function handleFaultClear(faultId: string) {
    // 先找到这个故障对应的边 ID
    const fault = faultInjection.faults.value?.find((f: any) => f.faultId === faultId)
    const edgeId = fault?.targetId || fault?.targetKey
    
    await faultInjection.clearFault(faultId)
    
    // 清除边的故障标记
    if (edgeId) {
      // 检查这条边是否还有其他故障
      const remainingFaults = faultInjection.faults.value?.filter(
        (f: any) => (f.targetId === edgeId || f.targetKey === edgeId) && f.faultId !== faultId
      )
      if (!remainingFaults?.length) {
        clearEdgeFaultMark(edgeId)
      }
    }
    
    ElMessage.success({ message: '故障已清除', ...msgOpts })
  }
  
  /**
   * 清除所有故障
   */
  async function handleClearAllFaults() {
    await faultInjection.clearAllFaults()
    clearAllFaultMarks()
    ElMessage.success({ message: '已清除全部故障', ...msgOpts })
  }
  
  /**
   * 应用故障模板
   * @param {Object} tpl - 模板对象
   * @param {Ref} hoveredEdge - 悬停的边
   */
  async function handleFaultTemplate(tpl: FaultTemplate, hoveredEdge?: Ref<any>) {
    const edge = selectedEdge.value || hoveredEdge?.value
    const targetId = edge?.id || 
                     edge?.getID?.() || 
                     edge?.getData?.()?.id || 
                     edge?.getData?.()?.edgeId
    
    if (!targetId) {
      ElMessage.warning({ message: '请先点击链路选中后再应用模板', ...msgOpts })
      return
    }
    
    const payload = {
      type: tpl.payload.type,
      targetId,
      targetType: 'edge' as const,
      targetName: formatEdgeLabel(edge),
      // 将友好名称也放入参数，便于后端/事件返回时携带
      params: {
        ...(tpl.payload.params || {}),
        targetName: formatEdgeLabel(edge),
        target_name: formatEdgeLabel(edge),
      },
    }
    
    const result = await faultInjection.injectFault(payload)
    const faultLabel = tpl.label || tpl.payload.type
    if (result?._action === 'updated') {
      ElMessage.info({ message: `${faultLabel} 已更新`, ...msgOpts })
    } else {
      ElMessage.success({ message: `${faultLabel} 已注入`, ...msgOpts })
    }

    // 注入后高亮为红色粗线，提示当前链路有故障
    markEdgeAsFaulted(edge)
  }
  
  /**
   * 将边标记为故障状态（红色粗线）
   */
  function markEdgeAsFaulted(edge: any) {
    if (!edge) return
    const graph = getGraphInstance()
    if (!graph) return
    
    const edgeId = edge.id || edge.getID?.()
    if (!edgeId) return
    
    // 记录故障边
    faultedEdges.add(edgeId)
    
    // 从图中获取边实例并设置样式
    const graphEdge = graph.getCellById(edgeId)
    if (graphEdge?.attr) {
      graphEdge.attr('line/stroke', '#ef4444')
      graphEdge.attr('line/strokeWidth', 6)
    }
  }

  /**
   * 生成链路友好标签：设备A(端口) → 设备B(端口)
   */
  function formatEdgeLabel(edge: any): string {
    if (!edge) return '未知链路'
    const data = edge.getData?.() || {}

    // 优先用图元上已有的友好名称
    const alias = data.alias || data.label || data.name || data.title
    const id = edge.id || edge.getID?.() || data.id || data.edgeId

    const sourceNode = edge.getSourceNode?.()
    const targetNode = edge.getTargetNode?.()
    const sourceData = sourceNode?.getData?.() || {}
    const targetData = targetNode?.getData?.() || {}

    const srcName = sourceData.name || sourceData.label || sourceData.deviceName
    const dstName = targetData.name || targetData.label || targetData.deviceName
    const srcPort = data.sourcePortName || data.sourcePort || sourceData.portName
    const dstPort = data.targetPortName || data.targetPort || targetData.portName

    if (srcName || dstName) {
      const left = srcName || '源设备'
      const right = dstName || '目标设备'
      const leftPort = srcPort ? `(${srcPort})` : ''
      const rightPort = dstPort ? `(${dstPort})` : ''
      return `${left}${leftPort} → ${right}${rightPort}`
    }

    return alias || shortId(id)
  }
  
  /**
   * 清除边的故障标记
   */
  function clearEdgeFaultMark(edgeId: string) {
    if (!edgeId) return
    faultedEdges.delete(edgeId)
    
    const graph = getGraphInstance()
    if (!graph) return
    
    const edge = graph.getCellById(edgeId)
    if (!edge) return
    
    const original = edgeOriginalStyles.get(edgeId)
    if (original) {
      edge.attr('line/stroke', original.stroke)
      edge.attr('line/strokeWidth', original.strokeWidth)
    }
  }
  
  /**
   * 清除所有故障边标记
   */
  function clearAllFaultMarks() {
    const graph = getGraphInstance()
    if (!graph) return
    
    faultedEdges.forEach(edgeId => {
      const edge = graph.getCellById(edgeId)
      if (!edge) return
      const original = edgeOriginalStyles.get(edgeId)
      if (original) {
        edge.attr('line/stroke', original.stroke)
        edge.attr('line/strokeWidth', original.strokeWidth)
      }
    })
    faultedEdges.clear()
  }
  
  /**
   * 刷新故障列表
   */
  async function refreshFaults() {
    await faultInjection.fetchFaults()
  }
  
  return {
    // 状态
    selectedEdge,
    isFaultInjectionMode,
    
    // 方法
    getSelectedEdgeId,
    setupEdgeEvents,
    highlightSelectedEdge,
    clearSelectedEdge,
    exitFaultMode,
    handleFaultClear,
    handleClearAllFaults,
    handleFaultTemplate,
    refreshFaults,
  }
}

export default useFaultInjectionUI
