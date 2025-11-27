import request from '@/utils/request'

/**
 * 创建仿真会话
 * @param {Object} data - { projectId, versionId }
 * @returns {Promise}
 */
export function createSimulationSession(data) {
  return request({
    url: '/simulation/sessions',
    method: 'post',
    data: data
  })
}

/**
 * 启动仿真会话
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function startSimulationSession(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/start`,
    method: 'post'
  })
}

/**
 * 停止仿真会话
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function stopSimulationSession(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/stop`,
    method: 'post'
  })
}

/**
 * 获取仿真会话状态
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function getSimulationStatus(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/status`,
    method: 'get'
  })
}

/**
 * 获取仿真报文数据
 * @param {String} sessionId - 会话ID
 * @param {Number} limit - 限制数量
 * @returns {Promise}
 */
export function getSimulationMessages(sessionId, limit = 100) {
  return request({
    url: `/simulation/sessions/${sessionId}/messages`,
    method: 'get',
    params: { limit }
  })
}

/**
 * 获取仿真带宽数据
 * @param {String} sessionId - 会话ID
 * @param {String} portId - 端口ID（可选）
 * @returns {Promise}
 */
export function getSimulationBandwidth(sessionId, portId = null) {
  return request({
    url: `/simulation/sessions/${sessionId}/bandwidth`,
    method: 'get',
    params: portId ? { portId } : {}
  })
}

/**
 * 获取仿真告警数据
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function getSimulationAlarms(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/alarms`,
    method: 'get'
  })
}

/**
 * 导出仿真数据
 * @param {String} sessionId - 会话ID
 * @param {Object} data - { exportFormat, dataType }
 * @returns {Promise}
 */
export function exportSimulationData(sessionId, data) {
  return request({
    url: `/simulation/sessions/${sessionId}/export`,
    method: 'post',
    data: data
  })
}

/**
 * 获取可用的数据填充策略列表
 * @returns {Promise}
 */
export function getFillStrategies() {
  return request({
    url: '/simulation/strategies',
    method: 'get'
  })
}
