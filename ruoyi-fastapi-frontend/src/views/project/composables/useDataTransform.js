/**
 * 数据转换处理 Composable
 * 负责设备数据、端口数据、拓扑数据的转换
 */
import { getPortColor } from '@/constants/portColor';

const BUS_TYPES = ['RS422', 'RS485', 'CAN', 'LAN', '1553B'];

export function useDataTransform() {
  /**
   * 解析端口方向，兼容中英文配置
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
   * 规范化总线类型
   */
  function normalizeBusType(type) {
    if (!type) return '';
    return String(type).toUpperCase();
  }

  /**
   * 推断连接总线类型
   */
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

  /**
   * 确保端口摘要
   */
  function ensurePortSummary(portId, ports, fallbackName, index, assignedBusType) {
    const port = Array.isArray(ports) ? ports.find((item) => item.id === portId) : null;
    if (port) {
      const declaredType =
        normalizeBusType(port.busType || port.interfaceType || port.protocolType) ||
        assignedBusType;
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

  /**
   * 转换设备接口数据为端口格式
   */
  function convertInterfacesToPorts(interfaces) {
    if (!interfaces || !Array.isArray(interfaces)) {
      return [];
    }

    return interfaces.map((intf, index) => {
      const busType = intf.interfaceType || intf.busType || 'RS422';
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
        interfaceType: busType,
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
   * 构建仿真 Payload
   */
  function buildSimulationPayload(graph, isSimulationToken) {
    if (!graph) {
      return { nodes: [], edges: [] };
    }

    const nodes = (graph.getNodes?.() || [])
      .filter((node) => !isSimulationToken(node))
      .map((node, index) => {
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

        const sourceNode = nodes.find((node) => node.id === sourceId);
        const targetNode = nodes.find((node) => node.id === targetId);

        if (!sourceNode || !targetNode) {
          return null;
        }

        const sourcePortRaw = sourceNode.ports?.find((item) => item.id === sourcePortId);
        const targetPortRaw = targetNode.ports?.find((item) => item.id === targetPortId);

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

  /**
   * 转换设备数据为操作符格式
   */
  function convertDevicesToOperators(devices) {
    if (!Array.isArray(devices) || devices.length === 0) {
      return [];
    }

    return devices.map((device) => {
      const interfaces = Array.isArray(device.interfaces) ? device.interfaces : [];
      const ports = convertInterfacesToPorts(interfaces);

      return {
        name: device.deviceName,
        value: device.remark || device.deviceDesc || '设备',
        category: device.categoryName || device.category || '未分类',
        deviceId: device.deviceId,
        deviceType: device.deviceType,
        busType: device.busType,
        manufacturer: device.manufacturer,
        model: device.model,
        version: device.version,
        ports,
        nodeType: 'device-port-node',
      };
    });
  }

  return {
    resolvePortDirection,
    normalizeBusType,
    inferConnectionBusType,
    ensurePortSummary,
    convertInterfacesToPorts,
    buildSimulationPayload,
    convertDevicesToOperators,
    BUS_TYPES,
  };
}
