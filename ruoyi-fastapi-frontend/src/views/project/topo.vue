<template>
  <ZxContentWrap class="home">
    <XflowDAG
      ref="dagRef"
      :operators="operators"
      :operators-loading="loading"
      :layout="layoutMode"
      :dnd-config="dndConfig"
      @node-dblclick="handleNodeDblclick"
    />

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />
  </ZxContentWrap>
</template>

<script setup name="Index">
import { ref, onMounted } from 'vue';
import XflowDAG from '@/components/business/Dag/index.vue';
import { NodeEditDrawer } from './components';
import { listDevice } from '@/api/device/device';
import { ElMessage } from 'element-plus';
import { getPortColor } from '@/constants/portColor';

const version = ref('3.9.0');

// DAG 组件配置 - 设备列表（从后端获取）
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal'); // 'vertical' | 'horizontal'

// DAG 组件引用
const dagRef = ref(null);

// 节点编辑抽屉
const nodeEditDrawerRef = ref(null);
const currentNode = ref(null);

// 可配置的文案和设置
const dndConfig = {
  title: '设备库',
  searchPlaceholder: '搜索设备...',
  textConfig: {
    loadingText: '正在加载设备库...',
    emptySearchText: '没有找到匹配的设备',
    emptySearchDesc: '请尝试使用其他关键词搜索',
    emptyDataText: '暂无可用设备',
    emptyDataDesc: '请先添加设备数据',
  },
};

/**
 * 解析端口方向，兼容中英文配置
 * @param {Object} intf - 接口数据
 * @returns {String} 方向标识
 */
function resolvePortDirection(intf) {
  const source = intf?.direction || intf?.params?.direction;
  const text = String(source || '').toLowerCase();
  if (text.includes('入') || text === 'input' || text === 'in') {
    return 'input';
  }
  if (text.includes('出') || text === 'output' || text === 'out') {
    return 'output';
  }
  return 'bidirectional';
}

/**
 * 转换设备接口数据为端口格式
 * @param {Array} interfaces - 接口列表
 * @returns {Array} 端口列表
 */
function convertInterfacesToPorts(interfaces) {
  if (!interfaces || !Array.isArray(interfaces)) {
    return [];
  }

  return interfaces.map((intf, index) => {
    // 总线类型用于展示和配色
    const busType = intf.interfaceType || intf.busType || 'RS422';

    // 使用接口自身的布局位置，保持与设备配置一致
    const position = String(intf.position || '').toLowerCase();
    const validGroups = ['left', 'right', 'top', 'bottom'];
    const group = validGroups.includes(position) ? position : 'right';

    const rawProtocol = intf.protocolConfig || intf.messageConfig || null;
    const protocolConfig = rawProtocol ? JSON.parse(JSON.stringify(rawProtocol)) : {};
    const protocolType = intf.protocolType || protocolConfig.protocolType || protocolConfig.type || '';
    const dataRate = intf.dataRate || intf.params?.dataRate || protocolConfig.dataRate || '';

    return {
      id: `port-${intf.interfaceId || index}`,
      interfaceId: intf.interfaceId,
      interfaceName: intf.interfaceName || `端口${index + 1}`,
      interfaceType: busType, // 与设备管理保持一致
      busType: busType,
      direction: resolvePortDirection(intf),
      group: group,
      description: intf.description || intf.remark || '',
      color: getPortColor(busType),
      dataRate,
      protocolType,
      protocolConfig,
      messageConfig: protocolConfig,
      params: intf.params || {},
    };
  });
}

/**
 * 从后端加载设备列表数据
 */
async function loadDeviceList() {
  loading.value = true;
  try {
    // 从后端获取设备列表
    const response = await listDevice({});
    console.log('response33333333', response);
    const devices = response?.rows || [];

    if (devices.length === 0) {
      ElMessage.warning('暂无设备数据，请先添加设备');
      operators.value = [];
      return;
    }
    // 确保端口数据存在，若列表未返回则补充查询详情
    const devicesWithPorts = devices.map(device => {
      const interfaces = Array.isArray(device.interfaces) ? device.interfaces : [];
      const ports = convertInterfacesToPorts(interfaces);

      return {
        // DAG组件需要的字段
        name: device.deviceName,
        value: device.remark || device.deviceDesc || '设备',
        category: device.categoryName || device.category || '未分类',

        // 设备原始数据（用于节点创建时使用）
        deviceId: device.deviceId,
        deviceType: device.deviceType,
        busType: device.busType,
        manufacturer: device.manufacturer,
        model: device.model,
        version: device.version,

        // 端口信息（用于连接桩）
        ports,

        // 节点类型标识
        nodeType: 'device-port-node',
      };
    });

    operators.value = devicesWithPorts;

    console.log('设备列表加载成功:', {
      total: devicesWithPorts.length,
      devices: devicesWithPorts,
    });
  } catch (error) {
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 处理节点双击事件
 * @param {Object} params - 包含 node, event, type
 */
function handleNodeDblclick({ node, event, type }) {
  console.log('节点双击:', { node, event, type });

  // 保存当前节点数据
  currentNode.value = node;

  // 打开抽屉
  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 * @param {Object} params - 包含 nodeId, node, name, ports
 */
function handleNodeUpdate({ nodeId, node, name, ports }) {
  console.log('更新节点:', { nodeId, node, name, ports });

  // 获取图实例
  const graph = dagRef.value?.getGraph();
  if (!graph) {
    console.error('图实例不存在');
    ElMessage.error('更新失败：图实例不存在');
    return;
  }

  // 通过节点ID获取节点实例
  const cellNode = graph.getCellById(nodeId);
  if (!cellNode) {
    ElMessage.error('更新失败：节点不存在');
    return;
  }

  // 获取当前节点数据
  const currentData = cellNode.getData() || {};

  // 更新节点数据（包含 label、name 和 ports 字段）
  const updatedData = {
    ...currentData,
    name: name,
    label: name,
    ports: ports || currentData.ports, // 更新端口信息（包含协议配置）
  };

  // 如果存在 properties.content 结构，也更新里面的 label
  if (currentData.properties?.content) {
    updatedData.properties = {
      ...currentData.properties,
      content: {
        ...currentData.properties.content,
        label: name,
      },
    };
  }

  // 使用 setData 方法更新节点数据
  // 节点组件会通过 watch 监听数据变化并自动重新渲染
  cellNode.setData(updatedData, { overwrite: false });

  console.log('节点数据已更新:', updatedData);

  // 如果需要更新到后端，可以在这里调用 API
  // await updateNodeName(nodeId, name)
  // await updateNodePorts(nodeId, ports)
}

// 页面加载时获取设备列表
onMounted(() => {
  loadDeviceList();
});

function goTarget(url) {
  window.open(url, '__blank');
}
</script>

<style lang="less">
.home {
  height: calc(100vh - 84px);
  display: flex;
  flex-direction: column;
  &.zx-content-wrap .el-card__body {
    height: 100%;
    .zx-content-wrap__content {
      height: 100%;
    }
  }
}
</style>
