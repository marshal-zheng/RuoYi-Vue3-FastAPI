<template>
  <ZxContentWrap
    title="设备端口配置"
    message="双击设备查看协议列表 | 双击端口编辑 | 右键设备可添加端口 | 右键端口可编辑/删除"
  >
    <template #header-right>
      <el-tag v-if="!loading" type="info" size="large"
        >已配置 {{ devicePorts.length }} 个端口</el-tag
      >
      <ZxButton type="primary" icon="Plus" @click="handleAddPort">添加端口</ZxButton>
      <ZxButton type="primary" icon="CircleCheck" @click="handleSave">保存</ZxButton>
    </template>
    <div class="h-[600px]">
      <XFlow>
        <XFlowGraph
          ref="graphRef"
          :readonly="false"
          :connection-options="connectionOptions"
          :connection-edge-options="connectionEdgeOptions"
          :custom-menu-handler="customMenuHandler"
          :enable-double-click-fit="false"
          @ready="onGraphReady"
          @node:click="onNodeClick"
          @node-dblclick="onNodeDblClick"
        >
          <XFlowGrid :size="14" type="mesh" :dot-size="2" color="#e6e6e6" />
        </XFlowGraph>
      </XFlow>
    </div>

    <PortEditDialog
      ref="portDialogRef"
      :title="portDialogTitle"
      :value="portForm"
      @submit="handlePortSubmit"
    />
    <PortConfigDrawer
      ref="portConfigDrawerRef"
      :title="portDrawerTitle"
      :port-info="currentPortInfo"
      @submit="handlePortConfigSubmit"
    />
    <DeviceNameDialog
      v-model="deviceNameDialogVisible"
      :value="deviceNameForm"
      @submit="handleDeviceNameSubmit"
      @close="handleDeviceNameDialogClose"
    />
    <ProtocolListDrawer
      ref="protocolDrawerRef"
      :title="`${deviceInfo.deviceName || '设备'} - 协议列表`"
      :device-ports="tempPorts"
      @protocol-click="handleProtocolClick"
    />
  </ZxContentWrap>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { cloneDeep } from 'lodash-es';
import { XFlow, XFlowGraph, XFlowGrid } from '@/components/business/ZxFlow';
import { registerDagShapes, DAG_EDGE } from '@/components/business/Dag/shapes/registerDagShapes';
import { getDevice, addDevice, updateDevice } from '@/api/device/device';
import PortEditDialog from '@/components/business/Device/PortEditDialog.vue';
import PortConfigDrawer from '@/components/business/Device/PortConfigDrawer.vue';
import DeviceNameDialog from '@/components/business/Device/DeviceNameDialog.vue';
import ProtocolListDrawer from '@/components/business/Device/ProtocolListDrawer.vue';

registerDagShapes();

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const deviceInfo = ref({});
const tempPorts = ref([]);
const devicePorts = ref([]);
const graphRef = ref(null);
const graphInstance = ref(null);
const selectedPortId = ref(null);

const portDialogRef = ref(null);
const portDialogTitle = ref('添加端口');
const portForm = reactive({
  interfaceId: null,
  deviceId: null,
  interfaceName: '',
  interfaceType: 'RS422',
  position: 'right',
  description: '',
});

const portConfigDrawerRef = ref(null);
const portDrawerTitle = ref('端口配置');
const currentPortInfo = ref({});

const deviceNameDialogVisible = ref(false);
const deviceNameFormRef = ref(null);
const deviceNameForm = reactive({ deviceName: '', categoryName: '' });

const connectionOptions = {
  snap: false,
  allowBlank: false,
  allowLoop: false,
  allowNode: false,
  allowEdge: false,
  allowPort: false,
  highlight: false,
  validateConnection: () => false,
};
const connectionEdgeOptions = {
  shape: DAG_EDGE,
  animated: false,
  zIndex: -1,
  attrs: {
    line: {
      stroke: '#C2C8D5',
      strokeWidth: 2,
      targetMarker: { name: 'block', width: 8, height: 6 },
    },
  },
};

const deviceId = computed(() => route.query.id);

function getDefaultParams(interfaceType) {
  const map = {
    RS422: { baudRate: 115200, dataBits: 8, stopBits: 1, parity: 'None' },
    RS485: { baudRate: 115200, dataBits: 8, stopBits: 1, parity: 'None' },
    CAN: { baudRate: 250000, canMode: 'A' },
    LAN: { ipAddress: '192.168.1.100', port: 8080, protocol: 'TCP' },
    '1553B': { busAddress: 0, rtAddress: 0, subAddress: 0 },
  };
  const cfg = map[interfaceType];
  return cfg ? cloneDeep(cfg) : {};
}

function getDefaultMessageConfig() {
  return cloneDeep({
    header: {
      sender: '设备1',
      receiver: '',
      frequency: 'once',
      baudRate: 460,
      method: '422',
      duration: 0,
      frameLength: 1,
      errorHandling: 'ignore',
    },
    fields: [],
  });
}

async function handleSave() {
  try {
    loading.value = true;
    const submitData = {
      deviceId: deviceInfo.value.deviceId || null,
      deviceName: deviceInfo.value.deviceName || '未命名设备',
      deviceType: deviceInfo.value.deviceType || '',
      manufacturer: deviceInfo.value.manufacturer || '',
      model: deviceInfo.value.model || '',
      version: deviceInfo.value.version || '',
      busType: deviceInfo.value.busType || '',
      categoryName: deviceInfo.value.categoryName || '',
      remark: deviceInfo.value.remark || '',
      interfaces: tempPorts.value.map(port => ({
        interfaceId: port.interfaceId || null,
        interfaceName: port.interfaceName,
        interfaceType: port.interfaceType,
        position: port.position,
        description: port.description || '',
        params: port.params || getDefaultParams(port.interfaceType),
        messageConfig: port.messageConfig || getDefaultMessageConfig(),
      })),
    };
    if (submitData.deviceId) {
      await updateDevice(submitData);
      ElMessage.success('设备配置保存成功');
    } else {
      const response = await addDevice(submitData);
      ElMessage.success('设备创建成功');
      const newDeviceId = response.data?.deviceId || response.deviceId;
      if (newDeviceId) {
        deviceInfo.value.deviceId = newDeviceId;
        router.replace('/device/detail?id=' + newDeviceId);
      }
    }
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.push('/device/list');
}

async function loadDeviceInfo() {
  const id = deviceId.value;
  if (!id) {
    deviceInfo.value = {
      deviceId: null,
      deviceName: '新设备',
      deviceType: '',
      manufacturer: '',
      model: '',
      version: '',
      busType: '',
      categoryName: '',
      remark: '',
      interfaces: [],
    };
    tempPorts.value = [];
    devicePorts.value = [];
    updateGraphData();
    return;
  }
  loading.value = true;
  try {
    const response = await getDevice(id);
    deviceInfo.value = response.data || response;
    await loadDevicePorts();
    updateGraphData();
  } finally {
    loading.value = false;
  }
}

async function loadDevicePorts() {
  if (deviceInfo.value.interfaces && deviceInfo.value.interfaces.length > 0) {
    tempPorts.value = deviceInfo.value.interfaces.map(intf => ({
      id: intf.interfaceId,
      interfaceId: intf.interfaceId,
      deviceId: deviceInfo.value.deviceId,
      interfaceName: intf.interfaceName,
      interfaceType: intf.interfaceType,
      position: intf.position || 'right',
      description: intf.description || '',
      params: intf.params ? cloneDeep(intf.params) : getDefaultParams(intf.interfaceType),
      messageConfig: intf.messageConfig ? cloneDeep(intf.messageConfig) : getDefaultMessageConfig(),
    }));
  }
  devicePorts.value = tempPorts.value;
}

function updateGraphData() {
  if (!graphInstance.value) return;
  const portsData = devicePorts.value.map((port, index) => ({
    id: port.id || `port_${index}`,
    group: port.position || 'right',
    interfaceId: port.interfaceId || port.id,
    interfaceName: port.interfaceName,
    interfaceType: port.interfaceType,
    description: port.description,
  }));

  const BASE_PORT_LABEL_ATTRS = {
    text: '',
    fontSize: 9,
    fontFamily: 'Arial, sans-serif',
    fontWeight: 500,
    fill: '#4b5563',
    textAnchor: 'middle',
    textVerticalAnchor: 'middle',
    'dominant-baseline': 'middle',
    x: 0,
    y: -2,
    pointerEvents: 'none',
  };

  const commonMarkup = [
    { tagName: 'rect', selector: 'portBody' },
    { tagName: 'text', selector: 'portLabel' },
  ];

  const createPortGroup = width => ({
    position: { name: 'absolute' },
    markup: commonMarkup.map(item => ({ ...item })),
    attrs: {
      portBody: {
        width,
        height: 12,
        x: -width / 2,
        y: -6,
        magnet: false,
        fill: '#fff',
        strokeWidth: 1,
        cursor: 'pointer',
        rx: 0,
        ry: 0,
      },
      portLabel: { ...BASE_PORT_LABEL_ATTRS },
    },
  });

  const portGroups = {
    top: createPortGroup(16),
    bottom: createPortGroup(16),
    left: createPortGroup(32),
    right: createPortGroup(32),
  };
  const colorMap = {
    RS422: '#f59e0b',
    RS485: '#f97316',
    CAN: '#3b82f6',
    LAN: '#10b981',
    '1553B': '#8b5cf6',
  };
  const x6Ports = devicePorts.value.map((port, index) => {
    const portId = port.id || `port_${index}`;
    const group = port.position || 'right';
    const busType = port.interfaceType || 'RS422';
    const color = colorMap[busType] || '#6b7280';
    const isTB = group === 'top' || group === 'bottom';
    const name = port.interfaceName || port.id;
    const text = name.length > (isTB ? 6 : 7) ? name.substring(0, isTB ? 5 : 6) + '..' : name;
    return {
      id: portId,
      group,
      args: { x: 0, y: 0 },
      attrs: { portBody: { stroke: color }, portLabel: { text } },
    };
  });
  graphInstance.value.clearCells();
  graphInstance.value.addNode({
    id: 'device_node',
    shape: 'device-port-node',
    x: 100,
    y: 75,
    width: 200,
    height: 150,
    data: {
      type: 'device',
      label: deviceInfo.value.deviceName || '设备',
      deviceId: deviceInfo.value.deviceId || null,
      busType: deviceInfo.value.busType || '',
      ports: portsData,
      selectedPortId: selectedPortId.value,
    },
    ports: { groups: portGroups, items: x6Ports },
  });
  nextTick(() => {
    graphInstance.value.zoomToFit({ padding: 50, maxScale: 1 });
  });
}

function customMenuHandler(items, type, target) {
  if (type === 'node' && target?.id === 'device_node') {
    return [
      {
        id: 'edit-device-name',
        label: '编辑设备信息',
        icon: 'Edit',
        action: () => handleEditDeviceName(),
      },
      { type: 'divider' },
      {
        id: 'add-left-port',
        label: '添加左侧端口',
        icon: 'Plus',
        action: () => handleAddPortWithPosition('left'),
      },
      {
        id: 'add-right-port',
        label: '添加右侧端口',
        icon: 'Plus',
        action: () => handleAddPortWithPosition('right'),
      },
    ];
  }
  return [];
}

function onGraphReady(graph) {
  graphInstance.value = graph;
  updateGraphData();
}

function onNodeDblClick({ node, event }) {
  if (!node) return;
  const e = event;
  const target = e?.target || e?.currentTarget || e?.srcElement;
  let portElement = null;
  try {
    if (target && typeof target.closest === 'function') {
      portElement = target.closest('[port]');
    }
  } catch {}
  if (portElement) {
    const portId = portElement.getAttribute('port');
    const portData = tempPorts.value.find(p => (p.id || p.interfaceId) === portId);
    if (portData) {
      handleEditPort(portData);
    }
  } else {
    handleShowProtocolList();
  }
}

function handlePortContextMenu({ port, e }) {
  e.preventDefault();
  const portData = tempPorts.value.find(
    p => (p.id || p.interfaceId) === (port.id || port.interfaceId)
  );
  if (!portData) return;
  ElMessageBox.confirm(`端口：${port.interfaceName} (${port.interfaceType})`, '端口操作', {
    confirmButtonText: '编辑',
    cancelButtonText: '删除',
    distinguishCancelAndClose: true,
    type: 'info',
  })
    .then(() => {
      handleEditPortDialog(portData);
    })
    .catch(action => {
      if (action === 'cancel') {
        ElMessageBox.confirm(`确定要删除端口 "${port.interfaceName}" 吗？`, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }).then(() => {
          handleDeletePort(port.id || port.interfaceId);
        });
      }
    });
}

function handleEditPortDialog(port) {
  portDialogTitle.value = '编辑端口';
  portForm.interfaceId = port.interfaceId || port.id;
  portForm.deviceId = port.deviceId || deviceId.value;
  portForm.interfaceName = port.interfaceName;
  portForm.interfaceType = port.interfaceType;
  portForm.position = port.position;
  portForm.description = port.description;
  portDialogRef.value?.open();
}

function onNodeClick({ e }) {
  const target = e.target;
  if (target && target.classList && target.classList.contains('port-item')) {
    const portId = target.dataset.portId;
    handlePortClick(portId);
  }
}

function handleAddPortWithPosition(position) {
  const label = { left: '左侧', right: '右侧', top: '顶部', bottom: '底部' }[position];
  portDialogTitle.value = `添加${label}端口`;
  portForm.interfaceId = null;
  portForm.deviceId = deviceId.value;
  portForm.interfaceName = '';
  portForm.interfaceType = 'RS422';
  portForm.position = position;
  portForm.description = '';
  handleBusTypeChange('RS422');
  portDialogRef.value?.open();
}

function handlePortClick(portId) {
  if (!portId) return;
  selectedPortId.value = selectedPortId.value === portId ? null : portId;
  updatePortHighlight();
}

function updatePortHighlight() {
  if (!graphInstance.value) return;
  const node = graphInstance.value.getCellById('device_node');
  if (node) {
    node.setData({ ...node.getData(), selectedPortId: selectedPortId.value });
  }
}

function handleBusTypeChange(busType) {
  if (!portForm.interfaceId && busType) {
    generatePortName(busType, portForm.position);
  }
}

function handlePositionChange(position) {}

function generatePortName(busType) {
  portForm.interfaceName = busType;
}

function handleAddPort() {
  portDialogTitle.value = '添加端口';
  portForm.interfaceId = null;
  portForm.deviceId = deviceId.value;
  portForm.interfaceName = '';
  portForm.interfaceType = 'RS422';
  portForm.position = 'right';
  portForm.description = '';
  portDialogRef.value?.open();
}

function handleEditPort(port) {
  portDrawerTitle.value = `端口配置 - ${port.interfaceName}`;
  currentPortInfo.value = { ...port };
  portConfigDrawerRef.value?.open();
}

async function handleDeletePort(interfaceId) {
  const index = tempPorts.value.findIndex(p => (p.id || p.interfaceId) === interfaceId);
  if (index > -1) {
    tempPorts.value.splice(index, 1);
    ElMessage.success('删除成功');
    await loadDevicePorts();
    updateGraphData();
  }
}

async function handlePortSubmit(formData) {
  if (formData.interfaceId) {
    const index = tempPorts.value.findIndex(p => (p.id || p.interfaceId) === formData.interfaceId);
    if (index > -1) {
      const oldPort = tempPorts.value[index];
      tempPorts.value[index] = {
        ...formData,
        params: oldPort.params,
        messageConfig: oldPort.messageConfig,
      };
      ElMessage.success('修改成功');
    }
  } else {
    const newPort = {
      ...formData,
      id: `port_${Date.now()}`,
      interfaceId: `port_${Date.now()}`,
      params: getDefaultParams(formData.interfaceType),
      messageConfig: getDefaultMessageConfig(),
    };
    tempPorts.value.push(newPort);
    ElMessage.success('添加成功');
  }
  portDialogRef.value?.close();
  await loadDevicePorts();
  updateGraphData();
}

async function handlePortConfigSubmit(portData) {
  const index = tempPorts.value.findIndex(
    p => (p.id || p.interfaceId) === (portData.interfaceId || portData.id)
  );
  if (index > -1) {
    tempPorts.value[index] = {
      ...tempPorts.value[index],
      params: portData.params ? cloneDeep(portData.params) : tempPorts.value[index].params,
      messageConfig: portData.messageConfig
        ? cloneDeep(portData.messageConfig)
        : tempPorts.value[index].messageConfig,
    };
  }
  await loadDevicePorts();
  updateGraphData();
}

function handleEditDeviceName() {
  deviceNameForm.deviceName = deviceInfo.value.deviceName || '设备';
  deviceNameForm.categoryName = deviceInfo.value.categoryName || '';
  deviceNameDialogVisible.value = true;
}

async function handleDeviceNameSubmit(formData) {
  deviceInfo.value.deviceName = formData.deviceName;
  deviceInfo.value.categoryName = formData.categoryName;
  deviceNameDialogVisible.value = false;
  updateGraphData();
  ElMessage.success('设备信息修改成功');
}

function handleDeviceNameDialogClose() {
  deviceNameFormRef.value?.resetFields();
}

const protocolDrawerRef = ref(null);
function handleShowProtocolList() {
  protocolDrawerRef.value?.open();
}
function handleProtocolClick({ port }) {
  protocolDrawerRef.value?.close();
  portDrawerTitle.value = `端口配置 - ${port.interfaceName}`;
  currentPortInfo.value = { ...port };
  portConfigDrawerRef.value?.open();
}

onMounted(() => {
  loadDeviceInfo();
});
onBeforeUnmount(() => {
  if (graphInstance.value) {
    graphInstance.value.off('port:contextmenu', handlePortContextMenu);
  }
});
</script>
