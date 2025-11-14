<template>
  <div ref="containerRef" class="xflow-minimap" :class="className" :style="containerStyle"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { NodeView } from '@antv/x6'
import { MiniMap } from '@antv/x6-plugin-minimap'
import { useGraphInstance } from '../composables/useGraphInstance'

// 简单节点视图类
class SimpleNodeView extends NodeView {
  static nodeBackground = '#8f8f8f'

  renderMarkup() {
    const tag = this.cell.shape === 'circle' ? 'circle' : 'rect'
    return this.renderJSONMarkup({
      tagName: tag,
      selector: 'body'
    })
  }

  update() {
    super.update({
      body: {
        refWidth: '100%',
        refHeight: '100%',
        fill: SimpleNodeView.nodeBackground
      }
    })
  }
}

// Props 定义
const props = defineProps({
  className: {
    type: String,
    default: ''
  },
  style: {
    type: Object,
    default: () => ({})
  },
  width: {
    type: Number,
    default: 200
  },
  height: {
    type: Number,
    default: 160
  },
  padding: {
    type: Number,
    default: 10
  },
  simple: {
    type: Boolean,
    default: false
  },
  simpleNodeBackground: {
    type: String,
    default: '#8f8f8f'
  },
  scalable: {
    type: Boolean,
    default: true
  },
  minScale: {
    type: Number,
    default: 0.01
  },
  maxScale: {
    type: Number,
    default: 16
  }
})

const containerRef = ref(null)
const graph = useGraphInstance()

// 容器样式：限制宽高并默认绝对定位，避免占满整行
const containerStyle = computed(() => {
  const base = {
    width: props.width + 'px',
    height: props.height + 'px',
    position: 'absolute',
    zIndex: 10
  }

  // 直接合并用户传入的样式，不做额外处理
  return {
    ...base,
    ...(props.style || {})
  }
})

// 初始化 Minimap 插件
const initMinimap = () => {
  if (!graph || !graph.value || !containerRef.value) return

  // 移除已存在的插件（用类引用更稳妥）
  if (graph.value.getPlugin(MiniMap)) {
    graph.value.removePlugin(MiniMap)
  }

  // 设置简单节点背景色
  SimpleNodeView.nodeBackground = props.simpleNodeBackground

  // 添加新插件
  graph.value.use(
    new MiniMap({
      container: containerRef.value,
      width: props.width,
      height: props.height,
      padding: props.padding,
      scalable: props.scalable,
      minScale: props.minScale,
      maxScale: props.maxScale,
      graphOptions: props.simple
        ? {
            createCellView(cell) {
              if (cell.isEdge()) {
                return null
              }
              if (cell.isNode()) {
                return SimpleNodeView
              }
              return undefined
            }
          }
        : undefined
    })
  )
}

onMounted(async () => {
  await nextTick()
  initMinimap()
})

// 监听属性变化重新初始化插件
watch(
  () => [
    props.width,
    props.height,
    props.padding,
    props.simple,
    props.simpleNodeBackground,
    props.scalable,
    props.minScale,
    props.maxScale
  ],
  () => {
    initMinimap()
  }
)

// 当 graph 实例就绪时再初始化（解决装载时序竞态）
watch(
  () => graph && graph.value,
  (g) => {
    if (g) initMinimap()
  },
  { immediate: true }
)
</script>

<style scoped>
.xflow-minimap {
  display: inline-block;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}
</style>
