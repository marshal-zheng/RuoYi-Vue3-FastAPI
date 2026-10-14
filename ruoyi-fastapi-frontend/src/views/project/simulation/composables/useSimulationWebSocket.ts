/**
 * 仿真WebSocket Composable
 * 封装WebSocket连接、消息处理、自动重连
 * 提供响应式数据流（优化版）
 */
import { ref, shallowRef, onUnmounted, type Ref, type ShallowRef } from 'vue';
import { ElMessage } from 'element-plus';
import request from '@/utils/request';
import { decodeWebSocketMessage, type WebSocketMessage } from './websocket-contract';
import type {
  SimulationStatusData,
  SimulationMessage,
  SimulationBandwidth as BandwidthDataPoint,
  SimulationAlarm as AlarmData,
  SimulationAnimation as AnimationEvent,
  SimulationFaultEvent as FaultEvent,
} from '@/api/simulation/types';
export type { WebSocketMessage, WebSocketMessageType } from './websocket-contract';
export type {
  SimulationStatusData,
  SimulationMessage,
  SimulationBandwidth as BandwidthDataPoint,
  SimulationAlarm as AlarmData,
  SimulationAnimation as AnimationEvent,
  SimulationFaultEvent as FaultEvent,
} from '@/api/simulation/types';

/**
 * WebSocket消息类型
 */

/**
 * WebSocket消息结构
 */

/**
 * 仿真状态数据
 */

/**
 * 仿真报文数据
 */

/**
 * 带宽数据点
 */

/**
 * 告警数据
 */

/**
 * 动画事件数据
 */

/**
 * 故障事件数据
 */

/**
 * WebSocket返回类型
 */
export interface UseSimulationWebSocketReturn {
  connected: Ref<boolean>;
  lastError: Ref<string | null>;
  statusData: Ref<SimulationStatusData | null>;
  messagesData: ShallowRef<SimulationMessage[]>;
  bandwidthData: ShallowRef<BandwidthDataPoint[]>;
  alarmsData: ShallowRef<AlarmData[]>;
  animationData: ShallowRef<AnimationEvent[]>;
  faultEventsData: ShallowRef<FaultEvent[]>;
  connect: (sessionId: string) => void;
  disconnect: () => void;
  clearData: () => void;
}

export function useSimulationWebSocket(): UseSimulationWebSocketReturn {
  const ws = ref<WebSocket | null>(null);
  const connected = ref<boolean>(false);
  const lastError = ref<string | null>(null);
  const reconnectAttempts = ref<number>(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3秒

  // 数据流（使用shallowRef优化性能）
  const statusData = ref<SimulationStatusData | null>(null);
  const messagesData = shallowRef<SimulationMessage[]>([]);
  const bandwidthData = shallowRef<BandwidthDataPoint[]>([]);
  const alarmsData = shallowRef<AlarmData[]>([]);
  const animationData = shallowRef<AnimationEvent[]>([]);
  const faultEventsData = shallowRef<FaultEvent[]>([]);

  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  // 已弹出通知的告警ID集合，防止重复弹出
  const notifiedAlarmIds = new Set<string>();

  /**
   * 连接WebSocket
   */
  const connect = (sessionId: string): void => {
    void connectInternal(sessionId);
  };

  const connectInternal = async (sessionId: string): Promise<void> => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      return;
    }

    let wsTicket = '';
    try {
      const ticketResp = await request<{ wsTicket?: string; ws_ticket?: string }>({
        url: '/auth/ws-ticket',
        method: 'post',
        data: { session_id: sessionId },
      });
      wsTicket = ticketResp.wsTicket || ticketResp.ws_ticket || '';
    } catch (err) {
      lastError.value = err instanceof Error ? err.message : '获取实时连接凭据失败';
      ElMessage.error('获取实时连接凭据失败');
      return;
    }

    if (!wsTicket) {
      ElMessage.error('实时连接凭据为空');
      return;
    }

    // 构建WebSocket URL，携带一次性ticket通过后端鉴权
    const buildWsUrl = (ticket: string): string => {
      const baseApi = import.meta.env.VITE_APP_BASE_API || '';
      const ticketQuery = `?ticket=${encodeURIComponent(ticket)}`;
      const relativePath = `/simulation/sessions/${sessionId}/ws${ticketQuery}`;

      // 如果 baseApi 是完整的 http(s) 地址，直接转换为 ws(s) 连接到真实后端
      if (/^https?:\/\//i.test(baseApi)) {
        const apiUrl = new URL(baseApi);
        const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        const basePath = apiUrl.pathname.replace(/\/$/, '');
        return `${wsProtocol}//${apiUrl.host}${basePath}${relativePath}`;
      }

      // 默认走当前站点 + API 前缀（走本地代理）
      const apiPrefix = (baseApi.startsWith('/') ? baseApi : `/${baseApi}`).replace(/\/$/, '');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.host;
      return `${protocol}//${wsHost}${apiPrefix}${relativePath}`;
    };

    const wsUrl = buildWsUrl(wsTicket);

    try {
      ws.value = new WebSocket(wsUrl);

      ws.value.onopen = () => {
        lastError.value = null;
        connected.value = true;
        reconnectAttempts.value = 0;

        // 启动心跳
        startHeartbeat();
      };

      ws.value.onmessage = (event: MessageEvent) => {
        try {
          const raw: unknown = JSON.parse(event.data);
          const message = decodeWebSocketMessage(raw);
          if (message) {
            handleMessage(message);
          } else {
            lastError.value = '实时消息格式无效';
          }
        } catch (err) {
          lastError.value = err instanceof Error ? err.message : '解析实时消息失败';
        }
      };

      ws.value.onerror = () => {
        lastError.value = '实时连接发生错误';
        connected.value = false;
      };

      ws.value.onclose = () => {
        connected.value = false;
        stopHeartbeat();

        // 尝试重连
        attemptReconnect(sessionId);
      };
    } catch (err) {
      lastError.value = err instanceof Error ? err.message : '无法建立实时连接';
      ElMessage.error('无法建立实时连接');
    }
  };

  /**
   * 处理接收到的消息
   */
  const handleMessage = (message: WebSocketMessage): void => {
    if (message.type === 'pong') return;
    const { type, data } = message;

    switch (type) {
      case 'status':
        statusData.value = data;
        break;

      case 'messages': {
        // 追加新报文，保留滑动窗口，避免前端内存爆炸
        const WS_MESSAGE_LIMIT = 50000;
        const merged = [...messagesData.value, ...data];
        messagesData.value = WS_MESSAGE_LIMIT ? merged.slice(-WS_MESSAGE_LIMIT) : merged;
        break;
      }

      case 'bandwidth': {
        // 追加带宽数据，保持最新600秒数据（对齐长窗口需求）
        const now = Date.now() / 1000;
        const cutoff = now - 600;
        const merged = [...bandwidthData.value, ...data];
        // 过滤旧数据并限制数量
        bandwidthData.value = merged.filter((item) => item.timestamp >= cutoff).slice(-600);
        break;
      }

      case 'alarms':
        // 追加告警，限制最多200条
        alarmsData.value = [...alarmsData.value, ...data].slice(-200);
        // 显示新告警通知
        if (data.length > 0) {
          const latestAlarm = data[data.length - 1];
          showAlarmNotification(latestAlarm);
        }
        break;

      case 'animation':
        // 动画事件，保留最近100条供拓扑动画消费
        animationData.value = [...animationData.value, ...data].slice(-100);
        break;

      case 'faults':
        // 故障事件增量，保留最近200条
        faultEventsData.value = [...faultEventsData.value, ...data].slice(-200);
        break;
    }
  };

  /**
   * 显示告警通知（去重处理，同一告警只弹一次）
   */
  const showAlarmNotification = (alarm: AlarmData): void => {
    // 检查是否已经弹出过该告警
    if (alarm.alarmId && notifiedAlarmIds.has(alarm.alarmId)) {
      return;
    }

    // 标记为已弹出
    if (alarm.alarmId) notifiedAlarmIds.add(alarm.alarmId);

    // 限制缓存大小，避免内存泄漏
    if (notifiedAlarmIds.size > 500) {
      const firstId = notifiedAlarmIds.values().next().value;
      if (firstId) {
        notifiedAlarmIds.delete(firstId);
      }
    }

    const severityMap: Record<string, 'info' | 'warning' | 'error'> = {
      info: 'info',
      warning: 'warning',
      error: 'error',
      critical: 'error',
    };

    const type = severityMap[alarm.severity || 'warning'] || 'warning';
    ElMessage({
      type,
      message: alarm.message || '仿真告警',
      duration: 5000,
    });
  };

  /**
   * 启动心跳
   */
  const startHeartbeat = (): void => {
    heartbeatTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 每30秒发送一次心跳
  };

  /**
   * 停止心跳
   */
  const stopHeartbeat = (): void => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  };

  /**
   * 尝试重连
   */
  const attemptReconnect = (sessionId: string): void => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      ElMessage.error('实时连接已断开，请刷新页面');
      return;
    }

    reconnectAttempts.value++;

    reconnectTimer = setTimeout(() => {
      connect(sessionId);
    }, reconnectDelay);
  };

  /**
   * 断开连接
   */
  const disconnect = (): void => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    stopHeartbeat();

    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }

    connected.value = false;
  };

  /**
   * 清空数据
   */
  const clearData = (): void => {
    statusData.value = null;
    messagesData.value = [];
    bandwidthData.value = [];
    alarmsData.value = [];
    animationData.value = [];
    faultEventsData.value = [];
    notifiedAlarmIds.clear();
  };

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect();
  });

  return {
    connected,
    lastError,
    statusData,
    messagesData,
    bandwidthData,
    alarmsData,
    animationData,
    faultEventsData,
    connect,
    disconnect,
    clearData,
  };
}
