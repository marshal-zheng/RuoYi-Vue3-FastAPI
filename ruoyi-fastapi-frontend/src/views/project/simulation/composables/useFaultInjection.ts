/**
 * 故障注入 Composable
 *
 * 管理仿真过程中的故障注入功能
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue';
import {
  injectFault as injectFaultApi,
  clearFault as clearFaultApi,
  clearAllFaults as clearAllFaultsApi,
  getFaults as getFaultsApi,
} from '@/api/simulation/simulation';

/**
 * 故障类型枚举
 */
export const FaultType = {
  DISCONNECT: 'disconnect',
  DEVICE_FAILURE: 'device_failure',
  PACKET_LOSS: 'packet_loss',
  DELAY: 'delay',
  BANDWIDTH_LIMIT: 'bandwidth_limit',
  PAYLOAD_CORRUPT: 'payload_corrupt',
  NOISE_FRAME: 'noise_frame',
  ERROR_FRAME: 'error_frame',
} as const;

export type FaultTypeValue = (typeof FaultType)[keyof typeof FaultType];

interface FaultParam {
  name: string;
  label: string;
  type: 'number' | 'string';
  default?: number | string;
  min?: number;
  max?: number;
}

interface FaultTypeConfig {
  label: string;
  icon: string;
  description: string;
  targetType: 'edge' | 'node';
  params?: FaultParam[];
}

interface Fault {
  faultId: string;
  sessionId?: string;
  faultType: string;
  targetType: string;
  targetId: string;
  targetKey: string;
  targetName?: string;
  params: Record<string, any>;
  status: string;
  startAt?: number;
  endAt?: number;
  priority?: number;
  createTime?: number;
  updateTime?: number;
  _action?: 'created' | 'updated';
}

interface FaultConfig {
  type: FaultTypeValue;
  targetId: string;
  targetType: 'edge' | 'node';
  params?: Record<string, any>;
  targetName?: string;
  targetLabel?: string;
}

interface FaultEvent {
  action?: string;
  fault?: any;
  [key: string]: any;
}

/**
 * 故障类型配置
 */
export const FAULT_TYPE_CONFIG: Record<FaultTypeValue, FaultTypeConfig> = {
  [FaultType.DISCONNECT]: {
    label: '断开连接',
    icon: 'Disconnect',
    description: '模拟链路断开，停止所有报文传输',
    targetType: 'edge',
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
      {
        name: 'durationMs',
        label: '持续时长(ms)',
        type: 'number',
        default: 5000,
        min: 100,
        max: 600000,
      },
      {
        name: 'startAfterMs',
        label: '延迟生效(ms)',
        type: 'number',
        default: 0,
        min: 0,
        max: 600000,
      },
    ],
  },
  [FaultType.DELAY]: {
    label: '注入延迟',
    icon: 'Timer',
    description: '为报文传输添加额外延迟',
    targetType: 'edge',
    params: [
      { name: 'delayMs', label: '延迟(ms)', type: 'number', default: 100, min: 1, max: 10000 },
      { name: 'jitterMs', label: '抖动(ms)', type: 'number', default: 10, min: 0, max: 5000 },
      {
        name: 'durationMs',
        label: '持续时长(ms)',
        type: 'number',
        default: 5000,
        min: 100,
        max: 600000,
      },
      {
        name: 'startAfterMs',
        label: '延迟生效(ms)',
        type: 'number',
        default: 0,
        min: 0,
        max: 600000,
      },
    ],
  },
  [FaultType.BANDWIDTH_LIMIT]: {
    label: '带宽限速',
    icon: 'Link',
    description: '限制链路QPS/带宽，模拟拥塞',
    targetType: 'edge',
    params: [
      {
        name: 'messagesPerSecond',
        label: '最大QPS',
        type: 'number',
        default: 20,
        min: 1,
        max: 10000,
      },
      {
        name: 'durationMs',
        label: '持续时长(ms)',
        type: 'number',
        default: 5000,
        min: 100,
        max: 600000,
      },
    ],
  },
  [FaultType.PAYLOAD_CORRUPT]: {
    label: '数据篡改',
    icon: 'Warning',
    description: '随机翻转payload位，模拟bit flip',
    targetType: 'edge',
    params: [
      { name: 'bitFlipCount', label: '翻转位数', type: 'number', default: 2, min: 1, max: 32 },
      {
        name: 'durationMs',
        label: '持续时长(ms)',
        type: 'number',
        default: 5000,
        min: 100,
        max: 600000,
      },
    ],
  },
  [FaultType.NOISE_FRAME]: {
    label: '噪声帧',
    icon: 'Warning',
    description: '注入无效帧/随机噪声',
    targetType: 'edge',
    params: [
      { name: 'length', label: '噪声字节数', type: 'number', default: 16, min: 1, max: 128 },
      {
        name: 'durationMs',
        label: '持续时长(ms)',
        type: 'number',
        default: 3000,
        min: 100,
        max: 600000,
      },
    ],
  },
  [FaultType.ERROR_FRAME]: {
    label: '错误帧',
    icon: 'Warning',
    description: '协议错误帧/仲裁失败模拟',
    targetType: 'edge',
    params: [{ name: 'count', label: '错误帧数量', type: 'number', default: 5, min: 1, max: 200 }],
  },
};

/**
 * 故障注入 Composable
 * @param {Ref<string>} sessionId - 会话ID
 * @returns {Object} 故障注入方法和状态
 */
export function useFaultInjection(sessionId: Ref<string | null>) {
  // 活跃的故障列表
  const faults: Ref<Fault[]> = ref([]);
  const faultEvents: Ref<FaultEvent[]> = ref([]);
  const loading: Ref<boolean> = ref(false);

  // 计算属性：按目标分组的故障
  const faultsByTarget: ComputedRef<Record<string, Fault[]>> = computed(() => {
    const grouped: Record<string, Fault[]> = {};
    faults.value.forEach((fault) => {
      const key = fault.targetKey || fault.targetId || fault.target;
      if (!key) return;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(fault);
    });
    return grouped;
  });

  // 计算属性：活跃故障数量
  const activeFaultCount: ComputedRef<number> = computed(() => {
    return faults.value.filter((f) => f.status === 'active').length;
  });

  function normalizeFault(raw: any): Fault | null {
    if (!raw) return null;
    const fault: Fault = {
      faultId: raw.faultId || raw.fault_id || raw.id,
      sessionId: raw.sessionId || raw.session_id,
      faultType: raw.faultType || raw.fault_type || raw.type,
      targetType: raw.targetType || raw.target_type || raw.targetType || 'edge',
      targetId: raw.targetId || raw.target_id || raw.targetId,
      targetKey: raw.targetId || raw.target_id || raw.targetId,
      targetName:
        raw.targetName ||
        raw.target_name ||
        raw.target_label ||
        raw.targetAlias ||
        raw.params?.target_name ||
        raw.params?.targetName,
      params: raw.params || {},
      status: raw.status || 'active',
      startAt: raw.startAt || raw.start_at,
      endAt: raw.endAt || raw.end_at,
      priority: raw.priority ?? 0,
      createTime: raw.createTime || raw.create_time,
      updateTime: raw.updateTime || raw.update_time,
    };
    return fault;
  }

  function upsertFault(local: Fault) {
    const idx = faults.value.findIndex((f) => f.faultId === local.faultId);
    if (idx >= 0) {
      faults.value[idx] = { ...faults.value[idx], ...local };
    } else {
      faults.value.push(local);
    }
  }

  async function fetchFaults(): Promise<Fault[]> {
    if (!sessionId.value) return [];
    loading.value = true;
    try {
      // http 客户端已解包 payload.data，res 直接是故障列表
      const res = await getFaultsApi(sessionId.value);
      const list = Array.isArray(res) ? res : [];
      // 只保留待生效和生效中的故障，避免已清除/过期占位
      faults.value = list
        .map(normalizeFault)
        .filter((f): f is Fault => f !== null && (f.status === 'active' || f.status === 'pending'));
      return faults.value;
    } finally {
      loading.value = false;
    }
  }

  /**
   * 注入故障
   * @param {Object} config - 故障配置
   * @returns {Promise<Object>} 故障信息（包含 _action: 'created'|'updated' 标识）
   */
  async function injectFault(config: FaultConfig): Promise<Fault> {
    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    const { type, targetId, targetType, params = {}, targetName, targetLabel } = config;

    if (!FAULT_TYPE_CONFIG[type]) {
      throw new Error(`不支持的故障类型: ${type}`);
    }

    const expectedTargetType = FAULT_TYPE_CONFIG[type].targetType;
    if (targetType !== expectedTargetType) {
      throw new Error(`故障类型 ${type} 只能应用于 ${expectedTargetType}`);
    }

    // 始终调用后端，后端实现幂等（同 target+type 会更新而非新增）
    const payload = {
      faultType: type,
      targetId,
      targetType,
      params: {
        ...params,
        targetName: targetName || targetLabel,
        target_name: targetName || targetLabel,
      },
      // 便于后端记录友好名称
      targetName: targetName || targetLabel,
    };

    const response = await injectFaultApi(sessionId.value, payload);
    // 后端返回已解包的数据
    const raw = response || { ...payload, faultId: `fault-${Date.now()}` };
    const fault = normalizeFault(raw);
    if (fault) {
      // 保留后端返回的 _action 标识
      fault._action = raw._action || 'created';
      // 覆盖/补充前端友好名称
      fault.targetName = fault.targetName || targetName || targetLabel;
      upsertFault(fault);
    }
    return fault!;
  }

  /**
   * 清除故障
   * @param {string} faultId - 故障ID
   */
  async function clearFault(faultId: string) {
    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    await clearFaultApi(sessionId.value, faultId);

    // 直接从列表移除
    const idx = faults.value.findIndex((f) => f.faultId === faultId);
    if (idx >= 0) faults.value.splice(idx, 1);
  }

  /**
   * 清除所有故障（调用后端批量清除接口）
   */
  async function clearAllFaults() {
    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    await clearAllFaultsApi(sessionId.value);

    // 直接清空列表
    faults.value = [];
  }

  /**
   * 清除指定目标的所有故障
   * @param {string} targetId - 目标ID
   */
  async function clearFaultsByTarget(targetId: string) {
    const targetFaults = faults.value.filter(
      (f) => f.targetId === targetId && f.status === 'active'
    );

    for (const fault of targetFaults) {
      await clearFault(fault.faultId);
    }
  }

  /**
   * 检查目标是否有活跃故障
   * @param {string} targetId - 目标ID
   * @returns {boolean}
   */
  function hasActiveFault(targetId: string): boolean {
    return faults.value.some((f) => f.targetId === targetId && f.status === 'active');
  }

  /**
   * 获取目标的活跃故障
   * @param {string} targetId - 目标ID
   * @returns {Array}
   */
  function getActiveFaults(targetId: string): Fault[] {
    return faults.value.filter((f) => f.targetId === targetId && f.status === 'active');
  }

  /**
   * 重置故障列表
   */
  function reset() {
    faults.value = [];
    faultEvents.value = [];
  }

  function ingestFaultEvents(events: FaultEvent[] = []) {
    events.forEach((evt) => {
      const fault = normalizeFault(evt?.fault);
      if (!fault) return;
      const action = evt?.action;
      // 维护事件窗口
      faultEvents.value.push({ ...evt, fault });
      if (faultEvents.value.length > 200) {
        faultEvents.value.splice(0, faultEvents.value.length - 200);
      }

      // 清除/过期事件：直接移除列表
      if (action === 'cleared' || action === 'expired') {
        const idx = faults.value.findIndex((f) => f.faultId === fault.faultId);
        if (idx >= 0) faults.value.splice(idx, 1);
        return;
      }

      if (action === 'created' || action === 'updated' || action === 'activated') {
        upsertFault(fault);
      }
    });
  }

  return {
    // 状态
    faults,
    faultsByTarget,
    activeFaultCount,
    faultEvents,
    loading,

    // 方法
    injectFault,
    clearFault,
    clearAllFaults,
    clearFaultsByTarget,
    hasActiveFault,
    getActiveFaults,
    reset,
    fetchFaults,
    ingestFaultEvents,
  };
}

export default useFaultInjection;
