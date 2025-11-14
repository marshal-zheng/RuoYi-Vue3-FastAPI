<template>
  <!-- State 组件不需要渲染内容，纯逻辑组件 -->
</template>

<script setup>
import { watch, onMounted, nextTick } from 'vue'
import { FunctionExt, ObjectExt, Point } from '@antv/x6'
import { useGraphInstance } from '../composables/useGraphInstance'
import { useGraphStore } from '../composables/useGraphStore'
import { useGraphEvent } from '../composables/useGraphEvent'

// Props 定义
const props = defineProps({
  centerView: {
    type: Boolean,
    default: false
  },
  centerViewOptions: {
    type: Object,
    default: () => ({})
  },
  fitView: {
    type: Boolean,
    default: false
  },
  fitViewOptions: {
    type: Object,
    default: () => ({})
  },
  connectionEdgeOptions: {
    type: Object,
    default: () => ({})
  },
  // 边动画时长（秒），与 React 保持一致的默认值 30s
  edgeAnimationDuration: {
    type: Number,
    default: 30
  }
})

const INNER_CALL = '__inner__'

// 获取 Graph 实例和状态管理
const graph = useGraphInstance()
const graphStore = useGraphStore()

// 预处理函数
const preprocess = (key, value, graph) => {
  if (key === 'position') {
    const { x, y } = Point.create(value).snapToGrid(graph.getGridSize())
    return { x, y }
  }
  if (key === 'size') {
    return {
      width: value.width,
      height: value.height
    }
  }
  return { [key]: value }
}

// 工具函数：扁平化对象
const flatten = (obj, prefix = '') => {
  const result = {}

  Object.keys(obj).forEach((key) => {
    const value = obj[key]
    const newKey = prefix ? `${prefix}/${key}` : key

    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(result, flatten(value, newKey))
    } else {
      result[newKey] = value
    }
  })

  return result
}

// 改变选中状态
const changeSelectionStatus = (items) => {
  if (!graph || !graph.value) return

  const added = items.filter((item) => item.selected)
  const removed = items.filter((item) => !item.selected)

  if (added.length > 0) {
    graph.value.select(
      added.map((item) => item.id),
      { [INNER_CALL]: true }
    )
  }

  if (removed.length > 0) {
    graph.value.unselect(
      removed.map((item) => item.id),
      { [INNER_CALL]: true }
    )
  }
}

// 改变动画状态（与React版本保持一致：直接设置cell属性）
const changeAnimatedStatus = (edges) => {
  if (!graph || !graph.value) return

  edges.forEach((item) => {
    const cell = graph.value.getCellById(item.id)
    if (cell && cell.isEdge && cell.isEdge()) {
      if (item.animated) {
        // 设置虚线样式
        cell.attr('line/strokeDasharray', 5, { [INNER_CALL]: true })
        // 设置动画
        cell.attr(
          'line/style/animation',
          `animated-line ${props.edgeAnimationDuration}s infinite linear`,
          { [INNER_CALL]: true }
        )
      } else {
        // 清除虚线和动画
        cell.attr('line/strokeDasharray', 0, { [INNER_CALL]: true })
        cell.attr('line/style/animation', '', { [INNER_CALL]: true })
      }
    }
  })
}

// 初始化数据
const initData = (g, data) => {
  g.fromJSON(ObjectExt.cloneDeep(data))

  if (props.centerView) {
    g.centerContent(props.centerViewOptions)
  }

  if (props.fitView) {
    g.zoomToFit({ maxScale: 1, ...props.fitViewOptions })
  }

  const { nodes = [], edges = [] } = data
  changeSelectionStatus([...nodes, ...edges])
  changeAnimatedStatus([...edges])
}

// 处理特殊属性变化
const onSpecialPropChange = (id, data) => {
  if (!graph || !graph.value) return

  const keys = Object.keys(data)
  if (keys.includes('selected')) {
    const selected = !!data.selected
    changeSelectionStatus([{ id, selected }])
  } else if (keys.includes('animated')) {
    const animated = !!data.animated
    changeAnimatedStatus([{ id, animated }])
  }
}

// 处理属性变化
const onPropChange = (id, data, batchName) => {
  if (!graph || !graph.value) return

  const cell = graph.value.getCellById(id)
  if (cell) {
    console.log('onPropChange - 开始更新节点:', {
      id,
      data,
      batchName,
      currentData: cell.getData()
    })

    graph.value.startBatch(batchName)
    // 当包含 data 字段时，优先通过 setData 合并更新，以触发 x6-vue-shape 的重渲染
    let changed = data
    if (changed && Object.prototype.hasOwnProperty.call(changed, 'data')) {
      const nextData = changed.data || {}
      const prevData = cell.getData() || {}
      // 合并并写回，不使用 INNER_CALL 标记，确保触发响应式更新
      const mergedData = { ...prevData, ...nextData }
      console.log('XFlowState - setData 合并数据:', { prevData, nextData, mergedData })
      cell.setData(mergedData)
      // 从后续属性处理中移除 data，避免被当成普通属性铺平
      const { data: _omit, ...rest } = changed
      changed = rest
    }
    // 其余属性仍按既有流程处理
    changed = cell.preprocess(changed, true)
    const properties = flatten(changed)

    console.log('onPropChange - 处理后的属性:', { changed, properties })

    Object.keys(properties).forEach((key) => {
      console.log('onPropChange - 设置属性:', key, properties[key])
      cell.setPropByPath(key, properties[key], {
        [INNER_CALL]: true,
        rewrite: true
      })
    })

    onSpecialPropChange(id, data)
    graph.value.stopBatch(batchName)

    console.log('onPropChange - 更新完成，新数据:', cell.getData())
  }
}

// 处理图形变化
const handleGraphChange = (g, changes) => {
  changes.forEach((changeItem) => {
    const { command, data } = changeItem

    switch (command) {
      case 'init':
        initData(g, data)
        break

      case 'addNodes':
        const nodes = ObjectExt.cloneDeep(data)
        g.addNodes(nodes, { [INNER_CALL]: true })
        changeSelectionStatus(nodes)
        break

      case 'removeNodes':
        g.removeCells(data, { [INNER_CALL]: true })
        break

      case 'updateNode':
        onPropChange(data.id, data.data, 'updateNode')
        break

      case 'addEdges':
        const edges = ObjectExt.cloneDeep(data)
        g.addEdges(edges, { [INNER_CALL]: true })
        changeSelectionStatus(edges)
        changeAnimatedStatus(edges)
        break

      case 'removeEdges':
        g.removeCells(data, { [INNER_CALL]: true })
        break

      case 'updateEdge':
        onPropChange(data.id, data.data, 'updateEdge')
        break

      default:
        break
    }
  })

  // 清理变更列表
  setTimeout(() => {
    graphStore.clearChangeList()
  })
}

// 监听状态变化
watch(
  () => graphStore.changeList,
  (changeList) => {
    if (graph && graph.value && changeList.length > 0) {
      handleGraphChange(graph.value, changeList)
    }
  },
  { deep: true }
)

// 设置图形事件监听
const setupGraphEvents = () => {
  if (!graph || !graph.value) return

  // 监听单元格添加
  useGraphEvent('cell:added', ({ cell, options }) => {
    if (!options || !options[INNER_CALL]) {
      if (cell.isNode()) {
        const nodes = [cell.toJSON()]
        graphStore.addNodes(nodes, { silent: true })
        changeSelectionStatus(nodes)
      } else if (cell.isEdge()) {
        const edges = [cell.toJSON()]
        graphStore.addEdges(edges, { silent: true })
        changeSelectionStatus(edges)
        changeAnimatedStatus(edges)
      }
    }
  })

  // 监听单元格移除
  useGraphEvent('cell:removed', ({ cell }) => {
    if (cell.isNode()) {
      graphStore.removeNodes([cell.id], { silent: true })
    } else if (cell.isEdge()) {
      graphStore.removeEdges([cell.id], { silent: true })
    }
  })

  // 监听单元格属性变化（防抖处理）
  const debouncedCellChange = FunctionExt.debounce(
    ({ cell, key, current, options }) => {
      if (!options || !options[INNER_CALL]) {
        if (!graph || !graph.value) return

        if (cell.isNode()) {
          graphStore.updateNode(cell.id, preprocess(key, current, graph.value), { silent: true })
        } else if (cell.isEdge()) {
          graphStore.updateEdge(cell.id, { [key]: current }, { silent: true })
        }
      }
    },
    100,
    { leading: true }
  )

  useGraphEvent('cell:change:*', debouncedCellChange)

  // 监听选择变化
  useGraphEvent('selection:changed', ({ added, removed, options }) => {
    if (!options || !options[INNER_CALL]) {
      added.forEach((item) => {
        if (item.isNode()) {
          graphStore.updateNode(item.id, { selected: true }, { silent: true })
        } else if (item.isEdge()) {
          graphStore.updateEdge(item.id, { selected: true }, { silent: true })
        }
      })

      removed.forEach((item) => {
        if (item.isNode()) {
          graphStore.updateNode(item.id, { selected: false }, { silent: true })
        } else if (item.isEdge()) {
          graphStore.updateEdge(item.id, { selected: false }, { silent: true })
        }
      })
    }
  })
}

// 组件挂载时设置事件监听
onMounted(() => {
  nextTick(() => {
    setupGraphEvents()
  })
})

// 监听动画时长变化，动态更新已启用动画的边
watch(
  () => props.edgeAnimationDuration,
  (val) => {
    if (!graph || !graph.value) return
    const edges = (graphStore?.edges || []).filter((e) => e.animated)
    edges.forEach((e) => {
      const cell = graph.value.getCellById(e.id)
      if (cell && cell.isEdge && cell.isEdge()) {
        cell.attr('line/style/animation', `animated-line ${val}s infinite linear`, {
          [INNER_CALL]: true
        })
      }
    })
  }
)
</script>
