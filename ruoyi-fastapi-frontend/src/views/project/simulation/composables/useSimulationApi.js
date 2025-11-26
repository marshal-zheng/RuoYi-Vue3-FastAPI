/**
 * 仿真API Composable
 * 封装所有仿真相关的HTTP请求，统一错误处理和loading状态管理
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
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
      
      if (response.code === 200) {
        return response.data
      } else {
        throw new Error(response.msg || '创建仿真会话失败')
      }
    } catch (err) {
      error.value = err.message
      ElMessage.error(err.message)
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
      
      if (response.code === 200) {
        ElMessage.success('仿真已启动')
        return response.data
      } else {
        throw new Error(response.msg || '启动仿真失败')
      }
    } catch (err) {
      error.value = err.message
      ElMessage.error(err.message)
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
      
      if (response.code === 200) {
        ElMessage.success('仿真已停止')
        return response.data
      } else {
        throw new Error(response.msg || '停止仿真失败')
      }
    } catch (err) {
      error.value = err.message
      ElMessage.error(err.message)
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
      
      if (response.code === 200) {
        return response.data
      } else {
        throw new Error(response.msg || '获取状态失败')
      }
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
      
      if (response.code === 200) {
        return response.data || []
      } else {
        throw new Error(response.msg || '获取报文数据失败')
      }
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
      
      if (response.code === 200) {
        return response.data || []
      } else {
        throw new Error(response.msg || '获取带宽数据失败')
      }
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
      
      if (response.code === 200) {
        return response.data || []
      } else {
        throw new Error(response.msg || '获取告警数据失败')
      }
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
      
      if (response.code === 200) {
        ElMessage.success('导出成功')
        return response.data
      } else {
        throw new Error(response.msg || '导出数据失败')
      }
    } catch (err) {
      error.value = err.message
      ElMessage.error(err.message)
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
