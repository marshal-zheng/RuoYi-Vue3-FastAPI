<template>
  <ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value">
    <!-- 空状态 -->
    <div
      v-if="!devicePorts || devicePorts.length === 0"
      class="flex flex-col items-center justify-center px-5 py-16 text-center"
    >
      <el-icon class="text-5xl text-gray-300 mb-4"><Box /></el-icon>
      <div class="text-base font-medium text-gray-500 mb-2">暂无端口数据</div>
      <div class="text-sm text-gray-400">请先添加设备端口</div>
    </div>

    <!-- 按总线类型分组展示协议 -->
    <div
      v-for="group in groupedPorts"
      :key="group.type"
      class="mb-4 bg-white border border-gray-200 rounded-lg overflow-hidden"
    >
      <!-- 总线类型分组头部 -->
      <div
        class="flex items-center px-4 py-3 bg-primary-50 cursor-pointer select-none transition-all border-b border-gray-200 hover:bg-primary-100"
        @click="togglePort(group.type)"
      >
        <el-icon
          class="text-base text-gray-600 transition-transform mr-2.5 shrink-0"
          :class="{ 'rotate-90': !collapsedPorts[group.type] }"
        >
          <ArrowRight />
        </el-icon>
        <div class="flex-1 flex items-center gap-2.5 min-w-0">
          <span class="text-[15px] font-semibold text-gray-900 truncate">{{ group.type }}</span>
          <el-tag :type="getBusTypeTagType(group.type)" size="small" class="shrink-0">
            {{ group.type }}
          </el-tag>
        </div>
        <span class="text-sm text-gray-600 bg-gray-200 px-3 py-1 rounded-full shrink-0">
          {{ group.totalProtocols }} 个协议
        </span>
      </div>

      <!-- 协议列表 -->
      <div v-show="!collapsedPorts[group.type]" class="bg-gray-50">
        <!-- 无协议提示 -->
        <div
          v-if="group.totalProtocols === 0"
          class="flex items-center justify-center gap-2 p-6 text-gray-400 text-sm"
        >
          <el-icon><Warning /></el-icon>
          <span>该类型端口暂无协议配置</span>
        </div>

        <!-- 协议列表 -->
        <div
          v-for="protocol in group.protocols"
          :key="protocol.id"
          class="group flex items-center px-4 py-3 m-2 bg-white border border-gray-200 rounded-md cursor-pointer transition-all hover:bg-primary-50 hover:border-primary-500 hover:shadow hover:translate-x-0.5"
          @click="handleProtocolClick(protocol.port, protocol.message)"
        >
          <div
            class="flex items-center justify-center w-9 h-9 rounded-md bg-gradient-to-br from-primary-50 to-indigo-50 text-primary-500 text-lg shrink-0"
          >
            <el-icon><Document /></el-icon>
          </div>
          <div class="flex-1 ml-3 min-w-0">
            <div class="text-sm font-medium text-gray-900 mb-1 truncate">
              {{ protocol.message.name || protocol.port.interfaceName + ' 协议' }}
            </div>
            <div class="flex items-center gap-3 flex-wrap">
              <span
                v-if="protocol.message.header?.sender"
                class="text-xs text-gray-600 whitespace-nowrap"
              >
                发送方: {{ protocol.message.header.sender }}
              </span>
              <span
                v-if="protocol.message.header?.receiver"
                class="text-xs text-gray-600 whitespace-nowrap"
              >
                接收方: {{ protocol.message.header.receiver }}
              </span>
              <span v-if="protocol.message.fields" class="text-xs text-gray-600 whitespace-nowrap">
                {{ protocol.message.fields.length }} 个字段
              </span>
            </div>
          </div>
          <el-icon
            class="text-sm text-gray-400 shrink-0 transition-transform group-hover:translate-x-0.5 group-hover:text-primary-500"
            ><ArrowRight
          /></el-icon>
        </div>
      </div>
    </div>
  </ZxDrawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
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

// 监听数据变化，打印调试信息
watch(
  () => props.devicePorts,
  (newPorts) => {
    if (newPorts && newPorts.length > 0) {
      newPorts.forEach((port, index) => {});
    }
  },
  { immediate: true, deep: true }
);

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
const handleClose = () => {
  emit('update:modelValue', false);
  drawer.close();
};

defineExpose({ open: drawer.open, close: drawer.close });
</script>

<style scoped></style>
