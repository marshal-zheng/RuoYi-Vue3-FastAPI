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
    <div class="h-[720px]">
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
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue';
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
import { getPortColor } from '@/constants/portColor';

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
const graphEventHandlers = {
  portClick: null,
  portDblClick: null,
  portContextMenu: null,
  blankClick: null,
  nodeContextMenu: null,
};

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

const deviceId = computed(() => {
  const normalize = (value) => {
    if (Array.isArray(value)) return value[0] ?? null;
    if (value === undefined || value === null || value === '') return null;
    return value;
  };
  const paramId = normalize(route.params?.deviceId);
  if (paramId) return paramId;
  const queryDeviceId = normalize(route.query?.deviceId);
  if (queryDeviceId) return queryDeviceId;
  return normalize(route.query?.id);
});

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
  return null;
}

function normalizeInterfaceId(value) {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return null;
}

function normalizePortKey(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
}

function getPortKey(port) {
  if (!port) return '';
  const idKey = normalizePortKey(port.id);
  if (idKey) {
    return idKey;
  }
  return normalizePortKey(port.interfaceId);
}

function findPortByKey(key) {
  const normalizedKey = normalizePortKey(key);
  if (!normalizedKey) return null;
  return tempPorts.value.find((port) => getPortKey(port) === normalizedKey) || null;
}

function findPortIndexByKey(key) {
  const normalizedKey = normalizePortKey(key);
  if (!normalizedKey) return -1;
  return tempPorts.value.findIndex((port) => getPortKey(port) === normalizedKey);
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
      interfaces: tempPorts.value.map((port) => ({
        interfaceId: normalizeInterfaceId(port.interfaceId),
        interfaceName: port.interfaceName,
        interfaceType: port.interfaceType,
        position: port.position,
        description: port.description || '',
        params: port.params || getDefaultParams(port.interfaceType),
        messageConfig: port.messageConfig || null,
      })),
    };
    if (submitData.deviceId) {
      await updateDevice(submitData);
      ElMessage.success('设备配置保存成功');
      router.push('/device/list');
    } else {
      const response = await addDevice(submitData);
      ElMessage.success('设备创建成功');
      router.push('/device/list');
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
    // 从 sessionStorage 读取新增设备的数据
    const newDeviceDataStr = sessionStorage.getItem('newDeviceData');
    let newDeviceData = null;
    console.log('newDeviceDataStr', newDeviceDataStr);
    if (newDeviceDataStr) {
      try {
        newDeviceData = JSON.parse(newDeviceDataStr);
        // 读取后清除
        sessionStorage.removeItem('newDeviceData');
        console.log('读取到新设备数据:', newDeviceData);
      } catch (e) {
        console.error('解析新增设备数据失败:', e);
      }
    }

    // 确保使用用户输入的设备名称
    const deviceName = newDeviceData?.deviceName || '新设备';

    console.log('newDeviceData', newDeviceData);

    deviceInfo.value = {
      deviceId: null,
      deviceName: deviceName,
      deviceType: '',
      manufacturer: '',
      model: '',
      version: '',
      busType: '',
      categoryName: newDeviceData?.categoryName || '',
      remark: newDeviceData?.remark || '',
      interfaces: [],
    };

    console.log('设备信息已设置:', deviceInfo.value);

    tempPorts.value = [];
    devicePorts.value = [];
    updateGraphData();
    return;
  }
  loading.value = true;
  try {
    const response = await getDevice(id);
    deviceInfo.value = response.data || response;
    loadDevicePorts();
    updateGraphData();
  } finally {
    loading.value = false;
  }
}

watch(
  [() => route.params.deviceId, () => route.query.id, () => route.query.deviceId],
  (newValues, oldValues) => {
    const normalize = (value) => {
      if (Array.isArray(value)) {
        return value[0] ?? null;
      }
      if (value === undefined || value === null || value === '') {
        return null;
      }
      return value;
    };
    const pickFirstValid = (values) => {
      if (!values) return null;
      for (const val of values) {
        const normalized = normalize(val);
        if (normalized) {
          return normalized;
        }
      }
      return null;
    };
    const newId = pickFirstValid(newValues);
    const oldId = pickFirstValid(oldValues);
    if (newId === oldId) {
      return;
    }
    loadDeviceInfo();
  }
);

function loadDevicePorts() {
  if (deviceInfo.value.interfaces && deviceInfo.value.interfaces.length > 0) {
    tempPorts.value = deviceInfo.value.interfaces.map((intf, index) => {
      const normalizedId = normalizePortKey(intf.interfaceId);
      // 兼容处理：将字符串 position 转为数组格式
      let position = intf.position || ['right'];
      if (typeof position === 'string') {
        position = [position];
      }
      return {
        id: normalizedId || `port_${index}`,
        interfaceId: intf.interfaceId,
        deviceId: deviceInfo.value.deviceId,
        interfaceName: intf.interfaceName,
        interfaceType: intf.interfaceType,
        position: position,
        description: intf.description || '',
        params: intf.params ? cloneDeep(intf.params) : getDefaultParams(intf.interfaceType),
        messageConfig: intf.messageConfig ? cloneDeep(intf.messageConfig) : null,
      };
    });
  }
  syncDevicePorts();
}

function syncDevicePorts() {
  devicePorts.value = tempPorts.value.map((port) => ({ ...port }));
}

function updateGraphData() {
  if (!graphInstance.value) return;
  const portsData = devicePorts.value.map((port, index) => {
    // 兼容处理：如果 position 是数组，取第一个值作为主位置
    let position = 'right';
    if (Array.isArray(port.position) && port.position.length > 0) {
      position = port.position[0];
    } else if (typeof port.position === 'string') {
      position = port.position;
    }
    return {
      id: port.id || `port_${index}`,
      group: position,
      interfaceId: port.interfaceId || port.id,
      interfaceName: port.interfaceName,
      interfaceType: port.interfaceType,
      description: port.description,
    };
  });

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

  const createPortGroup = (width) => ({
    position: { name: 'absolute' },
    markup: commonMarkup.map((item) => ({ ...item })),
    attrs: {
      portBody: {
        width,
        height: 12,
        x: -width / 2,
        y: -6,
        magnet: true,
        fill: '#fff',
        strokeWidth: 1,
        cursor: 'pointer',
        pointerEvents: 'all',
        'pointer-events': 'all',
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
  const x6Ports = devicePorts.value.map((port, index) => {
    const portId = port.id || `port_${index}`;
    const normalizedSelectedKey = normalizePortKey(selectedPortId.value);
    const normalizedPortKey = normalizePortKey(portId);
    const isSelected = normalizedSelectedKey && normalizedSelectedKey === normalizedPortKey;
    // 兼容处理：如果 position 是数组，取第一个值作为主位置
    let group = 'right';
    if (Array.isArray(port.position) && port.position.length > 0) {
      group = port.position[0];
    } else if (typeof port.position === 'string') {
      group = port.position;
    }
    const color = getPortColor({
      busType: port.busType,
      interfaceType: port.interfaceType,
    });
    const isTB = group === 'top' || group === 'bottom';
    const name = port.interfaceName || port.id;
    const text = name.length > (isTB ? 6 : 7) ? name.substring(0, isTB ? 5 : 6) + '..' : name;
    return {
      id: portId,
      group,
      args: { x: 0, y: 0 },
      zIndex: 10,
      attrs: {
        portBody: {
          stroke: color,
          strokeWidth: isSelected ? 2 : 1,
          fill: isSelected ? '#e8f3ff' : '#fff',
        },
        portLabel: {
          text,
          fill: isSelected ? '#1f4b99' : '#4b5563',
          fontWeight: isSelected ? 600 : 500,
        },
      },
    };
  });
  graphInstance.value.clearCells();

  const deviceLabel = deviceInfo.value.deviceName || '设备';
  console.log('更新图表,设备名称:', deviceLabel);

  graphInstance.value.addNode({
    id: 'device_node',
    shape: 'device-port-node',
    x: 100,
    y: 75,
    width: 200,
    height: 150,
    data: {
      type: 'device',
      label: deviceLabel,
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
      { type: 'divider' },
      {
        id: 'delete-selected-port',
        label: selectedPortId.value
          ? `删除端口：${findPortByKey(selectedPortId.value)?.interfaceName || selectedPortId.value}`
          : '删除端口（先选中）',
        icon: 'Delete',
        // disabled: !selectedPortId.value || !findPortByKey(selectedPortId.value),
        action: () => handleDeleteSelectedPort(),
      },
    ];
  }
  if (type === 'port' && target) {
    const portTarget = target.port || target;
    const targetId = portTarget?.id || portTarget?.interfaceId;
    const portData = findPortByKey(targetId);
    if (portData) {
      return [
        {
          id: 'edit-port',
          label: '编辑端口',
          icon: 'Edit',
          action: () => handleEditPortDialog(portData),
        },
        { type: 'divider' },
        {
          id: 'delete-port',
          label: '删除端口',
          icon: 'Delete',
          action: () => {
            ElMessageBox.confirm(`确定要删除端口 "${portData.interfaceName}" 吗？`, '删除确认', {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning',
            }).then(() => {
              handleDeletePort(portData.id || portData.interfaceId);
            });
          },
        },
      ];
    }
  }
  return [];
}

function onGraphReady(graph) {
  graphInstance.value = graph;
  bindGraphEvents(graph);
  updateGraphData();
}

function extractEventPortId(target) {
  if (!target || typeof target.closest !== 'function') return null;
  const portEl = target.closest('[port], .x6-port');
  if (!portEl) return null;
  return (
    portEl.getAttribute('port') ||
    portEl.getAttribute('data-port-id') ||
    portEl.getAttribute('data-port') ||
    portEl.dataset?.portId ||
    portEl.dataset?.port ||
    null
  );
}

function onNodeDblClick({ node, event }) {
  if (!node) return;
  const e = event;
  const target = e?.target || e?.currentTarget || e?.srcElement;
  const portId = extractEventPortId(target);
  if (portId) {
    const portData = findPortByKey(portId);
    if (portData) {
      handleEditPort(portData);
    }
  } else {
    handleShowProtocolList();
  }
}

function handleEditPortDialog(port) {
  portDialogTitle.value = '编辑端口';
  portForm.interfaceId = port.interfaceId || port.id;
  portForm.deviceId = port.deviceId || deviceId.value;
  portForm.interfaceName = port.interfaceName;
  portForm.interfaceType = port.interfaceType;
  // 编辑时禁止多选，只允许单个位置
  portForm.position = Array.isArray(port.position) ? port.position : [port.position];
  portForm.description = port.description;
  portDialogRef.value?.open();
}

function onNodeClick({ e }) {
  const target = e?.target || e?.currentTarget || e?.srcElement;
  const portId = extractEventPortId(target);
  if (portId) {
    handlePortClick(portId, { allowToggle: false });
    return;
  }
  if (selectedPortId.value) {
    selectedPortId.value = null;
    updatePortHighlight();
  }
}

function handleAddPortWithPosition(position) {
  const label = { left: '左侧', right: '右侧', top: '顶部', bottom: '底部' }[position];
  portDialogTitle.value = `添加${label}端口`;
  portForm.interfaceId = null;
  portForm.deviceId = deviceId.value;
  portForm.interfaceName = '';
  portForm.interfaceType = 'RS422';
  portForm.position = [position];
  portForm.description = '';
  handleBusTypeChange('RS422');
  portDialogRef.value?.open();
}

function handlePortClick(portId, { allowToggle = true } = {}) {
  const normalizedId = normalizePortKey(portId);
  if (!normalizedId) return;
  if (selectedPortId.value === normalizedId) {
    if (allowToggle) {
      selectedPortId.value = null;
    }
  } else {
    selectedPortId.value = normalizedId;
  }
  updatePortHighlight();
}

function updatePortHighlight() {
  if (!graphInstance.value) return;
  const node = graphInstance.value.getCellById('device_node');
  if (node) {
    const normalizedSelectedKey = normalizePortKey(selectedPortId.value);
    const ports = node.getPorts ? node.getPorts() : [];
    ports.forEach((port) => {
      const isSelected =
        normalizedSelectedKey && normalizePortKey(port?.id) === normalizedSelectedKey;
      node.setPortProp(port.id, ['attrs', 'portBody', 'strokeWidth'], isSelected ? 2 : 1);
      node.setPortProp(port.id, ['attrs', 'portBody', 'fill'], isSelected ? '#e8f3ff' : '#fff');
      node.setPortProp(port.id, ['attrs', 'portLabel', 'fill'], isSelected ? '#1f4b99' : '#4b5563');
      node.setPortProp(port.id, ['attrs', 'portLabel', 'fontWeight'], isSelected ? 600 : 500);
    });
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
  portForm.position = ['right'];
  portForm.description = '';
  portDialogRef.value?.open();
}

function handleEditPort(port) {
  portDrawerTitle.value = `端口配置 - ${port.interfaceName}`;
  currentPortInfo.value = {
    ...port,
    deviceName: deviceInfo.value.deviceName || '未命名设备',
  };
  portConfigDrawerRef.value?.open();
}

async function handleDeletePort(interfaceId) {
  const index = findPortIndexByKey(interfaceId);
  if (index > -1) {
    tempPorts.value.splice(index, 1);
    if (normalizePortKey(selectedPortId.value) === normalizePortKey(interfaceId)) {
      selectedPortId.value = null;
    }
    ElMessage.success('删除成功');
    syncDevicePorts();
    updateGraphData();
  }
}

async function handlePortSubmit(formData) {
  const hasInterfaceKey =
    formData.interfaceId !== null &&
    formData.interfaceId !== undefined &&
    formData.interfaceId !== '';

  if (hasInterfaceKey) {
    // 编辑模式：更新现有端口
    const index = findPortIndexByKey(formData.interfaceId);
    if (index > -1) {
      const oldPort = tempPorts.value[index];
      tempPorts.value[index] = {
        ...oldPort,
        ...formData,
        id: oldPort.id || formData.interfaceId || oldPort.interfaceId,
        interfaceId: oldPort.interfaceId ?? null,
        params: oldPort.params,
        messageConfig: oldPort.messageConfig,
      };
    }
    ElMessage.success('修改成功');
  } else {
    // 新增模式：如果选择了多个位置，为每个位置创建一个端口
    const positions = Array.isArray(formData.position) ? formData.position : [formData.position];

    if (positions.length === 0) {
      ElMessage.warning('请选择至少一个端口位置');
      return;
    }

    positions.forEach((pos, index) => {
      const tempId = `port_${Date.now()}_${index}`;
      const newPort = {
        ...formData,
        position: [pos], // 每个端口只有一个位置
        id: tempId,
        interfaceId: null,
        params: getDefaultParams(formData.interfaceType),
        messageConfig: null,
      };
      tempPorts.value.push(newPort);
    });

    const count = positions.length;
    ElMessage.success(`成功添加${count}个端口`);
  }

  portDialogRef.value?.close();
  syncDevicePorts();
  updateGraphData();
}

async function handlePortConfigSubmit(portData) {
  // 使用与 getPortKey 一致的逻辑：优先使用 id，然后是 interfaceId
  const index = findPortIndexByKey(portData.id || portData.interfaceId);
  if (index > -1) {
    tempPorts.value[index] = {
      ...tempPorts.value[index],
      params: portData.params ? cloneDeep(portData.params) : tempPorts.value[index].params,
      messageConfig: portData.messageConfig
        ? cloneDeep(portData.messageConfig)
        : tempPorts.value[index].messageConfig,
    };
  }
  syncDevicePorts();
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
  document.addEventListener('keydown', handleKeydownDelete, true);
});
onBeforeUnmount(() => {
  if (graphInstance.value) {
    if (graphEventHandlers.portClick) {
      graphInstance.value.off('port:click', graphEventHandlers.portClick);
    }
    if (graphEventHandlers.portDblClick) {
      graphInstance.value.off('port:dblclick', graphEventHandlers.portDblClick);
    }
    if (graphEventHandlers.portContextMenu) {
      graphInstance.value.off('port:contextmenu', graphEventHandlers.portContextMenu);
    }
    if (graphEventHandlers.nodeContextMenu) {
      graphInstance.value.off('node:contextmenu', graphEventHandlers.nodeContextMenu);
    }
    if (graphEventHandlers.blankClick) {
      graphInstance.value.off('blank:click', graphEventHandlers.blankClick);
    }
  }
  document.removeEventListener('keydown', handleKeydownDelete, true);
});

function bindGraphEvents(graph) {
  if (!graph) return;
  graphEventHandlers.portClick = ({ port }) => {
    const portId = port?.id || port?.interfaceId;
    handlePortClick(portId, { allowToggle: true });
  };
  graphEventHandlers.portDblClick = ({ port }) => {
    const portId = port?.id || port?.interfaceId;
    const portData = findPortByKey(portId);
    if (portData) {
      handleEditPort(portData);
    }
  };
  graphEventHandlers.portContextMenu = ({ port }) => {
    const portId = port?.id || port?.interfaceId;
    if (portId) {
      handlePortClick(portId);
    }
  };
  graphEventHandlers.blankClick = () => {
    if (selectedPortId.value) {
      selectedPortId.value = null;
      updatePortHighlight();
    }
  };
  graphEventHandlers.nodeContextMenu = ({ e }) => {
    // 兼容：如果右键发生在端口元素上但触发了 node:contextmenu，仍然选中该端口
    const portId = extractEventPortId(e?.target || e?.currentTarget || e?.srcElement);
    if (portId) {
      handlePortClick(portId, { allowToggle: false });
    }
  };
  graph.on('port:click', graphEventHandlers.portClick);
  graph.on('port:dblclick', graphEventHandlers.portDblClick);
  graph.on('port:contextmenu', graphEventHandlers.portContextMenu);
  graph.on('node:contextmenu', graphEventHandlers.nodeContextMenu);
  graph.on('blank:click', graphEventHandlers.blankClick);
}

function handleDeleteSelectedPort() {
  const portData = findPortByKey(selectedPortId.value);
  if (!portData) {
    selectedPortId.value = null;
    return;
  }
  const name = portData.interfaceName || portData.interfaceId || '端口';
  return ElMessageBox.confirm(`确定要删除端口 "${name}" 吗？`, '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    handleDeletePort(portData.id || portData.interfaceId);
  });
}

function handleKeydownDelete(e) {
  const key = e.key?.toLowerCase();
  const targetTag = (e?.target?.tagName || '').toLowerCase();
  const isTypingField =
    targetTag === 'input' || targetTag === 'textarea' || e?.target?.isContentEditable;
  if ((key === 'delete' || key === 'backspace') && selectedPortId.value && !isTypingField) {
    e.preventDefault();
    e.stopPropagation();
    handleDeleteSelectedPort();
  }
}
</script>
