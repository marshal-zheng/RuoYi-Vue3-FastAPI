<template>
  <ZxContentWrap class="home">
    <XflowDAG
      ref="dagRef"
      :operators="operators"
      :operators-loading="loading"
      :layout="layoutMode"
      :dnd-config="dndConfig"
      @node-dblclick="handleNodeDblclick"
    >
      <template #right>
        <el-button
          size="small"
          type="success"
          :loading="simulationLoading"
          :disabled="loading || simulationLoading"
          @click="handleRunSimulation"
        >
          执行仿真
        </el-button>
        <el-button size="small" type="primary" :disabled="loading" @click="handleSaveTopo">
          保存拓扑
        </el-button>
      </template>
    </XflowDAG>

    <!-- 节点编辑抽屉 -->
    <NodeEditDrawer ref="nodeEditDrawerRef" :node-data="currentNode" @submit="handleNodeUpdate" />

    <!-- 仿真结果对话框 -->
    <SimulationResultDialog ref="simulationDialogRef" />
  </ZxContentWrap>
</template>

<script setup name="Index">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import XflowDAG from '@/components/business/Dag/index.vue';
import { NodeEditDrawer } from './components';
import SimulationResultDialog from './components/SimulationResultDialog.vue';
import { listDevice } from '@/api/device/device';
import { saveProjectTopology, getProjectTopology } from '@/api/project/topology';
import { ElMessage } from 'element-plus';
import { getPortColor } from '@/constants/portColor';

const version = ref('3.9.0');
const simulationLoading = ref(false);
const simulationAnimationTimers = [];
const BUS_TYPES = ['RS422', 'RS485', 'CAN', 'LAN', '1553B'];

// 路由参数
const route = useRoute();
const router = useRouter();
const projectId = route.params.projectId;
const versionId = route.query.versionId;

// DAG 组件配置 - 设备列表（从后端获取）
const operators = ref([]);
const loading = ref(false);
const layoutMode = ref('horizontal'); // 'vertical' | 'horizontal'

// DAG 组件引用
const dagRef = ref(null);

// 节点编辑抽屉
const nodeEditDrawerRef = ref(null);
const currentNode = ref(null);
const simulationDialogRef = ref(null);

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

function normalizeBusType(type) {
  if (!type) return '';
  return String(type).toUpperCase();
}

function inferConnectionBusType(sourcePort, targetPort, index) {
  const candidate = normalizeBusType(
    sourcePort?.busType ||
      sourcePort?.interfaceType ||
      sourcePort?.protocolType ||
      targetPort?.busType ||
      targetPort?.interfaceType ||
      targetPort?.protocolType
  );
  if (candidate && BUS_TYPES.includes(candidate)) {
    return candidate;
  }
  return BUS_TYPES[index % BUS_TYPES.length];
}

function ensurePortSummary(portId, ports, fallbackName, index, assignedBusType) {
  const port = Array.isArray(ports) ? ports.find(item => item.id === portId) : null;
  if (port) {
    const declaredType =
      normalizeBusType(port.busType || port.interfaceType || port.protocolType) || assignedBusType;
    return {
      id: port.id || portId,
      name: port.interfaceName || port.interfaceLabel || `端口${index + 1}`,
      busType: declaredType || BUS_TYPES[index % BUS_TYPES.length],
    };
  }
  return {
    id: portId || `virtual-${index}`,
    name: fallbackName,
    busType: assignedBusType || BUS_TYPES[index % BUS_TYPES.length],
  };
}

function buildSimulationSummary(nodes, edges) {
  const coverage = new Set();
  edges.forEach(edge => {
    if (edge.busType) {
      coverage.add(edge.busType);
    }
  });
  return {
    deviceCount: nodes.length,
    connectionCount: edges.length,
    busCoverage: BUS_TYPES.map(type => ({
      name: type,
      active: coverage.has(type),
    })),
    generatedAt: new Date().toLocaleString(),
  };
}

function generateDesignFilePayload(projectName, versionName, nodes, edges) {
  const header = [
    '# === Bus Communication Design File ===',
    `# Project: ${projectName || '-'}`,
    `# Version: ${versionName || version.value}`,
    `# Generated: ${new Date().toISOString()}`,
    '',
    'BUS_ID,LINK_NAME,SOURCE_DEVICE,SOURCE_PORT,TARGET_DEVICE,TARGET_PORT,BUS_TYPE,DATA_RATE,REMARK',
  ];

  const lines = edges.map((edge, index) => {
    return [
      `BUS-${index + 1}`,
      `${edge.sourceDevice}-${edge.targetDevice}`,
      edge.sourceDevice,
      edge.sourcePort.name,
      edge.targetDevice,
      edge.targetPort.name,
      edge.busType,
      edge.dataRate,
      edge.remark,
    ].join(',');
  });

  return header.concat(lines).join('\n');
}

function generateIcdFilePayload(projectName, versionName, nodes, edges) {
  const header = [
    '# === Interface Control Document ===',
    `# Project: ${projectName || '-'}`,
    `# Version: ${versionName || version.value}`,
    `# Generated: ${new Date().toISOString()}`,
    '',
    'DEVICE,PORT_ID,PORT_NAME,BUS_TYPE,PEER_DEVICE,PEER_PORT,PROTOCOL,DATA_RATE',
  ];

  const lines = edges.flatMap(edge => {
    return [
      [
        edge.sourceDevice,
        edge.sourcePort.id,
        edge.sourcePort.name,
        edge.busType,
        edge.targetDevice,
        edge.targetPort.name,
        edge.protocolType,
        edge.dataRate,
      ].join(','),
      [
        edge.targetDevice,
        edge.targetPort.id,
        edge.targetPort.name,
        edge.busType,
        edge.sourceDevice,
        edge.sourcePort.name,
        edge.protocolType,
        edge.dataRate,
      ].join(','),
    ];
  });

  return header.concat(lines).join('\n');
}

function generateSimulationTimeline(edges) {
  return edges.map((edge, index) => {
    const delayMs = (index + 1) * 0.6;
    const color = ['primary', 'success', 'warning', 'danger', 'info'][index % 5];
    return {
      id: edge.id,
      title: `${edge.sourceDevice} → ${edge.targetDevice}`,
      description: `${edge.busType} 链路通过 ${edge.protocolType || '自定义协议'} 完成数据握手，速率 ${edge.dataRate}`,
      timestamp: `${delayMs.toFixed(1)} s`,
      busTypeTag: color,
    };
  });
}

function clearSimulationAnimationTimers() {
  while (simulationAnimationTimers.length) {
    const timer = simulationAnimationTimers.pop();
    clearTimeout(timer);
  }
}

function playSimulationAnimation(edgeIds) {
  const graph = dagRef.value?.getGraph?.();
  if (!graph || !edgeIds?.length) {
    return;
  }

  clearSimulationAnimationTimers();
  const highlightColor = '#67C23A';
  const nodeHighlightBorder = '#f59e0b';

  edgeIds.forEach((edgeId, index) => {
    const playTimer = setTimeout(() => {
      const edge = graph.getCellById(edgeId);
      if (!edge) {
        return;
      }

      const sourceNode = edge.getSourceNode?.();
      const targetNode = edge.getTargetNode?.();

      // 高亮边
      edge.attr('line/stroke', highlightColor);
      edge.attr('line/strokeWidth', 3);
      edge.attr('line/strokeDasharray', 6);

      // 高亮节点外框（依赖自定义节点 data.style 或 properties）
      if (sourceNode) {
        sourceNode.setData(
          {
            ...sourceNode.getData(),
            __simHighlight__: true,
            style: {
              ...(sourceNode.getData()?.style || {}),
              borderColor: nodeHighlightBorder,
            },
          },
          { overwrite: false }
        );
      }
      if (targetNode) {
        targetNode.setData(
          {
            ...targetNode.getData(),
            __simHighlight__: true,
            style: {
              ...(targetNode.getData()?.style || {}),
              borderColor: nodeHighlightBorder,
            },
          },
          { overwrite: false }
        );
      }

      const revertTimer = setTimeout(() => {
        edge.attr('line/stroke', '#C2C8D5');
        edge.attr('line/strokeWidth', 2);
        edge.attr('line/strokeDasharray', 0);

        // 还原节点样式
        if (sourceNode && sourceNode.getData?.().__simHighlight__) {
          const data = { ...sourceNode.getData() };
          delete data.__simHighlight__;
          if (data.style) {
            const style = { ...data.style };
            delete style.borderColor;
            data.style = style;
          }
          sourceNode.setData(data, { overwrite: true });
        }
        if (targetNode && targetNode.getData?.().__simHighlight__) {
          const data = { ...targetNode.getData() };
          delete data.__simHighlight__;
          if (data.style) {
            const style = { ...data.style };
            delete style.borderColor;
            data.style = style;
          }
          targetNode.setData(data, { overwrite: true });
        }
      }, 800);
      simulationAnimationTimers.push(revertTimer);
    }, index * 500);

    simulationAnimationTimers.push(playTimer);
  });
}

function buildSimulationPayload() {
  const graph = dagRef.value?.getGraph?.();
  if (!graph) {
    return { nodes: [], edges: [] };
  }

  const nodes = (graph.getNodes?.() || []).map((node, index) => {
    const data = node.getData?.() || {};
    return {
      id: node.id,
      name: data.name || data.label || `节点${index + 1}`,
      type: data.deviceType || data.nodeType || 'device',
      ports: data.ports || [],
    };
  });

  const edges = (graph.getEdges?.() || [])
    .map((edge, index) => {
      const sourceId = edge.getSourceCellId?.();
      const targetId = edge.getTargetCellId?.();
      const sourcePortId = edge.getSourcePortId?.();
      const targetPortId = edge.getTargetPortId?.();

      const sourceNode = nodes.find(node => node.id === sourceId);
      const targetNode = nodes.find(node => node.id === targetId);

      if (!sourceNode || !targetNode) {
        return null;
      }

      const sourcePortRaw = sourceNode.ports?.find(item => item.id === sourcePortId);
      const targetPortRaw = targetNode.ports?.find(item => item.id === targetPortId);

      const assignedBusType = inferConnectionBusType(sourcePortRaw, targetPortRaw, index);

      const sourcePort = ensurePortSummary(
        sourcePortId,
        sourceNode.ports,
        `端口${index + 1}`,
        index,
        assignedBusType
      );
      const targetPort = ensurePortSummary(
        targetPortId,
        targetNode.ports,
        `端口${index + 1}`,
        index,
        assignedBusType
      );

      return {
        id: edge.id,
        sourceId,
        targetId,
        sourceDevice: sourceNode.name,
        targetDevice: targetNode.name,
        sourcePort,
        targetPort,
        busType: assignedBusType,
        protocolType: sourcePortRaw?.protocolType || targetPortRaw?.protocolType || '自定义协议',
        dataRate: sourcePortRaw?.dataRate || targetPortRaw?.dataRate || '32Mbps',
        remark: '仿真示例链路',
      };
    })
    .filter(Boolean);

  return { nodes, edges };
}

function handleRunSimulation() {
  if (simulationLoading.value) {
    return;
  }

  const graph = dagRef.value?.getGraph?.();
  if (!graph) {
    ElMessage.error('仿真失败：图实例不存在');
    return;
  }

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (nodes.length < 2) {
    ElMessage.warning('请至少放置两个设备节点后再生成仿真');
    return;
  }

  if (!edges.length) {
    ElMessage.warning('请先建立设备之间的接口连线');
    return;
  }

  simulationLoading.value = true;

  setTimeout(() => {
    const { nodes: nodePayload, edges: edgePayload } = buildSimulationPayload();

    if (!edgePayload.length) {
      ElMessage.warning('暂未检测到有效连线');
      simulationLoading.value = false;
      return;
    }

    const summary = buildSimulationSummary(nodePayload, edgePayload);
    const designContent = generateDesignFilePayload(
      '多总线仿真工程',
      version.value,
      nodePayload,
      edgePayload
    );
    const icdContent = generateIcdFilePayload(
      '多总线仿真工程',
      version.value,
      nodePayload,
      edgePayload
    );
    const timeline = generateSimulationTimeline(edgePayload);

    simulationDialogRef.value?.open({
      summary,
      timeline,
      designFile: {
        name: 'bus_design.csv',
        content: designContent,
      },
      icdFile: {
        name: 'interface_control.csv',
        content: icdContent,
      },
    });

    simulationLoading.value = false;
    playSimulationAnimation(edgePayload.map(edge => edge.id));
  }, 500);
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
  } catch (error) {
    ElMessage.error('加载设备列表失败，请稍后重试');
    operators.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 根据当前节点构建端口到对端设备名的映射
 * @param {Object} node - 当前节点（X6 节点实例或其 JSON）
 * @returns {Record<string, string>} key 为端口 ID，value 为对端设备名称
 */
function buildPeerDeviceNameByPort(node) {
  const graph = dagRef.value?.getGraph();
  if (!graph || !node) return {};

  const nodeId = node.id;
  const result = {};
  const edges = graph.getEdges?.() || [];

  edges.forEach(edge => {
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

    if (deviceName) {
      result[localPortId] = deviceName;
    }
  });

  return result;
}

/**
 * 处理节点双击事件
 * @param {Object} params - 包含 node, event, type
 */
function handleNodeDblclick({ node, event, type }) {
  // 计算当前节点各端口对应的对端设备名称
  const peerDeviceNameByPort = buildPeerDeviceNameByPort(node);

  // 转为普通 JSON，确保包含 data / ports 等字段
  const jsonNode = typeof node?.toJSON === 'function' ? node.toJSON() : node;

  // 保存当前节点数据（附加端口到对端设备名的映射）
  currentNode.value = {
    ...jsonNode,
    peerDeviceNameByPort,
  };

  // 打开抽屉
  nodeEditDrawerRef.value?.open();
}

/**
 * 处理节点更新
 * @param {Object} params - 包含 nodeId, node, name, ports
 */
function handleNodeUpdate({ nodeId, node, name, ports }) {
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
  const graph = dagRef.value?.getGraph?.();
  if (!graph) {
    ElMessage.error('保存失败：图实例不存在');
    return null;
  }

  const nodes = graph.getNodes?.() || [];
  const edges = graph.getEdges?.() || [];

  if (!nodes.length) {
    ElMessage.warning('请先在画布中放置设备节点');
    return null;
  }

  const graphJson = typeof graph.toJSON === 'function' ? graph.toJSON() : null;

  const nodeSummaries = nodes.map(node => {
    const data = node.getData?.() || {};
    return {
      id: node.id,
      data,
    };
  });

  const edgeSummaries = edges.map(edge => {
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
    projectId: Number(projectId),
    versionId: versionId ? Number(versionId) : undefined,
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
  if (!projectId) {
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
      router.push(`/project/project-detail/index/${projectId}`);
    })
    .catch(() => {
      ElMessage.error('拓扑保存失败，请稍后重试');
    });
}

/**
 * 从后端加载并回显已保存的拓扑数据
 */
function restoreSavedTopology() {
  if (!projectId) {
    return;
  }

  const tryRestore = () => {
    const graph = dagRef.value?.getGraph?.();
    if (!graph) {
      setTimeout(tryRestore, 200);
      return;
    }

    getProjectTopology(projectId, versionId ? Number(versionId) : undefined)
      .then(res => {
        const topo = res?.data;
        const topoData = topo?.topologyData;
        const graphJson = topoData?.graph;
        if (!graphJson) {
          return;
        }
        graph.fromJSON(graphJson);
      })
      .catch(() => {});
  };

  tryRestore();
}

// 页面加载时获取设备列表并尝试回显拓扑
onMounted(() => {
  loadDeviceList();
  restoreSavedTopology();
});

onUnmounted(() => {
  clearSimulationAnimationTimers();
});
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

.simulation-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.simulation-summary {
  margin-bottom: 16px;
}

.simulation-tabs {
  .el-tab-pane {
    min-height: 240px;
  }
}

.simulation-file__header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.simulation-file__viewer {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  max-height: 280px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.simulation-timeline__title {
  font-weight: 600;
  margin-bottom: 4px;
}

.simulation-timeline__desc {
  color: #606266;
  margin: 0;
  font-size: 12px;
}
</style>
