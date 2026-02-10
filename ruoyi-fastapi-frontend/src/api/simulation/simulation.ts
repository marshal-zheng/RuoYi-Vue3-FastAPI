import request from '@/utils/request';

/**
 * 创建仿真会话
 * @param data - { projectId, versionId }
 */
export function createSimulationSession(data: Record<string, any>) {
  return request({
    url: '/simulation/sessions',
    method: 'post',
    data: data,
  });
}

/**
 * 启动仿真会话
 * @param sessionId - 会话ID
 */
export function startSimulationSession(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/start`,
    method: 'post',
  });
}

/**
 * 停止仿真会话
 * @param sessionId - 会话ID
 */
export function stopSimulationSession(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/stop`,
    method: 'post',
  });
}

/**
 * 获取仿真会话状态
 * @param sessionId - 会话ID
 */
export function getSimulationStatus(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/status`,
    method: 'get',
  });
}

/**
 * 获取仿真报文数据
 * @param sessionId - 会话ID
 * @param limit - 限制数量
 */
export function getSimulationMessages(sessionId: string, limit: number = 100) {
  return request({
    url: `/simulation/sessions/${sessionId}/messages`,
    method: 'get',
    params: { limit },
  });
}

/**
 * 获取仿真带宽数据
 * @param sessionId - 会话ID
 * @param portId - 端口ID（可选）
 */
export function getSimulationBandwidth(sessionId: string, portId: string | null = null) {
  return request({
    url: `/simulation/sessions/${sessionId}/bandwidth`,
    method: 'get',
    params: portId ? { portId } : {},
  });
}

/**
 * 获取仿真告警数据
 * @param sessionId - 会话ID
 */
export function getSimulationAlarms(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/alarms`,
    method: 'get',
  });
}

/**
 * 导出仿真数据
 * @param sessionId - 会话ID
 * @param data - { exportFormat, dataType }
 */
export function exportSimulationData(sessionId: string, data: Record<string, any>) {
  return request({
    url: `/simulation/sessions/${sessionId}/export`,
    method: 'post',
    data: data,
  });
}

/**
 * 获取可用的数据填充策略列表
 */
export function getFillStrategies() {
  return request({
    url: '/simulation/strategies',
    method: 'get',
  });
}

// ==================== 新增仿真控制接口 ====================

/**
 * 暂停仿真会话
 * @param sessionId - 会话ID
 */
export function pauseSimulationSession(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/pause`,
    method: 'post',
  });
}

/**
 * 继续仿真会话
 * @param sessionId - 会话ID
 */
export function resumeSimulationSession(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/resume`,
    method: 'post',
  });
}

/**
 * 单步执行仿真
 * @param sessionId - 会话ID
 */
export function stepSimulationSession(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/step`,
    method: 'post',
    headers: {
      repeatSubmit: false,
    },
  });
}

/**
 * 设置仿真速度
 * @param sessionId - 会话ID
 * @param speed - 速度倍率 (0.5-4.0)
 */
export function setSimulationSpeed(sessionId: string, speed: number) {
  return request({
    url: `/simulation/sessions/${sessionId}/speed`,
    method: 'post',
    data: { speed },
  });
}

// ==================== 故障注入接口 ====================

/**
 * 注入故障
 * @param sessionId - 会话ID
 * @param data - 故障配置
 */
export function injectFault(sessionId: string, data: Record<string, any>) {
  return request({
    url: `/simulation/faults`,
    method: 'post',
    data: {
      sessionId,
      ...data,
    },
  });
}

/**
 * 清除故障
 * @param sessionId - 会话ID
 * @param faultId - 故障ID
 */
export function clearFault(sessionId: string, faultId: string) {
  return request({
    url: `/simulation/faults/${faultId}`,
    method: 'delete',
    params: { sessionId },
  });
}

/**
 * 清除指定会话的所有故障
 * @param sessionId - 会话ID
 */
export function clearAllFaults(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/faults`,
    method: 'delete',
  });
}

/**
 * 获取故障列表
 * @param sessionId - 会话ID
 */
export function getFaults(sessionId: string) {
  return request({
    url: `/simulation/faults`,
    method: 'get',
    params: { sessionId },
  });
}

// ==================== 事件触发接口 ====================

/**
 * 创建事件
 * @param sessionId - 会话ID
 * @param data - 事件配置
 */
export function createEvent(sessionId: string, data: Record<string, any>) {
  return request({
    url: `/simulation/sessions/${sessionId}/events`,
    method: 'post',
    data,
  });
}

/**
 * 更新事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 * @param data - 事件配置
 */
export function updateEvent(sessionId: string, eventId: string, data: Record<string, any>) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}`,
    method: 'put',
    data,
  });
}

/**
 * 删除事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 */
export function deleteEvent(sessionId: string, eventId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}`,
    method: 'delete',
  });
}

/**
 * 手动触发事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 */
export function triggerEvent(sessionId: string, eventId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/events/${eventId}/trigger`,
    method: 'post',
  });
}

/**
 * 获取事件列表
 * @param sessionId - 会话ID
 */
export function getEvents(sessionId: string) {
  return request({
    url: `/simulation/sessions/${sessionId}/events`,
    method: 'get',
  });
}
