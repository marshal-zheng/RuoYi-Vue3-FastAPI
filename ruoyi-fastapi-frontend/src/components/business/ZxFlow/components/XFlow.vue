<template>
  <div class="xflow-container">
    <slot></slot>
  </div>
</template>

<script setup>
import { provideGraphInstance } from '../composables/useGraphInstance'

// 提供 Graph 实例上下文
const { graph, setGraph } = provideGraphInstance()

// 向外暴露方法供子组件使用
defineExpose({
  graph,
  setGraph
})
</script>

<style scoped>
.xflow-container {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
