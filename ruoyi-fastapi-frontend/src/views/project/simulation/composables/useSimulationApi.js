/**
 * 仿真API Composable
 * 封装所有仿真相关的HTTP请求，统一错误处理和loading状态管理
 */
import { ref } from 'vue'
import {
  createSimulationSession,
  startSimulationSession,
  stopSimulationSession,
  getSimulationStatus,
  getSimulationMessages,
  getSimulationBandwidth,
  getSimulationAlarms,
  exportSimulationData
} from '@/api/simulation/simulation'

export function useSimulationApi() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * 创建仿真会话
   */
  const createSession = async (projectId, versionId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await createSimulationSession({
        projectId,
        versionId
      })
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 启动仿真
   */
  const startSession = async (sessionId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await startSimulationSession(sessionId)
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 停止仿真
   */
  const stopSession = async (sessionId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await stopSimulationSession(sessionId)
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取仿真状态
   */
  const fetchStatus = async (sessionId) => {
    try {
      const response = await getSimulationStatus(sessionId)
      return response.data
    } catch (err) {
      console.error('获取仿真状态失败:', err)
      return null
    }
  }

  /**
   * 获取报文数据
   */
  const fetchMessages = async (sessionId, limit = 100) => {
    try {
      const response = await getSimulationMessages(sessionId, limit)
      return response.data || []
    } catch (err) {
      console.error('获取报文数据失败:', err)
      return []
    }
  }

  /**
   * 获取带宽数据
   */
  const fetchBandwidth = async (sessionId, portId = null) => {
    try {
      const response = await getSimulationBandwidth(sessionId, portId)
      return response.data || []
    } catch (err) {
      console.error('获取带宽数据失败:', err)
      return []
    }
  }

  /**
   * 获取告警数据
   */
  const fetchAlarms = async (sessionId) => {
    try {
      const response = await getSimulationAlarms(sessionId)
      return response.data || []
    } catch (err) {
      console.error('获取告警数据失败:', err)
      return []
    }
  }

  /**
   * 导出数据
   */
  const exportData = async (sessionId, exportFormat = 'json', dataType = 'messages') => {
    loading.value = true
    error.value = null
    
    try {
      const response = await exportSimulationData(sessionId, {
        exportFormat,
        dataType
      })
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    createSession,
    startSession,
    stopSession,
    fetchStatus,
    fetchMessages,
    fetchBandwidth,
    fetchAlarms,
    exportData
  }
}
