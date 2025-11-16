<template>
  <el-drawer
    :model-value="modelValue"
    :title="title"
    size="600px"
    direction="rtl"
    @close="handleClose"
  >
    <div class="protocol-list-container">
      <!-- 空状态 -->
      <div v-if="!devicePorts || devicePorts.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Box /></el-icon>
        <div class="empty-text">暂无端口数据</div>
        <div class="empty-desc">请先添加设备端口</div>
      </div>

      <!-- 按总线类型分组展示协议 -->
      <div v-else class="port-groups">
        <div
          v-for="group in groupedPorts"
          :key="group.type"
          class="port-group"
        >
          <!-- 总线类型分组头部 -->
          <div class="port-header" @click="togglePort(group.type)">
            <el-icon 
              class="port-icon" 
              :class="{ collapsed: collapsedPorts[group.type] }"
            >
              <ArrowRight />
            </el-icon>
            <div class="port-info">
              <span class="port-name">{{ group.type }}</span>
              <el-tag :type="getBusTypeTagType(group.type)" size="small">
                {{ group.type }}
              </el-tag>
            </div>
            <span class="protocol-count">
              {{ group.totalProtocols }} 个协议
            </span>
          </div>

          <!-- 协议列表 -->
          <div v-show="!collapsedPorts[group.type]" class="protocol-items">
            <!-- 无协议提示 -->
            <div v-if="group.totalProtocols === 0" class="no-protocol">
              <el-icon><Warning /></el-icon>
              <span>该类型端口暂无协议配置</span>
            </div>

            <!-- 协议列表 -->
            <div
              v-for="protocol in group.protocols"
              :key="protocol.id"
              class="protocol-item"
              @click="handleProtocolClick(protocol.port, protocol.message)"
            >
              <div class="protocol-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="protocol-content">
                <div class="protocol-title">
                  {{ protocol.message.name || protocol.port.interfaceName + ' 协议' }}
                </div>
                <div class="protocol-meta">
                  <span v-if="protocol.message.header?.sender" class="meta-item">
                    发送方: {{ protocol.message.header.sender }}
                  </span>
                  <span v-if="protocol.message.header?.receiver" class="meta-item">
                    接收方: {{ protocol.message.header.receiver }}
                  </span>
                  <span v-if="protocol.message.fields" class="meta-item">
                    {{ protocol.message.fields.length }} 个字段
                  </span>
                </div>
              </div>
              <el-icon class="protocol-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ArrowRight, Box, Warning, Document } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '设备协议列表'
  },
  devicePorts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'protocol-click'])

// 折叠状态（默认全部展开）
const collapsedPorts = ref({})

// 获取端口的协议列表
const getPortMessages = (port) => {
  // 检查是否有配置的协议数据
  if (!port.messageConfig) {
    return []
  }
  
  // 当前数据结构：每个端口只有一个 messageConfig（包含 header 和 fields）
  // 如果有 fields 数据，说明配置了协议
  if (port.messageConfig.fields && port.messageConfig.fields.length > 0) {
    // 返回一个包含该协议的数组
    return [{
      id: port.id || port.interfaceId,
      name: `${port.interfaceName} 协议`,
      messageId: port.id || port.interfaceId,
      direction: 'send', // 默认发送
      fields: port.messageConfig.fields,
      header: port.messageConfig.header
    }]
  }
  
  return []
}

// 按总线类型分组
const groupedPorts = computed(() => {
  if (!props.devicePorts || props.devicePorts.length === 0) {
    return []
  }

  // 按总线类型分组
  const groups = {}
  
  props.devicePorts.forEach(port => {
    const type = port.interfaceType
    if (!groups[type]) {
      groups[type] = {
        type: type,
        ports: [],
        protocols: [],
        totalProtocols: 0
      }
    }
    
    groups[type].ports.push(port)
    
    // 获取该端口的协议列表
    const messages = getPortMessages(port)
    messages.forEach(message => {
      groups[type].protocols.push({
        id: `${port.id || port.interfaceId}_${message.id}`,
        port: port,
        message: message
      })
    })
    
    groups[type].totalProtocols = groups[type].protocols.length
  })
  
  // 转换为数组并排序
  return Object.values(groups).sort((a, b) => a.type.localeCompare(b.type))
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  console.log('=== 协议列表 Drawer modelValue 变化 ===')
  console.log('新值:', newVal)
}, { immediate: true })

// 监听数据变化，打印调试信息
watch(() => props.devicePorts, (newPorts) => {
  console.log('=== 协议列表Drawer接收到的端口数据 ===')
  console.log('端口数量:', newPorts?.length || 0)
  if (newPorts && newPorts.length > 0) {
    newPorts.forEach((port, index) => {
      console.log(`端口 ${index + 1}:`, {
        id: port.id || port.interfaceId,
        name: port.interfaceName,
        type: port.interfaceType,
        messageConfig: port.messageConfig,
        hasFields: port.messageConfig?.fields?.length || 0,
        header: port.messageConfig?.header
      })
    })
  }
}, { immediate: true, deep: true })

// 切换端口折叠状态
const togglePort = (portId) => {
  collapsedPorts.value[portId] = !collapsedPorts.value[portId]
}

// 获取总线类型对应的标签类型
const getBusTypeTagType = (busType) => {
  const typeMap = {
    'RS422': 'warning',
    'RS485': 'danger',
    'CAN': 'primary',
    'LAN': 'success',
    '1553B': ''
  }
  return typeMap[busType] || 'info'
}

// 点击报文
const handleProtocolClick = (port, message) => {
  emit('protocol-click', { port, message })
}

// 关闭抽屉
const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style lang="scss" scoped>
.protocol-list-container {
  height: 100%;
  overflow-y: auto;

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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;

  .empty-icon {
    font-size: 48px;
    color: #d1d5db;
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 16px;
    font-weight: 500;
    color: #6b7280;
    margin-bottom: 8px;
  }

  .empty-desc {
    font-size: 14px;
    color: #9ca3af;
  }
}

.port-groups {
  padding: 12px;
}

.port-group {
  margin-bottom: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;

  &:last-child {
    margin-bottom: 0;
  }

  .port-header {
    display: flex;
    align-items: center;
    padding: 14px 16px;
    background: rgba(59, 130, 246, 0.04);
    cursor: pointer;
    user-select: none;
    transition: all 0.2s;
    border-bottom: 1px solid #e5e7eb;

    &:hover {
      background: rgba(59, 130, 246, 0.08);
    }

    .port-icon {
      font-size: 16px;
      color: #6b7280;
      transition: transform 0.2s;
      margin-right: 10px;
      flex-shrink: 0;

      &:not(.collapsed) {
        transform: rotate(90deg);
      }
    }

    .port-info {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;

      .port-name {
        font-size: 15px;
        font-weight: 600;
        color: #111827;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .el-tag {
        flex-shrink: 0;
      }
    }

    .protocol-count {
      font-size: 13px;
      color: #6b7280;
      background: rgba(107, 114, 128, 0.1);
      padding: 4px 12px;
      border-radius: 12px;
      flex-shrink: 0;
    }
  }

  .protocol-items {
    background: #fafafa;

    .no-protocol {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 24px;
      color: #9ca3af;
      font-size: 14px;

      .el-icon {
        font-size: 18px;
      }
    }

    .protocol-item {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      margin: 8px;
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background: #f0f9ff;
        border-color: #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12);
        transform: translateX(2px);
      }

      .protocol-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 6px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.15));
        color: #3b82f6;
        font-size: 18px;
        flex-shrink: 0;
      }

      .protocol-content {
        flex: 1;
        margin-left: 12px;
        min-width: 0;

        .protocol-title {
          font-size: 14px;
          font-weight: 500;
          color: #111827;
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .protocol-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;

          .meta-item {
            font-size: 12px;
            color: #6b7280;
            white-space: nowrap;

            &:not(:last-child)::after {
              content: '•';
              margin-left: 12px;
              color: #d1d5db;
            }
          }
        }
      }

      .protocol-arrow {
        font-size: 14px;
        color: #9ca3af;
        flex-shrink: 0;
        transition: transform 0.2s;
      }

      &:hover .protocol-arrow {
        transform: translateX(2px);
        color: #3b82f6;
      }
    }
  }
}
</style>

