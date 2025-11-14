<template>
  <!-- Transform 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { Transform } from '@antv/x6-plugin-transform'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  },
  resizing: {
    type: [Boolean, Object],
    default: true
  },
  rotating: {
    type: [Boolean, Object],
    default: true
  }
})

const graph = useGraphInstance()

// 初始化 Transform 插件
const initTransform = () => {
  if (!graph || !graph.value) return

  // 移除已存在的插件
  if (graph.value.getPlugin('transform')) {
    graph.value.disposePlugins('transform')
  }

  // 添加新插件
  graph.value.use(
    new Transform({
      enabled: props.enabled,
      resizing: props.resizing,
      rotating: props.rotating
    })
  )
}

onMounted(() => {
  initTransform()
})

// 监听属性变化重新初始化插件
watch(
  () => [props.enabled, props.resizing, props.rotating],
  () => {
    initTransform()
  }
)
</script>
