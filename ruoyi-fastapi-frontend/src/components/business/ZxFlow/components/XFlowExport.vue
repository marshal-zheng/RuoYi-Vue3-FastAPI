<template>
  <!-- Export 插件不渲染任何内容 → 仅负责安装图上导出能力 -->
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { Export } from '@antv/x6-plugin-export'
import { useGraphInstance } from '../composables/useGraphInstance'

const props = defineProps({
  enabled: {
    type: Boolean,
    default: true
  }
})

const graph = useGraphInstance()

const installExportPlugin = () => {
  const g = graph?.value
  if (!g) return

  if (g.getPlugin('export')) {
    g.disposePlugins('export')
  }

  if (!props.enabled) return

  g.use(new Export())
}

onMounted(() => {
  installExportPlugin()
})

watch(
  () => props.enabled,
  () => {
    installExportPlugin()
  }
)

watch(
  () => graph && graph.value,
  (val) => {
    if (val) installExportPlugin()
  },
  { immediate: true }
)
</script>
