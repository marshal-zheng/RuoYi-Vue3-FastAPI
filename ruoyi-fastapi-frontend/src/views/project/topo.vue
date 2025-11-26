<template>
  <ZxContentWrap class="home">
    <XflowDAG
      ref="dagRef"
      :operators="operators"
      :operators-loading="loading"
      :layout="layoutMode"
      :dnd-config="dndConfig"
      :show-graph-control="false"
      @node-dblclick="handleNodeDblclick"
    >
      <template #right>
        <zx-button size="small" type="primary" :disabled="loading" @click="handleSaveTopo">
          保存
        </zx-button>
      </template>
    </XflowDAG>

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />
  </ZxContentWrap>
</template>

<script setup name="Index">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import XflowDAG from '@/components/business/Dag/index.vue';
import { NodeEditDrawer } from './components';
import { listDevice } from '@/api/device/device';
import { saveProjectTopology, getProjectTopology } from '@/api/project/topology';
import { ElMessage } from 'element-plus';
import { getPortColor } from '@/constants/portColor';

const version = ref('3.9.0');

// 路由参数
const route = useRoute();
const router = useRouter();
const projectId = computed(() => route.params.projectId);
const versionId = computed(() => route.query.versionId);

// 仿真相关辅助函数（仿真功能已移除，但保留必要的判断函数以支持保存功能）
function isSimulationToken(node) {
  return node?.getData?.()?.isSimToken === true;
}

function getProjectIdNumber() {
  const id = projectId.value;
  return id ? Number(id) : null;
}

function getVersionIdNumber() {
  const id = versionId.value;
  return id ? Number(id) : undefined;
}

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

function getGraphInstance() {
  return dagRef.value?.getGraph?.() || null;
}

function clearGraphContent(graphInstance) {
  const graph = graphInstance || getGraphInstance();
  if (graph && typeof graph.clearCells === 'function') {
    graph.clearCells();
  }
}

/**
 * 解析端口方向，兼容中英文配置
 * @param {Object} intf - 接口数据
 * @returns {String} 方向标识
 */
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
    const protocolType =
      intf.protocolType || protocolConfig.protocolType || protocolConfig.type || '';
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
    const devices = response?.rows || [];

    if (devices.length === 0) {
      operators.value = [];
      return;
    }
    // 确保端口数据存在，若列表未返回则补充查询详情
    const devicesWithPorts = devices.map((device) => {
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
  } catch (error) {
    void error;
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 根据当前节点构建端口到对端设备名的映射
 * @param {Object} node - 当前节点（X6 节点实例或其 JSON）
 * @returns {Record<string, string | string[]>} key 为端口 ID，value 为对端设备名称（可能存在多条）
 */
function buildPeerDeviceNameByPort(node) {
  const graph = dagRef.value?.getGraph();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];
  const registerPeer = (portId, peerName) => {
    if (!portId || !peerName) return;
    const key = String(portId);
    const keys = [key];
    if (key.startsWith('port-')) {
      keys.push(key.replace(/^port-/, ''));
    }

    keys.forEach((k) => {
      if (!result[k]) {
        result[k] = [];
      }
      const list = Array.isArray(result[k]) ? result[k] : [result[k]];
      if (!list.includes(peerName)) {
        result[k] = list.concat(peerName);
      } else {
        result[k] = list;
      }
    });
  };

  edges.forEach((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    if (!sourceId || !targetId) {
      return;
    }

    let localPortId;
    let peerNodeId;

    if (sourceId === nodeId) {
      localPortId = edge.getSourcePortId?.();
      peerNodeId = targetId;
    } else if (targetId === nodeId) {
      localPortId = edge.getTargetPortId?.();
      peerNodeId = sourceId;
    } else {
      return;
    }

    if (!localPortId || !peerNodeId) {
      return;
    }

    const peerNode = graph.getCellById(peerNodeId);
    const data = peerNode?.getData?.() || {};
    const deviceName = data.name || data.label || data.deviceName || '';

    registerPeer(localPortId, deviceName);
  });

  return result;
}

/**
 * 构建本端端口到所有连接详情的映射
 * @param {Object} node - 当前节点（X6 节点实例或其 JSON）
 * @returns {Record<string, Array>} key 为端口 ID，value 为连接详情数组
 */
function buildPortConnectionsForNode(node) {
  const graph = dagRef.value?.getGraph();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];

  const pushConnection = (localPortId, peerNodeId, peerPortId, edgeId) => {
    if (!localPortId || !peerNodeId) return;

    const peerNode = graph.getCellById(peerNodeId);
    const peerData = peerNode?.getData?.() || {};
    const peerDeviceName = peerData.name || peerData.label || peerData.deviceName || '';

    const connection = {
      edgeId: edgeId,
      localPortId: String(localPortId),
      peerNodeId: String(peerNodeId),
      peerPortId: peerPortId ? String(peerPortId) : '',
      peerDeviceName,
    };

    const key = String(localPortId);
    const keys = [key];
    if (key.startsWith('port-')) {
      keys.push(key.replace(/^port-/, ''));
    }

    keys.forEach((k) => {
      if (!result[k]) {
        result[k] = [];
      }
      result[k] = result[k].concat(connection);
    });
  };

  edges.forEach((edge) => {
    const edgeId = edge.id;
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    if (!sourceId || !targetId) {
      return;
    }

    if (sourceId === nodeId) {
      const localPortId = edge.getSourcePortId?.();
      const peerPortId = edge.getTargetPortId?.();
      pushConnection(localPortId, targetId, peerPortId, edgeId);
    } else if (targetId === nodeId) {
      const localPortId = edge.getTargetPortId?.();
      const peerPortId = edge.getSourcePortId?.();
      pushConnection(localPortId, sourceId, peerPortId, edgeId);
    }
  });

  return result;
}

/**
 * 处理节点双击事件
 * @param {Object} params - 包含 node, event, type
 */
function handleNodeDblclick({ node }) {
  // 计算当前节点各端口对应的对端设备名称
  const peerDeviceNameByPort = buildPeerDeviceNameByPort(node);
  // 计算本端端口到所有连接详情的映射
  const portConnectionsByPort = buildPortConnectionsForNode(node);

  // 转为普通 JSON，确保包含 data / ports 等字段
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;

  // 保存当前节点数据（附加端口到对端设备名的映射和连接详情）
  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
    portConnectionsByPort,
  };

  // 打开抽屉
  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 * @param {Object} params - 包含 nodeId, node, name, ports
 */
function handleNodeUpdate({ nodeId, name, ports }) {
  // 获取图实例
  const graph = dagRef.value?.getGraph();
  if (!graph) {
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

  // 如果需要更新到后端，可以在这里调用 API
  // await updateNodeName(nodeId, name)
  // await updateNodePorts(nodeId, ports)
}

/**
 * 构建设计保存用的拓扑数据 payload
 */
function buildTopologySavePayload() {
  const graph = getGraphInstance();
  if (!graph) {
    ElMessage.error('保存失败：图实例不存在');
    return null;
  }

  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    ElMessage.error('保存失败：缺少工程ID');
    return null;
  }

  const nodes = (graph.getNodes?.() || []).filter((node) => !isSimulationToken(node));
  const edges = graph.getEdges?.() || [];

  if (!nodes.length) {
    ElMessage.warning('请先在画布中放置设备节点');
    return null;
  }

  const graphJson = typeof graph.toJSON === 'function' ? graph.toJSON() : null;
  if (graphJson && Array.isArray(graphJson.cells)) {
    graphJson.cells = graphJson.cells.filter((cell) => !cell?.data?.isSimToken);
  }

  const nodeSummaries = nodes.map((node) => {
    const data = node.getData?.() || {};
    return {
      id: node.id,
      data,
    };
  });

  const edgeSummaries = edges.map((edge) => {
    const sourceId = edge.getSourceCellId?.();
    const targetId = edge.getTargetCellId?.();
    const sourcePortId = edge.getSourcePortId?.();
    const targetPortId = edge.getTargetPortId?.();
    return {
      id: edge.id,
      sourceId,
      targetId,
      sourcePortId,
      targetPortId,
    };
  });

  return {
    projectId: currentProjectId,
    versionId: getVersionIdNumber(),
    topologyData: {
      version: version.value,
      savedAt: new Date().toISOString(),
      graph: graphJson,
      nodes: nodeSummaries,
      edges: edgeSummaries,
    },
  };
}

/**
 * 保存工程拓扑
 */
function handleSaveTopo() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    ElMessage.error('保存失败：缺少工程ID');
    return;
  }

  const payload = buildTopologySavePayload();
  if (!payload) {
    return;
  }

  saveProjectTopology(payload)
    .then(() => {
      ElMessage.success('拓扑保存成功');
      router.push(`/project/project-detail/index/${currentProjectId}`);
    })
    .catch(() => {
      ElMessage.error('拓扑保存失败，请稍后重试');
    });
}

/**
 * 从后端加载并回显已保存的拓扑数据
 */
function restoreSavedTopology() {
  const currentProjectId = getProjectIdNumber();
  if (!currentProjectId) {
    return;
  }

  const currentVersionId = getVersionIdNumber();

  const tryRestore = () => {
    const graph = dagRef.value?.getGraph?.();
    if (!graph) {
      setTimeout(tryRestore, 200);
      return;
    }

    clearGraphContent(graph);

    getProjectTopology(currentProjectId, currentVersionId)
      .then((res) => {
        const topo = res?.data;
        const topoData = topo?.topologyData;
        const graphJson = topoData?.graph;
        if (graphJson) {
          graph.fromJSON(graphJson);
        }
      })
      .catch(() => {});
  };

  tryRestore();
}

watch(
  () => [projectId.value, versionId.value],
  () => {
    restoreSavedTopology();
  }
);

// 页面加载时获取设备列表并尝试回显拓扑
onMounted(() => {
  loadDeviceList();
  restoreSavedTopology();
});

// 清理：移除仿真相关的卸载逻辑（仿真功能已移除）
// 若未来需要添加其他卸载逻辑，可在此处补充
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

/* simulation-related styles removed from topo view */
</style>
