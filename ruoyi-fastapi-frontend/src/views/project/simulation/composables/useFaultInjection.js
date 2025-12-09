/**
 * 故障注入 Composable
 * 
 * 管理仿真过程中的故障注入功能
 */
import { ref, computed } from 'vue'
import {
  injectFault as injectFaultApi,
  clearFault as clearFaultApi,
} from '@/api/simulation/simulation'

/**
 * 故障类型枚举
 */
export const FaultType = {
  DISCONNECT: 'disconnect',       // 断开连接
  ERROR_FRAME: 'error_frame',     // 注入错误帧
  DEVICE_FAILURE: 'device_failure', // 设备故障
  PACKET_LOSS: 'packet_loss',     // 丢包
  DELAY: 'delay',                 // 延迟
}

/**
 * 故障类型配置
 */
export const FAULT_TYPE_CONFIG = {
  [FaultType.DISCONNECT]: {
    label: '断开连接',
    icon: 'Disconnect',
    description: '模拟链路断开，停止所有报文传输',
    targetType: 'edge',
  },
  [FaultType.ERROR_FRAME]: {
    label: '注入错误帧',
    icon: 'Warning',
    description: '在链路上生成指定数量的错误帧',
    targetType: 'edge',
    params: [
      { name: 'errorCount', label: '错误帧数量', type: 'number', default: 10, min: 1, max: 100 },
    ],
  },
  [FaultType.DEVICE_FAILURE]: {
    label: '模拟设备故障',
    icon: 'CircleClose',
    description: '使设备停止响应，模拟离线状态',
    targetType: 'node',
  },
  [FaultType.PACKET_LOSS]: {
    label: '设置丢包率',
    icon: 'Delete',
    description: '按设定概率随机丢弃报文',
    targetType: 'edge',
    params: [
      { name: 'lossRate', label: '丢包率(%)', type: 'number', default: 10, min: 0, max: 100 },
    ],
  },
  [FaultType.DELAY]: {
    label: '注入延迟',
    icon: 'Timer',
    description: '为报文传输添加额外延迟',
    targetType: 'edge',
    params: [
      { name: 'delayMs', label: '延迟(ms)', type: 'number', default: 100, min: 1, max: 10000 },
    ],
  },
}

/**
 * 故障注入 Composable
 * @param {Ref<string>} sessionId - 会话ID
 * @returns {Object} 故障注入方法和状态
 */
export function useFaultInjection(sessionId) {
  // 活跃的故障列表
  const faults = ref([])

  // 计算属性：按目标分组的故障
  const faultsByTarget = computed(() => {
    const grouped = {}
    faults.value.forEach(fault => {
      if (!grouped[fault.targetId]) {
        grouped[fault.targetId] = []
      }
      grouped[fault.targetId].push(fault)
    })
    return grouped
  })

  // 计算属性：活跃故障数量
  const activeFaultCount = computed(() => {
    return faults.value.filter(f => f.status === 'active').length
  })

  /**
   * 注入故障
   * @param {Object} config - 故障配置
   * @returns {Promise<Object>} 故障信息
   */
  async function injectFault(config) {
    if (!sessionId.value) {
      throw new Error('仿真会话不存在')
    }

    const { type, targetId, targetType, params = {} } = config

    // 验证故障类型
    if (!FAULT_TYPE_CONFIG[type]) {
      throw new Error(`不支持的故障类型: ${type}`)
    }

    // 验证目标类型
    const expectedTargetType = FAULT_TYPE_CONFIG[type].targetType
    if (targetType !== expectedTargetType) {
      throw new Error(`故障类型 ${type} 只能应用于 ${expectedTargetType}`)
    }

    // 调用 API
    const response = await injectFaultApi(sessionId.value, {
      type,
      targetId,
      targetType,
      params,
    })

    // 添加到本地列表
    const fault = {
      faultId: response.data?.faultId || `fault-${Date.now()}`,
      type,
      targetId,
      targetType,
      params,
      status: 'active',
      createTime: Date.now(),
    }

    faults.value.push(fault)

    return fault
  }

  /**
   * 清除故障
   * @param {string} faultId - 故障ID
   */
  async function clearFault(faultId) {
    if (!sessionId.value) {
      throw new Error('仿真会话不存在')
    }

    await clearFaultApi(sessionId.value, faultId)

    // 更新本地状态
    const fault = faults.value.find(f => f.faultId === faultId)
    if (fault) {
      fault.status = 'cleared'
    }
  }

  /**
   * 清除所有故障
   */
  async function clearAllFaults() {
    const activeFaults = faults.value.filter(f => f.status === 'active')
    
    for (const fault of activeFaults) {
      await clearFault(fault.faultId)
    }
  }

  /**
   * 清除指定目标的所有故障
   * @param {string} targetId - 目标ID
   */
  async function clearFaultsByTarget(targetId) {
    const targetFaults = faults.value.filter(
      f => f.targetId === targetId && f.status === 'active'
    )

    for (const fault of targetFaults) {
      await clearFault(fault.faultId)
    }
  }

  /**
   * 检查目标是否有活跃故障
   * @param {string} targetId - 目标ID
   * @returns {boolean}
   */
  function hasActiveFault(targetId) {
    return faults.value.some(
      f => f.targetId === targetId && f.status === 'active'
    )
  }

  /**
   * 获取目标的活跃故障
   * @param {string} targetId - 目标ID
   * @returns {Array}
   */
  function getActiveFaults(targetId) {
    return faults.value.filter(
      f => f.targetId === targetId && f.status === 'active'
    )
  }

  /**
   * 重置故障列表
   */
  function reset() {
    faults.value = []
  }

  return {
    // 状态
    faults,
    faultsByTarget,
    activeFaultCount,

    // 方法
    injectFault,
    clearFault,
    clearAllFaults,
    clearFaultsByTarget,
    hasActiveFault,
    getActiveFaults,
    reset,
  }
}

export default useFaultInjection
