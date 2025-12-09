/**
 * 仿真数据管理 Composable
 * 
 * 管理仿真过程中的带宽、报文、告警数据
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import { useSimulationWebSocket } from './useSimulationWebSocket'

/**
 * 数据清理配置
 */
const DATA_LIMITS = {
  MAX_MESSAGES: 10000,      // 最大报文数量
  MAX_BANDWIDTH_POINTS: 600, // 最大带宽数据点（10分钟，每秒1个）
  MAX_ALARMS: 1000,         // 最大告警数量
}

/**
 * 报文过滤器
 * @param {Array} messages - 报文列表
 * @param {Object} filter - 过滤条件
 * @returns {Array} 过滤后的报文列表
 */
export function filterMessages(messages, filter) {
  if (!messages || !Array.isArray(messages)) {
    return []
  }

  if (!filter || Object.keys(filter).length === 0) {
    return messages
  }

  return messages.filter(msg => {
    // 协议类型过滤
    if (filter.protocolType && msg.protocolType !== filter.protocolType) {
      return false
    }

    // 源节点过滤
    if (filter.senderNodeId && msg.senderNodeId !== filter.senderNodeId) {
      return false
    }

    // 目标节点过滤
    if (filter.receiverNodeId && msg.receiverNodeId !== filter.receiverNodeId) {
      return false
    }

    // 关键字过滤（搜索报文内容）
    if (filter.keyword) {
      const keyword = filter.keyword.toLowerCase()
      const searchFields = [
        msg.senderNodeName,
        msg.receiverNodeName,
        msg.protocolType,
        msg.payloadHex,
      ].filter(Boolean).map(s => s.toLowerCase())

      if (!searchFields.some(field => field.includes(keyword))) {
        return false
      }
    }

    // 时间范围过滤
    if (filter.startTime && msg.timestamp < filter.startTime) {
      return false
    }
    if (filter.endTime && msg.timestamp > filter.endTime) {
      return false
    }

    // 错误报文过滤
    if (filter.errorOnly && !msg.isError) {
      return false
    }

    return true
  })
}

/**
 * 检查报文是否匹配过滤条件
 * @param {Object} message - 报文
 * @param {Object} filter - 过滤条件
 * @returns {boolean} 是否匹配
 */
export function matchesFilter(message, filter) {
  return filterMessages([message], filter).length > 0
}

/**
 * 清理旧数据，保留最新的数据
 * @param {Array} data - 数据数组
 * @param {number} maxLength - 最大长度
 * @returns {Array} 清理后的数据
 */
export function cleanupOldData(data, maxLength) {
  if (!Array.isArray(data) || data.length <= maxLength) {
    return data
  }
  return data.slice(-maxLength)
}

/**
 * 提取增量数据
 * @param {Array} data - 完整数据数组
 * @param {number} lastIndex - 上次推送的索引
 * @returns {Object} { newData: Array, newIndex: number }
 */
export function extractIncrementalData(data, lastIndex) {
  if (!Array.isArray(data)) {
    return { newData: [], newIndex: 0 }
  }

  const newData = data.slice(lastIndex)
  return {
    newData,
    newIndex: data.length,
  }
}

/**
 * 仿真数据管理 Composable
 * @param {Ref<string>} sessionId - 会话ID
 * @returns {Object} 数据管理方法和状态
 */
export function useSimulationData(sessionId) {
  // 原始数据
  const bandwidthData = ref([])
  const messageData = ref([])
  const alarmData = ref([])

  // 过滤条件
  const messageFilter = ref({})
  const alarmFilter = ref({})

  // 增量数据追踪
  const lastMessageIndex = ref(0)
  const lastBandwidthIndex = ref(0)
  const lastAlarmIndex = ref(0)

  // WebSocket 连接
  const wsManager = useSimulationWebSocket()

  // 计算属性：过滤后的报文
  const filteredMessages = computed(() => {
    return filterMessages(messageData.value, messageFilter.value)
  })

  // 计算属性：过滤后的告警
  const filteredAlarms = computed(() => {
    if (!alarmFilter.value || Object.keys(alarmFilter.value).length === 0) {
      return alarmData.value
    }

    return alarmData.value.filter(alarm => {
      if (alarmFilter.value.level && alarm.level !== alarmFilter.value.level) {
        return false
      }
      if (alarmFilter.value.type && alarm.type !== alarmFilter.value.type) {
        return false
      }
      return true
    })
  })

  // 计算属性：按协议类型分组的带宽数据
  const bandwidthByProtocol = computed(() => {
    const grouped = {}
    bandwidthData.value.forEach(item => {
      const protocol = item.protocolType || 'unknown'
      if (!grouped[protocol]) {
        grouped[protocol] = []
      }
      grouped[protocol].push(item)
    })
    return grouped
  })

  // 计算属性：最新的带宽数据（每个端口）
  const latestBandwidth = computed(() => {
    const latest = {}
    bandwidthData.value.forEach(item => {
      const key = `${item.nodeId}:${item.portId}`
      if (!latest[key] || item.timestamp > latest[key].timestamp) {
        latest[key] = item
      }
    })
    return Object.values(latest)
  })

  /**
   * 更新带宽数据
   */
  function updateBandwidthData(newData) {
    if (!newData || !Array.isArray(newData)) return

    bandwidthData.value = cleanupOldData(
      [...bandwidthData.value, ...newData],
      DATA_LIMITS.MAX_BANDWIDTH_POINTS
    )
  }

  /**
   * 更新报文数据
   */
  function updateMessageData(newData) {
    if (!newData || !Array.isArray(newData)) return

    messageData.value = cleanupOldData(
      [...messageData.value, ...newData],
      DATA_LIMITS.MAX_MESSAGES
    )
  }

  /**
   * 更新告警数据
   */
  function updateAlarmData(newData) {
    if (!newData || !Array.isArray(newData)) return

    alarmData.value = cleanupOldData(
      [...alarmData.value, ...newData],
      DATA_LIMITS.MAX_ALARMS
    )
  }

  /**
   * 设置报文过滤条件
   */
  function setMessageFilter(filter) {
    messageFilter.value = filter || {}
  }

  /**
   * 设置告警过滤条件
   */
  function setAlarmFilter(filter) {
    alarmFilter.value = filter || {}
  }

  /**
   * 清空所有数据
   */
  function clearData() {
    bandwidthData.value = []
    messageData.value = []
    alarmData.value = []
    lastMessageIndex.value = 0
    lastBandwidthIndex.value = 0
    lastAlarmIndex.value = 0
  }

  /**
   * 获取增量报文数据
   */
  function getNewMessages() {
    const result = extractIncrementalData(messageData.value, lastMessageIndex.value)
    lastMessageIndex.value = result.newIndex
    return result.newData
  }

  /**
   * 获取增量带宽数据
   */
  function getNewBandwidth() {
    const result = extractIncrementalData(bandwidthData.value, lastBandwidthIndex.value)
    lastBandwidthIndex.value = result.newIndex
    return result.newData
  }

  /**
   * 获取增量告警数据
   */
  function getNewAlarms() {
    const result = extractIncrementalData(alarmData.value, lastAlarmIndex.value)
    lastAlarmIndex.value = result.newIndex
    return result.newData
  }

  // 监听 WebSocket 数据
  watch(() => wsManager.messagesData.value, (newData) => {
    if (newData && newData.length > 0) {
      updateMessageData(newData)
    }
  })

  watch(() => wsManager.bandwidthData.value, (newData) => {
    if (newData && newData.length > 0) {
      updateBandwidthData(newData)
    }
  })

  watch(() => wsManager.alarmsData.value, (newData) => {
    if (newData && newData.length > 0) {
      updateAlarmData(newData)
    }
  })

  // 监听会话ID变化，连接/断开 WebSocket
  watch(sessionId, (newSessionId, oldSessionId) => {
    if (oldSessionId) {
      wsManager.disconnect()
    }
    if (newSessionId) {
      wsManager.connect(newSessionId)
    }
  })

  // 清理
  onUnmounted(() => {
    wsManager.disconnect()
  })

  return {
    // 数据
    bandwidthData,
    messageData,
    alarmData,
    filteredMessages,
    filteredAlarms,
    bandwidthByProtocol,
    latestBandwidth,

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
    getNewMessages,
    getNewBandwidth,
    getNewAlarms,

    // WebSocket 管理器
    wsManager,
  }
}

export default useSimulationData
