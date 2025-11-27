/**
 * 健康自检 Composable
 * 用于仿真前的配置完整性和有效性检查
 *
 * 检查项目：
 * 1. 拓扑完整性检查 - 节点数量、连接存在性
 * 2. 端口配置完整性检查 - 各协议类型必需参数
 * 3. 连接有效性检查 - 协议类型匹配、端口存在性
 * 4. 通信参数一致性检查 - 波特率匹配、IP地址有效性
 * 5. 配置冲突检测 - 回环、多连接
 */

/**
 * 检查结果状态
 * @typedef {'success' | 'warning' | 'error'} CheckStatus
 */

/**
 * 检查项结果
 * @typedef {Object} CheckItem
 * @property {string} id - 检查项ID
 * @property {string} category - 检查分类
 * @property {string} name - 检查项名称
 * @property {CheckStatus} status - 检查状态
 * @property {string} message - 检查结果消息
 * @property {string} [suggestion] - 修复建议
 * @property {Object} [details] - 详细信息
 */

/**
 * 健康检查报告
 * @typedef {Object} HealthReport
 * @property {boolean} healthy - 是否健康（无error）
 * @property {boolean} canSimulate - 是否可以执行仿真
 * @property {number} totalChecks - 总检查项数
 * @property {number} passedChecks - 通过检查项数
 * @property {number} warningChecks - 警告检查项数
 * @property {number} errorChecks - 错误检查项数
 * @property {CheckItem[]} items - 检查项列表
 * @property {string} timestamp - 检查时间戳
 */

// 协议类型必需参数配置
const PROTOCOL_REQUIRED_PARAMS = {
  RS422: ['baudRate', 'dataBits', 'stopBits', 'parity'],
  RS485: ['baudRate', 'dataBits', 'stopBits', 'parity'],
  CAN: ['baudRate'],
  LAN: ['ipAddress', 'port', 'protocol'],
  '1553B': ['busAddress', 'rtAddress', 'subAddress'],
};

// 协议类型显示名称
const PROTOCOL_NAMES = {
  RS422: 'RS-422',
  RS485: 'RS-485',
  CAN: 'CAN 总线',
  LAN: '以太网',
  '1553B': 'MIL-STD-1553B',
};

// 参数显示名称
const PARAM_NAMES = {
  baudRate: '波特率',
  dataBits: '数据位',
  stopBits: '停止位',
  parity: '校验方式',
  canMode: '工作模式',
  ipAddress: 'IP 地址',
  port: '端口号',
  protocol: '协议类型',
  busAddress: '总线地址',
  rtAddress: 'RT 地址',
  subAddress: '子地址',
};

export function useHealthCheck() {
  /**
   * 执行健康自检
   * @param {Object} graph - X6 图实例
   * @param {Function} isSimulationToken - 判断是否为仿真令牌的函数
   * @returns {HealthReport} 健康检查报告
   */
  function runHealthCheck(graph, isSimulationToken = () => false) {
    const items = [];
    const timestamp = new Date().toISOString();

    if (!graph) {
      return {
        healthy: false,
        canSimulate: false,
        totalChecks: 1,
        passedChecks: 0,
        warningChecks: 0,
        errorChecks: 1,
        items: [
          {
            id: 'graph-instance',
            category: '系统检查',
            name: '图实例检查',
            status: 'error',
            message: '图实例不存在，无法执行健康检查',
            suggestion: '请刷新页面后重试',
          },
        ],
        timestamp,
      };
    }

    // 获取节点和边
    const nodes = (graph.getNodes?.() || []).filter((node) => !isSimulationToken(node));
    const edges = graph.getEdges?.() || [];

    // 1. 拓扑完整性检查
    items.push(...checkTopologyIntegrity(nodes, edges));

    // 2. 端口配置完整性检查
    items.push(...checkPortConfiguration(nodes));

    // 3. 连接有效性检查
    items.push(...checkConnectionValidity(nodes, edges));

    // 4. 通信参数一致性检查
    items.push(...checkParameterConsistency(nodes, edges));

    // 5. 配置冲突检测
    items.push(...checkConfigurationConflicts(nodes, edges));

    // 计算统计信息
    const passedChecks = items.filter((item) => item.status === 'success').length;
    const warningChecks = items.filter((item) => item.status === 'warning').length;
    const errorChecks = items.filter((item) => item.status === 'error').length;

    // 判断是否可以仿真（无致命错误即可）
    const canSimulate = errorChecks === 0 && nodes.length >= 2 && edges.length > 0;

    return {
      healthy: errorChecks === 0 && warningChecks === 0,
      canSimulate,
      totalChecks: items.length,
      passedChecks,
      warningChecks,
      errorChecks,
      items,
      timestamp,
    };
  }

  /**
   * 1. 拓扑完整性检查
   */
  function checkTopologyIntegrity(nodes, edges) {
    const items = [];

    // 1.1 设备节点数量检查
    if (nodes.length === 0) {
      items.push({
        id: 'topology-nodes-empty',
        category: '拓扑完整性',
        name: '设备节点检查',
        status: 'error',
        message: '拓扑图中没有任何设备节点',
        suggestion: '请从设备库拖拽至少2个设备到画布上',
      });
    } else if (nodes.length === 1) {
      items.push({
        id: 'topology-nodes-single',
        category: '拓扑完整性',
        name: '设备节点检查',
        status: 'error',
        message: '仅有1个设备节点，无法进行通信仿真',
        suggestion: '通信仿真至少需要2个设备节点',
      });
    } else {
      items.push({
        id: 'topology-nodes-ok',
        category: '拓扑完整性',
        name: '设备节点检查',
        status: 'success',
        message: `共有 ${nodes.length} 个设备节点`,
      });
    }

    // 1.2 连接检查
    if (edges.length === 0) {
      items.push({
        id: 'topology-edges-empty',
        category: '拓扑完整性',
        name: '通信连接检查',
        status: 'error',
        message: '没有建立任何设备间的通信连接',
        suggestion: '请使用端口连线功能建立设备间的通信链路',
      });
    } else {
      items.push({
        id: 'topology-edges-ok',
        category: '拓扑完整性',
        name: '通信连接检查',
        status: 'success',
        message: `共建立 ${edges.length} 条通信链路`,
      });
    }

    // 1.3 检查孤立节点（有节点但没有任何连接）
    if (nodes.length > 1 && edges.length > 0) {
      const connectedNodeIds = new Set();
      edges.forEach((edge) => {
        const sourceId = edge.getSourceCellId?.();
        const targetId = edge.getTargetCellId?.();
        if (sourceId) connectedNodeIds.add(sourceId);
        if (targetId) connectedNodeIds.add(targetId);
      });

      const isolatedNodes = nodes.filter((node) => !connectedNodeIds.has(node.id));

      if (isolatedNodes.length > 0) {
        const nodeNames = isolatedNodes
          .map((node) => {
            const data = node.getData?.() || {};
            return data.name || data.label || node.id;
          })
          .join('、');

        items.push({
          id: 'topology-isolated-nodes',
          category: '拓扑完整性',
          name: '孤立节点检查',
          status: 'warning',
          message: `发现 ${isolatedNodes.length} 个孤立设备：${nodeNames}`,
          suggestion: '孤立设备不参与通信仿真，建议建立连接或移除',
          details: { isolatedNodes: isolatedNodes.map((n) => n.id) },
        });
      }
    }

    return items;
  }

  /**
   * 2. 端口配置完整性检查
   */
  function checkPortConfiguration(nodes) {
    const items = [];
    const portIssues = [];

    nodes.forEach((node) => {
      const data = node.getData?.() || {};
      const nodeName = data.name || data.label || node.id;
      const ports = data.ports || [];

      if (ports.length === 0) {
        portIssues.push({
          nodeId: node.id,
          nodeName,
          issue: 'no-ports',
          message: `设备 "${nodeName}" 没有配置任何端口`,
        });
        return;
      }

      ports.forEach((port) => {
        const portName = port.interfaceName || port.name || port.id;
        const interfaceType = (port.interfaceType || port.busType || '').toUpperCase();
        const params = port.params || {};

        // 检查协议类型
        if (!interfaceType) {
          portIssues.push({
            nodeId: node.id,
            nodeName,
            portId: port.id,
            portName,
            issue: 'no-protocol',
            message: `端口 "${portName}" 未配置协议类型`,
          });
          return;
        }

        // 检查必需参数
        const requiredParams = PROTOCOL_REQUIRED_PARAMS[interfaceType];
        if (requiredParams) {
          const missingParams = requiredParams.filter((param) => {
            const value = params[param];
            return value === undefined || value === null || value === '';
          });

          if (missingParams.length > 0) {
            const missingParamNames = missingParams.map((p) => PARAM_NAMES[p] || p).join('、');
            portIssues.push({
              nodeId: node.id,
              nodeName,
              portId: port.id,
              portName,
              interfaceType,
              issue: 'missing-params',
              message: `"${nodeName}" 的端口 "${portName}" 缺少参数：${missingParamNames}`,
              missingParams,
            });
          }
        }

        // LAN协议特殊检查：IP地址格式
        if (interfaceType === 'LAN' && params.ipAddress) {
          const ipPattern =
            /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
          if (!ipPattern.test(params.ipAddress)) {
            portIssues.push({
              nodeId: node.id,
              nodeName,
              portId: port.id,
              portName,
              issue: 'invalid-ip',
              message: `端口 "${portName}" 的IP地址格式无效：${params.ipAddress}`,
            });
          }
        }
      });
    });

    // 汇总端口配置检查结果
    if (portIssues.length === 0) {
      items.push({
        id: 'port-config-ok',
        category: '端口配置',
        name: '端口参数完整性',
        status: 'success',
        message: '所有端口配置参数完整',
      });
    } else {
      // 按严重程度分类
      const errorIssues = portIssues.filter(
        (i) => i.issue === 'no-ports' || i.issue === 'no-protocol'
      );
      const warningIssues = portIssues.filter(
        (i) => i.issue === 'missing-params' || i.issue === 'invalid-ip'
      );

      if (errorIssues.length > 0) {
        items.push({
          id: 'port-config-error',
          category: '端口配置',
          name: '端口基础配置',
          status: 'error',
          message: `${errorIssues.length} 个端口存在严重配置问题`,
          suggestion: '请为所有端口配置协议类型',
          details: { issues: errorIssues },
        });
      }

      if (warningIssues.length > 0) {
        items.push({
          id: 'port-config-warning',
          category: '端口配置',
          name: '端口参数配置',
          status: 'warning',
          message: `${warningIssues.length} 个端口参数配置不完整`,
          suggestion: '双击设备节点完善端口参数配置',
          details: { issues: warningIssues },
        });
      }
    }

    return items;
  }

  /**
   * 3. 连接有效性检查
   */
  function checkConnectionValidity(nodes, edges) {
    const items = [];
    const connectionIssues = [];

    // 构建节点端口映射
    const nodePortMap = new Map();
    nodes.forEach((node) => {
      const data = node.getData?.() || {};
      const ports = data.ports || [];
      nodePortMap.set(node.id, {
        name: data.name || data.label || node.id,
        ports: new Map(ports.map((p) => [p.id, p])),
      });
    });

    edges.forEach((edge) => {
      const sourceNodeId = edge.getSourceCellId?.();
      const targetNodeId = edge.getTargetCellId?.();
      const sourcePortId = edge.getSourcePortId?.();
      const targetPortId = edge.getTargetPortId?.();

      const sourceNode = nodePortMap.get(sourceNodeId);
      const targetNode = nodePortMap.get(targetNodeId);

      // 检查节点存在性
      if (!sourceNode || !targetNode) {
        connectionIssues.push({
          edgeId: edge.id,
          issue: 'invalid-node',
          message: '连接引用了不存在的设备节点',
        });
        return;
      }

      // 检查端口存在性
      const sourcePort = sourceNode.ports.get(sourcePortId);
      const targetPort = targetNode.ports.get(targetPortId);

      if (!sourcePort) {
        connectionIssues.push({
          edgeId: edge.id,
          issue: 'invalid-source-port',
          message: `设备 "${sourceNode.name}" 上不存在源端口`,
        });
      }

      if (!targetPort) {
        connectionIssues.push({
          edgeId: edge.id,
          issue: 'invalid-target-port',
          message: `设备 "${targetNode.name}" 上不存在目标端口`,
        });
      }

      // 检查协议类型匹配
      if (sourcePort && targetPort) {
        const sourceType = (sourcePort.interfaceType || sourcePort.busType || '').toUpperCase();
        const targetType = (targetPort.interfaceType || targetPort.busType || '').toUpperCase();

        if (sourceType && targetType && sourceType !== targetType) {
          const sourceTypeName = PROTOCOL_NAMES[sourceType] || sourceType;
          const targetTypeName = PROTOCOL_NAMES[targetType] || targetType;
          connectionIssues.push({
            edgeId: edge.id,
            issue: 'protocol-mismatch',
            message: `协议类型不匹配：${sourceNode.name}(${sourceTypeName}) ↔ ${targetNode.name}(${targetTypeName})`,
            sourceType,
            targetType,
          });
        }
      }
    });

    // 汇总连接有效性检查结果
    if (connectionIssues.length === 0 && edges.length > 0) {
      items.push({
        id: 'connection-validity-ok',
        category: '连接有效性',
        name: '连接配置检查',
        status: 'success',
        message: '所有通信连接配置有效',
      });
    } else if (connectionIssues.length > 0) {
      const protocolMismatch = connectionIssues.filter((i) => i.issue === 'protocol-mismatch');
      const invalidRefs = connectionIssues.filter((i) => i.issue !== 'protocol-mismatch');

      if (invalidRefs.length > 0) {
        items.push({
          id: 'connection-invalid-refs',
          category: '连接有效性',
          name: '连接引用检查',
          status: 'error',
          message: `${invalidRefs.length} 条连接引用无效`,
          suggestion: '请检查连接是否正确关联到设备端口',
          details: { issues: invalidRefs },
        });
      }

      if (protocolMismatch.length > 0) {
        items.push({
          id: 'connection-protocol-mismatch',
          category: '连接有效性',
          name: '协议类型匹配',
          status: 'warning',
          message: `${protocolMismatch.length} 条连接的协议类型不匹配`,
          suggestion: '建议连接相同协议类型的端口以确保通信兼容性',
          details: { issues: protocolMismatch },
        });
      }
    }

    return items;
  }

  /**
   * 4. 通信参数一致性检查
   */
  function checkParameterConsistency(nodes, edges) {
    const items = [];
    const parameterIssues = [];

    // 构建节点端口映射
    const nodePortMap = new Map();
    nodes.forEach((node) => {
      const data = node.getData?.() || {};
      const ports = data.ports || [];
      nodePortMap.set(node.id, {
        name: data.name || data.label || node.id,
        ports: new Map(ports.map((p) => [p.id, p])),
      });
    });

    edges.forEach((edge) => {
      const sourceNodeId = edge.getSourceCellId?.();
      const targetNodeId = edge.getTargetCellId?.();
      const sourcePortId = edge.getSourcePortId?.();
      const targetPortId = edge.getTargetPortId?.();

      const sourceNode = nodePortMap.get(sourceNodeId);
      const targetNode = nodePortMap.get(targetNodeId);

      if (!sourceNode || !targetNode) return;

      const sourcePort = sourceNode.ports.get(sourcePortId);
      const targetPort = targetNode.ports.get(targetPortId);

      if (!sourcePort || !targetPort) return;

      const sourceParams = sourcePort.params || {};
      const targetParams = targetPort.params || {};
      const sourceType = (sourcePort.interfaceType || sourcePort.busType || '').toUpperCase();
      const targetType = (targetPort.interfaceType || targetPort.busType || '').toUpperCase();

      // 只检查相同协议类型的参数一致性
      if (sourceType !== targetType) return;

      // RS422/RS485/CAN: 检查波特率一致性
      if (['RS422', 'RS485', 'CAN'].includes(sourceType)) {
        const sourceBaudRate = sourceParams.baudRate;
        const targetBaudRate = targetParams.baudRate;

        if (sourceBaudRate && targetBaudRate && sourceBaudRate !== targetBaudRate) {
          parameterIssues.push({
            edgeId: edge.id,
            issue: 'baudrate-mismatch',
            message: `波特率不一致：${sourceNode.name}(${sourceBaudRate}) ↔ ${targetNode.name}(${targetBaudRate})`,
            sourceValue: sourceBaudRate,
            targetValue: targetBaudRate,
          });
        }
      }

      // RS422/RS485: 检查数据位、停止位、校验方式一致性
      if (['RS422', 'RS485'].includes(sourceType)) {
        if (sourceParams.dataBits && targetParams.dataBits && sourceParams.dataBits !== targetParams.dataBits) {
          parameterIssues.push({
            edgeId: edge.id,
            issue: 'databits-mismatch',
            message: `数据位不一致：${sourceNode.name}(${sourceParams.dataBits}) ↔ ${targetNode.name}(${targetParams.dataBits})`,
          });
        }

        if (sourceParams.parity && targetParams.parity && sourceParams.parity !== targetParams.parity) {
          parameterIssues.push({
            edgeId: edge.id,
            issue: 'parity-mismatch',
            message: `校验方式不一致：${sourceNode.name}(${sourceParams.parity}) ↔ ${targetNode.name}(${targetParams.parity})`,
          });
        }
      }
    });

    // 汇总参数一致性检查结果
    if (parameterIssues.length === 0 && edges.length > 0) {
      items.push({
        id: 'param-consistency-ok',
        category: '参数一致性',
        name: '通信参数一致性',
        status: 'success',
        message: '所有连接的通信参数配置一致',
      });
    } else if (parameterIssues.length > 0) {
      items.push({
        id: 'param-consistency-warning',
        category: '参数一致性',
        name: '通信参数一致性',
        status: 'warning',
        message: `${parameterIssues.length} 条连接存在参数不一致`,
        suggestion: '通信双方参数不一致可能导致仿真结果不准确',
        details: { issues: parameterIssues },
      });
    }

    return items;
  }

  /**
   * 5. 配置冲突检测
   */
  function checkConfigurationConflicts(nodes, edges) {
    const items = [];

    // 5.1 回环检测（自连接）
    const loopbackEdges = edges.filter((edge) => {
      const sourceId = edge.getSourceCellId?.();
      const targetId = edge.getTargetCellId?.();
      return sourceId && targetId && sourceId === targetId;
    });

    if (loopbackEdges.length > 0) {
      items.push({
        id: 'conflict-loopback',
        category: '配置冲突',
        name: '回环连接检测',
        status: 'warning',
        message: `检测到 ${loopbackEdges.length} 个回环连接（设备自连接）`,
        suggestion: '回环连接通常用于自测试场景，请确认是否符合预期',
        details: { edgeIds: loopbackEdges.map((e) => e.id) },
      });
    } else {
      items.push({
        id: 'conflict-loopback-ok',
        category: '配置冲突',
        name: '回环连接检测',
        status: 'success',
        message: '未检测到回环连接',
      });
    }

    // 5.2 多连接检测（一个端口连接多个端口）
    const portConnections = new Map(); // {nodeId:portId: count}

    edges.forEach((edge) => {
      const sourceNodeId = edge.getSourceCellId?.();
      const targetNodeId = edge.getTargetCellId?.();
      const sourcePortId = edge.getSourcePortId?.();
      const targetPortId = edge.getTargetPortId?.();

      if (sourceNodeId && sourcePortId) {
        const key = `${sourceNodeId}:${sourcePortId}`;
        portConnections.set(key, (portConnections.get(key) || 0) + 1);
      }

      if (targetNodeId && targetPortId) {
        const key = `${targetNodeId}:${targetPortId}`;
        portConnections.set(key, (portConnections.get(key) || 0) + 1);
      }
    });

    const multiConnectedPorts = [];
    portConnections.forEach((count, key) => {
      if (count > 1) {
        multiConnectedPorts.push({ key, count });
      }
    });

    if (multiConnectedPorts.length > 0) {
      items.push({
        id: 'conflict-multi-connection',
        category: '配置冲突',
        name: '多连接检测',
        status: 'warning',
        message: `检测到 ${multiConnectedPorts.length} 个端口存在多连接`,
        suggestion: '单个端口连接多个目标可能导致信号冲突，请确认是否符合总线拓扑设计',
        details: { ports: multiConnectedPorts },
      });
    } else {
      items.push({
        id: 'conflict-multi-connection-ok',
        category: '配置冲突',
        name: '多连接检测',
        status: 'success',
        message: '未检测到端口多连接冲突',
      });
    }

    return items;
  }

  /**
   * 获取检查结果的汇总文本
   */
  function getSummaryText(report) {
    if (report.healthy) {
      return '✅ 健康检查通过，所有配置正常';
    } else if (report.canSimulate) {
      return `⚠️ 检查完成，有 ${report.warningChecks} 项警告，可以执行仿真`;
    } else {
      return `❌ 检查未通过，有 ${report.errorChecks} 项错误需要修复`;
    }
  }

  /**
   * 按分类分组检查项
   */
  function groupItemsByCategory(items) {
    const groups = {};
    items.forEach((item) => {
      if (!groups[item.category]) {
        groups[item.category] = [];
      }
      groups[item.category].push(item);
    });
    return groups;
  }

  return {
    runHealthCheck,
    getSummaryText,
    groupItemsByCategory,
    PROTOCOL_REQUIRED_PARAMS,
    PROTOCOL_NAMES,
    PARAM_NAMES,
  };
}


