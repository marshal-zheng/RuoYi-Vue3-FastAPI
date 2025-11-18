<template>
  <ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value">
    <!-- 空状态 -->
    <div
      v-if="!portList || portList.length === 0"
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
          @click="handleProtocolClick(protocol)"
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

  <!-- 协议配置对话框 -->
  <ProtocolEditDialog ref="protocolDialogRef" @submit="handleProtocolSubmit" />
</template>

<script setup>
import { ref, reactive, watch, nextTick, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useDrawer } from '@zxio/zxui';
import { Box, ArrowRight, Document, Warning } from '@element-plus/icons-vue';
import ProtocolEditDialog from './ProtocolEditDialog.vue';

const props = defineProps({
  nodeData: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['submit']);

const formRef = ref(null);

// 使用 useDrawer
const drawer = useDrawer({
  title: () => `节点配置 - ${formData.name || '未命名节点'}`,
  size: '700px',
  placement: 'right',
  okText: '保存',
  formRef,
  formModel: computed(() => formData),
  preValidate: true,
  autoScrollToError: true,
  async onConfirm() {
    // 触发提交事件，传递节点数据、修改后的名称和端口信息
    emit('submit', {
      nodeId: props.nodeData?.id,
      node: props.nodeData,
      name: formData.name,
      ports: portList.value,
    });

    ElMessage.success('保存成功');
    return true;
  },
});

// 表单数据
const formData = reactive({
  name: '',
  deviceType: '',
  model: '',
  manufacturer: '',
  version: '',
  remark: '',
});

// 端口列表
const portList = ref([]);

// 折叠状态（默认全部展开）
const collapsedPorts = ref({});

// 协议配置对话框
const protocolDialogRef = ref(null);
const currentPortIndex = ref(-1);

// 监听 nodeData 变化，当打开时初始化数据
watch(
  () => props.nodeData,
  newVal => {
    if (newVal && Object.keys(newVal).length > 0) {
      initFormData();
    }
  },
  { deep: true }
);

// 初始化表单数据
const initFormData = () => {
  nextTick(() => {
    const data = props.nodeData?.data || {};
    formData.name = data.name || data.label || '';
    formData.deviceType = data.deviceType || '';
    formData.model = data.model || '';
    formData.manufacturer = data.manufacturer || '';
    formData.version = data.version || '';
    formData.remark = data.remark || data.value || '';

    // 加载端口列表，并附加对端设备名称
    const peerMap = props.nodeData?.peerDeviceNameByPort || {};
    const ports = Array.isArray(data.ports) ? data.ports : [];
    portList.value = ports.map(port => {
      const portKey = port.id || port.interfaceId;
      return {
        ...port,
        peerDeviceName: (portKey && peerMap[portKey]) || port.peerDeviceName || '',
      };
    });

    // 清除验证状态
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
};

const cloneHeader = header => JSON.parse(JSON.stringify(header || {}));
const cloneFields = fields => JSON.parse(JSON.stringify(Array.isArray(fields) ? fields : []));
const resolvePortKey = port => port?.id || port?.interfaceId;
const getPeerDeviceName = port => {
  if (port?.peerDeviceName) return port.peerDeviceName;
  const peerMap = props.nodeData?.peerDeviceNameByPort || {};
  const key = resolvePortKey(port);
  return (key && peerMap[key]) || '';
};

// 获取端口的协议列表（当前端口 + 对端方向）
const getPortMessages = port => {
  if (!port || !port.messageConfig) {
    return [];
  }

  const messageConfig = port.messageConfig || {};
  const currentDeviceName =
    formData.name || props.nodeData?.data?.name || props.nodeData?.data?.label || '';
  const peerDeviceName = getPeerDeviceName(port);
  const baseHeader = cloneHeader(messageConfig.header);
  const baseFields = cloneFields(messageConfig.fields);

  if (!baseHeader.sender && currentDeviceName) {
    baseHeader.sender = currentDeviceName;
  }
  if (!baseHeader.receiver && (peerDeviceName || currentDeviceName)) {
    baseHeader.receiver = peerDeviceName || currentDeviceName;
  }

  const protocolId = messageConfig.protocolId || port.protocolId || null;
  const portId = resolvePortKey(port);
  const baseProtocol = {
    id: portId,
    name: `${port.interfaceName} 协议`,
    messageId: portId,
    port,
    direction: 'forward',
    message: {
      header: baseHeader,
      fields: baseFields,
      protocolId,
    },
  };

  const result = [baseProtocol];

  if (peerDeviceName) {
    const reverseHeader = cloneHeader(baseHeader);
    const forwardSender = baseHeader.sender || currentDeviceName || '';
    const forwardReceiver = baseHeader.receiver || peerDeviceName || '';
    reverseHeader.sender = forwardReceiver || peerDeviceName || forwardSender;
    reverseHeader.receiver = forwardSender || currentDeviceName || forwardReceiver;

    result.push({
      ...baseProtocol,
      id: `${portId}-reverse`,
      direction: 'reverse',
      isReverse: true,
      message: {
        header: reverseHeader,
        fields: cloneFields(messageConfig.fields),
        protocolId,
      },
    });
  }

  return result;
};

// 按总线类型分组
const groupedPorts = computed(() => {
  if (!portList.value || portList.value.length === 0) {
    return [];
  }

  // 按总线类型分组
  const groups = {};

  portList.value.forEach((port, index) => {
    const type = port.interfaceType || port.busType;
    if (!groups[type]) {
      groups[type] = {
        type: type,
        ports: [],
        protocols: [],
        totalProtocols: 0,
      };
    }

    // 保存原始索引，用于配置协议时定位
    const portWithIndex = { ...port, _originalIndex: index };
    groups[type].ports.push(portWithIndex);

    // 获取该端口的协议列表
    const messages = getPortMessages(portWithIndex);
    messages.forEach(message => {
      groups[type].protocols.push({
        id: `${port.id || port.interfaceId}_${message.id}`,
        port: portWithIndex,
        message: message,
      });
    });

    groups[type].totalProtocols = groups[type].protocols.length;
  });

  // 转换为数组并排序
  return Object.values(groups).sort((a, b) => a.type.localeCompare(b.type));
});

// 切换端口折叠状态
const togglePort = portType => {
  collapsedPorts.value[portType] = !collapsedPorts.value[portType];
};

// 获取总线类型对应的标签类型
const getBusTypeTagType = busType => {
  const typeMap = {
    RS422: 'warning',
    RS485: 'danger',
    CAN: 'primary',
    Ethernet: 'success',
    '1553B': 'info',
  };
  return typeMap[busType] || 'info';
};

// 点击协议卡片
const handleProtocolClick = protocolItem => {
  if (!protocolItem) return;
  const port = protocolItem.port;
  const message = protocolItem.message || {};
  const direction = protocolItem.direction || (protocolItem.isReverse ? 'reverse' : 'forward');
  if (!port) return;

  const currentDeviceName =
    formData.name || props.nodeData?.data?.name || props.nodeData?.data?.label || '';
  const peerDeviceName = getPeerDeviceName(port);

  const portInfo = {
    ...port,
    deviceName: currentDeviceName || port.deviceName || '',
    peerDeviceName,
    direction,
    messageConfig: {
      header: cloneHeader(message.header),
      fields: cloneFields(message.fields),
    },
    protocolId: message.protocolId || port.protocolId || null,
  };
  currentPortIndex.value = port._originalIndex;
  protocolDialogRef.value?.open(portInfo);
};

// 协议提交回调
const handleProtocolSubmit = ({ messageConfig, protocolId }) => {
  // 更新端口的协议信息
  if (currentPortIndex.value >= 0) {
    portList.value[currentPortIndex.value] = {
      ...portList.value[currentPortIndex.value],
      messageConfig,
      protocolId,
    };
  }
};

defineExpose({
  open: drawer.open,
  close: drawer.close,
});
</script>

<style lang="less" scoped>
// 样式已通过 Tailwind CSS 类实现
</style>
