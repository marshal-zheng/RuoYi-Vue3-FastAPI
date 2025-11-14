<template>
  <!-- History 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { History } from '@antv/x6-plugin-history'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  },
  ignoreAdd: {
    type: Boolean,
    default: false
  },
  ignoreRemove: {
    type: Boolean,
    default: false
  },
  ignoreChange: {
    type: Boolean,
    default: false
  },
  beforeAddCommand: {
    type: Function,
    default: null
  },
  afterAddCommand: {
    type: Function,
    default: null
  }
})

const graph = useGraphInstance()

// 初始化 History 插件
const initHistory = () => {
  if (!graph || !graph.value) return

  // 移除已存在的插件
  if (graph.value.getPlugin('history')) {
    graph.value.disposePlugins('history')
  }

  // 添加新插件
  graph.value.use(
    new History({
      enabled: props.enabled,
      ignoreAdd: props.ignoreAdd,
      ignoreRemove: props.ignoreRemove,
      ignoreChange: props.ignoreChange,
      beforeAddCommand: props.beforeAddCommand,
      afterAddCommand: props.afterAddCommand
    })
  )
}

onMounted(() => {
  initHistory()
})

// 监听属性变化重新初始化插件
watch(
  () => [
    props.enabled,
    props.ignoreAdd,
    props.ignoreRemove,
    props.ignoreChange,
    props.beforeAddCommand,
    props.afterAddCommand
  ],
  () => {
    initHistory()
  }
)

// 监听 graph 实例就绪后初始化
watch(
  () => graph && graph.value,
  (val) => {
    if (val) initHistory()
  },
  { immediate: true }
)
</script>
