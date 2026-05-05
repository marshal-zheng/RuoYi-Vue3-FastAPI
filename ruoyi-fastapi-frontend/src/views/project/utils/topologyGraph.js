import {
  DAG_EDGE,
  DAG_NODE,
} from "@/components/business/Dag/shapes/registerDagShapes";
import { generateNodePorts } from "@/components/business/Dag/config/portConfig";

function resolveEdgeEndpoint(endpoint, fallbackKeys = []) {
  if (typeof endpoint === "string" || typeof endpoint === "number") {
    return String(endpoint);
  }
  if (endpoint && typeof endpoint === "object") {
    return String(
      endpoint.cell || endpoint.id || endpoint.nodeId || endpoint.node_id || "",
    );
  }
  for (const keyValue of fallbackKeys) {
    if (keyValue !== undefined && keyValue !== null && keyValue !== "") {
      return String(keyValue);
    }
  }
  return "";
}

function normalizeSimpleTopologyGraph(graphData) {
  const nodes = Array.isArray(graphData?.nodes) ? graphData.nodes : [];
  const edges = Array.isArray(graphData?.edges) ? graphData.edges : [];

  const nodeCells = nodes.map((node, index) => {
    const label =
      node.label ||
      node.name ||
      node.deviceName ||
      node.id ||
      `节点${index + 1}`;
    const type = node.type || node.nodeType || "device";

    return {
      id: String(node.id || `node-${index + 1}`),
      shape: DAG_NODE,
      x: Number(node.x) || 120 + (index % 3) * 260,
      y: Number(node.y) || 120 + Math.floor(index / 3) * 160,
      width: 180,
      height: 80,
      data: {
        ...node,
        type,
        label,
        name: label,
        status: "default",
        layoutDirection: "horizontal",
        properties: {
          ...(node.properties || {}),
          content: {
            ...(node.properties?.content || {}),
            label,
          },
        },
        originalData: node,
      },
      ports: generateNodePorts(type),
      draggable: true,
      locked: false,
    };
  });

  const edgeCells = edges
    .map((edge, index) => {
      const sourceCell = resolveEdgeEndpoint(edge.source, [
        edge.sourceNodeId,
        edge.sourceId,
      ]);
      const targetCell = resolveEdgeEndpoint(edge.target, [
        edge.targetNodeId,
        edge.targetId,
      ]);
      if (!sourceCell || !targetCell) {
        return null;
      }

      return {
        id: String(edge.id || `edge-${sourceCell}-${targetCell}-${index + 1}`),
        shape: DAG_EDGE,
        source: { cell: sourceCell, port: edge.sourcePortId || "b" },
        target: { cell: targetCell, port: edge.targetPortId || "t" },
        animated: false,
      };
    })
    .filter(Boolean);

  return { cells: [...nodeCells, ...edgeCells] };
}

export function resolveTopologyGraphJson(topologyData) {
  const graphData = topologyData?.graph || topologyData;

  if (!graphData || typeof graphData !== "object") {
    return null;
  }

  if (Array.isArray(graphData.cells)) {
    return graphData;
  }

  if (Array.isArray(graphData.nodes)) {
    return normalizeSimpleTopologyGraph(graphData);
  }

  return null;
}
