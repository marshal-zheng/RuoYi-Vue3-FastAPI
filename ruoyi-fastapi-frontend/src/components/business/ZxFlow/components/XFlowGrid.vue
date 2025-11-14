<template>
  <!-- Grid 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch, nextTick } from 'vue'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  size: {
    type: Number,
    default: 10,
    description: '网格间距（点与点之间的距离）'
  },
  type: {
    type: String,
    default: 'dot', // 'dot' | 'fixedDot' | 'mesh'
    validator: (value) => ['dot', 'fixedDot', 'mesh'].includes(value)
  },
  // 新增：点的大小配置
  dotSize: {
    type: Number,
    default: 1,
    description: 'dot 类型网格中点的大小（直径）'
  },
  // 网格颜色
  color: {
    type: String,
    default: '#ddd',
    description: '网格颜色'
  },
  args: {
    type: Object,
    default: () => ({})
  },
  visible: {
    type: Boolean,
    default: true
  }
})

const graph = useGraphInstance()

// 更新网格
const updateGrid = async () => {
  if (!graph || !graph.value) return

  // 等待DOM更新
  await nextTick()

  try {
    // 先清除，再根据最新类型重绘，保证切换立即生效
    graph.value.clearGrid()

    if (props.visible) {
      // 根据 X6 API，不同类型的网格参数传递方式不同
      const gridOptions = {
        type: props.type
      }

      if (props.type === 'dot' || props.type === 'fixedDot') {
        // dot 类型网格：size 作为顶级参数，点大小和颜色在 args 中
        gridOptions.size = props.size
        gridOptions.args = {
          color: props.color,
          thickness: props.dotSize,
          ...props.args
        }
      } else if (props.type === 'mesh') {
        // mesh 类型网格：size 在 args 中
        gridOptions.args = {
          size: props.size,
          color: props.color,
          ...props.args
        }
      } else {
        // 其他类型：保持原有逻辑
        gridOptions.args = {
          size: props.size,
          color: props.color,
          ...props.args
        }
      }

      console.log('XFlowGrid: Drawing grid with options:', gridOptions)
      graph.value.drawGrid(gridOptions)
      // 显示网格
      graph.value.showGrid()
    } else {
      // 隐藏网格
      graph.value.hideGrid()
    }
  } catch (error) {
    console.warn('Grid update error:', error)
  }
}

onMounted(async () => {
  // 等待一小段时间确保Graph完全初始化
  await nextTick()
  setTimeout(() => {
    updateGrid()
  }, 100)
})

// 监听属性变化
watch(
  () => [props.size, props.type, props.dotSize, props.color, props.args, props.visible],
  () => {
    updateGrid()
  }
)
</script>
