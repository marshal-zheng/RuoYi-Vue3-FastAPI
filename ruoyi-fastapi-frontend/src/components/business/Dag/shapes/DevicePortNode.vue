<template>
  <div class="device-port-node relative overflow-visible" :style="{ width: containerWidth + 'px', height: containerHeight + 'px' }">
    <!-- 设备主体 - 金属芯片铭牌效果 -->
    <div 
      class="device-body absolute rounded-md shadow-2xl overflow-hidden"
      :style="{
        width: '70px',
        height: deviceRectHeight + 'px',
        left: deviceBodyLeft + 'px',
        top: deviceBodyTop + 'px',
        background: 'linear-gradient(135deg, #434343 0%, #282828 25%, #1a1a1a 50%, #282828 75%, #434343 100%)',
        border: '1px solid rgba(100, 100, 100, 0.6)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1), inset 0 -1px 0 rgba(0, 0, 0, 0.5)'
      }"
    >
      <!-- 顶部高光条 -->
      <div 
        class="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"
      ></div>
      
      <!-- 四角装饰螺丝孔 -->
      <div 
        v-for="corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right']"
        :key="corner"
        :class="[
          'absolute w-1.5 h-1.5 rounded-full bg-gradient-to-br from-zinc-600 to-zinc-800 shadow-inner',
          corner === 'top-left' ? 'top-1.5 left-1.5' : '',
          corner === 'top-right' ? 'top-1.5 right-1.5' : '',
          corner === 'bottom-left' ? 'bottom-1.5 left-1.5' : '',
          corner === 'bottom-right' ? 'bottom-1.5 right-1.5' : ''
        ]"
      >
        <!-- 螺丝孔中心点 -->
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-0.5 bg-black/60 rounded-full"></div>
      </div>
      
      <!-- 设备名称 - 竖向文字带金属质感 -->
      <div 
        class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-sm font-bold whitespace-nowrap"
        style="
          writing-mode: vertical-rl; 
          letter-spacing: 0.5em; 
          text-orientation: upright;
          color: #e0e0e0;
          text-shadow: 
            0 1px 0 rgba(255, 255, 255, 0.3),
            0 -1px 0 rgba(0, 0, 0, 0.8),
            0 0 10px rgba(200, 200, 200, 0.2);
        "
      >
        {{ label }}
      </div>
      
      <!-- 底部暗影条 -->
      <div 
        class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-black/50 to-transparent"
      ></div>
    </div>
    
    <!-- 注意：端口现在完全由 X6 的连接桩渲染，不再需要 HTML port-item -->
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  graph: {
    type: Object,
    default: null
  }
})

const dataVersion = ref(0)

const nodeData = computed(() => {
  dataVersion.value // 强制响应式依赖
  return props.node?.getData?.() || {}
})

const label = computed(() => nodeData.value.label || '设备')
const busType = computed(() => nodeData.value.busType || '')
const ports = computed(() => nodeData.value.ports || [])

// 尺寸常量
const DEVICE_WIDTH = 70  // 设备主体宽度
const SIDE_PORT_WIDTH = 32  // 左右端口宽度
const TOP_BOTTOM_PORT_HEIGHT = 12  // 上下端口高度
const BASE_DEVICE_HEIGHT = 80
const TEXT_FONT_SIZE = 14
const LETTER_SPACING_EM = 0.5
const TEXT_LINE_HEIGHT = TEXT_FONT_SIZE + TEXT_FONT_SIZE * LETTER_SPACING_EM
const CONTENT_VERTICAL_PADDING = 24
const TOP_BOTTOM_MARGIN = 0  // 上下端口紧贴设备主体，无间距

const labelLength = computed(() => Math.max(label.value.length, 1))

// 按位置分组端口（需要在容器尺寸计算之前定义）
const topPorts = computed(() => ports.value.filter(p => p.group === 'top'))
const rightPorts = computed(() => ports.value.filter(p => p.group === 'right'))
const bottomPorts = computed(() => ports.value.filter(p => p.group === 'bottom'))
const leftPorts = computed(() => ports.value.filter(p => p.group === 'left'))

// 根据设备名称长度计算设备主体高度
const deviceRectHeight = computed(() => {
  const textHeight = labelLength.value * TEXT_LINE_HEIGHT
  return Math.max(BASE_DEVICE_HEIGHT, textHeight + CONTENT_VERTICAL_PADDING)
})

// 容器尺寸（紧凑布局，刚好包裹设备和端口）
const containerWidth = computed(() => {
  const hasLeftPorts = leftPorts.value.length > 0
  const hasRightPorts = rightPorts.value.length > 0
  return (hasLeftPorts ? SIDE_PORT_WIDTH : 0) + DEVICE_WIDTH + (hasRightPorts ? SIDE_PORT_WIDTH : 0)
})

const containerHeight = computed(() => {
  const hasTopPorts = topPorts.value.length > 0
  const hasBottomPorts = bottomPorts.value.length > 0
  return (hasTopPorts ? TOP_BOTTOM_PORT_HEIGHT + TOP_BOTTOM_MARGIN : 0) + 
         deviceRectHeight.value + 
         (hasBottomPorts ? TOP_BOTTOM_MARGIN + TOP_BOTTOM_PORT_HEIGHT : 0)
})

// 设备主体在容器中的位置
const deviceBodyLeft = computed(() => {
  return leftPorts.value.length > 0 ? SIDE_PORT_WIDTH : 0
})

const deviceBodyTop = computed(() => {
  return topPorts.value.length > 0 ? TOP_BOTTOM_PORT_HEIGHT + TOP_BOTTOM_MARGIN : 0
})

// 设备中心 Y 坐标（用于左右端口定位）
const deviceCenterY = computed(() => deviceBodyTop.value + deviceRectHeight.value / 2)

// 端口位置计算函数（用于同步 X6 连接桩位置）
function getTopPortX(index, total) {
  const spacing = 25
  const deviceCenterX = deviceBodyLeft.value + DEVICE_WIDTH / 2
  const startX = deviceCenterX - ((total - 1) * spacing) / 2
  return startX + index * spacing
}

function getRightPortY(index, total) {
  const spacing = 20
  const centerY = deviceCenterY.value
  const startY = centerY - ((total - 1) * spacing) / 2
  return startY + index * spacing
}

function getBottomPortX(index, total) {
  const spacing = 25
  const deviceCenterX = deviceBodyLeft.value + DEVICE_WIDTH / 2
  const startX = deviceCenterX - ((total - 1) * spacing) / 2
  return startX + index * spacing
}

function getLeftPortY(index, total) {
  const spacing = 20
  const centerY = deviceCenterY.value
  const startY = centerY - ((total - 1) * spacing) / 2
  return startY + index * spacing
}

// 根据实际内容同步 X6 节点尺寸
const syncNodeSize = () => {
  if (!props.node || typeof props.node.getSize !== 'function' || typeof props.node.resize !== 'function') {
    return
  }
  const currentSize = props.node.getSize()
  const targetWidth = containerWidth.value
  const targetHeight = containerHeight.value
  if (!currentSize || currentSize.width !== targetWidth || currentSize.height !== targetHeight) {
    props.node.resize(targetWidth, targetHeight)
  }
}

// 同步 X6 端口位置，使其与视觉端口对齐
const syncPortPositions = () => {
  if (!props.node || typeof props.node.setPortProp !== 'function') {
    return
  }

  const allPorts = ports.value || []
  
  allPorts.forEach((port, index) => {
    const group = port.group
    let x, y
    
    // 根据端口组计算位置（相对于节点的坐标）
    // 注意：端口矩形在 X6 中是中心对齐的，所以需要调整 y 坐标让端口紧贴设备
    if (group === 'top') {
      const portIndex = topPorts.value.findIndex(p => p.id === port.id)
      if (portIndex >= 0) {
        x = getTopPortX(portIndex, topPorts.value.length)
        y = TOP_BOTTOM_PORT_HEIGHT / 2  // 端口中心在半高处，矩形从 0 到 12，紧贴设备顶部
      }
    } else if (group === 'bottom') {
      const portIndex = bottomPorts.value.findIndex(p => p.id === port.id)
      if (portIndex >= 0) {
        x = getBottomPortX(portIndex, bottomPorts.value.length)
        y = containerHeight.value - TOP_BOTTOM_PORT_HEIGHT / 2  // 端口中心在底部往上半高，紧贴设备底部
      }
    } else if (group === 'left') {
      const portIndex = leftPorts.value.findIndex(p => p.id === port.id)
      if (portIndex >= 0) {
        x = SIDE_PORT_WIDTH / 2  // 端口中心在半宽处，紧贴设备左侧
        y = getLeftPortY(portIndex, leftPorts.value.length)
      }
    } else if (group === 'right') {
      const portIndex = rightPorts.value.findIndex(p => p.id === port.id)
      if (portIndex >= 0) {
        x = containerWidth.value - SIDE_PORT_WIDTH / 2  // 端口中心在右边往左半宽，紧贴设备右侧
        y = getRightPortY(portIndex, rightPorts.value.length)
      }
    }
    
    if (x !== undefined && y !== undefined) {
      // 使用绝对定位更新端口位置
      props.node.setPortProp(port.id, 'args', { x, y })
      props.node.setPortProp(port.id, ['position', 'name'], 'absolute')
    }
  })
}

watch(
  [() => props.node, () => containerWidth.value, () => containerHeight.value, () => ports.value],
  () => {
    syncNodeSize()
    // 延迟一帧执行端口同步，确保尺寸先更新
    setTimeout(() => {
      syncPortPositions()
    }, 0)
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  syncNodeSize()
  // 初始延迟
  setTimeout(() => {
    syncPortPositions()
  }, 100)
  
  // 额外的延迟同步，确保拖拽创建的节点也能正确同步
  setTimeout(() => {
    syncPortPositions()
  }, 300)
})

// 注意：端口交互现在完全由 X6 的连接桩处理
// 所有端口的点击、右键菜单等事件都在 detail.vue 中通过 X6 事件系统处理

// 监听节点数据变化
watch(
  () => props.node?.getData?.(),
  () => {
    dataVersion.value++
  },
  { deep: true }
)

// 监听X6节点的数据变化事件
if (props.node) {
  props.node.on('change:data', () => {
    dataVersion.value++
  })
}
</script>

<style lang="scss" scoped>
.device-port-node {
  // 设备主体样式
  .device-body {
    pointer-events: all;
  }
}

// foreignObject 容器样式
:global(.dag-page foreignObject > body) {
  margin: 0;
  min-height: 100%;
  display: block;
  overflow: visible;
}

// 覆盖 X6 选择框样式
:global(.x6-widget-selection-box) {
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

// X6 连接桩样式（矩形 + 文本标签）
:global(.x6-port-body) {
  cursor: crosshair !important;
  transition: all 0.2s ease-in-out;
  
  // 悬停效果 - 保持原有颜色，增加阴影和边框宽度
  &:hover {
    stroke-width: 2 !important;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
  }
}

// 连接桩文本标签
:global(.x6-port text) {
  pointer-events: none;
  user-select: none;
}

// 连接模式时高亮所有可用端口（保持原有颜色）
:global(.x6-graph.connecting) {
  .x6-port-body {
    stroke-width: 2 !important;
    animation: port-pulse 1.5s ease-in-out infinite;
    filter: drop-shadow(0 2px 6px currentColor);
  }
}

@keyframes port-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
