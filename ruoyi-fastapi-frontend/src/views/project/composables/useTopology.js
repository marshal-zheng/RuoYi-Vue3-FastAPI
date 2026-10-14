/**
 * 拓扑管理 Composable
 * 负责拓扑的保存、加载、构建
 */

import { ElMessage } from 'element-plus';
import { saveProjectTopology, getProjectTopology } from '@/api/project/topology';

export function useTopology(version, getGraphInstance, clearGraphContent, isSimulationToken) {
  /**
   * 构建拓扑保存 Payload
   */
  function buildTopologySavePayload(projectId, versionId) {
    const graph = getGraphInstance();
    if (!graph) {
      ElMessage.error('保存失败：图实例不存在');
      return null;
    }

    if (!projectId) {
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
      projectId,
      versionId,
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
   * 保存拓扑
   */
  async function saveTopo(projectId, versionId) {
    if (!projectId) {
      ElMessage.error('保存失败：缺少工程ID');
      return false;
    }

    const payload = buildTopologySavePayload(projectId, versionId);
    if (!payload) {
      return false;
    }

    await saveProjectTopology(payload);
    return true;
  }

  /**
   * 恢复保存的拓扑
   */
  function restoreSavedTopology(projectId, versionId, dagRef) {
    if (!projectId) {
      return;
    }

    const tryRestore = () => {
      const graph = dagRef.value?.getGraph?.();
      if (!graph) {
        setTimeout(tryRestore, 200);
        return;
      }

      clearGraphContent(graph);

      getProjectTopology(projectId, versionId)
        .then((res) => {
          // http 客户端已解包 payload.data，res 直接是拓扑数据
          const topoData = res?.topologyData;
          const graphJson = topoData?.graph;
          if (graphJson) {
            graph.fromJSON(graphJson);
          }
        })
        .catch(() => {});
    };

    tryRestore();
  }

  /**
   * 构建端口到对端设备名的映射
   */
  function buildPeerDeviceNameByPort(node, graph) {
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

  return {
    buildTopologySavePayload,
    saveTopo,
    restoreSavedTopology,
    buildPeerDeviceNameByPort,
  };
}
