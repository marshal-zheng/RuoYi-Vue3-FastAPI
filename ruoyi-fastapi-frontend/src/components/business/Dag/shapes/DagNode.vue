<template>
  <div
    class="zx-dag-node"
    :class="[
      orientationClass,
      nodeTypeClass,
      { 'has-model': hasModel, 'no-model': !hasModel, 'is-collapsed': isCollapsed }
    ]"
  >
    <button
      v-if="canCollapse"
      type="button"
      :class="collapseButtonClass"
      :title="collapseTitle"
      @click.stop="toggleCollapse"
    >
      {{ collapseLabel }}
    </button>

    <div v-if="hasWeight" class="zx-dag-node__weight">{{ weightDisplay }}</div>

    <div class="zx-dag-node__label">
      <span v-if="isVerticalLayout" class="zx-dag-node__label-text vertical">
        <span v-for="(char, index) in verticalLabelChars" :key="index">{{ char }}</span>
      </span>
      <span v-else class="zx-dag-node__label-text">{{ label }}</span>
    </div>

    <!-- 状态指示器 / 模型信息 -->
    <div v-if="showIndicator" class="zx-dag-node__indicator">
      <el-popover
        v-if="hasModel && modelData"
        :width="400"
        :title="modelPopoverTitle"
        trigger="click"
        :placement="tooltipPlacement"
      >
        <template #reference>
          <el-tooltip :content="modelTooltip" :placement="tooltipPlacement" :offset="12">
            <el-icon :size="14" :color="modelIconColor" style="cursor: pointer">
              <Setting />
            </el-icon>
          </el-tooltip>
        </template>
        <!-- 紧凑型模型信息展示 -->
        <div class="model-info">
          <div class="info-row">
            <span class="label">名称</span>
            <span class="value">{{ modelDisplayName }}</span>
          </div>
          <div v-if="modelData.oprModelDesc || modelData.description" class="info-row">
            <span class="label">描述</span>
            <span class="value">{{ modelData.oprModelDesc || modelData.description }}</span>
          </div>
          <div class="info-row">
            <span class="label">ID</span>
            <span class="value code">{{ modelData.id }}</span>
          </div>
          <div v-if="modelData.oprModelPath" class="info-row">
            <span class="label">路径</span>
            <span class="value code">{{ modelData.oprModelPath }}</span>
          </div>
          <div v-if="modelData.index !== undefined" class="info-row">
            <span class="label">顺序</span>
            <span class="value">{{ modelData.index }}</span>
          </div>
          <div class="info-row">
            <span class="label">状态</span>
            <span class="value" :class="modelStatusClass">{{ modelStatusText }}</span>
          </div>
          <div v-if="modelData.createTime" class="info-row">
            <span class="label">创建</span>
            <span class="value">{{ formatTime(modelData.createTime) }}</span>
          </div>
        </div>
      </el-popover>
      <el-tooltip v-else :content="modelTooltip" :placement="tooltipPlacement" :offset="12">
        <el-icon :size="14" :color="modelIconColor">
          <QuestionFilled />
        </el-icon>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useOptionalGraphInstance } from '@/components/business/ZxFlow/composables/useGraphInstance'
import { Setting, QuestionFilled } from '@element-plus/icons-vue'
import { toggleNodeCollapse } from '../utils/collapse.js'

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

// 响应式数据版本号，用于强制重新计算
const dataVersion = ref(0)
const graphInstance = useOptionalGraphInstance()

const formatWeightDisplay = (value) => {
  const num = Number(value)
  if (!Number.isFinite(num)) return '--'
  // 使用 Math.round 来避免浮点数精度问题，与 IndicatorDagEditor 保持一致
  const rounded = Math.round(num * 100) / 100
  const fixed = rounded.toFixed(2)
  return fixed.endsWith('.00') ? String(rounded.toFixed(0)) : fixed
}

const nodeData = computed(() => {
  // 依赖dataVersion来强制重新计算
  dataVersion.value
  const data = props.node?.getData?.() || {}
  return data
})

// 监听节点数据变化，强制更新
watch(
  () => props.node?.getData?.(),
  (newData, oldData) => {
    // 强制重新计算
    dataVersion.value++
  },
  { deep: true, immediate: false }
)

// 支持两种数据结构：旧的直接结构和新的 properties 结构
const properties = computed(() => {
  const props = nodeData.value.properties || {}
  return props
})
const content = computed(() => {
  const contentData = properties.value.content || {}
  return contentData
})

const label = computed(() => {
  // 优先使用顶层 label，然后是 content.label，最后回退到空字符串
  const labelValue = nodeData.value.label || content.value.label || ''
  return labelValue
})

// 计算模型相关的计算属性
const nodeType = computed(() => {
  // 优先使用新结构，回退到旧结构
  return nodeData.value.type || (properties.value.level === 1 ? 'root-node' : 'leaf-node')
})

const isLeafNode = computed(() => nodeType.value === 'leaf-node')
const nodeTypeClass = computed(() => (isLeafNode.value ? 'leaf-node' : 'non-leaf-node'))
const layoutDirection = computed(() => {
  const direction = nodeData.value.layoutDirection || 'horizontal'
  const normalized = direction === 'vertical' ? 'vertical' : 'horizontal'
  return normalized
})
const orientationClass = computed(() => layoutDirection.value)
const isVerticalLayout = computed(() => layoutDirection.value === 'vertical')
const verticalLabelChars = computed(() => {
  if (!isVerticalLayout.value) return []
  const text = label.value || ''
  return Array.from(String(text))
})
const tooltipPlacement = computed(() => (layoutDirection.value === 'vertical' ? 'top' : 'bottom'))
const showIndicator = computed(() => isLeafNode.value)
const isCollapsed = computed(() => nodeData.value.collapsed === true)
const weightValue = computed(() => {
  const directWeight = nodeData.value.weight
  const propertyWeight = properties.value.weight
  const contentWeight = content.value.weight
  return directWeight ?? propertyWeight ?? contentWeight ?? null
})
const hasWeight = computed(() => {
  const value = weightValue.value
  return value !== null && value !== undefined && value !== ''
})
const weightDisplay = computed(() => {
  if (!hasWeight.value) return ''
  const value = weightValue.value
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value.toString() : ''
  }
  return String(value)
})
const modelData = computed(() => {
  // 优先使用新结构，回退到旧结构
  return properties.value.otherData || nodeData.value.otherData || {}
})
const hasModel = computed(
  () => isLeafNode.value && modelData.value && Object.keys(modelData.value).length > 0
)

const canCollapse = computed(() => {
  dataVersion.value
  const flag = nodeData.value.hasChildren
  if (typeof flag === 'boolean') {
    return flag
  }
  const node = props.node
  const graph = props.graph || graphInstance?.value || node?.graph || node?.model?.graph
  const edges = graph?.getOutgoingEdges?.(node) || node?.getOutgoingEdges?.()
  return Array.isArray(edges) ? edges.length > 0 : false
})

const collapseLabel = computed(() => (isCollapsed.value ? '+' : '-'))
const collapseTitle = computed(() => (isCollapsed.value ? '展开节点' : '收起节点'))
const collapseButtonClass = computed(() => [
  'zx-dag-node__collapse',
  orientationClass.value === 'vertical' ? 'vertical' : 'horizontal',
  isCollapsed.value ? 'is-collapsed' : 'is-expanded'
])

const toggleCollapse = () => {
  if (!props.node) return
  const graphRef =
    props.graph || graphInstance?.value || props.node?.graph || props.node?.model?.graph
  if (!graphRef) return
  toggleNodeCollapse(graphRef, props.node.id)
}

// 模型图标配置
const modelIconColor = computed(() => {
  if (!isLeafNode.value) {
    return '#d9d9d9' // 非叶子节点置灰
  }
  return hasModel.value ? 'var(--el-color-primary)' : 'var(--el-color-danger)'
})

const modelPopoverTitle = computed(() => {
  if (!isLeafNode.value) {
    return '节点信息'
  }
  return hasModel.value ? '计算模型信息' : '未绑定计算模型'
})

const modelTooltip = computed(() => {
  if (!isLeafNode.value) {
    return '非叶子节点'
  }
  return hasModel.value ? '点击查看计算模型详情' : '该节点尚未绑定计算模型'
})

// 新增的模型信息展示相关计算属性
const modelDisplayName = computed(() => {
  return (
    modelData.value.oprModelName ||
    modelData.value.title ||
    modelData.value.label ||
    modelData.value.name ||
    '未命名模型'
  )
})

const modelStatusText = computed(() => {
  const state = modelData.value.state
  if (state === null || state === undefined) return '未知状态'
  if (state === 0) return '未启用'
  if (state === 1) return '已启用'
  return `状态${state}`
})

const modelStatusClass = computed(() => {
  const state = modelData.value.state
  if (state === 1) return 'status-active'
  if (state === 0) return 'status-inactive'
  return 'status-unknown'
})

// 时间格式化方法
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  try {
    // 如果是标准时间格式，直接返回
    if (timeStr.includes('-') && timeStr.includes(':')) {
      return timeStr
    }
    // 如果是时间戳，转换为可读格式
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return timeStr
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return timeStr
  }
}

// 监听节点数据变化
watch(
  () => props.node,
  (newNode, oldNode) => {
    if (newNode && newNode !== oldNode) {
      dataVersion.value++
    }
  },
  { immediate: false }
)

// 监听X6节点的数据变化事件
if (props.node) {
  // 监听节点的change:data事件
  props.node.on('change:data', () => {
    dataVersion.value++
  })
}
</script>

<style lang="scss">
.dag-page foreignObject > body {
  margin: 0;
  min-height: 100%;
  display: block;
  place-items: initial;
}

.zx-dag-node {
  display: flex;
  align-items: stretch;
  width: 100%;
  height: 100%;
  position: relative;
  // min-height: 40px;
  border: 1px solid #d9dfe7;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 34, 58, 0.08);
  cursor: pointer;
  box-sizing: border-box;
  overflow: visible;

  &__collapse {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 1px solid rgba(64, 158, 255, 0.6);
    background: #409eff;
    color: #fff;
    font-size: 16px;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
    z-index: 2;
    box-shadow: 0 4px 10px rgba(64, 158, 255, 0.15);
    transition:
      transform 0.15s ease,
      background 0.15s ease;
    pointer-events: auto;
  }

  &__collapse:hover {
    background: #66b1ff;
  }

  &__collapse.horizontal {
    top: 50%;
    right: -21px;
    transform: translateY(-50%);
    border-radius: 0 10px 10px 0;
  }

  &__collapse.vertical {
    bottom: -21px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 0 0 10px 10px;
  }

  &__collapse.is-collapsed {
    background: #67c23a;
    border-color: rgba(103, 194, 58, 0.28);
    box-shadow: 0 2px 6px rgba(103, 194, 58, 0.25);
  }

  &__collapse.horizontal.is-collapsed {
    border-radius: 0 10px 10px 0;
  }

  &__collapse.vertical.is-collapsed {
    border-radius: 0 0 10px 10px;
  }

  &__weight {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 44px;
    padding: 0 8px;
    background: #f5f7fa;
    color: #1f2d3d;
    font-size: 13px;
    font-weight: 600;
    border-right: 1px solid #e3e8ee;
    white-space: nowrap;
  }

  &__indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    padding: 0 4px;
    border-left: 1px solid #e3e8ee;
    background: transparent;
    color: #909399;
  }

  &.leaf-node &__indicator {
    color: #409eff;
  }

  &.non-leaf-node &__indicator {
    color: #909399;
  }

  &__label {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px 12px;
    color: #303133;
    font-size: 14px;
    font-weight: 500;
    overflow: hidden;
  }

  &__label-text {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    text-align: center;
    line-height: 1.4;
    word-break: break-all;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__label-text.vertical {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1px;
    width: auto;
    max-width: 100%;
    overflow: visible;
    text-overflow: unset;
  }

  &__label-text.vertical > span {
    display: block;
    white-space: nowrap;
  }

  &.vertical {
    flex-direction: column;
    width: 100%;
    min-height: 160px;
    border-color: #d6e4ff;
    background: linear-gradient(180deg, #f7f9ff 0%, #ffffff 85%);
  }

  &.vertical &__weight {
    min-width: auto;
    width: 100%;
    height: 36px;
    border-right: none;
    border-bottom: 1px solid #dae1f0;
    font-size: 14px;
    order: 1;
  }

  &.vertical &__label {
    width: 100%;
    padding: 16px 12px;
    min-height: 120px;
    color: #1f2d3d;
    font-size: 16px;
    font-weight: 600;
    order: 2;
    flex: 1;
  }

  &.vertical &__label-text.vertical {
    width: 100%;
  }

  &.vertical &__indicator {
    width: 100%;
    height: 36px;
    border-left: none;
    border-top: 1px solid #dae1f0;
    border-radius: 0 0 6px 6px;
    order: 3;
  }

  &.vertical.leaf-node.has-model &__indicator {
    background: rgba(255, 153, 0, 0.14);
    color: #fa8c16;
  }

  &.vertical.leaf-node.no-model &__indicator {
    background: rgba(255, 77, 79, 0.12);
    color: #f56c6c;
  }

  &.horizontal &__label-text {
    writing-mode: initial;
    text-orientation: initial;
    letter-spacing: 0;
    white-space: nowrap;
  }
}

// 紧凑型模型信息展示
.model-info {
  padding: 12px;
  min-width: 280px;
  max-width: 380px;

  .info-row {
    display: flex;
    margin-bottom: 8px;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      width: 60px;
      color: #909399;
      font-size: 12px;
      flex-shrink: 0;
    }

    .value {
      flex: 1;
      color: #606266;
      font-size: 12px;
      word-break: break-all;

      &.code {
        font-family: monospace;
        background: #f5f7fa;
        padding: 2px 4px;
        border-radius: 2px;
        font-size: 11px;
      }

      &.status-active {
        color: #67c23a;
        font-weight: 500;
      }

      &.status-inactive {
        color: #e6a23c;
        font-weight: 500;
      }

      &.status-unknown {
        color: #f56c6c;
        font-weight: 500;
      }
    }
  }
}
</style>
