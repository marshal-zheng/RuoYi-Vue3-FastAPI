<template>
  <!-- Background 插件不需要渲染内容 -->
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useGraphInstance } from '../composables/useGraphInstance'

// Props 定义
const props = defineProps({
  color: {
    type: String,
    default: '#ffffff'
  },
  image: {
    type: String,
    default: ''
  },
  position: {
    type: String,
    default: 'center'
  },
  size: {
    type: String,
    default: 'auto auto'
  },
  repeat: {
    type: String,
    default: 'no-repeat'
  },
  opacity: {
    type: Number,
    default: 1
  }
})

const graph = useGraphInstance()

// 更新背景
const updateBackground = () => {
  if (!graph || !graph.value) return

  const backgroundOptions = {
    color: props.color,
    opacity: props.opacity
  }

  if (props.image) {
    backgroundOptions.image = props.image
    backgroundOptions.position = props.position
    backgroundOptions.size = props.size
    backgroundOptions.repeat = props.repeat
  }

  graph.value.drawBackground(backgroundOptions)
}

onMounted(() => {
  updateBackground()
})

// 监听属性变化
watch(
  () => [props.color, props.image, props.position, props.size, props.repeat, props.opacity],
  () => {
    updateBackground()
  }
)
</script>
