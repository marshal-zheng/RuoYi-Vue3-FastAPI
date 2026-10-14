<template>
  <ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value">
    <!-- 空状态 -->
    <div
      v-if="!devicePorts || devicePorts.length === 0"
      class="flex flex-col items-center justify-center px-5 py-16 text-center"
    >
      <el-icon class="protocol-muted text-5xl mb-4"><Box /></el-icon>
      <div class="protocol-primary text-base font-medium mb-2">暂无端口数据</div>
      <div class="protocol-muted text-sm">请先添加设备端口</div>
    </div>

    <!-- 按总线类型分组展示协议 -->
    <div
      v-for="group in groupedPorts"
      :key="group.type"
      class="protocol-group mb-4 rounded-lg overflow-hidden"
      data-zx-surface="card"
    >
      <!-- 总线类型分组头部 -->
      <div
        class="protocol-group__header flex items-center px-4 py-3 cursor-pointer select-none transition-all"
        @click="togglePort(group.type)"
      >
        <el-icon
          class="protocol-muted text-base transition-transform mr-2.5 shrink-0"
          :class="{ 'rotate-90': !collapsedPorts[group.type] }"
        >
          <ArrowRight />
        </el-icon>
        <div class="flex-1 flex items-center gap-2.5 min-w-0">
          <span class="protocol-primary text-[15px] font-semibold truncate">{{ group.type }}</span>
          <el-tag :type="getBusTypeTagType(group.type)" size="small" class="shrink-0">
            {{ group.type }}
          </el-tag>
        </div>
        <span class="protocol-group__count text-sm px-3 py-1 rounded-full shrink-0">
          {{ group.totalProtocols }} 个协议
        </span>
      </div>

      <!-- 协议列表 -->
      <div v-show="!collapsedPorts[group.type]" class="protocol-group__list">
        <!-- 无协议提示 -->
        <div
          v-if="group.totalProtocols === 0"
          class="protocol-muted flex items-center justify-center gap-2 p-6 text-sm"
        >
          <el-icon><Warning /></el-icon>
          <span>该类型端口暂无协议配置</span>
        </div>

        <!-- 协议列表 -->
        <div
          v-for="protocol in group.protocols"
          :key="protocol.id"
          class="protocol-item group flex items-center px-4 py-3 m-2 rounded-md cursor-pointer transition-all hover:shadow hover:translate-x-0.5"
          @click="handleProtocolClick(protocol.port, protocol.message)"
        >
          <div
            class="protocol-item__icon flex items-center justify-center w-9 h-9 rounded-md text-lg shrink-0"
          >
            <el-icon><Document /></el-icon>
          </div>
          <div class="flex-1 ml-3 min-w-0">
            <div class="protocol-primary text-sm font-medium mb-1 truncate">
              {{ protocol.message.name || protocol.port.interfaceName + ' 协议' }}
            </div>
            <div class="flex items-center gap-3 flex-wrap">
              <span
                v-if="protocol.message.header?.sender"
                class="protocol-muted text-xs whitespace-nowrap"
              >
                发送方: {{ protocol.message.header.sender }}
              </span>
              <span
                v-if="protocol.message.header?.receiver"
                class="protocol-muted text-xs whitespace-nowrap"
              >
                接收方: {{ protocol.message.header.receiver }}
              </span>
              <span v-if="protocol.message.fields" class="protocol-muted text-xs whitespace-nowrap">
                {{ protocol.message.fields.length }} 个字段
              </span>
            </div>
          </div>
          <el-icon
            class="protocol-item__arrow text-sm shrink-0 transition-transform group-hover:translate-x-0.5"
            ><ArrowRight
          /></el-icon>
        </div>
      </div>
    </div>
  </ZxDrawer>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useDrawer } from '@zxio/zxui';
import { ArrowRight, Box, Warning, Document } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '设备协议列表',
  },
  devicePorts: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['update:modelValue', 'protocol-click']);

const drawer = useDrawer({
  title: computed(() => props.title),
  size: '600px',
  placement: 'right',
  onClose: () => emit('update:modelValue', false),
});

// 折叠状态（默认全部展开）
const collapsedPorts = ref({});

// 获取端口的协议列表
const getPortMessages = (port) => {
  // 检查是否有配置的协议数据
  if (!port.messageConfig) {
    return [];
  }

  // 当前数据结构：每个端口只有一个 messageConfig（包含 header 和 fields）
  // 如果有 fields 数据，说明配置了协议
  if (port.messageConfig.fields && port.messageConfig.fields.length > 0) {
    // 返回一个包含该协议的数组
    return [
      {
        id: port.id || port.interfaceId,
        name: `${port.interfaceName} 协议`,
        messageId: port.id || port.interfaceId,
        direction: 'send', // 默认发送
        fields: port.messageConfig.fields,
        header: port.messageConfig.header,
      },
    ];
  }

  return [];
};

// 按总线类型分组
const groupedPorts = computed(() => {
  if (!props.devicePorts || props.devicePorts.length === 0) {
    return [];
  }

  // 按总线类型分组
  const groups = {};

  props.devicePorts.forEach((port) => {
    const type = port.interfaceType;
    if (!groups[type]) {
      groups[type] = {
        type: type,
        ports: [],
        protocols: [],
        totalProtocols: 0,
      };
    }

    groups[type].ports.push(port);

    // 获取该端口的协议列表
    const messages = getPortMessages(port);
    messages.forEach((message) => {
      groups[type].protocols.push({
        id: `${port.id || port.interfaceId}_${message.id}`,
        port: port,
        message: message,
      });
    });

    groups[type].totalProtocols = groups[type].protocols.length;
  });

  // 转换为数组并排序
  return Object.values(groups).sort((a, b) => a.type.localeCompare(b.type));
});

// 监听 modelValue 变化
// 通过父组件 ref 控制打开/关闭，无需监听外部 v-model

// 切换端口折叠状态
const togglePort = (portId) => {
  collapsedPorts.value[portId] = !collapsedPorts.value[portId];
};

// 获取总线类型对应的标签类型
const getBusTypeTagType = (busType) => {
  const typeMap = {
    RS422: 'warning',
    RS485: 'danger',
    CAN: 'primary',
    LAN: 'success',
    '1553B': '',
  };
  return typeMap[busType] || 'info';
};

// 点击报文
const handleProtocolClick = (port, message) => {
  emit('protocol-click', { port, message });
};

// 关闭抽屉

defineExpose({ open: drawer.open, close: drawer.close });
</script>

<style scoped>
.protocol-primary {
  color: var(--zx-semantic-text-primary);
}

.protocol-muted {
  color: var(--zx-semantic-text-secondary);
}

.protocol-group__header {
  background-color: var(--zx-semantic-surface-header-fill);
  border-bottom: 1px solid var(--zx-semantic-border-subtle);
}

.protocol-group__header:hover {
  background-color: var(--zx-semantic-fill-hover);
}

.protocol-group__count {
  background-color: var(--zx-semantic-fill-subtle);
  color: var(--zx-semantic-surface-header-on-text-secondary);
}

.protocol-group__list {
  background-color: var(--zx-semantic-surface-canvas-fill);
}

.protocol-item {
  background-color: var(--zx-semantic-surface-card-fill);
  border: 1px solid var(--zx-semantic-border-subtle);
}

.protocol-item:hover {
  background-color: var(--zx-semantic-fill-hover);
  border-color: var(--zx-semantic-accent-base);
}

.protocol-item__icon {
  background-color: var(--zx-semantic-fill-selected);
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
}

.protocol-item__arrow {
  color: var(--zx-semantic-text-secondary);
}

.protocol-item:hover .protocol-item__arrow {
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
}
</style>
