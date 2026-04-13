/**
 * 仿真数据管理 Composable
 *
 * 管理仿真过程中的带宽、报文、告警数据
 */
import { ref, computed, watch, onUnmounted, type Ref, type ComputedRef } from 'vue';
import { useSimulationWebSocket } from './useSimulationWebSocket';

interface Message {
  [key: string]: any;
  timestamp: number;
  sendTimestamp?: number;
  receiveTimestamp?: number;
  payloadHex?: string;
  fieldValues?: Record<string, any>;
  senderNodeId?: string;
  receiverNodeId?: string;
  senderNodeName?: string;
  receiverNodeName?: string;
  protocolType?: string;
  senderPortId?: string;
  receiverPortId?: string;
  fillStrategy?: string;
  sizeBytes?: number;
  isError?: boolean;
}

interface MessageFilter {
  protocolType?: string;
  senderNodeId?: string;
  receiverNodeId?: string;
  keyword?: string;
  startTime?: number;
  endTime?: number;
  errorOnly?: boolean;
  conditions?: FilterCondition[];
  conditionLogic?: 'and' | 'or';
}

interface FilterCondition {
  type?: string;
  operator?: string;
  value?: string;
  key?: string;
  field?: string;
  min?: number;
  max?: number;
}

interface BandwidthData {
  [key: string]: any;
  timestamp: number;
  protocolType?: string;
  nodeId?: string;
  portId?: string;
}

interface AlarmData {
  [key: string]: any;
  alarmId?: string;
  level?: string;
  type?: string;
  timestamp: number;
}

interface AlarmFilter {
  level?: string;
  type?: string;
}

interface FaultEventData {
  [key: string]: any;
}

interface IncrementalData<T> {
  newData: T[];
  newIndex: number;
}

/**
 * 数据清理配置
 */
const DATA_LIMITS = {
  // 为避免前端内存爆炸，保留一个滑动窗口；总数显示继续累加
  MAX_MESSAGES: 50000,
  MAX_BANDWIDTH_POINTS: 600, // 最大带宽数据点（10分钟，每秒1个）
  MAX_ALARMS: 1000, // 最大告警数量
};

/**
 * 计算报文时延（毫秒）
 */
function getLatencyMs(message: Message): number | null {
  const send = message?.sendTimestamp ?? message?.timestamp;
  const recv = message?.receiveTimestamp;
  if (!send || !recv) return null;
  return Math.max(0, (recv - send) * 1000);
}

/**
 * 单条条件匹配
 */
function matchesCondition(message: Message, condition: FilterCondition): boolean | null {
  if (!condition) return null;
  const type = condition.type || 'payload';
  const operator = (condition.operator || 'includes').toLowerCase();

  if (type === 'payload') {
    const payload = String(message?.payloadHex || '').toLowerCase();
    const value = String(condition.value || '').toLowerCase();
    if (!value) return null;
    if (operator === 'startswith') return payload.startsWith(value);
    if (operator === 'equals') return payload === value;
    return payload.includes(value);
  }

  if (type === 'field') {
    const fieldValues = message?.fieldValues || {};
    const keyFilter = String(condition.key || '').toLowerCase();
    const valueFilter = String(condition.value || '').toLowerCase();
    if (!keyFilter && !valueFilter) return null;
    return Object.entries(fieldValues).some(([k, v]) => {
      const kText = String(k || '').toLowerCase();
      const vText = String(v ?? '').toLowerCase();
      if (keyFilter && !kText.includes(keyFilter)) return false;
      if (valueFilter)
        return vText.includes(valueFilter) || (!keyFilter && kText.includes(valueFilter));
      return true;
    });
  }

  if (type === 'node') {
    const field = condition.field || 'senderNodeId';
    const target = String((message as any)?.[field] || '').toLowerCase();
    const value = String(condition.value || '').toLowerCase();
    if (!value) return null;
    return target.includes(value);
  }

  if (type === 'protocol') {
    const protocol = String(message?.protocolType || '').toLowerCase();
    const value = String(condition.value || '').toLowerCase();
    if (!value) return null;
    if (operator === 'equals') return protocol === value;
    return protocol.includes(value);
  }

  if (type === 'size') {
    const size = Number(message?.sizeBytes || 0);
    const min =
      condition.min !== undefined && condition.min !== null ? Number(condition.min) : null;
    const max =
      condition.max !== undefined && condition.max !== null ? Number(condition.max) : null;
    if (min === null && max === null) return null;
    if (Number.isFinite(min) && size < min!) return false;
    if (Number.isFinite(max) && size > max!) return false;
    return true;
  }

  if (type === 'latency') {
    const latency = getLatencyMs(message);
    if (latency === null) return false;
    const min =
      condition.min !== undefined && condition.min !== null ? Number(condition.min) : null;
    const max =
      condition.max !== undefined && condition.max !== null ? Number(condition.max) : null;
    if (min === null && max === null) return null;
    if (Number.isFinite(min) && latency < min!) return false;
    if (Number.isFinite(max) && latency > max!) return false;
    return true;
  }

  return null;
}

/**
 * 多条件匹配（支持 AND / OR）
 */
function matchesConditions(message: Message, filter: MessageFilter): boolean {
  const conditions = Array.isArray(filter?.conditions) ? filter.conditions : [];
  if (!conditions.length) return true;

  const normalized = conditions
    .map((c) => ({
      ...c,
      type: c?.type || 'payload',
    }))
    .filter((c) => {
      if (c.type === 'size' || c.type === 'latency') {
        return c.min !== undefined || c.max !== undefined;
      }
      return Boolean(String(c.value || c.key || '').trim());
    });

  if (!normalized.length) return true;

  const logic = (filter?.conditionLogic || 'and').toLowerCase() === 'or' ? 'or' : 'and';
  const results = normalized
    .map((cond) => matchesCondition(message, cond))
    .filter((res) => res !== null);

  if (!results.length) return true;
  return logic === 'or' ? results.some(Boolean) : results.every(Boolean);
}

/**
 * 报文过滤器
 * @param {Array} messages - 报文列表
 * @param {Object} filter - 过滤条件
 * @returns {Array} 过滤后的报文列表
 */
export function filterMessages(messages: Message[], filter: MessageFilter): Message[] {
  if (!messages || !Array.isArray(messages)) {
    return [];
  }

  if (!filter || Object.keys(filter).length === 0) {
    return messages;
  }

  return messages.filter((msg) => {
    // 协议类型过滤
    if (filter.protocolType && msg.protocolType !== filter.protocolType) {
      return false;
    }

    // 源节点过滤
    if (filter.senderNodeId && msg.senderNodeId !== filter.senderNodeId) {
      return false;
    }

    // 目标节点过滤
    if (filter.receiverNodeId && msg.receiverNodeId !== filter.receiverNodeId) {
      return false;
    }

    // 关键字过滤（搜索报文内容）
    if (filter.keyword) {
      const keyword = filter.keyword.toLowerCase();
      const searchFields = [
        msg.senderNodeName,
        msg.receiverNodeName,
        msg.protocolType,
        msg.payloadHex,
        msg.senderPortId,
        msg.receiverPortId,
        msg.fillStrategy,
        ...(msg.fieldValues ? Object.values(msg.fieldValues) : []),
      ]
        .filter(Boolean)
        .map((s) => String(s).toLowerCase());

      if (!searchFields.some((field) => field.includes(keyword))) {
        return false;
      }
    }

    // 时间范围过滤
    if (filter.startTime && msg.timestamp < filter.startTime) {
      return false;
    }
    if (filter.endTime && msg.timestamp > filter.endTime) {
      return false;
    }

    // 错误报文过滤
    if (filter.errorOnly && !msg.isError) {
      return false;
    }

    // 多条件过滤
    if (!matchesConditions(msg, filter)) {
      return false;
    }

    return true;
  });
}

/**
 * 检查报文是否匹配过滤条件
 * @param {Object} message - 报文
 * @param {Object} filter - 过滤条件
 * @returns {boolean} 是否匹配
 */
export function matchesFilter(message: Message, filter: MessageFilter): boolean {
  return filterMessages([message], filter).length > 0;
}

/**
 * 清理旧数据，保留最新的数据
 * @param {Array} data - 数据数组
 * @param {number} maxLength - 最大长度
 * @returns {Array} 清理后的数据
 */
export function cleanupOldData<T>(data: T[], maxLength: number): T[] {
  // maxLength 无效或无限时不做截断
  if (
    !Array.isArray(data) ||
    !Number.isFinite(maxLength) ||
    maxLength <= 0 ||
    data.length <= maxLength
  ) {
    return data;
  }
  return data.slice(-maxLength);
}

/**
 * 提取增量数据
 * @param {Array} data - 完整数据数组
 * @param {number} lastIndex - 上次推送的索引
 * @returns {Object} { newData: Array, newIndex: number }
 */
export function extractIncrementalData<T>(data: T[], lastIndex: number): IncrementalData<T> {
  if (!Array.isArray(data)) {
    return { newData: [], newIndex: 0 };
  }

  const newData = data.slice(lastIndex);
  return {
    newData,
    newIndex: data.length,
  };
}

/**
 * 仿真数据管理 Composable
 * @param {Ref<string>} sessionId - 会话ID
 * @returns {Object} 数据管理方法和状态
 */
export function useSimulationData(sessionId: Ref<string | null> = ref(null)) {
  // 原始数据
  const bandwidthData: Ref<BandwidthData[]> = ref([]);
  const messageData: Ref<Message[]> = ref([]);
  const alarmData: Ref<AlarmData[]> = ref([]);
  const faultEventData: Ref<FaultEventData[]> = ref([]);
  const statistics: Ref<Record<string, any>> = ref({});

  // 过滤条件
  const messageFilter: Ref<MessageFilter> = ref({});
  const alarmFilter: Ref<AlarmFilter> = ref({});

  // 增量数据追踪
  const lastMessageIndex: Ref<number> = ref(0);
  const lastBandwidthIndex: Ref<number> = ref(0);
  const lastAlarmIndex: Ref<number> = ref(0);
  const lastFaultEventIndex: Ref<number> = ref(0);

  // WebSocket 连接
  const wsManager = useSimulationWebSocket();

  // 计算属性：过滤后的报文
  const filteredMessages: ComputedRef<Message[]> = computed(() => {
    return filterMessages(messageData.value, messageFilter.value);
  });

  // 计算属性：过滤后的告警
  const filteredAlarms: ComputedRef<AlarmData[]> = computed(() => {
    if (!alarmFilter.value || Object.keys(alarmFilter.value).length === 0) {
      return alarmData.value;
    }

    return alarmData.value.filter((alarm) => {
      if (alarmFilter.value.level && alarm.level !== alarmFilter.value.level) {
        return false;
      }
      if (alarmFilter.value.type && alarm.type !== alarmFilter.value.type) {
        return false;
      }
      return true;
    });
  });

  // 计算属性：按协议类型分组的带宽数据
  const bandwidthByProtocol: ComputedRef<Record<string, BandwidthData[]>> = computed(() => {
    const grouped: Record<string, BandwidthData[]> = {};
    bandwidthData.value.forEach((item) => {
      const protocol = item.protocolType || 'unknown';
      if (!grouped[protocol]) {
        grouped[protocol] = [];
      }
      grouped[protocol].push(item);
    });
    return grouped;
  });

  // 计算属性：最新的带宽数据（每个端口）
  const latestBandwidth: ComputedRef<BandwidthData[]> = computed(() => {
    const latest: Record<string, BandwidthData> = {};
    bandwidthData.value.forEach((item) => {
      const key = `${item.nodeId}:${item.portId}`;
      if (!latest[key] || item.timestamp > latest[key].timestamp) {
        latest[key] = item;
      }
    });
    return Object.values(latest);
  });

  /**
   * 更新带宽数据
   */
  function updateBandwidthData(newData: BandwidthData[]) {
    if (!newData || !Array.isArray(newData)) return;

    bandwidthData.value = cleanupOldData(
      [...bandwidthData.value, ...newData],
      DATA_LIMITS.MAX_BANDWIDTH_POINTS
    );
  }

  /**
   * 更新报文数据
   */
  function updateMessageData(newData: Message[]) {
    if (!newData || !Array.isArray(newData)) return;

    messageData.value = cleanupOldData(
      [...messageData.value, ...newData],
      DATA_LIMITS.MAX_MESSAGES
    );
  }

  /**
   * 更新告警数据
   */
  function updateAlarmData(newData: AlarmData[]) {
    if (!newData || !Array.isArray(newData)) return;

    alarmData.value = cleanupOldData([...alarmData.value, ...newData], DATA_LIMITS.MAX_ALARMS);
  }

  /**
   * 设置报文过滤条件
   */
  function setMessageFilter(filter: MessageFilter) {
    messageFilter.value = filter || {};
    // 过滤条件变化后清空累计数量，等待新数据重新累计
    messageData.value = [];
    lastMessageIndex.value = 0;
    wsManager.messagesData.value = [];
  }

  /**
   * 设置告警过滤条件
   */
  function setAlarmFilter(filter: AlarmFilter) {
    alarmFilter.value = filter || {};
  }

  /**
   * 清空所有数据
   */
  function clearData() {
    bandwidthData.value = [];
    messageData.value = [];
    alarmData.value = [];
    faultEventData.value = [];
    statistics.value = {};
    lastMessageIndex.value = 0;
    lastBandwidthIndex.value = 0;
    lastAlarmIndex.value = 0;
    lastFaultEventIndex.value = 0;
  }

  /**
   * 获取增量报文数据
   */
  function getNewMessages(): Message[] {
    const result = extractIncrementalData(messageData.value, lastMessageIndex.value);
    lastMessageIndex.value = result.newIndex;
    return result.newData;
  }

  /**
   * 获取增量带宽数据
   */
  function getNewBandwidth(): BandwidthData[] {
    const result = extractIncrementalData(bandwidthData.value, lastBandwidthIndex.value);
    lastBandwidthIndex.value = result.newIndex;
    return result.newData;
  }

  /**
   * 获取增量告警数据
   */
  function getNewAlarms(): AlarmData[] {
    const result = extractIncrementalData(alarmData.value, lastAlarmIndex.value);
    lastAlarmIndex.value = result.newIndex;
    return result.newData;
  }

  /**
   * 获取增量故障事件
   */
  function getNewFaultEvents(): FaultEventData[] {
    const result = extractIncrementalData(faultEventData.value, lastFaultEventIndex.value);
    lastFaultEventIndex.value = result.newIndex;
    return result.newData;
  }

  function addMessage(message: Partial<Message> & Record<string, any>) {
    const nextMessage = message as Message;
    const latest = messageData.value[messageData.value.length - 1];
    messageData.value.push(nextMessage);
    if (latest && (nextMessage.timestamp || 0) < (latest.timestamp || 0)) {
      messageData.value.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    }
    if (messageData.value.length >= 1500) {
      messageData.value.splice(0, messageData.value.length - 1000);
    }
  }

  function addAlarm(alarm: Partial<AlarmData> & Record<string, any>) {
    alarmData.value = cleanupOldData(
      [...alarmData.value, alarm as AlarmData],
      DATA_LIMITS.MAX_ALARMS
    );
  }

  function updateStatistics(nextStatistics: Record<string, any>) {
    statistics.value = { ...(nextStatistics || {}) };
  }

  function getMessagesByProtocol(protocol: string) {
    return messageData.value.filter(
      (message) => (message.protocol || message.protocolType) === protocol
    );
  }

  function getMessagesByTimeRange(startTime: number, endTime: number) {
    return messageData.value.filter(
      (message) => message.timestamp >= startTime && message.timestamp <= endTime
    );
  }

  function getLatestMessages(limit: number) {
    return [...messageData.value]
      .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
      .slice(0, limit);
  }

  function getAlarmsByLevel(level: string) {
    return alarmData.value.filter((alarm) => alarm.level === level);
  }

  function getAlarmsByType(type: string) {
    return alarmData.value.filter((alarm) => alarm.type === type);
  }

  function getAlarmCounts() {
    return alarmData.value.reduce<Record<string, number>>((counts, alarm) => {
      const level = alarm.level || 'unknown';
      counts[level] = (counts[level] || 0) + 1;
      return counts;
    }, {});
  }

  function clearAcknowledgedAlarms() {
    alarmData.value = alarmData.value.filter((alarm) => !alarm.acknowledged);
  }

  function getMessageRate() {
    const total = Number(statistics.value.total_messages || statistics.value.total || 0);
    const duration = Number(statistics.value.duration || 0);
    return duration ? total / duration : 0;
  }

  function getProtocolDistribution() {
    const source = (statistics.value.messages_by_protocol || {}) as Record<string, unknown>;
    const total = Object.values(source).reduce<number>((sum, value) => sum + Number(value || 0), 0);
    if (!total) return {};
    return Object.entries(source).reduce<Record<string, number>>((result, [protocol, count]) => {
      result[protocol] = (Number(count || 0) / total) * 100;
      return result;
    }, {});
  }

  function getAverageLatency() {
    const latencies = messageData.value
      .map((message) => {
        const sent = message.sent_time ?? message.sendTimestamp;
        const received = message.received_time ?? message.receiveTimestamp;
        return sent !== undefined && received !== undefined
          ? Number(received) - Number(sent)
          : null;
      })
      .filter((latency): latency is number => latency !== null);

    return latencies.length
      ? latencies.reduce((sum, latency) => sum + latency, 0) / latencies.length
      : 0;
  }

  function detectPattern(protocol: string) {
    const messages = getMessagesByProtocol(protocol).sort(
      (a, b) => (a.timestamp || 0) - (b.timestamp || 0)
    );
    if (messages.length < 3) {
      return { isPeriodic: false, period: 0 };
    }
    const intervals = messages.slice(1).map((message, index) => {
      return (message.timestamp || 0) - (messages[index].timestamp || 0);
    });
    const period = intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length;
    const isPeriodic = intervals.every((interval) => Math.abs(interval - period) <= period * 0.1);
    return { isPeriodic, period };
  }

  function getCommunicationPairs() {
    return messageData.value.reduce<Record<string, number>>((pairs, message) => {
      const source = message.source || message.senderNodeId || message.senderNodeName;
      const target = message.target || message.receiverNodeId || message.receiverNodeName;
      if (!source || !target) return pairs;
      const key = `${source}->${target}`;
      pairs[key] = (pairs[key] || 0) + 1;
      return pairs;
    }, {});
  }

  function exportMessagesCSV() {
    const lines = messageData.value.map((message) => {
      return [
        message.id || '',
        message.timestamp || '',
        message.protocol || message.protocolType || '',
        message.source || message.senderNodeId || '',
        message.target || message.receiverNodeId || '',
      ].join(',');
    });
    return ['id,timestamp,protocol,source,target', ...lines].join('\n');
  }

  function exportAlarmsJSON() {
    return JSON.stringify(alarmData.value);
  }

  function exportSummary() {
    return { ...statistics.value };
  }

  function clearMessages() {
    messageData.value = [];
  }

  function clearAlarms() {
    alarmData.value = [];
  }

  // 监听 WebSocket 数据
  watch(
    () => wsManager.messagesData.value,
    (newData) => {
      if (newData && newData.length > 0) {
        updateMessageData(newData);
      }
    }
  );

  watch(
    () => wsManager.bandwidthData.value,
    (newData) => {
      if (newData && newData.length > 0) {
        updateBandwidthData(newData);
      }
    }
  );

  watch(
    () => wsManager.alarmsData.value,
    (newData) => {
      if (newData && newData.length > 0) {
        updateAlarmData(newData);
      }
    }
  );

  watch(
    () => wsManager.faultEventsData.value,
    (newData) => {
      if (newData && newData.length > 0) {
        faultEventData.value = cleanupOldData([...faultEventData.value, ...newData], 200);
      }
    }
  );

  // 监听会话ID变化，连接/断开 WebSocket
  watch(sessionId, (newSessionId, oldSessionId) => {
    if (oldSessionId) {
      wsManager.disconnect();
    }
    if (newSessionId) {
      wsManager.connect(newSessionId);
    }
  });

  // 清理
  onUnmounted(() => {
    wsManager.disconnect();
  });

  return {
    // 数据
    bandwidthData,
    messageData,
    messages: messageData,
    alarmData,
    alarms: alarmData,
    statistics,
    statusData: wsManager.statusData,
    filteredMessages,
    filteredAlarms,
    bandwidthByProtocol,
    latestBandwidth,
    faultEventData,

    // 过滤条件
    messageFilter,
    alarmFilter,

    // 方法
    updateBandwidthData,
    updateMessageData,
    updateAlarmData,
    setMessageFilter,
    setAlarmFilter,
    clearData,
    clear: clearData,
    addMessage,
    addAlarm,
    updateStatistics,
    getMessagesByProtocol,
    getMessagesByTimeRange,
    getLatestMessages,
    getAlarmsByLevel,
    getAlarmsByType,
    getAlarmCounts,
    clearAcknowledgedAlarms,
    getMessageRate,
    getProtocolDistribution,
    getAverageLatency,
    detectPattern,
    getCommunicationPairs,
    exportMessagesCSV,
    exportAlarmsJSON,
    exportSummary,
    clearMessages,
    clearAlarms,
    getNewMessages,
    getNewBandwidth,
    getNewAlarms,
    getNewFaultEvents,
  };
}

export default useSimulationData;
