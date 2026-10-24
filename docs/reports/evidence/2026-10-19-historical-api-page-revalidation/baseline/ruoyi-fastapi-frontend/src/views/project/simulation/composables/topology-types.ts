import type { Graph, Node, Edge, Cell, Registry } from '@antv/x6';
import type { ProtocolObject } from '@/api/simulation/types';

export type SimulationGraph = Graph;
export type HealthCheckGraph = Pick<Graph, 'getNodes' | 'getEdges'>;
export type SimulationNode = Node;
export type SimulationEdge = Edge;
export type SimulationCell = Cell;

export interface SimulationPort {
  id?: string;
  interfaceName?: string;
  name?: string;
  interfaceType?: string;
  busType?: string;
  params?: ProtocolObject;
  messageConfig?: { header?: ProtocolObject };
}

export interface SimulationNodeData {
  name?: string;
  label?: string;
  deviceName?: string;
  portName?: string;
  ports?: SimulationPort[];
  _originalStyles?: Record<
    string,
    { stroke: Registry.Attr.ComplexAttrValue; strokeWidth: Registry.Attr.ComplexAttrValue }
  >;
}

export interface SimulationEdgeData {
  id?: string;
  edgeId?: string;
  alias?: string;
  label?: string;
  name?: string;
  title?: string;
  sourcePortName?: string;
  sourcePort?: string;
  targetPortName?: string;
  targetPort?: string;
}
