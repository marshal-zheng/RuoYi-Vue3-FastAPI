/**
 * 仿真API Composable
 * 封装所有仿真相关的HTTP请求，统一错误处理和loading状态管理
 */
import { ref, type Ref } from 'vue';
import type {
  SimulationSessionData,
  SimulationStatusData,
  SimulationMessage,
  SimulationBandwidth,
  SimulationAlarm,
  ExportDataResult,
  SimulationSessionCommandAccepted,
} from '@/api/simulation/types';
export type {
  SimulationSessionParams,
  SimulationSessionData,
  SimulationStatusData,
  SimulationMessage,
  SimulationBandwidth,
  SimulationAlarm,
  ExportDataParams,
  ExportDataResult,
  SimulationSessionCommandAccepted,
} from '@/api/simulation/types';
import {
  createSimulationSession,
  startSimulationSession,
  stopSimulationSession,
  getSimulationStatus,
  getSimulationMessages,
  getSimulationBandwidth,
  getSimulationAlarms,
  exportSimulationData,
} from '@/api/simulation/simulation';

/**
 * 仿真API返回类型
 */
export interface UseSimulationApiReturn {
  loading: Ref<boolean>;
  error: Ref<string | null>;
  createSession: (
    projectId: number | string,
    versionId: number | string
  ) => Promise<SimulationSessionData>;
  startSession: (sessionId: string) => Promise<SimulationSessionCommandAccepted<'start'>>;
  stopSession: (sessionId: string) => Promise<SimulationSessionCommandAccepted<'stop'>>;
  fetchStatus: (sessionId: string) => Promise<SimulationStatusData | null>;
  fetchMessages: (sessionId: string, limit?: number) => Promise<SimulationMessage[]>;
  fetchBandwidth: (sessionId: string, portId?: string | null) => Promise<SimulationBandwidth[]>;
  fetchAlarms: (sessionId: string) => Promise<SimulationAlarm[]>;
  exportData: (
    sessionId: string,
    exportFormat?: string,
    dataType?: string
  ) => Promise<ExportDataResult>;
}

export function useSimulationApi(): UseSimulationApiReturn {
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);

  /**
   * 创建仿真会话
   */
  const createSession = async (
    projectId: number | string,
    versionId: number | string
  ): Promise<SimulationSessionData> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await createSimulationSession({
        projectId,
        versionId,
      });
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * 启动仿真
   */
  const startSession = async (
    sessionId: string
  ): Promise<SimulationSessionCommandAccepted<'start'>> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await startSimulationSession(sessionId);
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * 停止仿真
   */
  const stopSession = async (
    sessionId: string
  ): Promise<SimulationSessionCommandAccepted<'stop'>> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await stopSimulationSession(sessionId);
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * 获取仿真状态
   */
  const fetchStatus = async (sessionId: string): Promise<SimulationStatusData | null> => {
    try {
      const response = await getSimulationStatus(sessionId);
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取仿真状态失败:';
      return null;
    }
  };

  /**
   * 获取报文数据
   */
  const fetchMessages = async (
    sessionId: string,
    limit: number = 100
  ): Promise<SimulationMessage[]> => {
    try {
      const response = await getSimulationMessages(sessionId, limit);
      return response.items;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取报文数据失败:';
      return [];
    }
  };

  /**
   * 获取带宽数据
   */
  const fetchBandwidth = async (
    sessionId: string,
    portId: string | null = null
  ): Promise<SimulationBandwidth[]> => {
    try {
      const response = await getSimulationBandwidth(sessionId, portId);
      return response.items;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取带宽数据失败:';
      return [];
    }
  };

  /**
   * 获取告警数据
   */
  const fetchAlarms = async (sessionId: string): Promise<SimulationAlarm[]> => {
    try {
      const response = await getSimulationAlarms(sessionId);
      return response.items;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取告警数据失败:';
      return [];
    }
  };

  /**
   * 导出数据
   */
  const exportData = async (
    sessionId: string,
    exportFormat: string = 'json',
    dataType: string = 'messages'
  ): Promise<ExportDataResult> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await exportSimulationData(sessionId, {
        exportFormat,
        dataType,
      });
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  };

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
    exportData,
  };
}
