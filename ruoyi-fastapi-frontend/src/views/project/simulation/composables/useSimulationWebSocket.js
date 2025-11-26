/**
 * 仿真WebSocket Composable
 * 封装WebSocket连接、消息处理、自动重连
 * 提供响应式数据流
 */
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'

export function useSimulationWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000 // 3秒

  // 数据流
  const statusData = ref(null)
  const messagesData = ref([])
  const bandwidthData = ref([])
  const alarmsData = ref([])

  let reconnectTimer = null
  let heartbeatTimer = null

  /**
   * 连接WebSocket
   */
  const connect = (sessionId) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接')
      return
    }

    // 构建WebSocket URL，携带token以通过后端鉴权
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseApi = import.meta.env.VITE_APP_BASE_API || ''
    const apiPrefix = (baseApi.startsWith('/') ? baseApi : `/${baseApi}`).replace(/\/$/, '')
    const wsHost = window.location.host
    const token = getToken()
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : ''
    const wsPath = `${apiPrefix}/simulation/sessions/${sessionId}/ws${tokenQuery}`
    const wsUrl = `${protocol}//${wsHost}${wsPath}`

    try {
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket连接成功')
        connected.value = true
        reconnectAttempts.value = 0
        
        // 启动心跳
        startHeartbeat()
      }

      ws.value.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('解析WebSocket消息失败:', err)
        }
      }

      ws.value.onerror = (error) => {
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
  const handleMessage = (message) => {
    const { type, data } = message

    switch (type) {
      case 'status':
        statusData.value = data
        break
      
      case 'messages':
        // 追加新报文，保持最新的100条
        messagesData.value = [...messagesData.value, ...data].slice(-100)
        break
      
      case 'bandwidth':
        // 追加带宽数据，保持最新的600秒数据
        bandwidthData.value = [...bandwidthData.value, ...data]
        // 清理超过600秒的数据
        const now = Date.now() / 1000
        bandwidthData.value = bandwidthData.value.filter(
          item => now - item.timestamp <= 600
        )
        break
      
      case 'alarms':
        // 追加告警
        alarmsData.value = [...alarmsData.value, ...data]
        // 显示新告警通知
        if (data.length > 0) {
          const latestAlarm = data[data.length - 1]
          showAlarmNotification(latestAlarm)
        }
        break
      
      case 'pong':
        // 心跳响应
        break
      
      default:
        console.warn('未知的消息类型:', type)
    }
  }

  /**
   * 显示告警通知
   */
  const showAlarmNotification = (alarm) => {
    const severityMap = {
      info: 'info',
      warning: 'warning',
      error: 'error',
      critical: 'error'
    }
    
    const type = severityMap[alarm.severity] || 'warning'
    ElMessage({
      type,
      message: alarm.message,
      duration: 5000
    })
  }

  /**
   * 启动心跳
   */
  const startHeartbeat = () => {
    heartbeatTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 每30秒发送一次心跳
  }

  /**
   * 停止心跳
   */
  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  /**
   * 尝试重连
   */
  const attemptReconnect = (sessionId) => {
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
  const disconnect = () => {
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
  const clearData = () => {
    statusData.value = null
    messagesData.value = []
    bandwidthData.value = []
    alarmsData.value = []
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
    connect,
    disconnect,
    clearData
  }
}
