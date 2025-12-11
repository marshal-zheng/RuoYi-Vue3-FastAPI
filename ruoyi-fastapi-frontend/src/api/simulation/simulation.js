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

// ==================== 新增仿真控制接口 ====================

/**
 * 暂停仿真会话
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function pauseSimulationSession(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/pause`,
    method: 'post'
  })
}

/**
 * 继续仿真会话
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function resumeSimulationSession(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/resume`,
    method: 'post'
  })
}

/**
 * 单步执行仿真
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function stepSimulationSession(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/step`,
    method: 'post',
    headers: {
      repeatSubmit: false,
    },
  })
}

/**
 * 设置仿真速度
 * @param {String} sessionId - 会话ID
 * @param {Number} speed - 速度倍率 (0.5-4.0)
 * @returns {Promise}
 */
export function setSimulationSpeed(sessionId, speed) {
  return request({
    url: `/simulation/sessions/${sessionId}/speed`,
    method: 'post',
    data: { speed }
  })
}

// ==================== 故障注入接口 ====================

/**
 * 注入故障
 * @param {String} sessionId - 会话ID
 * @param {Object} data - 故障配置
 * @returns {Promise}
 */
export function injectFault(sessionId, data) {
  return request({
    url: `/simulation/faults`,
    method: 'post',
    data: {
      sessionId,
      ...data,
    },
  })
}

/**
 * 清除故障
 * @param {String} sessionId - 会话ID
 * @param {String} faultId - 故障ID
 * @returns {Promise}
 */
export function clearFault(sessionId, faultId) {
  return request({
    url: `/simulation/faults/${faultId}`,
    method: 'delete',
    params: { sessionId },
  })
}

/**
 * 清除指定会话的所有故障
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function clearAllFaults(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/faults`,
    method: 'delete',
  })
}

/**
 * 获取故障列表
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function getFaults(sessionId) {
  return request({
    url: `/simulation/faults`,
    method: 'get',
    params: { sessionId },
  })
}

// ==================== 事件触发接口 ====================

/**
 * 创建事件
 * @param {String} sessionId - 会话ID
 * @param {Object} data - 事件配置
 * @returns {Promise}
 */
export function createEvent(sessionId, data) {
  return request({
    url: `/simulation/sessions/${sessionId}/events`,
    method: 'post',
    data
  })
}

/**
 * 更新事件
 * @param {String} sessionId - 会话ID
 * @param {String} eventId - 事件ID
 * @param {Object} data - 事件配置
 * @returns {Promise}
 */
export function updateEvent(sessionId, eventId, data) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}`,
    method: 'put',
    data
  })
}

/**
 * 删除事件
 * @param {String} sessionId - 会话ID
 * @param {String} eventId - 事件ID
 * @returns {Promise}
 */
export function deleteEvent(sessionId, eventId) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}`,
    method: 'delete'
  })
}

/**
 * 手动触发事件
 * @param {String} sessionId - 会话ID
 * @param {String} eventId - 事件ID
 * @returns {Promise}
 */
export function triggerEvent(sessionId, eventId) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}/trigger`,
    method: 'post'
  })
}

/**
 * 获取事件列表
 * @param {String} sessionId - 会话ID
 * @returns {Promise}
 */
export function getEvents(sessionId) {
  return request({
    url: `/simulation/sessions/${sessionId}/events`,
    method: 'get'
  })
}
