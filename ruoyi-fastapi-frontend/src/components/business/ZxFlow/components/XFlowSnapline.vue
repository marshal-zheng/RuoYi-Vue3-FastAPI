<template>
  <!-- Snapline 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch, nextTick } from 'vue'
import { Snapline } from '@antv/x6-plugin-snapline'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  },
  className: {
    type: String,
    default: 'x6-widget-snapline'
  },
  tolerance: {
    type: Number,
    default: 10
  },
  sharp: {
    type: Boolean,
    default: false
  }
})

const graph = useGraphInstance()

// 初始化 Snapline 插件
const initSnapline = async () => {
  await nextTick()

  if (!graph) {
    if (import.meta.env?.DEV) {
      console.warn('[ZxFlow] Snapline requires graph context. Did you forget to wrap with <XFlow>?')
    }
    return
  }

  if (!graph.value) {
    return
  }

  try {
    // 移除已存在的插件
    if (graph.value.getPlugin('snapline')) {
      graph.value.disposePlugins('snapline')
    }

    // 添加新插件
    const snaplinePlugin = new Snapline({
      enabled: props.enabled,
      className: props.className,
      tolerance: props.tolerance,
      sharp: props.sharp
    })

    graph.value.use(snaplinePlugin)
  } catch (error) {
    console.error('Failed to initialize snapline plugin:', error)
  }
}

// 监听 graph 实例变化
watch(
  graph,
  async (newGraph) => {
    if (newGraph) {
      await initSnapline()
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await initSnapline()
})

// 监听属性变化重新初始化插件
watch(
  () => [props.enabled, props.className, props.tolerance, props.sharp],
  async () => {
    await initSnapline()
  }
)
</script>
