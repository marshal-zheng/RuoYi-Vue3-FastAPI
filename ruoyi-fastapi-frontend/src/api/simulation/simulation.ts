import request from '@/utils/request';

type SessionId = string | number;

/**
 * 创建仿真会话
 * @param data - { projectId, versionId }
 */
export function createSimulationSession(data: Record<string, any>) {
  return request.post('/simulation/sessions', data, {
    feedback: { mode: 'silent' },
  });
}

/**
 * 启动仿真会话
 * @param sessionId - 会话ID
 */
export function startSimulationSession(sessionId: SessionId, data?: Record<string, any>) {
  return request.post(`/simulation/sessions/${sessionId}/start`, data, {
    feedback: { mode: 'auto', key: 'simulation.session.start' },
  });
}

/**
 * 停止仿真会话
 * @param sessionId - 会话ID
 */
export function stopSimulationSession(sessionId: SessionId) {
  return request.post(`/simulation/sessions/${sessionId}/stop`, undefined, {
    feedback: { mode: 'silent' },
  });
}

/**
 * 获取仿真会话状态
 * @param sessionId - 会话ID
 */
export function getSimulationStatus(sessionId: SessionId) {
  return request.get(`/simulation/sessions/${sessionId}/status`);
}

/**
 * 获取仿真报文数据
 * @param sessionId - 会话ID
 * @param limit - 限制数量
 */
export function getSimulationMessages(
  sessionId: SessionId,
  limitOrParams: number | Record<string, any> = 100
) {
  return request.get(`/simulation/sessions/${sessionId}/messages`, {
    params: typeof limitOrParams === 'number' ? { limit: limitOrParams } : limitOrParams,
  });
}

/**
 * 获取仿真带宽数据
 * @param sessionId - 会话ID
 * @param portId - 端口ID（可选）
 */
export function getSimulationBandwidth(sessionId: SessionId, portId: string | null = null) {
  return request.get(`/simulation/sessions/${sessionId}/bandwidth`, {
    params: portId ? { portId } : {},
  });
}

/**
 * 获取仿真告警数据
 * @param sessionId - 会话ID
 */
export function getSimulationAlarms(sessionId: SessionId, params?: Record<string, any>) {
  return params
    ? request.get(`/simulation/sessions/${sessionId}/alarms`, { params })
    : request.get(`/simulation/sessions/${sessionId}/alarms`);
}

/**
 * 导出仿真数据
 * @param sessionId - 会话ID
 * @param data - { exportFormat, dataType }
 */
export function exportSimulationData(sessionId: SessionId, data: Record<string, any>) {
  return request.post(`/simulation/sessions/${sessionId}/export`, data, {
    feedback: { mode: 'silent' },
  });
}

/**
 * 获取可用的数据填充策略列表
 */
export function getFillStrategies() {
  return request.get('/simulation/strategies');
}

// ==================== 新增仿真控制接口 ====================

/**
 * 暂停仿真会话
 * @param sessionId - 会话ID
 */
export function pauseSimulationSession(sessionId: SessionId) {
  return request.post(`/simulation/sessions/${sessionId}/pause`, undefined, {
    feedback: { mode: 'silent' },
  });
}

/**
 * 继续仿真会话
 * @param sessionId - 会话ID
 */
export function resumeSimulationSession(sessionId: SessionId) {
  return request.post(`/simulation/sessions/${sessionId}/resume`, undefined, {
    feedback: { mode: 'silent' },
  });
}

/**
 * 单步执行仿真
 * @param sessionId - 会话ID
 */
export function stepSimulationSession(sessionId: SessionId) {
  return request.post(`/simulation/sessions/${sessionId}/step`, undefined, {
    headers: {
      repeatSubmit: false,
    },
    feedback: { mode: 'silent' },
  });
}

/**
 * 设置仿真速度
 * @param sessionId - 会话ID
 * @param speed - 速度倍率 (0.5-4.0)
 */
export function setSimulationSpeed(sessionId: SessionId, speed: number) {
  return request.post(
    `/simulation/sessions/${sessionId}/speed`,
    { speed },
    {
      feedback: { mode: 'silent' },
    }
  );
}

// ==================== 故障注入接口 ====================

/**
 * 注入故障
 * @param sessionId - 会话ID
 * @param data - 故障配置
 */
export function injectFault(sessionId: SessionId, data: Record<string, any>) {
  return request.post(
    '/simulation/faults',
    {
      sessionId,
      ...data,
    },
    {
      feedback: { mode: 'manual' },
    }
  );
}

/**
 * 清除故障
 * @param sessionId - 会话ID
 * @param faultId - 故障ID
 */
export function clearFault(sessionId: SessionId, faultId: string) {
  return request.delete(`/simulation/faults/${faultId}`, {
    params: { sessionId },
    feedback: { mode: 'manual' },
  });
}

/**
 * 清除指定会话的所有故障
 * @param sessionId - 会话ID
 */
export function clearAllFaults(sessionId: SessionId) {
  return request.delete(`/simulation/sessions/${sessionId}/faults`, {
    feedback: { mode: 'manual' },
  });
}

/**
 * 获取故障列表
 * @param sessionId - 会话ID
 */
export function getFaults(sessionId: SessionId) {
  return request.get('/simulation/faults', {
    params: { sessionId },
  });
}

// ==================== 事件触发接口 ====================

/**
 * 创建事件
 * @param sessionId - 会话ID
 * @param data - 事件配置
 */
export function createEvent(sessionId: SessionId, data: Record<string, any>) {
  return request.post(`/simulation/sessions/${sessionId}/events`, data, {
    feedback: { mode: 'auto', key: 'simulation.event.create' },
  });
}

/**
 * 更新事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 * @param data - 事件配置
 */
export function updateEvent(sessionId: SessionId, eventId: string, data: Record<string, any>) {
  return request.put(`/simulation/sessions/${sessionId}/events/${eventId}`, data, {
    feedback: { mode: 'auto', key: 'simulation.event.update' },
  });
}

/**
 * 删除事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 */
export function deleteEvent(sessionId: SessionId, eventId: string) {
  return request.delete(`/simulation/sessions/${sessionId}/events/${eventId}`, {
    feedback: { mode: 'auto', key: 'simulation.event.delete' },
  });
}

/**
 * 手动触发事件
 * @param sessionId - 会话ID
 * @param eventId - 事件ID
 */
export function triggerEvent(sessionId: SessionId, eventIdOrData: string | Record<string, any>) {
  if (typeof eventIdOrData !== 'string') {
    return request.post(`/simulation/${sessionId}/event`, eventIdOrData, {
      feedback: { mode: 'auto', key: 'simulation.event.trigger' },
    });
  }
  return request.post(
    `/simulation/sessions/${sessionId}/events/${eventIdOrData}/trigger`,
    undefined,
    {
      feedback: { mode: 'auto', key: 'simulation.event.trigger' },
    }
  );
}

/**
 * 获取事件列表
 * @param sessionId - 会话ID
 */
export function getEvents(sessionId: SessionId) {
  return request.get(`/simulation/sessions/${sessionId}/events`);
}

export function startSimulation(projectId: number | string, config: Record<string, any> = {}) {
  return request.post(
    '/simulation/start',
    {
      project_id: projectId,
      config,
    },
    {
      feedback: { mode: 'silent' },
    }
  );
}

export const pauseSimulation = pauseSimulationSession;
export const resumeSimulation = resumeSimulationSession;
export const stopSimulation = stopSimulationSession;

export function getSimulationStatistics(sessionId: SessionId) {
  return request.get(`/simulation/${sessionId}/statistics`);
}

export function exportSimulationResults(sessionId: SessionId, format: string) {
  return request.get(`/simulation/${sessionId}/export`, {
    params: { format },
    responseType: 'blob',
  });
}

export function connectSimulationWebSocket(sessionId: SessionId) {
  const base = import.meta.env.VITE_APP_WS_API || '';
  return new WebSocket(`${base}/simulation/${sessionId}/ws`);
}
