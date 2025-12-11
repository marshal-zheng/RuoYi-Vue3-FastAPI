/**
 * 告警管理Composable
 * 管理告警列表、过滤、统计
 * 告警只在浮动面板中显示，不使用弹框通知
 */
import { ref, computed } from 'vue'

export function useAlarmManager() {
  const alarms = ref([]) // 告警列表
  const filterSeverity = ref(null) // 过滤严重程度
  const filterType = ref(null) // 过滤告警类型
  const searchKeyword = ref('') // 搜索关键字

  /**
   * 添加告警（去重处理）
   */
  const addAlarm = (alarm) => {
    if (Array.isArray(alarm)) {
      // 过滤掉已存在的告警（基于 alarmId 去重）
      const existingIds = new Set(alarms.value.map(a => a.alarmId))
      const newAlarms = alarm.filter(a => !existingIds.has(a.alarmId))
      if (newAlarms.length > 0) {
        alarms.value = [...alarms.value, ...newAlarms]
      }
    } else {
      // 检查是否已存在
      const exists = alarms.value.some(a => a.alarmId === alarm.alarmId)
      if (!exists) {
        alarms.value.push(alarm)
      }
    }
  }

  /**
   * 过滤后的告警列表
   */
  const filteredAlarms = computed(() => {
    let result = alarms.value

    // 按严重程度过滤
    if (filterSeverity.value) {
      result = result.filter(alarm => alarm.severity === filterSeverity.value)
    }

    // 按类型过滤
    if (filterType.value) {
      result = result.filter(alarm => alarm.alarmType === filterType.value)
    }

    // 按关键字搜索
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter(alarm => 
        alarm.message.toLowerCase().includes(keyword) ||
        (alarm.affectedNodes && JSON.stringify(alarm.affectedNodes).toLowerCase().includes(keyword))
      )
    }

    // 按时间戳倒序排列（最新的在前）
    return result.sort((a, b) => b.timestamp - a.timestamp)
  })

  /**
   * 告警统计
   */
  const alarmStats = computed(() => {
    const stats = {
      total: 0,
      info: 0,
      warning: 0,
      error: 0,
      critical: 0,
      byType: {}
    }

    const list = filteredAlarms.value
    stats.total = list.length

    list.forEach(alarm => {
      if (alarm.severity) {
        stats[alarm.severity] = (stats[alarm.severity] || 0) + 1
      }

      if (alarm.alarmType) {
        stats.byType[alarm.alarmType] = (stats.byType[alarm.alarmType] || 0) + 1
      }
    })

    return stats
  })

  /**
   * 获取告警类型列表
   */
  const alarmTypes = computed(() => {
    const types = new Set()
    alarms.value.forEach(alarm => {
      if (alarm.alarmType) {
        types.add(alarm.alarmType)
      }
    })
    return Array.from(types)
  })

  /**
   * 获取严重程度列表
   */
  const severityLevels = ['info', 'warning', 'error', 'critical']

  /**
   * 获取严重程度颜色
   */
  const getSeverityColor = (severity) => {
    const colorMap = {
      info: '#909399',
      warning: '#E6A23C',
      error: '#F56C6C',
      critical: '#C03639'
    }
    return colorMap[severity] || colorMap.warning
  }

  /**
   * 获取严重程度标签
   */
  const getSeverityLabel = (severity) => {
    const labelMap = {
      info: '信息',
      warning: '警告',
      error: '错误',
      critical: '严重'
    }
    return labelMap[severity] || severity
  }

  /**
   * 获取告警类型标签
   */
  const getAlarmTypeLabel = (type) => {
    const labelMap = {
      loopback: '回环连接',
      multi_connection: '多端口连接',
      disconnected_node: '孤立节点',
      bandwidth_overflow: '带宽溢出',
      bandwidth_limit: '带宽限速',
      protocol_mismatch: '协议不匹配',
      config_error: '配置错误',
      collision: '报文冲突',
      packet_loss: '丢包',
      delay: '延迟注入',
      payload_corrupt: '数据篡改',
      noise_frame: '噪声帧',
      error_frame: '错误帧',
      congestion: '总线超载',
      bandwidth_exceed: '带宽超限',
      value_overflow: '参数越界',
      unconfigured_port: '端口未配置',
      insufficient_nodes: '设备不足',
      no_connection: '缺少连接',
      device_failure: '设备故障',
      disconnect: '链路断开',
    }
    return labelMap[type] || type
  }

  /**
   * 清除指定告警
   */
  const removeAlarm = (alarmId) => {
    const index = alarms.value.findIndex(alarm => alarm.alarmId === alarmId)
    if (index !== -1) {
      alarms.value.splice(index, 1)
    }
  }

  /**
   * 清除所有告警
   */
  const clearAllAlarms = () => {
    alarms.value = []
  }

  /**
   * 清除已读告警
   */
  const clearReadAlarms = () => {
    alarms.value = alarms.value.filter(alarm => !alarm.read)
  }

  /**
   * 标记告警为已读
   */
  const markAsRead = (alarmId) => {
    const alarm = alarms.value.find(a => a.alarmId === alarmId)
    if (alarm) {
      alarm.read = true
    }
  }

  /**
   * 标记所有告警为已读
   */
  const markAllAsRead = () => {
    alarms.value.forEach(alarm => {
      alarm.read = true
    })
  }

  /**
   * 导出告警数据
   */
  const exportAlarms = (format = 'json') => {
    if (format === 'json') {
      return JSON.stringify(alarms.value, null, 2)
    } else if (format === 'csv') {
      const headers = ['告警ID', '类型', '严重程度', '消息', '时间戳', '受影响节点']
      const rows = alarms.value.map(alarm => [
        alarm.alarmId,
        getAlarmTypeLabel(alarm.alarmType),
        getSeverityLabel(alarm.severity),
        alarm.message,
        new Date(alarm.timestamp * 1000).toLocaleString(),
        JSON.stringify(alarm.affectedNodes || [])
      ])
      
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n')
      
      return csvContent
    }
    return ''
  }

  /**
   * 重置过滤器
   */
  const resetFilters = () => {
    filterSeverity.value = null
    filterType.value = null
    searchKeyword.value = ''
  }

  return {
    alarms,
    filteredAlarms,
    alarmStats,
    alarmTypes,
    severityLevels,
    filterSeverity,
    filterType,
    searchKeyword,
    addAlarm,
    removeAlarm,
    clearAllAlarms,
    clearReadAlarms,
    markAsRead,
    markAllAsRead,
    getSeverityColor,
    getSeverityLabel,
    getAlarmTypeLabel,
    exportAlarms,
    resetFilters
  }
}
