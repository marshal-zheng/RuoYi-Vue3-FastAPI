<template>
  <div class="operator-library">
    <!-- Header区域 -->
    <div class="library-header">
      <h3 class="header-title">{{ title }}</h3>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        :placeholder="searchPlaceholder"
        :prefix-icon="Search"
        clearable
        size="default"
        :disabled="loading"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="loading-icon is-loading"><Loading /></el-icon>
      <div class="loading-text">{{ textConfig.loadingText }}</div>
    </div>

    <!-- 算子列表 - 分类展示 -->
    <div v-else class="operator-list">
      <!-- 搜索模式：扁平展示 -->
      <template v-if="searchKeyword">
        <div
          v-for="item in displayOperators"
          :key="item.key"
          class="operator-item"
          @mousedown.stop.prevent="(e) => handleMouseDown(e, item)"
        >
          <div class="operator-icon">
            <el-icon><Box /></el-icon>
          </div>
          <div class="operator-content">
            <div class="operator-title">{{ item.title }}</div>
            <div class="operator-category">{{ item.category }}</div>
          </div>
        </div>

        <!-- 搜索无结果状态 -->
        <div v-if="displayOperators.length === 0" class="empty-state">
          <el-icon class="empty-icon"><Search /></el-icon>
          <div class="empty-text">{{ textConfig.emptySearchText }}</div>
          <div class="empty-desc">{{ textConfig.emptySearchDesc }}</div>
        </div>
      </template>

      <!-- 分类模式：按分类展示 -->
      <template v-else>
        <div
          v-for="group in displayCategoryGroups"
          :key="group.key"
          class="category-group"
        >
          <div class="category-header" @click="toggleCategory(group.key)">
            <el-icon class="category-icon" :class="{ collapsed: collapsedCategories[group.key] }">
              <ArrowRight />
            </el-icon>
            <span class="category-title">{{ group.title }}</span>
            <span class="category-count">{{ group.items.length }}</span>
          </div>
          <div v-show="!collapsedCategories[group.key]" class="category-items">
            <div
              v-for="item in group.items"
              :key="item.key"
              class="operator-item"
              @mousedown.stop.prevent="(e) => handleMouseDown(e, item)"
            >
              <div class="operator-icon">
                <el-icon><Box /></el-icon>
              </div>
              <div class="operator-title">{{ item.title }}</div>
            </div>
          </div>
        </div>

        <!-- 无数据状态 -->
        <div v-if="displayCategoryGroups.length === 0" class="empty-state">
          <el-icon class="empty-icon"><Box /></el-icon>
          <div class="empty-text">{{ textConfig.emptyDataText }}</div>
          <div class="empty-desc">{{ textConfig.emptyDataDesc }}</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef } from 'vue'
import { Search, Box, Loading, ArrowRight } from '@element-plus/icons-vue'
import { useDnd } from '../../ZxFlow/composables/useDnd'
import { DAG_NODE, DEVICE_PORT_NODE, registerDagShapes } from '../shapes/registerDagShapes'
import { useUserOperators } from '../composables/useUserOperators'
import { generateNodeId, generateContentId } from '../utils/nodeDataUtils'
import { getNodeSizeByLayout } from '../utils/nodeGeometry.js'

registerDagShapes()

// 分类折叠状态
const collapsedCategories = ref({})

// Props 定义
const props = defineProps({
  /**
   * 主图实例引用（可选），用于在图渲染后获取最新的 Graph
   */
  graphInstance: {
    type: [Object, Function],
    default: null
  },
  /**
   * 是否为只读模式（只读时禁用拖拽）
   */
  readonly: {
    type: Boolean,
    default: false
  },
  /**
   * 用户传入的简单数据列表
   * @type {Array<{name: string, value: string}>}
   */
  operators: {
    type: Array,
    default: () => []
  },
  /**
   * 是否显示加载状态
   */
  loading: {
    type: Boolean,
    default: false
  },
  /**
   * 搜索框占位符
   */
  searchPlaceholder: {
    type: String,
    default: '搜索算子、组件...'
  },
  /**
   * 库标题
   */
  title: {
    type: String,
    default: '算子库'
  },
  /**
   * 布局方向：vertical(竖向-上下连接桩) | horizontal(横向-左右连接桩)
   */
  layout: {
    type: String,
    default: 'horizontal',
    validator: (value) => ['vertical', 'horizontal'].includes(value)
  },
  /**
   * 文案配置
   */
  textConfig: {
    type: Object,
    default: () => ({
      loadingText: '正在加载算子...',
      emptySearchText: '未找到相关算子',
      emptySearchDesc: '请尝试其他关键词',
      emptyDataText: '暂无算子数据',
      emptyDataDesc: '请传入算子数据'
    })
  }
})

const searchKeyword = ref('')
const idSeed = ref(0)
const graphInstanceRef = toRef(props, 'graphInstance')
const { startDrag } = useDnd(graphInstanceRef)

// 使用新的 composable 处理用户数据
const { processedOperators, categoryGroups, stats } = useUserOperators(
  computed(() => props.operators),
  computed(() => props.layout)
)

// 搜索时的扁平展示
const displayOperators = computed(() => {
  if (!searchKeyword.value) {
    return processedOperators.value
  }
  const lowerKeyword = searchKeyword.value.toLowerCase()
  return processedOperators.value.filter(
    (item) =>
      item.title.toLowerCase().includes(lowerKeyword) ||
      (item.shortDesc && item.shortDesc.toLowerCase().includes(lowerKeyword)) ||
      (item.category && item.category.toLowerCase().includes(lowerKeyword)) ||
      (item.originalData.value && item.originalData.value.toLowerCase().includes(lowerKeyword))
  )
})

// 分类展示
const displayCategoryGroups = computed(() => {
  return categoryGroups.value || []
})

// 切换分类折叠状态
const toggleCategory = (key) => {
  collapsedCategories.value[key] = !collapsedCategories.value[key]
}

const createNodeId = () => {
  return generateNodeId()
}

const handleMouseDown = (event, item) => {
  if (props.readonly) {
    return
  }
  const id = createNodeId()
  const layoutDirection = props.layout === 'vertical' ? 'vertical' : 'horizontal'
  
  // 判断是否为设备节点（有 nodeType 和 ports 字段）
  // useUserOperators 会把所有字段展平，所以直接从 item 上读取
  const isDeviceNode = item.nodeType === 'device-port-node' && 
                       item.ports && 
                       Array.isArray(item.ports)

  console.log('拖拽节点信息:', {
    title: item.title,
    nodeType: item.nodeType,
    isDeviceNode,
    ports: item.ports,
    item
  })

  // 根据节点类型选择 shape 和尺寸
  let shape, width, height, ports
  
  if (isDeviceNode) {
    // 设备节点使用 DEVICE_PORT_NODE shape
    shape = DEVICE_PORT_NODE
    width = 190
    height = 120
    
    // 构建端口组配置（与 device/detail.vue 保持一致）
    const portGroups = {
      top: {
        position: { name: 'absolute' },
        markup: [
          { tagName: 'rect', selector: 'portBody' },
          { tagName: 'text', selector: 'portLabel' }
        ],
        attrs: {
          portBody: {
            width: 24,
            height: 12,
            x: -12,
            y: -6,
            magnet: true,
            fill: '#fff',
            strokeWidth: 1,
            cursor: 'crosshair',
            rx: 0,
            ry: 0
          },
          portLabel: {
            text: '',
            fontSize: 7,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
            fill: '#4b5563',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            x: 0,
            y: 0,
            pointerEvents: 'none'
          }
        }
      },
      bottom: {
        position: { name: 'absolute' },
        markup: [
          { tagName: 'rect', selector: 'portBody' },
          { tagName: 'text', selector: 'portLabel' }
        ],
        attrs: {
          portBody: {
            width: 24,
            height: 12,
            x: -12,
            y: -6,
            magnet: true,
            fill: '#fff',
            strokeWidth: 1,
            cursor: 'crosshair',
            rx: 0,
            ry: 0
          },
          portLabel: {
            text: '',
            fontSize: 7,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
            fill: '#4b5563',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            x: 0,
            y: 0,
            pointerEvents: 'none'
          }
        }
      },
      left: {
        position: { name: 'absolute' },
        markup: [
          { tagName: 'rect', selector: 'portBody' },
          { tagName: 'text', selector: 'portLabel' }
        ],
        attrs: {
          portBody: {
            width: 32,
            height: 12,
            x: -16,
            y: -6,
            magnet: true,
            fill: '#fff',
            strokeWidth: 1,
            cursor: 'crosshair',
            rx: 0,
            ry: 0
          },
          portLabel: {
            text: '',
            fontSize: 7,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
            fill: '#4b5563',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            x: 0,
            y: 0,
            pointerEvents: 'none'
          }
        }
      },
      right: {
        position: { name: 'absolute' },
        markup: [
          { tagName: 'rect', selector: 'portBody' },
          { tagName: 'text', selector: 'portLabel' }
        ],
        attrs: {
          portBody: {
            width: 32,
            height: 12,
            x: -16,
            y: -6,
            magnet: true,
            fill: '#fff',
            strokeWidth: 1,
            cursor: 'crosshair',
            rx: 0,
            ry: 0
          },
          portLabel: {
            text: '',
            fontSize: 7,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
            fill: '#4b5563',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            x: 0,
            y: 0,
            pointerEvents: 'none'
          }
        }
      }
    }
    
    // 使用设备的端口信息创建 X6 端口项
    const portItems = item.ports.map(port => {
      // 从端口数据中读取颜色（由业务层预先计算好）
      const portColor = port.color || '#6b7280'  // 默认灰色
      
      // 文本截断
      const isTopBottom = port.group === 'top' || port.group === 'bottom'
      const portName = port.interfaceName || port.id
      const displayText = portName.length > (isTopBottom ? 6 : 7) 
        ? portName.substring(0, isTopBottom ? 5 : 6) + '..' 
        : portName
      
      return {
        id: port.id,
        group: port.group,
        args: { x: 0, y: 0 }, // 初始位置，后续由 syncPortPositions 更新
        attrs: {
          portBody: {
            stroke: portColor  // 根据总线类型设置边框颜色
          },
          portLabel: {
            text: displayText
          }
        }
      }
    })
    
    // 组装完整的端口配置
    ports = {
      groups: portGroups,
      items: portItems
    }
  } else {
    // 普通 DAG 节点
    shape = DAG_NODE
    const sizeConfig = getNodeSizeByLayout(layoutDirection)
    width = sizeConfig.width
    height = sizeConfig.height
    
    // 根据当前布局动态生成固定 ID 的四向连接桩（t/b/l/r），并按需隐藏
    const generatePorts = () => {
      const isHorizontal = layoutDirection === 'horizontal'
      const make = (pid, group, visible, role) => ({
        id: pid,
        group,
        attrs: {
          circle: {
            magnet: visible ? (role === 'output' ? true : 'passive') : false,
            style: { display: visible ? '' : 'none' }
          }
        }
      })
      return [
        make('t', 'top', !isHorizontal, 'input'),
        make('b', 'bottom', !isHorizontal, 'output'),
        make('l', 'left', isHorizontal, 'input'),
        make('r', 'right', isHorizontal, 'output')
      ]
    }
    ports = generatePorts()
  }

  // 构建节点数据
  const nodeData = {
    // 新的数据结构
    type: 'leaf-node', // 新拖入的节点默认为叶子节点
    layoutDirection,
    collapsed: false,
    properties: {
      content: {
        id: generateContentId(),
        label: item.title
      },
      weight: 50,
      otherData: {}, // 空的计算模型数据
      parentNodeId: null, // 稍后会在连线时更新
      customType: '',
      customProperties: '',
      unit: '',
      priority: '',
      defaultValue: '',
      notes: '',
      level: 1 // 稍后会根据实际位置更新
    },
    // 兼容旧结构
    id,
    label: item.title,
    status: 'default',
    description: item.shortDesc || item.value,
    originalData: { name: item.title, value: item.shortDesc }
  }

  // 如果是设备节点，添加设备特有的数据
  if (isDeviceNode) {
    nodeData.deviceId = item.deviceId
    nodeData.deviceType = item.deviceType
    nodeData.busType = item.busType
    nodeData.manufacturer = item.manufacturer
    nodeData.model = item.model
    nodeData.version = item.version
    nodeData.ports = item.ports // 端口信息供 DevicePortNode.vue 使用
    nodeData.nodeType = 'device-port-node'
    
    // 保存完整的原始数据
    nodeData.originalData = {
      name: item.name,
      value: item.value,
      deviceId: item.deviceId,
      deviceType: item.deviceType,
      busType: item.busType,
      manufacturer: item.manufacturer,
      model: item.model,
      version: item.version
    }
  }

  startDrag(
    {
      id,
      shape,
      width,
      height,
      data: nodeData,
      ports,
      // 确保节点默认可拖拽和未锁定
      draggable: true,
      locked: false
    },
    event
  )
}
</script>

<style scoped lang="scss">
.operator-library {
  width: 100%;
  max-width: 320px;
  height: 100%;
  background: rgb(247, 248, 250);
  border: 1px solid #eee;
  // border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  box-sizing: border-box;

  .library-header {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 42px;
    padding: 0 16px;
    background: #f6f8fa;
    border-bottom: 1px solid #eaebed;

    .header-title {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: #1f2937;
      letter-spacing: -0.01em;
    }
  }

  .search-section {
    padding: 10px;
    background: rgb(247, 248, 250);
    border-bottom: 1px solid #e2e8f0;

    :deep(.el-input) {
      .el-input__wrapper {
        // border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 8px 12px;

        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        &.is-focus {
          box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }
      }

      .el-input__inner {
        font-size: 14px;
        height: 20px;
      }
    }
  }

  .operator-list {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 12px;
    // background: #ffffff;
    // border: 1px solid #e2e8f0;
    border-radius: 8px;
    // margin: 12px;
    box-sizing: border-box;

    /* 自定义滚动条 */
    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background: #d1d5db;
      border-radius: 3px;

      &:hover {
        background: #9ca3af;
      }
    }
  }

  // 分类组样式
  .category-group {
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .category-header {
      display: flex;
      align-items: center;
      padding: 8px 12px;
      background: rgba(59, 130, 246, 0.05);
      border-radius: 4px;
      cursor: pointer;
      user-select: none;
      transition: all 0.2s;
      margin-bottom: 8px;

      &:hover {
        background: rgba(59, 130, 246, 0.1);
      }

      .category-icon {
        font-size: 14px;
        color: #6b7280;
        transition: transform 0.2s;
        margin-right: 6px;

        &:not(.collapsed) {
          transform: rotate(90deg);
        }
      }

      .category-title {
        flex: 1;
        font-size: 13px;
        font-weight: 600;
        color: #374151;
      }

      .category-count {
        font-size: 12px;
        color: #9ca3af;
        background: rgba(156, 163, 175, 0.15);
        padding: 2px 8px;
        border-radius: 10px;
        min-width: 20px;
        text-align: center;
      }
    }

    .category-items {
      padding-left: 4px;
    }
  }

  .operator-item {
    display: flex;
    align-items: center;
    padding: 6px 12px;
    background: #ffffff;
    border-radius: 4px;
    cursor: grab;
    user-select: none;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 6px;
    box-sizing: border-box;
    width: 100%;

    &:last-child {
      margin-bottom: 0;
    }

    &:hover {
      background: #f0f9ff;
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12);
      transform: translateX(2px);
    }

    &:active {
      transform: translateX(0);
      box-shadow: 0 1px 4px rgba(59, 130, 246, 0.08);
    }

    .operator-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 6px;
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.15));
      color: #3b82f6;
      font-size: 16px;
      flex-shrink: 0;
    }

    .operator-content {
      flex: 1;
      margin-left: 12px;
      min-width: 0;

      .operator-title {
        font-size: 14px;
        font-weight: 500;
        color: #111827;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.4;
      }

      .operator-category {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    .operator-title {
      flex: 1;
      text-align: left;
      font-size: 14px;
      font-weight: 500;
      color: #111827;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-left: 12px;
      min-width: 0;
    }
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;

    .loading-icon {
      font-size: 32px;
      color: #3b82f6;
      margin-bottom: 12px;

      &.is-loading {
        animation: rotate 2s linear infinite;
      }
    }

    .loading-text {
      font-size: 14px;
      font-weight: 500;
      color: #6b7280;
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;

    .empty-icon {
      font-size: 32px;
      color: #d1d5db;
      margin-bottom: 12px;
    }

    .empty-text {
      font-size: 14px;
      font-weight: 500;
      color: #6b7280;
      margin-bottom: 4px;
    }

    .empty-desc {
      font-size: 12px;
      color: #9ca3af;
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
