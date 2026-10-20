<template>
  <ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value">
    <!-- 空状态 -->
    <div
      v-if="!portList || portList.length === 0"
      class="flex flex-col items-center justify-center px-5 py-16 text-center"
    >
      <el-icon
        class="text-5xl text-[var(--sim-text-disabled,var(--zx-semantic-text-disabled))] mb-4"
        ><Box
      /></el-icon>
      <div
        class="text-base font-medium text-[var(--sim-text-secondary,var(--zx-semantic-text-secondary))] mb-2"
      >
        暂无端口数据
      </div>
      <div class="text-sm text-[var(--sim-text-tertiary,var(--zx-semantic-text-secondary))]">
        请先添加设备端口
      </div>
    </div>

    <!-- 按总线类型分组展示协议 -->
    <div v-for="group in groupedPorts" :key="group.type" class="node-group-card mb-4">
      <!-- 总线类型分组头部 -->
      <div
        class="node-group-header flex items-center justify-between px-4 py-3 cursor-pointer select-none transition-all"
        @click="togglePort(group.type)"
      >
        <div class="flex items-center gap-2">
          <el-icon
            class="text-base node-group-arrow transition-transform shrink-0"
            :class="{ 'rotate-90': !collapsedPorts[group.type] }"
          >
            <ArrowRight />
          </el-icon>
          <span class="node-group-title text-[15px] font-bold truncate">{{ group.type }}</span>
          <span class="node-group-chip px-2 py-0.5 text-xs rounded-md shrink-0">
            {{ group.type }}
          </span>
        </div>
        <span class="node-group-count px-3 py-1 text-sm rounded-full shrink-0">
          {{ group.totalProtocols }} 个协议
        </span>
      </div>

      <!-- 协议列表 -->
      <div v-show="!collapsedPorts[group.type]" class="node-protocol-list p-2">
        <!-- 无协议提示 -->
        <div
          v-if="group.totalProtocols === 0"
          class="node-empty-tip flex items-center justify-center gap-2 p-6 text-sm"
        >
          <el-icon><Warning /></el-icon>
          <span>该类型端口暂无协议配置</span>
        </div>

        <!-- 协议列表 -->
        <div
          v-for="protocol in group.protocols"
          :key="protocol.id"
          class="group flex items-center justify-between px-4 py-3 mb-2 last:mb-0 node-protocol-card cursor-pointer transition-all"
          @click="handleProtocolClick(protocol)"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="node-protocol-icon flex items-center justify-center w-8 h-8 rounded shrink-0"
            >
              <el-icon class="text-lg"><Document /></el-icon>
            </div>
            <div class="flex flex-col min-w-0">
              <span class="node-protocol-title text-sm font-medium truncate">
                {{ protocol.message.name || protocol.port.interfaceName + ' 协议' }}
              </span>
            </div>
          </div>
          <el-icon class="node-protocol-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </ZxDrawer>

  <!-- 协议配置对话框 -->
  <ProtocolEditDialog ref="protocolDialogRef" @submit="handleProtocolSubmit" />
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useDrawer } from '@zxio/zxui/hooks';
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
  defaultData: () => ({
    name: '',
    deviceType: '',
    model: '',
    manufacturer: '',
    version: '',
    remark: '',
  }),
  divider: false,
  title: () => `节点配置 - ${drawer.state.data.name || '未命名节点'}`,
  size: '700px',
  placement: 'right',
  okText: '保存',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  async onConfirm() {
    // 触发提交事件，传递节点数据、修改后的名称和端口信息
    emit('submit', {
      nodeId: props.nodeData?.id,
      node: props.nodeData,
      name: drawer.state.data.name,
      ports: portList.value,
    });

    // message-governance-allow-local: 节点抽屉仅提交本地画布状态
    ElMessage.success('保存成功');
    return true;
  },
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
  (newVal) => {
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
    drawer.setData({
      name: data.name || data.label || '',
      deviceType: data.deviceType || '',
      model: data.model || '',
      manufacturer: data.manufacturer || '',
      version: data.version || '',
      remark: data.remark || data.value || '',
    });

    // 加载端口列表，并附加对端设备名称
    const ports = Array.isArray(data.ports) ? data.ports : [];
    portList.value = ports.map((port) => {
      const peerNames = getPeerDeviceNames(port);
      return {
        ...port,
        peerDeviceName: peerNames[0] || port.peerDeviceName || '',
        peerDeviceNames: peerNames,
      };
    });

    // 清除验证状态
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
};

const cloneHeader = (header) => JSON.parse(JSON.stringify(header || {}));
const cloneFields = (fields) => JSON.parse(JSON.stringify(Array.isArray(fields) ? fields : []));
const resolvePortKeyVariants = (port) => {
  const variants = [];
  const id = port?.id;
  const interfaceId = port?.interfaceId;
  if (id) {
    variants.push(String(id));
    if (String(id).startsWith('port-')) {
      variants.push(String(id).replace(/^port-/, ''));
    }
  }
  if (interfaceId) {
    variants.push(String(interfaceId));
  }
  return variants;
};
const getPeerDeviceNames = (port) => {
  if (!port) return [];

  // 若端口对象上已缓存 peerDeviceNames，优先使用，保证顺序与去重结果一致
  if (Array.isArray(port.peerDeviceNames) && port.peerDeviceNames.length > 0) {
    return port.peerDeviceNames.filter(Boolean);
  }

  const peerMap = props.nodeData?.peerDeviceNameByPort || {};
  const keys = resolvePortKeyVariants(port);
  for (const key of keys) {
    if (peerMap[key]) {
      const peers = Array.isArray(peerMap[key]) ? peerMap[key] : [peerMap[key]];
      return peers.filter(Boolean);
    }
  }
  return [];
};
const getPeerDeviceName = (port) => {
  if (port?.peerDeviceName) return port.peerDeviceName;
  const peers = getPeerDeviceNames(port);
  return peers[0] || '';
};

// 获取端口的协议列表（仅保留「当前设备作为发送方」的唯一协议）
const getPortMessages = (port) => {
  if (!port || !port.messageConfig) {
    return [];
  }

  const messageConfig = port.messageConfig || {};
  const currentDeviceName =
    drawer.state.data.name || props.nodeData?.data?.name || props.nodeData?.data?.label || '';
  const peerDeviceNames = getPeerDeviceNames(port);
  const baseHeader = cloneHeader(messageConfig.header);

  const protocolId = messageConfig.protocolId || port.protocolId || null;
  const portId = resolvePortKeyVariants(port)[0];

  const buildHeader = (receiver) => {
    const header = cloneHeader(baseHeader);
    // 发送方强制为当前节点名称
    if (currentDeviceName) {
      header.sender = currentDeviceName;
    }
    // 接收方强制为传入的对端名称
    header.receiver = receiver || '';
    return header;
  };

  if (peerDeviceNames.length === 0) {
    // 没有任何对端设备，不生成协议；仅为已建立连接的端口生成协议
    return [];
  }

  return peerDeviceNames.map((peer, index) => {
    return {
      id: `${portId}-${index}`,
      name: `${port.interfaceName} 协议`,
      messageId: `${portId}-${index}`,
      port,
      direction: 'forward',
      message: {
        header: buildHeader(peer || ''),
        fields: cloneFields(messageConfig.fields),
        protocolId,
      },
    };
  });
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
        seenKeys: new Set(),
      };
    }

    // 保存原始索引，用于配置协议时定位
    const portWithIndex = { ...port, _originalIndex: index };
    groups[type].ports.push(portWithIndex);

    // 获取该端口的协议列表
    const messages = getPortMessages(portWithIndex);
    messages.forEach((message) => {
      const sender = message.message?.header?.sender || '';
      const receiver = message.message?.header?.receiver || '';
      const keyBase =
        resolvePortKeyVariants(portWithIndex)[0] ||
        portWithIndex.id ||
        portWithIndex.interfaceId ||
        '';
      const uniqKey = `${keyBase}__${sender}__${receiver}`;
      if (!groups[type].seenKeys.has(uniqKey)) {
        groups[type].seenKeys.add(uniqKey);
        groups[type].protocols.push({
          id: `${port.id || port.interfaceId}_${message.id}`,
          port: portWithIndex,
          message: message,
        });
      }
    });

    groups[type].totalProtocols = groups[type].protocols.length;
  });

  // 转换为数组并排序
  return Object.values(groups)
    .map((group) => {
      // 仅用于去重，不需要暴露到 UI
      const rest = { ...group };
      delete rest.seenKeys;
      return rest;
    })
    .sort((a, b) => a.type.localeCompare(b.type));
});

// 切换端口折叠状态
const togglePort = (portType) => {
  collapsedPorts.value[portType] = !collapsedPorts.value[portType];
};

// 获取总线类型对应的标签类型

// 点击协议卡片
const handleProtocolClick = (protocolItem) => {
  if (!protocolItem) return;
  const port = protocolItem.port;
  const messageWrapper = protocolItem.message || {};
  // 实际的消息配置数据在 messageWrapper.message 中
  const messageData = messageWrapper.message || {};
  const direction = messageWrapper.direction || (protocolItem.isReverse ? 'reverse' : 'forward');
  if (!port) return;

  const currentDeviceName =
    drawer.state.data.name || props.nodeData?.data?.name || props.nodeData?.data?.label || '';

  // 优先使用协议消息头中的接收方作为对端设备名称
  let peerDeviceName = messageData.header?.receiver;

  // 如果没有获取到，尝试通过 messageWrapper.id 解析索引来获取对应的 peerDeviceName
  if (!peerDeviceName && messageWrapper.id) {
    const parts = messageWrapper.id.toString().split('-');
    const index = parseInt(parts[parts.length - 1]);
    if (!isNaN(index) && Array.isArray(port.peerDeviceNames)) {
      peerDeviceName = port.peerDeviceNames[index];
    }
  }

  // 最后回退到默认获取方式
  if (!peerDeviceName) {
    peerDeviceName = getPeerDeviceName(port);
  }

  // 强制确保 header.receiver 与 peerDeviceName 一致
  const header = cloneHeader(messageData.header);
  if (peerDeviceName) {
    header.receiver = peerDeviceName;
  }

  const portInfo = {
    ...port,
    deviceName: currentDeviceName || port.deviceName || '',
    peerDeviceName,
    direction,
    messageConfig: {
      header: header,
      fields: cloneFields(messageData.fields),
    },
    protocolId: messageData.protocolId || port.protocolId || null,
  };
  console.log('Opening dialog with portInfo:', portInfo);
  currentPortIndex.value = port._originalIndex;
  protocolDialogRef.value?.open(portInfo);
};

const buildParamsFromHeader = (header) => {
  const pick = (...keys) => {
    for (const k of keys) {
      const val = header?.[k];
      if (val !== undefined && val !== null && val !== '') return val;
    }
    return undefined;
  };

  return {
    baudRate: pick('baudRate', 'speed'),
    dataBits: pick('dataBits'),
    stopBits: pick('stopBits'),
    parity: pick('parity'),
    canMode: pick('canMode', 'mode'),
    ipAddress: pick('ipAddress'),
    port: pick('port'),
    protocol: pick('protocol'),
    busAddress: pick('busAddress'),
    rtAddress: pick('rtAddress'),
    subAddress: pick('subAddress'),
  };
};

// 协议提交回调
const handleProtocolSubmit = ({ messageConfig, protocolId }) => {
  // 更新端口的协议信息
  if (currentPortIndex.value >= 0) {
    const paramsPatch = buildParamsFromHeader(messageConfig?.header || {});
    portList.value[currentPortIndex.value] = {
      ...portList.value[currentPortIndex.value],
      messageConfig,
      protocolId,
      params: {
        ...(portList.value[currentPortIndex.value].params || {}),
        ...paramsPatch,
      },
    };
  }
};

defineExpose({
  open: drawer.open,
  close: drawer.close,
});
</script>

<style lang="less" scoped>
// Simulation scopes keep their own variables; other consumers inherit ZXUI.

.node-group-card {
  background: var(--sim-bg-panel, var(--zx-semantic-surface-card-fill));
  border: 1px solid var(--sim-border-base, var(--zx-semantic-border-default));
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--sim-shadow-md, var(--zx-semantic-surface-card-depth));
}

.node-group-header {
  background: var(--sim-accent-bg, var(--zx-semantic-surface-header-fill));
  border-bottom: 1px solid var(--sim-border-accent, var(--zx-semantic-border-default));
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));
}

.node-group-title {
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));
}

.node-group-arrow {
  color: var(--sim-text-secondary, var(--zx-semantic-text-secondary));
}

.node-group-chip {
  background: var(--sim-bg-main, var(--zx-semantic-surface-canvas-fill));
  border: 1px solid var(--sim-border-light, var(--zx-semantic-border-subtle));
  color: var(--sim-text-secondary, var(--zx-semantic-text-secondary));
}

.node-group-count {
  background: var(--sim-accent-bg, var(--zx-semantic-fill-selected));
  border: 1px solid var(--sim-border-accent, var(--zx-semantic-border-default));
  color: var(--sim-accent, var(--zx-semantic-accent-base));
}

.node-protocol-list {
  background: var(--sim-bg-main, var(--zx-semantic-surface-canvas-fill));
}

.node-empty-tip {
  color: var(--sim-text-tertiary, var(--zx-semantic-text-secondary));
}

.node-protocol-card {
  background: var(--sim-fill-light, var(--zx-semantic-surface-card-fill));
  border: 1px solid var(--sim-border-base, var(--zx-semantic-border-default));
  border-radius: 10px;
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));

  &:hover {
    border-color: var(--sim-border-hover, var(--zx-semantic-border-strong));
    box-shadow: var(--sim-shadow-glow-accent, var(--zx-semantic-surface-card-depth));
  }
}

.node-protocol-icon {
  background: var(--sim-accent-bg, var(--zx-semantic-fill-selected));
  color: var(--sim-accent, var(--zx-semantic-accent-base));
}

.node-protocol-title {
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));
}

.node-protocol-arrow {
  color: var(--sim-text-secondary, var(--zx-semantic-text-secondary));

  .group:hover & {
    color: var(--sim-accent, var(--zx-semantic-accent-base));
  }
}
</style>
