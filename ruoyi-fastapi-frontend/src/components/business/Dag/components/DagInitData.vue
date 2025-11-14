<template></template>

<script setup>
import { onMounted, watch, nextTick } from 'vue'
import { useOptionalGraphInstance } from '../../ZxFlow/composables/useGraphInstance'
import { useGraphStore } from '../../ZxFlow/composables/useGraphStore'
import { dagreLayout } from '../utils/layout.js'
import { getNodeSizeByLayout } from '../utils/nodeGeometry.js'
import { registerDagShapes, DAG_NODE, DAG_EDGE } from '../shapes/registerDagShapes'
import { refreshCollapseState } from '../utils/collapse.js'
import { generateNodePorts } from '../constants/portConfig.js'

// Props 定义
const props = defineProps({
  // 初始数据，支持静态数据、Promise或函数
  initialData: {
    type: [Object, Promise, Function],
    default: null
  },
  // 是否自动布局
  autoLayout: {
    type: Boolean,
    default: true
  },
  // 布局方向
  layoutDirection: {
    type: String,
    default: 'LR',
    validator: (value) => ['LR', 'TB'].includes(value)
  }
})

const graph = useOptionalGraphInstance()
const graphStore = useGraphStore()
// 向父级通知数据或布局完成
const emit = defineEmits(['data-updated'])

// 注册 DAG 图形
registerDagShapes()

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const ensureGraphReady = async (maxAttempts = 20, delay = 100) => {
  let attempts = 0

  while (attempts < maxAttempts) {
    const instance = graph?.value
    if (instance) {
      return instance
    }
    attempts++
    await wait(delay)
  }

  return null
}

// 将数据转换为DAG画布格式
const convertToDAGFormat = (data) => {
  if (!data || !data.nodes || !data.edges) {
    return { nodes: [], edges: [] }
  }

  const layoutOrientation = props.layoutDirection === 'TB' ? 'vertical' : 'horizontal'
  const sizeConfig = getNodeSizeByLayout(layoutOrientation)

  const childMap = new Map()
  ;(data.edges || []).forEach((edge) => {
    const sourceId = edge.sourceNodeId
    if (!sourceId) return
    if (!childMap.has(sourceId)) {
      childMap.set(sourceId, new Set())
    }
    childMap.get(sourceId).add(edge.targetNodeId)
  })

  const nodes = data.nodes.map((node) => ({
    id: node.id,
    shape: DAG_NODE,
    x: node.x || 0,
    y: node.y || 0,
    width: sizeConfig.width,
    height: sizeConfig.height,
    data: {
      // 支持新的数据结构
      type: node.type,
      properties: node.properties,
      // 兼容旧结构
      label: node.properties?.content?.label || node.label || '未命名节点',
      status: 'default',
      layoutDirection: layoutOrientation,
      collapsed: node.collapsed === true,
      hasChildren: (childMap.get(node.id)?.size || 0) > 0,
      // 保存原始数据
      originalData: node
    },
    ports: generateNodePorts(node.type),
    draggable: true,
    locked: false
  }))

  const edges = data.edges.map((edge) => ({
    id: edge.id,
    shape: DAG_EDGE,
    source: { cell: edge.sourceNodeId, port: 'b' }, // 指定源端口为底部
    target: { cell: edge.targetNodeId, port: 't' }, // 指定目标端口为顶部
    animated: false
  }))

  return { nodes, edges }
}

// 加载和设置数据
const loadAndSetData = async (dataSource) => {
  try {
    let data

    // 如果是函数，调用函数获取数据
    if (typeof dataSource === 'function') {
      data = await dataSource()
    }
    // 如果是Promise，等待解析
    else if (dataSource && typeof dataSource.then === 'function') {
      data = await dataSource
    } else {
      data = dataSource
    }

    if (!data) {
      return
    }

    if (!data.nodes || !Array.isArray(data.nodes)) {
      return
    }

    // 获取 graphStore，如果还未准备好则等待
    if (!graphStore) {
      console.warn('GraphStore not ready, cannot load data')
      return
    }

    // 清空现有数据 - 使用正确的方法
    const allNodes = graphStore.nodes.map((node) => node.id)
    const allEdges = graphStore.edges.map((edge) => edge.id)

    if (allNodes.length > 0) {
      graphStore.removeNodes(allNodes)
    }
    if (allEdges.length > 0) {
      graphStore.removeEdges(allEdges)
    }

    // 转换数据格式
    const { nodes, edges } = convertToDAGFormat(data)

    // 添加节点和边
    if (nodes.length > 0) {
      graphStore.addNodes(nodes)
    }

    if (edges.length > 0) {
      graphStore.addEdges(edges)
    }

    // 等待图实例准备好，然后进行布局
    waitForGraphAndLayout(nodes)
  } catch (error) {}
}

const waitForGraphAndLayout = async (nodes) => {
  const g = await ensureGraphReady()

  if (g) {
    refreshCollapseState(g)

    if (props.autoLayout && nodes.length > 0) {
      // 先让节点渲染完成，再进行布局
      await wait(200)
      await dagreLayout(g, props.layoutDirection, 100, 80)
      refreshCollapseState(g)
      g.centerContent()
    }
  }

  // 通知父级刷新小地图或其他依赖
  emit('data-updated')
}

// 监听初始数据变化
watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      // 延迟执行，确保图实例已经准备好
      setTimeout(() => {
        loadAndSetData(newData)
      }, 100)
    }
  },
  { immediate: false, deep: true }
) // 改为 false，避免在图实例准备前执行

watch(
  () => props.layoutDirection,
  async (newDirection, oldDirection) => {
    if (!newDirection || newDirection === oldDirection) return
    await nextTick()
    const g = graph?.value || (await ensureGraphReady(10, 100))
    if (!g) return
    try {
      await dagreLayout(g, newDirection, 100, 80)
      refreshCollapseState(g)
      g.centerContent?.()
    } catch (error) {}
  }
)

onMounted(async () => {
  // 等待足够的时间确保 XFlowGraph 完全初始化
  await ensureGraphReady(10, 100)
  await wait(300)

  // 如果有初始数据，加载它
  if (props.initialData) {
    await loadAndSetData(props.initialData)
  }
})
</script>

<style scoped></style>
