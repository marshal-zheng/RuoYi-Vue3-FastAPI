<template></template>

<script setup>
import { ElMessageBox } from 'element-plus'
import { onMounted, onUnmounted, watch } from 'vue'
import { useGraphStore } from '../../ZxFlow/composables/useGraphStore'
import { useOptionalGraphInstance } from '../../ZxFlow/composables/useGraphInstance'
import { willCreateCycle } from '../utils/graphConstraints.js'
import {
  updateNodeTypeAndLevel,
  hasComputeModel,
  clearNodeComputeModel,
  getParentNodeId
} from '../utils/nodeDataUtils.js'
import { refreshCollapseState } from '../utils/collapse.js'

const graphStore = useGraphStore()
const graph = useOptionalGraphInstance()

// 检查节点是否为叶子节点并且有计算模型
function checkNodeHasModel(node) {
  if (!node) return false
  const data = node.getData?.() || {}
  const nodeType = data.type

  return nodeType === 'leaf-node' && hasComputeModel(data)
}

// 连线前检查函数
const handleEdgeAdding = async ({ edge, isNew, options }) => {
  const g = graph?.value
  console.log('g', g)
  if (!g) return
  console.log('g', g)

  try {
    const sourceId = edge.getSourceCellId?.()
    const targetId = edge.getTargetCellId?.()
    if (!sourceId || !targetId) return

    // 检查是否会形成环
    if (willCreateCycle(g, sourceId, targetId)) {
      // 阻止新增该边
      options?.cancel && (options.cancel = true)
      edge.remove?.()
      return
    }

    // 检查源节点是否为已绑定计算模型的叶子节点
    const sourceNode = g.getCellById(sourceId)
    console.log('检查节点是否有计算模型:', checkNodeHasModel(sourceNode))
    if (checkNodeHasModel(sourceNode)) {
      try {
        // 显示确认对话框
        await ElMessageBox.confirm('连线后会清除该节点的计算模型配置，是否继续？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          center: true
        })

        // 用户确认后，清除计算模型
        clearNodeComputeModel(g, sourceId)
        console.log('用户确认，已清除计算模型')
      } catch (error) {
        // 用户取消，阻止连线
        console.log('用户取消连线')
        options?.cancel && (options.cancel = true)
        edge.remove?.()
        return
      }
    }
  } catch (e) {
    console.warn('Edge adding validation error:', e)
  }
}

// 连线完成后处理函数
const handleEdgeConnected = async ({ edge }) => {
  const g = graph?.value
  if (!edge || !g) return
  console.log('[DagConnect] edge:connected', edge?.id)

  // 二次保险：若已形成环，直接删除该边
  try {
    const sourceId = edge.getSourceCellId?.()
    const targetId = edge.getTargetCellId?.()
    if (sourceId && targetId && willCreateCycle(g, sourceId, targetId)) {
      edge.remove?.()
      return
    }
  } catch (e) {}

  // 检查源节点是否为已绑定计算模型的叶子节点
  try {
    const sourceId = edge.getSourceCellId?.()
    if (sourceId) {
      const sourceNode = g.getCellById(sourceId)
      const needConfirm = checkNodeHasModel(sourceNode)
      console.log('[DagConnect] source has model?', needConfirm)
      if (needConfirm) {
        try {
          await ElMessageBox.confirm('连线后会清除该节点的计算模型配置，是否继续？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
            center: true
          })
          // 用户确认后清除计算模型
          clearNodeComputeModel(g, sourceId)
          console.log('[DagConnect] 已清除源节点计算模型')
        } catch (err) {
          // 用户取消：移除刚建立的连线并终止后续处理
          console.log('[DagConnect] 用户取消，撤销本次连线')
          edge.remove?.()
          return
        }
      }
    }
  } catch (e) {
    console.warn('[DagConnect] connected confirm error:', e)
  }

  // 更新相关节点的类型和层级
  try {
    const sourceId = edge.getSourceCellId?.()
    const targetId = edge.getTargetCellId?.()
    if (sourceId) updateNodeTypeAndLevel(g, sourceId)
    if (targetId) updateNodeTypeAndLevel(g, targetId)

    // 修复bug: 为目标节点设置parentNodeId
    if (targetId) {
      const targetNode = g.getCellById(targetId)
      if (targetNode) {
        const parentId = getParentNodeId(g, targetId)
        if (parentId) {
          const currentData = targetNode.getData() || {}
          const properties = currentData.properties || {}
          targetNode.setData({
            ...currentData,
            properties: {
              ...properties,
              parentNodeId: parentId
            }
          })
          console.log(`[DagConnect] 设置目标节点 ${targetId} 的 parentNodeId: ${parentId}`)
        }
      }
    }
  } catch (e) {
    console.warn('Failed to update node types:', e)
  }

  if (edge.id) {
    graphStore.updateEdge(edge.id, { animated: false })
  }
  refreshCollapseState(g)
}

// 边删除处理函数
const handleEdgeRemoved = ({ edge }) => {
  const g = graph?.value
  if (!edge || !g) return

  try {
    const sourceId = edge.getSourceCellId?.()
    const targetId = edge.getTargetCellId?.()

    // 更新相关节点的类型和层级
    if (sourceId) updateNodeTypeAndLevel(g, sourceId)
    if (targetId) updateNodeTypeAndLevel(g, targetId)

    // 修复bug: 更新目标节点的parentNodeId
    if (targetId) {
      const targetNode = g.getCellById(targetId)
      if (targetNode) {
        const newParentId = getParentNodeId(g, targetId)
        const currentData = targetNode.getData() || {}
        const properties = currentData.properties || {}
        targetNode.setData({
          ...currentData,
          properties: {
            ...properties,
            parentNodeId: newParentId || null
          }
        })
        console.log(
          `[DagConnect] 更新目标节点 ${targetId} 的 parentNodeId: ${newParentId || 'null'}`
        )
      }
    }
  } catch (e) {
    console.warn('Edge removed handling error:', e)
  }
  refreshCollapseState(g)
}

// 节点添加处理函数
const handleNodeAdded = ({ node }) => {
  const g = graph?.value
  if (!g || !node) return

  // 延迟一下再处理，确保节点已经完全添加到图中
  setTimeout(() => {
    try {
      // 更新节点的类型和层级
      updateNodeTypeAndLevel(g, node.id)

      // 更新父节点ID
      const parentId = getParentNodeId(g, node.id)
      if (parentId) {
        const currentData = node.getData() || {}
        const properties = currentData.properties || {}
        node.setData({
          ...currentData,
          properties: {
            ...properties,
            parentNodeId: parentId
          }
        })
      }
    } catch (e) {
      console.warn('Node added handling error:', e)
    }
    refreshCollapseState(g)
  }, 100)
}

// 注册事件监听器
const registerEventListeners = () => {
  const g = graph?.value
  if (!g) return

  console.log('注册图事件监听器')

  // 注册事件监听器
  g.on('edge:adding', handleEdgeAdding)
  g.on('edge:connected', handleEdgeConnected)
  g.on('edge:removed', handleEdgeRemoved)
  g.on('node:added', handleNodeAdded)
}

// 清理事件监听器
const cleanupEventListeners = () => {
  const g = graph?.value
  if (!g) return

  g.off('edge:adding', handleEdgeAdding)
  g.off('edge:connected', handleEdgeConnected)
  g.off('edge:removed', handleEdgeRemoved)
  g.off('node:added', handleNodeAdded)
}

// 监听 graph 实例变化
watch(
  graph,
  (newGraph, oldGraph) => {
    if (oldGraph) {
      // 清理旧的事件监听器
      cleanupEventListeners()
    }

    if (newGraph) {
      // 注册新的事件监听器
      registerEventListeners()
    }
  },
  { immediate: true }
)

// 组件挂载时注册事件
onMounted(() => {
  // 如果图实例已存在,立即注册事件
  if (graph?.value) {
    registerEventListeners()
  }
})

// 组件卸载时清理事件
onUnmounted(() => {
  cleanupEventListeners()
})
</script>

<style scoped></style>
