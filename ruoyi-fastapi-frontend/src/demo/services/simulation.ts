import {
  ProjectRepository,
  ProjectVersionRepository,
  SimulationRepository,
} from '@/demo/repositories';
import type {
  DemoRecord,
  DemoSimulationAlarm,
  DemoSimulationBandwidth,
  DemoSimulationEvent,
  DemoSimulationFault,
  DemoSimulationFrame,
  DemoSimulationMessage,
  DemoSimulationSession,
} from '@/demo/scenarios';

import { DemoAuthError } from './auth';

type DemoSimulationStatusValue = 'idle' | 'running' | 'paused' | 'stopped' | 'error';
type DemoRealtimeFrameType =
  | 'status'
  | 'messages'
  | 'bandwidth'
  | 'alarms'
  | 'animation'
  | 'faults'
  | 'pong';

export interface DemoSimulationSessionPayload {
  projectId?: number | string | null;
  versionId?: number | string | null;
}

export interface DemoSimulationExportPayload {
  exportFormat?: string;
  dataType?: string;
}

export interface DemoSimulationSessionDetail {
  sessionId: string;
  projectId: number;
  versionId: number;
  status: DemoSimulationStatusValue;
  createdAt: string;
  createTime: string;
  updateTime: string;
  speed: number;
  readonly: true;
}

export interface DemoSimulationStatus {
  sessionId: string;
  status: DemoSimulationStatusValue;
  startTime: string;
  endTime?: string;
  createdAt: string;
  speed: number;
  elapsedTime: number;
  messageCount: number;
  alarmCount: number;
  errorCount: number;
}

export interface DemoSimulationMessageDetail {
  id: string;
  timestamp: number;
  sendTimestamp: number;
  receiveTimestamp: number;
  senderNodeId: string;
  receiverNodeId: string;
  senderNodeName: string;
  receiverNodeName: string;
  senderPortId: string;
  receiverPortId: string;
  protocolType: string;
  messageType: string;
  payloadHex: string;
  sizeBytes: number;
  fillStrategy: string;
  data: DemoRecord;
}

export interface DemoSimulationBandwidthDetail {
  timestamp: number;
  nodeId: string;
  portId: string;
  protocolType: string;
  bandwidth: number;
  utilization: number;
  bandwidthMbps: number;
  bandwidth_mbps: number;
  loadPercent: number;
  load_percent: number;
  messageCount: number;
}

export interface DemoSimulationAlarmDetail {
  alarmId: string;
  timestamp: number;
  severity: 'info' | 'warning' | 'error' | 'critical';
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  alarmType: string;
  type: string;
  targetId?: string;
  targetNodeId?: string;
  targetEdgeId?: string;
  edgeId?: string;
  nodeId?: string;
  affectedNodes?: string[];
  details: DemoRecord;
}

export interface DemoSimulationFaultDetail {
  faultId: string;
  sessionId: string;
  faultType: string;
  targetType: string;
  targetId: string;
  targetKey: string;
  targetName?: string;
  params: DemoRecord;
  status: string;
  startAt?: number;
  endAt?: number;
  priority: number;
  createTime: number;
  updateTime: number;
}

export interface DemoSimulationEventDetail {
  eventId: string;
  name: string;
  condition: {
    type: string;
    value: DemoRecord;
  };
  action: {
    type: string;
    params: DemoRecord;
  };
  status: 'pending' | 'triggered' | 'disabled';
  triggerCount: number;
  createTime: number;
  lastTriggerTime?: number;
}

export interface DemoSimulationExportResult {
  downloadUrl: string;
  fileName: string;
  fileSize: number;
  content: string;
}

export interface DemoRealtimeFrame {
  frameId: string;
  sessionId: string;
  order: number;
  type: DemoRealtimeFrameType;
  delayMs: number;
  payload: unknown;
}

export class DemoSimulationError extends DemoAuthError {
  constructor(message: string, status = 400, code = status) {
    super(message, status, code);
    this.name = 'DemoSimulationError';
  }
}

function hasText(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function normalizeText(value: unknown, fallback = ''): string {
  return hasText(value) ? value.trim() : fallback;
}

function resolveOptionalNumber(value: number | string | null | undefined): number | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new DemoSimulationError('请求参数格式错误', 400);
  }

  return Math.floor(parsed);
}

function ensureNumber(value: number | string | null | undefined, fieldLabel: string): number {
  const parsed = resolveOptionalNumber(value);
  if (!parsed) {
    throw new DemoSimulationError(`${fieldLabel}不能为空`, 400);
  }
  return parsed;
}

function secondsFromDate(value: unknown): number {
  if (typeof value === 'number') {
    return value > 1e12 ? value / 1000 : value;
  }

  if (value instanceof Date) {
    return value.getTime() / 1000;
  }

  const parsed = Date.parse(String(value ?? ''));
  if (!Number.isNaN(parsed)) {
    return parsed / 1000;
  }

  return Math.floor(Date.now() / 1000);
}

function isoFromValue(value: unknown, fallback = new Date().toISOString()): string {
  if (typeof value === 'string' && value.trim()) {
    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return new Date(parsed).toISOString();
    }
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    return new Date(value > 1e12 ? value : value * 1000).toISOString();
  }

  return fallback;
}

function randomSessionId(projectId: number, versionId: number): string {
  const suffix =
    typeof globalThis.crypto?.randomUUID === 'function'
      ? globalThis.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  return `demo-session-${projectId}-${versionId}-${suffix}`;
}

function normalizeStatus(value: unknown): DemoSimulationStatusValue {
  const normalized = normalizeText(value, 'running').toLowerCase();
  if (normalized === 'running' || normalized === 'paused' || normalized === 'stopped') {
    return normalized;
  }
  if (normalized === 'error') {
    return 'error';
  }
  return 'idle';
}

function toHexString(value: unknown): string {
  const text = normalizeText(value);
  if (!text) {
    return '';
  }

  return Array.from(text)
    .map((char) => char.charCodeAt(0).toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase();
}

function clampPercent(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

function stableSortByTimestamp<T extends { timestamp: number }>(left: T, right: T): number {
  return left.timestamp - right.timestamp;
}

function severityValue(value: unknown): 'info' | 'warning' | 'error' | 'critical' {
  const normalized = normalizeText(value, 'info').toLowerCase();
  if (normalized === 'warning' || normalized === 'error' || normalized === 'critical') {
    return normalized;
  }
  return 'info';
}

function normalizeSimulationSession(session: DemoSimulationSession): DemoSimulationSessionDetail {
  const createTime = isoFromValue(session.createTime);
  return {
    sessionId: normalizeText(session.sessionId),
    projectId: Number(session.projectId),
    versionId: Number(session.versionId),
    status: normalizeStatus(session.status),
    createdAt: createTime,
    createTime,
    updateTime: isoFromValue(session.updateTime, createTime),
    speed: Number((session as DemoRecord).speed ?? 1) || 1,
    readonly: true,
  };
}

function normalizeSimulationMessage(message: DemoSimulationMessage): DemoSimulationMessageDetail {
  const record = message as DemoSimulationMessage & DemoRecord;
  const timestamp = secondsFromDate(record.timestamp);
  const senderNodeName = normalizeText(
    record.senderNodeName ?? record.source ?? record.sourceNode,
    '源节点'
  );
  const receiverNodeName = normalizeText(
    record.receiverNodeName ?? record.target ?? record.targetNode,
    '目标节点'
  );
  const protocolType = normalizeText(record.protocolType ?? record.protocol, 'LAN');
  const payloadHex = normalizeText(
    record.payloadHex,
    toHexString(record.content ?? record.message)
  );
  const sizeBytes = Number(record.sizeBytes ?? record.size ?? payloadHex.length / 2) || 0;

  return {
    id: normalizeText(record.id ?? record.messageId, `message-${timestamp}`),
    timestamp,
    sendTimestamp: Number(record.sendTimestamp ?? timestamp),
    receiveTimestamp: Number(record.receiveTimestamp ?? timestamp + 0.02),
    senderNodeId: normalizeText(record.senderNodeId ?? record.sourceNodeId ?? senderNodeName),
    receiverNodeId: normalizeText(record.receiverNodeId ?? record.targetNodeId ?? receiverNodeName),
    senderNodeName,
    receiverNodeName,
    senderPortId: normalizeText(record.senderPortId ?? record.sourcePortId),
    receiverPortId: normalizeText(record.receiverPortId ?? record.targetPortId),
    protocolType,
    messageType: normalizeText(record.messageType, 'telemetry'),
    payloadHex,
    sizeBytes,
    fillStrategy: normalizeText(record.fillStrategy, 'preset'),
    data:
      typeof record.data === 'object' && record.data
        ? (record.data as DemoRecord)
        : {
            content: record.content ?? '',
          },
  };
}

function normalizeSimulationBandwidth(
  bandwidth: DemoSimulationBandwidth
): DemoSimulationBandwidthDetail {
  const record = bandwidth as DemoSimulationBandwidth & DemoRecord;
  const timestamp = secondsFromDate(record.timestamp);
  const bandwidthMbps =
    Number(record.bandwidthMbps ?? record.bandwidth_mbps ?? record.bandwidth ?? record.value) || 0;
  const loadPercent = clampPercent(
    Number(record.loadPercent ?? record.load_percent ?? record.utilization ?? bandwidthMbps)
  );

  return {
    timestamp,
    nodeId: normalizeText(record.nodeId),
    portId: normalizeText(record.portId, 'port-unknown'),
    protocolType: normalizeText(record.protocolType ?? record.protocol, 'LAN'),
    bandwidth: bandwidthMbps,
    utilization: loadPercent,
    bandwidthMbps,
    bandwidth_mbps: bandwidthMbps,
    loadPercent,
    load_percent: loadPercent,
    messageCount: Number(record.messageCount ?? 1) || 0,
  };
}

function normalizeSimulationAlarm(alarm: DemoSimulationAlarm): DemoSimulationAlarmDetail {
  const record = alarm as DemoSimulationAlarm & DemoRecord;
  const severity = severityValue(record.severity ?? record.level);
  const alarmType = normalizeText(record.alarmType ?? record.type, 'bandwidth_exceed');

  return {
    alarmId: normalizeText(record.alarmId, `alarm-${secondsFromDate(record.timestamp)}`),
    timestamp: secondsFromDate(record.timestamp),
    severity,
    level: severity,
    message: normalizeText(record.message, '离线演示告警'),
    alarmType,
    type: alarmType,
    targetId: hasText(record.targetId) ? record.targetId.trim() : undefined,
    targetNodeId: hasText(record.targetNodeId) ? record.targetNodeId.trim() : undefined,
    targetEdgeId: hasText(record.targetEdgeId) ? record.targetEdgeId.trim() : undefined,
    edgeId: hasText(record.edgeId) ? record.edgeId.trim() : undefined,
    nodeId: hasText(record.nodeId) ? record.nodeId.trim() : undefined,
    affectedNodes: Array.isArray(record.affectedNodes)
      ? (record.affectedNodes as string[])
      : Array.isArray(record.affected_nodes)
        ? (record.affected_nodes as string[])
        : undefined,
    details:
      typeof record.details === 'object' && record.details
        ? (record.details as DemoRecord)
        : {
            message: normalizeText(record.message),
          },
  };
}

function normalizeFaultStatus(value: unknown): string {
  const normalized = normalizeText(value, 'active').toLowerCase();
  if (normalized === 'inactive') {
    return 'pending';
  }
  if (normalized === 'resolved' || normalized === 'cleared') {
    return 'cleared';
  }
  return normalized || 'active';
}

function normalizeSimulationFault(fault: DemoSimulationFault): DemoSimulationFaultDetail {
  const record = fault as DemoSimulationFault & DemoRecord;
  return {
    faultId: normalizeText(record.faultId, `fault-${secondsFromDate(record.timestamp)}`),
    sessionId: normalizeText(record.sessionId),
    faultType: normalizeText(record.faultType ?? record.type, 'disconnect'),
    targetType: normalizeText(record.targetType, 'edge'),
    targetId: normalizeText(record.targetId ?? record.target, ''),
    targetKey: normalizeText(record.targetKey ?? record.targetId ?? record.target, ''),
    targetName: hasText(record.targetName) ? record.targetName.trim() : undefined,
    params: typeof record.params === 'object' && record.params ? (record.params as DemoRecord) : {},
    status: normalizeFaultStatus(record.status),
    startAt: Number(record.startAt ?? record.start_at) || undefined,
    endAt: Number(record.endAt ?? record.end_at) || undefined,
    priority: Number(record.priority ?? 0) || 0,
    createTime: secondsFromDate(record.createTime ?? record.timestamp),
    updateTime: secondsFromDate(record.updateTime ?? record.timestamp),
  };
}

function normalizeEventStatus(value: unknown): 'pending' | 'triggered' | 'disabled' {
  const normalized = normalizeText(value, 'pending').toLowerCase();
  if (normalized === 'triggered' || normalized === 'disabled') {
    return normalized;
  }
  return 'pending';
}

function normalizeFrameType(value: unknown): DemoRealtimeFrameType | undefined {
  const normalized = normalizeText(value).toLowerCase();
  if (
    normalized === 'status' ||
    normalized === 'messages' ||
    normalized === 'bandwidth' ||
    normalized === 'alarms' ||
    normalized === 'animation' ||
    normalized === 'faults' ||
    normalized === 'pong'
  ) {
    return normalized;
  }

  return undefined;
}

function normalizeSimulationEvent(event: DemoSimulationEvent): DemoSimulationEventDetail {
  const record = event as DemoSimulationEvent & DemoRecord;
  const conditionValue =
    typeof record.conditionValue === 'object' && record.conditionValue
      ? (record.conditionValue as DemoRecord)
      : {};
  const actionParams =
    typeof record.actionParams === 'object' && record.actionParams
      ? (record.actionParams as DemoRecord)
      : {};

  return {
    eventId: normalizeText(record.eventId, `event-${secondsFromDate(record.triggerTime)}`),
    name: normalizeText(record.name, '演示事件'),
    condition: {
      type: normalizeText(record.conditionType, 'manual'),
      value: conditionValue,
    },
    action: {
      type: normalizeText(record.actionType, 'log'),
      params: actionParams,
    },
    status: normalizeEventStatus(record.status),
    triggerCount: Number(record.triggerCount ?? 0) || 0,
    createTime: secondsFromDate(record.createTime ?? record.triggerTime),
    lastTriggerTime:
      record.lastTriggerTime !== undefined ? secondsFromDate(record.lastTriggerTime) : undefined,
  };
}

function buildExportData(content: string, fileName: string): DemoSimulationExportResult {
  return {
    downloadUrl: `data:application/json;charset=utf-8,${encodeURIComponent(content)}`,
    fileName,
    fileSize: new Blob([content]).size,
    content,
  };
}

function readArrayPayload(value: unknown, fallback: unknown[]): unknown[] {
  if (Array.isArray(value)) {
    return value;
  }

  if (value && typeof value === 'object') {
    const record = value as DemoRecord;
    if (Array.isArray(record.items)) {
      return record.items;
    }
    if (Array.isArray(record.data)) {
      return record.data;
    }
  }

  return fallback;
}

function createFaultEvents(faults: DemoSimulationFaultDetail[]): DemoRecord[] {
  return faults.map((fault) => ({
    action: fault.status === 'cleared' ? 'cleared' : 'created',
    fault,
  }));
}

function createFramePayload(
  type: DemoRealtimeFrameType,
  rawPayload: unknown,
  defaults: Record<DemoRealtimeFrameType, unknown>
): unknown {
  if (type === 'status') {
    return {
      ...(defaults.status as DemoRecord),
      ...(rawPayload && typeof rawPayload === 'object' && !Array.isArray(rawPayload)
        ? (rawPayload as DemoRecord)
        : {}),
    };
  }

  if (type === 'pong') {
    return rawPayload && typeof rawPayload === 'object' && !Array.isArray(rawPayload)
      ? rawPayload
      : defaults.pong;
  }

  return readArrayPayload(rawPayload, defaults[type] as unknown[]);
}

const DEFAULT_REALTIME_FRAME_DELAYS: Record<DemoRealtimeFrameType, number> = {
  status: 0,
  messages: 50,
  bandwidth: 100,
  alarms: 150,
  animation: 200,
  faults: 250,
  pong: 300,
};

const DEFAULT_REALTIME_FRAME_ORDER: Record<DemoRealtimeFrameType, number> = {
  status: 1,
  messages: 2,
  bandwidth: 3,
  alarms: 4,
  animation: 5,
  faults: 6,
  pong: 7,
};

export class DemoSimulationService {
  constructor(
    private readonly projectRepository: ProjectRepository,
    private readonly projectVersionRepository: ProjectVersionRepository,
    private readonly simulationRepository: SimulationRepository
  ) {}

  private async requireProject(projectId: number) {
    const project = await this.projectRepository.get(projectId);
    if (!project) {
      throw new DemoSimulationError('工程不存在或已被删除', 404);
    }
    return project;
  }

  private async resolveVersion(projectId: number, versionId?: number): Promise<number> {
    if (versionId !== undefined) {
      const version = await this.projectVersionRepository.get(versionId);
      if (!version) {
        throw new DemoSimulationError('版本不存在或已被删除', 404);
      }
      if (Number(version.projectId) !== projectId) {
        throw new DemoSimulationError('版本不属于当前工程', 400);
      }
      return versionId;
    }

    const versions = await this.projectVersionRepository.listByProject(projectId);
    const latest = versions.sort(
      (left, right) =>
        Date.parse(String(right.updateTime ?? right.createTime ?? '')) -
        Date.parse(String(left.updateTime ?? left.createTime ?? ''))
    )[0];

    if (!latest) {
      throw new DemoSimulationError('当前工程没有可用版本', 400);
    }

    return Number(latest.versionId);
  }

  async createSession(payload: DemoSimulationSessionPayload): Promise<DemoSimulationSessionDetail> {
    const projectId = ensureNumber(payload.projectId, '工程ID');
    await this.requireProject(projectId);
    const versionId = await this.resolveVersion(
      projectId,
      resolveOptionalNumber(payload.versionId)
    );
    const existing = await this.simulationRepository.findSessionByProjectVersion(
      projectId,
      versionId
    );

    if (existing) {
      const updated = await this.simulationRepository.updateSession(existing.sessionId, {
        updateTime: new Date().toISOString(),
        status: existing.status ?? 'running',
        speed: (existing as DemoRecord).speed ?? 1,
      });
      return normalizeSimulationSession(updated);
    }

    const now = new Date().toISOString();
    const created: DemoSimulationSession = {
      sessionId: randomSessionId(projectId, versionId),
      projectId,
      versionId,
      status: 'running',
      createTime: now,
      updateTime: now,
      speed: 1,
      readonly: true,
    };

    await this.simulationRepository.saveSession(created);
    return normalizeSimulationSession(created);
  }

  async getSession(sessionId: string): Promise<DemoSimulationSessionDetail> {
    const session = await this.simulationRepository.getSession(sessionId);
    if (!session) {
      throw new DemoSimulationError('仿真会话不存在', 404);
    }

    return normalizeSimulationSession(session);
  }

  async getStatus(sessionId: string): Promise<DemoSimulationStatus> {
    const session = await this.getSession(sessionId);
    const messages = await this.simulationRepository.listMessages(sessionId);
    const alarms = await this.simulationRepository.listAlarms(sessionId);
    const normalizedAlarms = alarms.map(normalizeSimulationAlarm);
    const errorCount = normalizedAlarms.filter(
      (item) => item.severity === 'error' || item.severity === 'critical'
    ).length;

    return {
      sessionId,
      status: session.status,
      startTime: session.createdAt,
      createdAt: session.createdAt,
      speed: session.speed,
      elapsedTime: Math.max(0, Math.floor(Date.now() / 1000 - secondsFromDate(session.createdAt))),
      messageCount: messages.length,
      alarmCount: alarms.length,
      errorCount,
    };
  }

  async listMessages(sessionId: string, limit = 100): Promise<DemoSimulationMessageDetail[]> {
    await this.getSession(sessionId);
    const normalized = (await this.simulationRepository.listMessages(sessionId))
      .map(normalizeSimulationMessage)
      .sort(stableSortByTimestamp);

    return limit > 0 ? normalized.slice(-limit) : normalized;
  }

  async listBandwidth(
    sessionId: string,
    options: { portId?: string | null } = {}
  ): Promise<DemoSimulationBandwidthDetail[]> {
    await this.getSession(sessionId);
    const normalized = (await this.simulationRepository.listBandwidth(sessionId))
      .map(normalizeSimulationBandwidth)
      .filter((item) => (options.portId ? item.portId === options.portId : true))
      .sort(stableSortByTimestamp);

    return normalized;
  }

  async listAlarms(sessionId: string): Promise<DemoSimulationAlarmDetail[]> {
    await this.getSession(sessionId);
    return (await this.simulationRepository.listAlarms(sessionId))
      .map(normalizeSimulationAlarm)
      .sort(stableSortByTimestamp);
  }

  async listFaults(sessionId: string): Promise<DemoSimulationFaultDetail[]> {
    await this.getSession(sessionId);
    return (await this.simulationRepository.listFaults(sessionId))
      .map(normalizeSimulationFault)
      .sort((left, right) => right.updateTime - left.updateTime);
  }

  async listEvents(sessionId: string): Promise<DemoSimulationEventDetail[]> {
    await this.getSession(sessionId);
    return (await this.simulationRepository.listEvents(sessionId))
      .map(normalizeSimulationEvent)
      .sort((left, right) => left.createTime - right.createTime);
  }

  async exportSession(
    sessionId: string,
    payload: DemoSimulationExportPayload = {}
  ): Promise<DemoSimulationExportResult> {
    const [status, messages, bandwidth, alarms, faults, events] = await Promise.all([
      this.getStatus(sessionId),
      this.listMessages(sessionId, 1000),
      this.listBandwidth(sessionId),
      this.listAlarms(sessionId),
      this.listFaults(sessionId),
      this.listEvents(sessionId),
    ]);

    const content = JSON.stringify(
      {
        kind: 'demo-simulation-export',
        generatedAt: new Date().toISOString(),
        sessionId,
        exportFormat: normalizeText(payload.exportFormat, 'json'),
        dataType: normalizeText(payload.dataType, 'all'),
        status,
        messages,
        bandwidth,
        alarms,
        faults,
        events,
      },
      null,
      2
    );

    return buildExportData(content, `${sessionId}-simulation-export.json`);
  }

  async listStreamFrames(sessionId: string): Promise<DemoRealtimeFrame[]> {
    const [status, messages, bandwidth, alarms, faults, frames] = await Promise.all([
      this.getStatus(sessionId),
      this.listMessages(sessionId, 1000),
      this.listBandwidth(sessionId),
      this.listAlarms(sessionId),
      this.listFaults(sessionId),
      this.simulationRepository.listFrames(sessionId),
    ]);
    const defaults: Record<DemoRealtimeFrameType, unknown> = {
      status,
      messages,
      bandwidth,
      alarms,
      animation: [],
      faults: createFaultEvents(faults),
      pong: {},
    };
    const normalizedFrames = frames
      .map((frame, index) => this.normalizeStreamFrame(frame, index, defaults))
      .filter((frame): frame is DemoRealtimeFrame => Boolean(frame));
    const existingTypes = new Set(normalizedFrames.map((frame) => frame.type));
    const generatedFrames = (Object.keys(DEFAULT_REALTIME_FRAME_DELAYS) as DemoRealtimeFrameType[])
      .filter((type) => !existingTypes.has(type))
      .map((type) => ({
        frameId: `generated-${sessionId}-${type}`,
        sessionId,
        order: DEFAULT_REALTIME_FRAME_ORDER[type],
        type,
        delayMs: DEFAULT_REALTIME_FRAME_DELAYS[type],
        payload: defaults[type],
      }));

    return [...normalizedFrames, ...generatedFrames].sort(
      (left, right) => left.delayMs - right.delayMs || left.order - right.order
    );
  }

  private normalizeStreamFrame(
    frame: DemoSimulationFrame,
    index: number,
    defaults: Record<DemoRealtimeFrameType, unknown>
  ): DemoRealtimeFrame | undefined {
    const type = normalizeFrameType(frame.type);
    if (!type) {
      return undefined;
    }

    return {
      frameId: normalizeText(frame.frameId, `frame-${index + 1}`),
      sessionId: normalizeText(frame.sessionId),
      order: Number(frame.order ?? index + 1) || index + 1,
      type,
      delayMs: Math.max(0, Number(frame.delayMs ?? DEFAULT_REALTIME_FRAME_DELAYS[type]) || 0),
      payload: createFramePayload(type, frame.payload, defaults),
    };
  }
}
