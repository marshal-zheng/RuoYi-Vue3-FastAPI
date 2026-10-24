import { isRecord } from '@/types/http-contract';
import type {
  ProtocolValue,
  ProtocolObject,
  SimulationStatusData,
  SimulationMessage,
  SimulationBandwidth,
  SimulationAlarm,
  SimulationAnimation,
  SimulationFaultEvent,
  FaultWire,
  AlarmDetails,
} from '@/api/simulation/types';

export type WebSocketMessage =
  | { type: 'status'; data: SimulationStatusData }
  | { type: 'messages'; data: SimulationMessage[] }
  | { type: 'bandwidth'; data: SimulationBandwidth[] }
  | { type: 'alarms'; data: SimulationAlarm[] }
  | { type: 'animation'; data: SimulationAnimation[] }
  | { type: 'faults'; data: SimulationFaultEvent[] }
  | { type: 'pong' };

export type WebSocketMessageType = WebSocketMessage['type'];

const optionalFields = (
  value: Record<string, unknown>,
  names: readonly string[],
  kind: 'string' | 'number' | 'boolean'
): boolean => names.every((name) => value[name] === undefined || typeof value[name] === kind);

const optionalStrings = (value: Record<string, unknown>, names: readonly string[]) =>
  optionalFields(value, names, 'string');
const optionalNumbers = (value: Record<string, unknown>, names: readonly string[]) =>
  optionalFields(value, names, 'number');

const nullableFields = (value: Record<string, unknown>, names: readonly string[]) =>
  names.every(
    (name) => value[name] === undefined || value[name] === null || typeof value[name] === 'string'
  );
const nullableNumbers = (value: Record<string, unknown>, names: readonly string[]) =>
  names.every(
    (name) => value[name] === undefined || value[name] === null || typeof value[name] === 'number'
  );

function isProtocolValue(value: unknown): value is ProtocolValue {
  return (
    value === null ||
    ['string', 'number', 'boolean'].includes(typeof value) ||
    (Array.isArray(value) && value.every(isProtocolValue)) ||
    isProtocolObject(value)
  );
}

function isProtocolObject(value: unknown): value is ProtocolObject {
  return (
    isRecord(value) &&
    Object.values(value).every((item) => item === undefined || isProtocolValue(item))
  );
}

function isStatus(value: unknown): value is SimulationStatusData {
  return (
    isRecord(value) &&
    typeof value.sessionId === 'string' &&
    ['idle', 'created', 'running', 'paused', 'stopped', 'error', 'not_found'].includes(
      String(value.status)
    ) &&
    typeof value.messageCount === 'number' &&
    typeof value.alarmCount === 'number' &&
    optionalNumbers(value, ['errorCount', 'elapsedTime', 'speed']) &&
    optionalStrings(value, ['startTime', 'endTime'])
  );
}

function isMessage(value: unknown): value is SimulationMessage {
  return (
    isRecord(value) &&
    optionalNumbers(value, ['timestamp']) &&
    (value.id === undefined || typeof value.id === 'number' || typeof value.id === 'string') &&
    optionalStrings(value, [
      'messageId',
      'sourceNode',
      'targetNode',
      'messageType',
      'payloadHex',
      'senderNodeId',
      'receiverNodeId',
      'senderNodeName',
      'receiverNodeName',
      'senderPortId',
      'receiverPortId',
      'sender',
      'receiver',
      'source',
      'target',
      'protocolType',
      'protocol',
      'fillStrategy',
    ]) &&
    optionalNumbers(value, [
      'size',
      'sizeBytes',
      'sendTimestamp',
      'receiveTimestamp',
      'sent_time',
      'received_time',
    ]) &&
    optionalFields(value, ['isError'], 'boolean') &&
    (value.data === undefined || isProtocolValue(value.data)) &&
    (value.fieldValues === undefined || isProtocolObject(value.fieldValues))
  );
}

function isBandwidth(value: unknown): value is SimulationBandwidth {
  return (
    isRecord(value) &&
    typeof value.timestamp === 'number' &&
    optionalStrings(value, ['portId', 'nodeId', 'protocolType', 'protocol_type', 'protocol']) &&
    optionalNumbers(value, [
      'bandwidth',
      'bandwidthMbps',
      'bandwidth_mbps',
      'loadPercent',
      'load_percent',
      'utilization',
      'messageCount',
    ])
  );
}

function isAlarmDetails(value: unknown): value is AlarmDetails {
  return (
    isRecord(value) &&
    optionalStrings(value, ['edgeId', 'edge_id', 'nodeId', 'node_id', 'portId', 'port_id']) &&
    (value.connections === undefined ||
      (Array.isArray(value.connections) &&
        value.connections.every(
          (connection: unknown) =>
            isRecord(connection) && optionalStrings(connection, ['edgeId', 'edge_id'])
        )))
  );
}

function isAlarm(value: unknown): value is SimulationAlarm {
  return (
    isRecord(value) &&
    typeof value.timestamp === 'number' &&
    (value.id === undefined || typeof value.id === 'number' || typeof value.id === 'string') &&
    (value.severity === undefined ||
      ['info', 'warning', 'error', 'critical'].includes(String(value.severity))) &&
    optionalStrings(value, [
      'alarmId',
      'level',
      'type',
      'alarmType',
      'message',
      'targetId',
      'targetEdgeId',
      'targetNodeId',
      'nodeId',
      'edgeId',
    ]) &&
    ['edgeIds', 'affectedNodes', 'affected_nodes', 'affectedNodeIds'].every((name) => {
      const ids = value[name];
      return (
        ids === undefined ||
        (Array.isArray(ids) && ids.every((id: unknown) => typeof id === 'string'))
      );
    }) &&
    optionalFields(value, ['acknowledged'], 'boolean') &&
    (value.details === undefined || isAlarmDetails(value.details))
  );
}

function isAnimation(value: unknown): value is SimulationAnimation {
  return (
    isRecord(value) &&
    ['traffic', 'error', 'node-active', 'node-error'].includes(String(value.type)) &&
    optionalStrings(value, ['edgeId', 'nodeId', 'protocolType']) &&
    optionalNumbers(value, ['duration'])
  );
}

function isFault(value: unknown): value is FaultWire {
  return (
    isRecord(value) &&
    nullableFields(value, [
      'faultId',
      'fault_id',
      'id',
      'sessionId',
      'session_id',
      'faultType',
      'fault_type',
      'type',
      'targetType',
      'target_type',
      'targetId',
      'target_id',
      'targetKey',
      'targetName',
      'target_name',
      'target_label',
      'targetAlias',
      'status',
    ]) &&
    nullableNumbers(value, [
      'startAt',
      'start_at',
      'endAt',
      'end_at',
      'priority',
      'createTime',
      'create_time',
      'updateTime',
      'update_time',
    ]) &&
    (value._action === undefined || value._action === 'created' || value._action === 'updated') &&
    (value.params === undefined ||
      (isProtocolObject(value.params) &&
        nullableFields(value.params, ['targetName', 'target_name'])))
  );
}

function isFaultEvent(value: unknown): value is SimulationFaultEvent {
  return (
    isRecord(value) &&
    optionalStrings(value, ['action', 'faultId', 'faultType', 'targetNode', 'targetEdge']) &&
    optionalNumbers(value, ['timestamp']) &&
    (value.fault === undefined || isFault(value.fault)) &&
    (value.parameters === undefined || isProtocolObject(value.parameters))
  );
}

/** Decode the documented frame variants before exposing data to reactive consumers. */
export function decodeWebSocketMessage(value: unknown): WebSocketMessage | null {
  if (!isRecord(value)) return null;
  const data = value.data;
  switch (value.type) {
    case 'pong':
      return { type: 'pong' };
    case 'status':
      return isStatus(data) ? { type: 'status', data } : null;
    case 'messages':
      return Array.isArray(data) && data.every(isMessage) ? { type: 'messages', data } : null;
    case 'bandwidth':
      return Array.isArray(data) && data.every(isBandwidth) ? { type: 'bandwidth', data } : null;
    case 'alarms':
      return Array.isArray(data) && data.every(isAlarm) ? { type: 'alarms', data } : null;
    case 'animation':
      return Array.isArray(data) && data.every(isAnimation) ? { type: 'animation', data } : null;
    case 'faults':
      return Array.isArray(data) && data.every(isFaultEvent) ? { type: 'faults', data } : null;
    default:
      return null;
  }
}
