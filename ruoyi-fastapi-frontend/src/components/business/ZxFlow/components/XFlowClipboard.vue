<template>
  <!-- Clipboard 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { Clipboard } from '@antv/x6-plugin-clipboard'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  },
  useLocalStorage: {
    type: Boolean,
    default: false
  }
})

const graph = useGraphInstance()

// 初始化 Clipboard 插件
const initClipboard = () => {
  if (!graph || !graph.value) return

  // 移除已存在的插件
  if (graph.value.getPlugin('clipboard')) {
    graph.value.disposePlugins('clipboard')
  }

  // 添加新插件
  graph.value.use(
    new Clipboard({
      enabled: props.enabled,
      useLocalStorage: props.useLocalStorage
    })
  )
}

onMounted(() => {
  initClipboard()
})

// 监听属性变化重新初始化插件
watch(
  () => [props.enabled, props.useLocalStorage],
  () => {
    initClipboard()
  }
)

// 监听 graph 实例就绪后初始化（避免初始化早于 Graph 创建导致未安装插件）
watch(
  () => graph && graph.value,
  (val) => {
    if (val) initClipboard()
  },
  { immediate: true }
)
</script>
