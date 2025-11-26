/**
 * 仿真文件生成 Composable
 * 负责生成设计文件、ICD文件、时间线等
 */

export function useSimulationFiles(version) {
  /**
   * 构建仿真摘要
   */
  function buildSimulationSummary(nodes, edges, BUS_TYPES) {
    const coverage = new Set();
    edges.forEach((edge) => {
      if (edge.busType) {
        coverage.add(edge.busType);
      }
    });
    return {
      deviceCount: nodes.length,
      connectionCount: edges.length,
      busCoverage: BUS_TYPES.map((type) => ({
        name: type,
        active: coverage.has(type),
      })),
      generatedAt: new Date().toLocaleString(),
    };
  }

  /**
   * 生成设计文件 Payload
   */
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

  /**
   * 生成 ICD 文件 Payload
   */
  function generateIcdFilePayload(projectName, versionName, nodes, edges) {
    const header = [
      '# === Interface Control Document ===',
      `# Project: ${projectName || '-'}`,
      `# Version: ${versionName || version.value}`,
      `# Generated: ${new Date().toISOString()}`,
      '',
      'DEVICE,PORT_ID,PORT_NAME,BUS_TYPE,PEER_DEVICE,PEER_PORT,PROTOCOL,DATA_RATE',
    ];

    const lines = edges.flatMap((edge) => {
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

  /**
   * 生成仿真时间线
   */
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

  return {
    buildSimulationSummary,
    generateDesignFilePayload,
    generateIcdFilePayload,
    generateSimulationTimeline,
  };
}
