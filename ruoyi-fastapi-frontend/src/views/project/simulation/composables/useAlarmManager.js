/**
 * 告警管理Composable
 * 管理告警列表、过滤、统计
 * 提供告警通知功能
 */
import { ref, computed } from 'vue'
import { ElNotification } from 'element-plus'

export function useAlarmManager() {
  const alarms = ref([]) // 告警列表
  const filterSeverity = ref(null) // 过滤严重程度
  const filterType = ref(null) // 过滤告警类型
  const searchKeyword = ref('') // 搜索关键字
  const enableNotification = ref(true) // 是否启用通知

  /**
   * 添加告警
   */
  const addAlarm = (alarm) => {
    if (Array.isArray(alarm)) {
      alarms.value = [...alarms.value, ...alarm]
      // 显示最新的告警通知
      if (alarm.length > 0 && enableNotification.value) {
        showAlarmNotification(alarm[alarm.length - 1])
      }
    } else {
      alarms.value.push(alarm)
      if (enableNotification.value) {
        showAlarmNotification(alarm)
      }
    }
  }

  /**
   * 显示告警通知
   */
  const showAlarmNotification = (alarm) => {
    const severityConfig = {
      info: {
        type: 'info',
        title: '信息'
      },
      warning: {
        type: 'warning',
        title: '警告'
      },
      error: {
        type: 'error',
        title: '错误'
      },
      critical: {
        type: 'error',
        title: '严重错误'
      }
    }

    const config = severityConfig[alarm.severity] || severityConfig.warning

    ElNotification({
      title: config.title,
      message: alarm.message,
      type: config.type,
      duration: 5000,
      position: 'top-right'
    })
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
      total: alarms.value.length,
      info: 0,
      warning: 0,
      error: 0,
      critical: 0,
      byType: {}
    }

    alarms.value.forEach(alarm => {
      // 按严重程度统计
      if (alarm.severity) {
        stats[alarm.severity] = (stats[alarm.severity] || 0) + 1
      }

      // 按类型统计
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
      bandwidth_overflow: '带宽溢出',
      protocol_mismatch: '协议不匹配',
      config_error: '配置错误'
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
    enableNotification,
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
