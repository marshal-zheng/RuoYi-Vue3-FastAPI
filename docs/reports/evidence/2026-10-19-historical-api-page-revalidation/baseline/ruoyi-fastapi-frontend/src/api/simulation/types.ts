/** Transport values carried by protocol payloads and user-defined injection parameters. */
export type ProtocolValue = string | number | boolean | null | ProtocolValue[] | ProtocolObject;
export interface ProtocolObject {
  [key: string]: ProtocolValue | undefined;
}

export interface SimulationSessionOptions {
  speed?: number;
  injectionStrategy?: string;
  injectionParams?: ProtocolObject;
}

export interface SimulationFillStrategy {
  value: string;
  label: string;
  description: string;
  icon: string;
  params: string[];
}

export interface SimulationSessionCommandAccepted<
  TAction extends 'start' | 'stop' = 'start' | 'stop',
> {
  sessionId: string;
  action: TAction;
  status: 'accepted';
}

export interface SimulationSessionParams extends SimulationSessionOptions {
  projectId: number | string;
  versionId?: number | string;
}

export interface SimulationSessionData {
  sessionId: string;
  status: string;
  message: string;
}

export interface SimulationStatusData {
  sessionId: string;
  status: 'idle' | 'created' | 'running' | 'paused' | 'stopped' | 'error' | 'not_found';
  startTime?: string;
  endTime?: string;
  messageCount: number;
  alarmCount: number;
  errorCount?: number;
  elapsedTime?: number;
  speed?: number;
}

export interface SimulationMessage {
  id?: string | number;
  messageId?: string;
  timestamp?: number;
  sourceNode?: string;
  targetNode?: string;
  messageType?: string;
  data?: ProtocolValue;
  size?: number;
  sendTimestamp?: number;
  receiveTimestamp?: number;
  sent_time?: number;
  received_time?: number;
  payloadHex?: string;
  fieldValues?: ProtocolObject;
  senderNodeId?: string;
  receiverNodeId?: string;
  senderNodeName?: string;
  receiverNodeName?: string;
  senderPortId?: string;
  receiverPortId?: string;
  sender?: string;
  receiver?: string;
  source?: string;
  target?: string;
  protocolType?: string;
  protocol?: string;
  fillStrategy?: string;
  sizeBytes?: number;
  isError?: boolean;
}

export interface SimulationBandwidth {
  timestamp: number;
  portId?: string;
  nodeId?: string;
  bandwidth?: number;
  bandwidthMbps?: number;
  bandwidth_mbps?: number;
  loadPercent?: number;
  load_percent?: number;
  utilization?: number;
  protocolType?: string;
  protocol_type?: string;
  protocol?: string;
  messageCount?: number;
}

export interface AlarmDetails {
  edgeId?: string;
  edge_id?: string;
  nodeId?: string;
  node_id?: string;
  portId?: string;
  port_id?: string;
  connections?: Array<{ edgeId?: string; edge_id?: string }>;
}

export interface SimulationAlarm {
  alarmId?: string;
  id?: string | number;
  timestamp: number;
  severity?: 'info' | 'warning' | 'error' | 'critical';
  level?: string;
  type?: string;
  alarmType?: string;
  message?: string;
  targetId?: string;
  targetEdgeId?: string;
  targetNodeId?: string;
  nodeId?: string;
  edgeId?: string;
  edgeIds?: string[];
  affectedNodes?: string[];
  affected_nodes?: string[];
  affectedNodeIds?: string[];
  details?: AlarmDetails;
  acknowledged?: boolean;
}

export interface SimulationStatistics {
  total_messages?: number;
  total_alarms?: number;
  total?: number;
  duration?: number;
  messages_by_protocol?: Record<string, number>;
  messageCount?: number;
  alarmCount?: number;
  elapsedTime?: number;
}

export interface FaultParameters extends ProtocolObject {
  targetName?: string | null;
  target_name?: string | null;
}

export interface FaultWire {
  faultId?: string | null;
  fault_id?: string | null;
  id?: string | null;
  sessionId?: string | null;
  session_id?: string | null;
  faultType?: string | null;
  fault_type?: string | null;
  type?: string | null;
  targetType?: string | null;
  target_type?: string | null;
  targetId?: string | null;
  target_id?: string | null;
  targetKey?: string | null;
  targetName?: string | null;
  target_name?: string | null;
  target_label?: string | null;
  targetAlias?: string | null;
  params?: FaultParameters;
  status?: string | null;
  startAt?: number | null;
  start_at?: number | null;
  endAt?: number | null;
  end_at?: number | null;
  priority?: number | null;
  createTime?: number | null;
  create_time?: number | null;
  updateTime?: number | null;
  update_time?: number | null;
  _action?: 'created' | 'updated';
}

export interface SimulationFaultEvent {
  action?: string;
  fault?: FaultWire;
  faultId?: string;
  timestamp?: number;
  faultType?: string;
  targetNode?: string;
  targetEdge?: string;
  parameters?: ProtocolObject;
}

export interface SimulationAnimation {
  type: 'traffic' | 'error' | 'node-active' | 'node-error';
  edgeId?: string;
  nodeId?: string;
  protocolType?: string;
  duration?: number;
}

export interface EventConditionValues {
  time?: number;
  count?: number;
  threshold?: number;
  portId?: string;
  pattern?: string;
  protocolType?: string;
}

export interface EventActionParams {
  sourceNodeId?: string;
  targetNodeId?: string;
  commandType?: string;
  payload?: string;
  protocolType?: string;
  faultType?: string;
  targetId?: string;
  message?: string;
  level?: string;
}

export interface SimulationEventCondition {
  type: string;
  value: EventConditionValues;
}

export interface SimulationEventAction {
  type: string;
  params: EventActionParams;
}

export interface SimulationEventConfig {
  name: string;
  condition: SimulationEventCondition;
  action: SimulationEventAction;
}

export interface SimulationEvent extends Partial<SimulationEventConfig> {
  eventId: string;
  name: string;
  status: 'pending' | 'triggered' | 'disabled';
  triggerCount?: number;
  createTime?: number;
  lastTriggerTime?: number;
}

export interface SimulationEventRequest {
  name?: string;
  conditionType?: string;
  conditionValue?: EventConditionValues;
  actionType?: string;
  actionParams?: EventActionParams;
  condition?: SimulationEventCondition;
  action?: SimulationEventAction;
  status?: SimulationEvent['status'];
}

export interface ExportDataParams {
  exportFormat: string;
  dataType: string;
}

export interface ExportDataResult {
  downloadUrl: string;
  fileName: string;
  fileSize: number;
}
