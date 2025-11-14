<template>
  <div class="dag-control">
    <el-dropdown trigger="click" @command="(key) => changeZoom('zoomTo', key)">
      <el-button size="small" class="dag-control__dropdown">
        {{ Math.round(zoom * 100) }}%
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item v-for="item in dropDownItems" :key="item.key" :command="item.key">
            {{ item.label }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <el-tooltip content="放大" placement="top">
      <el-button size="small" @click="() => changeZoom('zoomIn')" :disabled="zoom >= 1.5">
        <el-icon><ZoomIn /></el-icon>
      </el-button>
    </el-tooltip>

    <el-tooltip content="缩小" placement="top">
      <el-button size="small" @click="() => changeZoom('zoomOut')" :disabled="zoom <= 0.5">
        <el-icon><ZoomOut /></el-icon>
      </el-button>
    </el-tooltip>

    <el-tooltip content="适应屏幕" placement="top">
      <el-button size="small" @click="() => changeZoom('zoomToFit')">
        <el-icon><FullScreen /></el-icon>
      </el-button>
    </el-tooltip>

    <el-tooltip content="回到起点" placement="top">
      <el-button size="small" @click="() => changeZoom('zoomToOrigin')">
        <el-icon><Aim /></el-icon>
      </el-button>
    </el-tooltip>
  </div>
</template>

<script setup>
import { isRef, onMounted, ref, watch } from 'vue'
import { Aim, FullScreen, ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import { useGraphEvent } from '../../ZxFlow/composables/useGraphEvent'
import { useGraphInstance } from '../../ZxFlow/composables/useGraphInstance'

const dropDownItems = [
  { key: '1', label: '50%' },
  { key: '2', label: '75%' },
  { key: '3', label: '100%' },
  { key: '4', label: '125%' },
  { key: '5', label: '150%' }
]

const props = defineProps({
  graph: {
    type: Object,
    default: null
  }
})

const graph = props.graph
  ? isRef(props.graph)
    ? props.graph
    : ref(props.graph)
  : useGraphInstance({ required: false })
const zoom = ref(1)

useGraphEvent(
  'scale',
  ({ sx }) => {
    zoom.value = sx
  },
  graph
)

const syncZoom = () => {
  const g = graph?.value
  if (g && typeof g.zoom === 'function') {
    zoom.value = g.zoom()
  }
}

onMounted(() => {
  syncZoom()
})

watch(
  () => graph?.value,
  (next) => {
    if (next) {
      syncZoom()
    }
  }
)

const changeZoom = (type, key) => {
  const g = graph?.value
  if (!g) return
  switch (type) {
    case 'zoomIn':
      if (zoom.value < 1.5) {
        g.zoom(0.25)
      }
      break
    case 'zoomOut':
      if (zoom.value > 0.5) {
        g.zoom(-0.25)
      }
      break
    case 'zoomToFit':
      g.zoomToFit({ maxScale: 1 })
      break
    case 'zoomToOrigin':
      g.zoomTo(1)
      break
    case 'zoomTo': {
      const idx = parseInt(key || '1', 10)
      const zoomNum = 0.25 * (idx + 1)
      g.zoomTo(zoomNum)
      break
    }
    default:
      break
  }
  zoom.value = g.zoom()
}
</script>

<style scoped lang="scss">
.dag-control {
  display: inline-flex;
  gap: 6px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  &__dropdown {
    min-width: 72px;
  }
}
</style>
