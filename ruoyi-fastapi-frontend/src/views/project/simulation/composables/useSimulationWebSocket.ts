/**
 * 仿真WebSocket Composable
 * 封装WebSocket连接、消息处理、自动重连
 * 提供响应式数据流（优化版）
 */
import { ref, shallowRef, onUnmounted, type Ref, type ShallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'

/**
 * WebSocket消息类型
 */
export type WebSocketMessageType = 
  | 'status' 
  | 'messages' 
  | 'bandwidth' 
  | 'alarms' 
  | 'animation' 
  | 'faults' 
  | 'pong'

/**
 * WebSocket消息结构
 */
export interface WebSocketMessage {
  type: WebSocketMessageType
  data: any
}

/**
 * 仿真状态数据
 */
export interface SimulationStatusData {
  sessionId: string
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'error'
  startTime?: string
  endTime?: string
  messageCount: number
  alarmCount: number
  errorCount: number
}

/**
 * 仿真报文数据
 */
export interface SimulationMessage {
  id: string
  timestamp: number
  sourceNode: string
  targetNode: string
  protocolType: string
  messageType: string
  data: any
  size: number
}

/**
 * 带宽数据点
 */
export interface BandwidthDataPoint {
  timestamp: number
  portId: string
  bandwidth: number
  utilization: number
}

/**
 * 告警数据
 */
export interface AlarmData {
  alarmId: string
  timestamp: number
  severity: 'info' | 'warning' | 'error' | 'critical'
  message: string
  nodeId?: string
  edgeId?: string
  details?: any
}

/**
 * 动画事件数据
 */
export interface AnimationEvent {
  type: 'traffic' | 'error' | 'node-active' | 'node-error'
  edgeId?: string
  nodeId?: string
  protocolType?: string
  duration?: number
}

/**
 * 故障事件数据
 */
export interface FaultEvent {
  faultId: string
  timestamp: number
  faultType: string
  targetNode?: string
  targetEdge?: string
  parameters: any
}

/**
 * WebSocket返回类型
 */
export interface UseSimulationWebSocketReturn {
  connected: Ref<boolean>
  statusData: Ref<SimulationStatusData | null>
  messagesData: ShallowRef<SimulationMessage[]>
  bandwidthData: ShallowRef<BandwidthDataPoint[]>
  alarmsData: ShallowRef<AlarmData[]>
  animationData: ShallowRef<AnimationEvent[]>
  faultEventsData: ShallowRef<FaultEvent[]>
  connect: (sessionId: string) => void
  disconnect: () => void
  clearData: () => void
}

export function useSimulationWebSocket(): UseSimulationWebSocketReturn {
  const ws = ref<WebSocket | null>(null)
  const connected = ref<boolean>(false)
  const reconnectAttempts = ref<number>(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000 // 3秒

  // 数据流（使用shallowRef优化性能）
  const statusData = ref<SimulationStatusData | null>(null)
  const messagesData = shallowRef<SimulationMessage[]>([])
  const bandwidthData = shallowRef<BandwidthDataPoint[]>([])
  const alarmsData = shallowRef<AlarmData[]>([])
  const animationData = shallowRef<AnimationEvent[]>([])
  const faultEventsData = shallowRef<FaultEvent[]>([])

  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  // 已弹出通知的告警ID集合，防止重复弹出
  const notifiedAlarmIds = new Set<string>()

  /**
   * 连接WebSocket
   */
  const connect = (sessionId: string): void => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接')
      return
    }

    // 构建WebSocket URL，携带token以通过后端鉴权
    const buildWsUrl = (): string => {
      const baseApi = import.meta.env.VITE_APP_BASE_API || ''
      const token = getToken()
      const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : ''
      const relativePath = `/simulation/sessions/${sessionId}/ws${tokenQuery}`

      // 如果 baseApi 是完整的 http(s) 地址，直接转换为 ws(s) 连接到真实后端
      if (/^https?:\/\//i.test(baseApi)) {
        const apiUrl = new URL(baseApi)
        const wsProtocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'
        const basePath = apiUrl.pathname.replace(/\/$/, '')
        return `${wsProtocol}//${apiUrl.host}${basePath}${relativePath}`
      }

      // 默认走当前站点 + API 前缀（走本地代理）
      const apiPrefix = (baseApi.startsWith('/') ? baseApi : `/${baseApi}`).replace(/\/$/, '')
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = window.location.host
      return `${protocol}//${wsHost}${apiPrefix}${relativePath}`
    }

    const wsUrl = buildWsUrl()

    try {
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket连接成功')
        connected.value = true
        reconnectAttempts.value = 0

        // 启动心跳
        startHeartbeat()
      }

      ws.value.onmessage = (event: MessageEvent) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('解析WebSocket消息失败:', err)
        }
      }

      ws.value.onerror = (error: Event) => {
        console.error('WebSocket错误:', error)
        connected.value = false
      }

      ws.value.onclose = () => {
        console.log('WebSocket连接关闭')
        connected.value = false
        stopHeartbeat()

        // 尝试重连
        attemptReconnect(sessionId)
      }
    } catch (err) {
      console.error('创建WebSocket连接失败:', err)
      ElMessage.error('无法建立实时连接')
    }
  }

  /**
   * 处理接收到的消息
   */
  const handleMessage = (message: WebSocketMessage): void => {
    const { type, data } = message

    switch (type) {
      case 'status':
        statusData.value = data
        break

      case 'messages': {
        // 追加新报文，保留滑动窗口，避免前端内存爆炸
        const WS_MESSAGE_LIMIT = 50000
        const merged = [...messagesData.value, ...data]
        messagesData.value = WS_MESSAGE_LIMIT
          ? merged.slice(-WS_MESSAGE_LIMIT)
          : merged
        break
      }

      case 'bandwidth': {
        // 追加带宽数据，保持最新600秒数据（对齐长窗口需求）
        const now = Date.now() / 1000
        const cutoff = now - 600
        const merged = [...bandwidthData.value, ...data]
        // 过滤旧数据并限制数量
        bandwidthData.value = merged.filter((item) => item.timestamp >= cutoff).slice(-600)
        break
      }

      case 'alarms':
        // 追加告警，限制最多200条
        alarmsData.value = [...alarmsData.value, ...data].slice(-200)
        // 显示新告警通知
        if (data.length > 0) {
          const latestAlarm = data[data.length - 1]
          showAlarmNotification(latestAlarm)
        }
        break

      case 'animation':
        // 动画事件，保留最近100条供拓扑动画消费
        animationData.value = [...animationData.value, ...data].slice(-100)
        break

      case 'faults':
        // 故障事件增量，保留最近200条
        faultEventsData.value = [...faultEventsData.value, ...data].slice(-200)
        break

      case 'pong':
        // 心跳响应
        break

      default:
        console.warn('未知的消息类型:', type)
    }
  }

  /**
   * 显示告警通知（去重处理，同一告警只弹一次）
   */
  const showAlarmNotification = (alarm: AlarmData): void => {
    // 检查是否已经弹出过该告警
    if (notifiedAlarmIds.has(alarm.alarmId)) {
      return
    }

    // 标记为已弹出
    notifiedAlarmIds.add(alarm.alarmId)

    // 限制缓存大小，避免内存泄漏
    if (notifiedAlarmIds.size > 500) {
      const firstId = notifiedAlarmIds.values().next().value
      if (firstId) {
        notifiedAlarmIds.delete(firstId)
      }
    }

    const severityMap: Record<string, 'info' | 'warning' | 'error'> = {
      info: 'info',
      warning: 'warning',
      error: 'error',
      critical: 'error',
    }

    const type = severityMap[alarm.severity] || 'warning'
    ElMessage({
      type,
      message: alarm.message,
      duration: 5000,
    })
  }

  /**
   * 启动心跳
   */
  const startHeartbeat = (): void => {
    heartbeatTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 每30秒发送一次心跳
  }

  /**
   * 停止心跳
   */
  const stopHeartbeat = (): void => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  /**
   * 尝试重连
   */
  const attemptReconnect = (sessionId: string): void => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      ElMessage.error('实时连接已断开，请刷新页面')
      return
    }

    reconnectAttempts.value++
    console.log(`尝试重连 (${reconnectAttempts.value}/${maxReconnectAttempts})`)

    reconnectTimer = setTimeout(() => {
      connect(sessionId)
    }, reconnectDelay)
  }

  /**
   * 断开连接
   */
  const disconnect = (): void => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    stopHeartbeat()

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    connected.value = false
  }

  /**
   * 清空数据
   */
  const clearData = (): void => {
    statusData.value = null
    messagesData.value = []
    bandwidthData.value = []
    alarmsData.value = []
    animationData.value = []
    faultEventsData.value = []
    notifiedAlarmIds.clear()
  }

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    statusData,
    messagesData,
    bandwidthData,
    alarmsData,
    animationData,
    faultEventsData,
    connect,
    disconnect,
    clearData,
  }
}
