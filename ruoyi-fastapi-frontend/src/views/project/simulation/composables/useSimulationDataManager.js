/**
 * 仿真数据管理 Composable
 * 优化 WebSocket 数据更新性能
 */
import { shallowRef, ref } from 'vue'

/**
 * 节流函数
 */
function throttle(fn, delay = 100) {
  let timer = null
  let lastRun = 0
  
  return function(...args) {
    const now = Date.now()
    
    if (now - lastRun >= delay) {
      lastRun = now
      fn.apply(this, args)
    } else {
      clearTimeout(timer)
      timer = setTimeout(() => {
        lastRun = Date.now()
        fn.apply(this, args)
      }, delay - (now - lastRun))
    }
  }
}

export function useSimulationDataManager() {
  // 使用 shallowRef 减少深度监听开销
  const bandwidthData = shallowRef([])
  const messageData = shallowRef([])
  const alarmData = shallowRef([])
  
  // 数据限制配置
  const MAX_BANDWIDTH_POINTS = 600 // 最多保留600个数据点
  const MAX_MESSAGES = 100 // 最多保留100条报文
  const BANDWIDTH_TIME_WINDOW = 600 // 600秒时间窗口
  
  /**
   * 更新带宽数据（节流优化）
   */
  const updateBandwidthData = throttle((newData) => {
    if (!newData || newData.length === 0) return
    
    const now = Date.now() / 1000
    const cutoffTime = now - BANDWIDTH_TIME_WINDOW
    
    // 合并新数据
    const merged = [...bandwidthData.value, ...newData]
    
    // 过滤旧数据并限制数量
    const filtered = merged
      .filter(item => item.timestamp >= cutoffTime)
      .slice(-MAX_BANDWIDTH_POINTS)
    
    bandwidthData.value = filtered
  }, 200) // 200ms 节流
  
  /**
   * 更新报文数据（节流优化）
   */
  const updateMessageData = throttle((newData) => {
    if (!newData || newData.length === 0) return
    
    // 格式化新数据
    const formatted = newData.map(msg => ({
      messageId: msg.messageId,
      sendTimestamp: msg.sendTimestamp || msg.timestamp,
      senderNodeId: msg.senderNodeId || msg.sender,
      senderPortId: msg.senderPortId,
      receiverNodeId: msg.receiverNodeId || msg.receiver,
      receiverPortId: msg.receiverPortId,
      protocolType: msg.protocolType || msg.protocol,
      sizeBytes: msg.sizeBytes || msg.size,
      receiveTimestamp: msg.receiveTimestamp,
    }))
    
    // 追加并限制数量
    messageData.value = [...messageData.value, ...formatted].slice(-MAX_MESSAGES)
  }, 200) // 200ms 节流
  
  /**
   * 更新告警数据
   */
  function updateAlarmData(newData) {
    if (!newData || newData.length === 0) return
    alarmData.value = [...alarmData.value, ...newData]
  }
  
  /**
   * 清空所有数据
   */
  function clearAllData() {
    bandwidthData.value = []
    messageData.value = []
    alarmData.value = []
  }
  
  return {
    bandwidthData,
    messageData,
    alarmData,
    updateBandwidthData,
    updateMessageData,
    updateAlarmData,
    clearAllData,
  }
}

