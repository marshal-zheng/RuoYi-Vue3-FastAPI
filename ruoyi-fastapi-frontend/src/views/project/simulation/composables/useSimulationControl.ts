/**
 * 仿真控制 Composable
 *
 * 管理仿真会话的生命周期和状态
 */
import { ref, reactive, computed, onUnmounted, isRef, type Ref, type ComputedRef } from 'vue';
import type { SimulationSessionOptions } from '@/api/simulation/types';
import {
  createSimulationSession,
  startSimulationSession,
  pauseSimulationSession,
  resumeSimulationSession,
  stopSimulationSession,
  stepSimulationSession,
  setSimulationSpeed,
} from '@/api/simulation/simulation';

/**
 * 仿真状态枚举
 */
export const SimulationStatus = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  STOPPED: 'stopped',
} as const;

export type SimulationStatusType = (typeof SimulationStatus)[keyof typeof SimulationStatus];

/**
 * 仿真速度范围
 */
export const SpeedRange = {
  MIN: 0.5,
  MAX: 4.0,
  DEFAULT: 1.0,
};

interface SimulationState {
  status: SimulationStatusType;
  elapsedTime: number;
  speed: number;
  messageCount: number;
  alarmCount: number;
  startTime: number | null;
}

type SessionOptions = SimulationSessionOptions;

interface StatusUpdate {
  status?: SimulationStatusType;
  speed?: number;
  elapsedTime?: number;
  messageCount?: number;
  alarmCount?: number;
}

interface StatsUpdate {
  messageCount?: number;
  alarmCount?: number;
  elapsedTime?: number;
}

/**
 * 限制速度值在有效范围内
 * @param {number} speed - 速度值
 * @returns {number} 限制后的速度值
 */
export function clampSpeed(speed: number): number {
  if (typeof speed !== 'number' || isNaN(speed)) {
    return SpeedRange.DEFAULT;
  }
  return Math.max(SpeedRange.MIN, Math.min(SpeedRange.MAX, speed));
}

/**
 * 验证状态转换是否有效
 * @param {string} currentStatus - 当前状态
 * @param {string} targetStatus - 目标状态
 * @returns {boolean} 是否可以转换
 */
export function isValidTransition(
  currentStatus: SimulationStatusType,
  targetStatus: SimulationStatusType
): boolean {
  const validTransitions: Record<SimulationStatusType, SimulationStatusType[]> = {
    [SimulationStatus.IDLE]: [SimulationStatus.RUNNING],
    [SimulationStatus.RUNNING]: [SimulationStatus.PAUSED, SimulationStatus.STOPPED],
    [SimulationStatus.PAUSED]: [SimulationStatus.RUNNING, SimulationStatus.STOPPED],
    [SimulationStatus.STOPPED]: [SimulationStatus.RUNNING],
  };

  const allowed = validTransitions[currentStatus] || [];
  return allowed.includes(targetStatus);
}

/**
 * 仿真控制 Composable
 * @param {Ref<number>} projectId - 项目ID
 * @param {Ref<number|undefined>} versionId - 版本ID
 * @returns {Object} 仿真控制方法和状态
 */
export function useSimulationControl(
  projectId: Ref<number> | number,
  versionId?: Ref<number | undefined> | number
) {
  const projectIdRef = isRef(projectId) ? projectId : ref(projectId);
  const versionIdRef = isRef(versionId) ? versionId : ref(versionId);

  // 会话ID
  const sessionId: Ref<string | null> = ref(null);

  // 仿真状态
  const simulationState = reactive<SimulationState>({
    status: SimulationStatus.IDLE,
    elapsedTime: 0,
    speed: SpeedRange.DEFAULT,
    messageCount: 0,
    alarmCount: 0,
    startTime: null,
  });

  // 计时器
  let timerInterval: number | null = null;

  // 计算属性
  const isRunning: ComputedRef<boolean> = computed(
    () => simulationState.status === SimulationStatus.RUNNING
  );
  const isPaused: ComputedRef<boolean> = computed(
    () => simulationState.status === SimulationStatus.PAUSED
  );
  const isStopped: ComputedRef<boolean> = computed(
    () => simulationState.status === SimulationStatus.STOPPED
  );
  const isIdle: ComputedRef<boolean> = computed(
    () => simulationState.status === SimulationStatus.IDLE
  );
  const currentTime = computed({
    get: () => simulationState.elapsedTime,
    set: (value: number) => {
      simulationState.elapsedTime = value;
    },
  });
  const speed = computed({
    get: () => simulationState.speed,
    set: (value: number) => {
      simulationState.speed = value;
    },
  });
  const formattedTime = computed(() => {
    const totalMilliseconds = Math.max(0, simulationState.elapsedTime) * 1000;
    const hours = Math.floor(totalMilliseconds / 3600000);
    const minutes = Math.floor((totalMilliseconds % 3600000) / 60000);
    const seconds = Math.floor((totalMilliseconds % 60000) / 1000);
    const milliseconds = Math.floor(totalMilliseconds % 1000);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(
      seconds
    ).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
  });

  // 最近一次前端主动设置速度的时间戳（用于防止状态回写冲掉本地设置）
  const lastSpeedSetAt: Ref<number> = ref(0);

  /**
   * 启动计时器
   */
  function startTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    const startTimestamp = Date.now() - simulationState.elapsedTime * 1000;

    timerInterval = window.setInterval(() => {
      if (simulationState.status === SimulationStatus.RUNNING) {
        const elapsed = (Date.now() - startTimestamp) / 1000;
        simulationState.elapsedTime = elapsed * simulationState.speed;
      }
    }, 100); // 每100ms更新一次
  }

  /**
   * 停止计时器
   */
  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  /**
   * 创建仿真会话
   */
  async function createSession(options: SessionOptions = {}): Promise<string> {
    const response = await createSimulationSession({
      projectId: projectIdRef.value,
      versionId: versionIdRef?.value,
      ...options,
    });

    if (response?.sessionId) {
      sessionId.value = response.sessionId;
      return response.sessionId;
    }

    throw new Error('创建仿真会话失败');
  }

  /**
   * 启动仿真
   */
  async function start(options: SessionOptions = {}) {
    if (!isValidTransition(simulationState.status, SimulationStatus.RUNNING)) {
      throw new Error('当前状态不允许启动仿真');
    }

    // 如果没有会话，先创建
    if (!sessionId.value) {
      await createSession(options);
    }

    // 启动仿真
    await startSimulationSession(sessionId.value!, {
      speed: simulationState.speed,
      ...options,
    });

    // 更新状态
    simulationState.status = SimulationStatus.RUNNING;
    simulationState.startTime = Date.now();

    // 启动计时器
    startTimer();
  }

  /**
   * 暂停仿真
   */
  async function pause() {
    if (!isValidTransition(simulationState.status, SimulationStatus.PAUSED)) {
      throw new Error('当前状态不允许暂停仿真');
    }

    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    await pauseSimulationSession(sessionId.value);

    simulationState.status = SimulationStatus.PAUSED;
    stopTimer();
  }

  /**
   * 继续仿真
   */
  async function resume() {
    if (!isValidTransition(simulationState.status, SimulationStatus.RUNNING)) {
      throw new Error('当前状态不允许继续仿真');
    }

    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    await resumeSimulationSession(sessionId.value);

    simulationState.status = SimulationStatus.RUNNING;
    startTimer();
  }

  /**
   * 停止仿真
   */
  async function stop() {
    if (!isValidTransition(simulationState.status, SimulationStatus.STOPPED)) {
      // 如果是 idle 状态，直接返回
      if (simulationState.status === SimulationStatus.IDLE) {
        return;
      }
      throw new Error('当前状态不允许停止仿真');
    }

    if (sessionId.value) {
      await stopSimulationSession(sessionId.value);
    }

    simulationState.status = SimulationStatus.STOPPED;
    stopTimer();
  }

  /**
   * 单步执行
   */
  async function step() {
    if (simulationState.status !== SimulationStatus.PAUSED) {
      throw new Error('只有在暂停状态下才能单步执行');
    }

    if (!sessionId.value) {
      throw new Error('仿真会话不存在');
    }

    await stepSimulationSession(sessionId.value);

    // 更新时间（假设每步100ms）
    simulationState.elapsedTime += 0.1;
  }

  /**
   * 设置仿真速度
   */
  async function setSpeed(speed: number) {
    const clampedSpeed = clampSpeed(speed);
    const prevSpeed = simulationState.speed;
    simulationState.speed = clampedSpeed;
    lastSpeedSetAt.value = Date.now();

    // 后端对 <1x 可能异常，传输时最低保持 1x，前端仍按 clampedSpeed 展示/动画
    const backendSpeed = Math.max(1, clampedSpeed);

    // 仅在有有效会话且处于运行/暂停时下发后端
    if (sessionId.value && (isRunning.value || isPaused.value)) {
      try {
        await setSimulationSpeed(sessionId.value, backendSpeed);
      } catch (err) {
        // 回滚到上一次速度，避免卡死
        simulationState.speed = prevSpeed;
        throw err;
      }
    }
  }

  function updateTime(time: number) {
    if (time < 0) {
      throw new Error('仿真时间不能为负数');
    }
    simulationState.elapsedTime = time;
  }

  /**
   * 同步后端状态（WS 状态推送）
   */
  function syncStatus(status: StatusUpdate) {
    if (!status || typeof status !== 'object') return;

    if (status.status) {
      simulationState.status = status.status;
    }
    if (status.speed !== undefined) {
      const now = Date.now();
      const incoming = clampSpeed(Number(status.speed));
      // 如果刚刚（1秒内）本地设置过速度，则不被后端回写立即覆盖
      if (now - lastSpeedSetAt.value > 1000) {
        simulationState.speed = incoming;
      }
    }
    if (status.elapsedTime !== undefined) {
      simulationState.elapsedTime = Number(status.elapsedTime) || 0;
    }
    if (status.messageCount !== undefined) {
      simulationState.messageCount = Number(status.messageCount) || 0;
    }
    if (status.alarmCount !== undefined) {
      simulationState.alarmCount = Number(status.alarmCount) || 0;
    }
  }

  /**
   * 重置状态
   */
  function reset() {
    stopTimer();
    sessionId.value = null;
    simulationState.status = SimulationStatus.IDLE;
    simulationState.elapsedTime = 0;
    simulationState.speed = SpeedRange.DEFAULT;
    simulationState.messageCount = 0;
    simulationState.alarmCount = 0;
    simulationState.startTime = null;
  }

  /**
   * 更新统计数据
   */
  function updateStats(stats: StatsUpdate) {
    if (stats.messageCount !== undefined) {
      simulationState.messageCount = stats.messageCount;
    }
    if (stats.alarmCount !== undefined) {
      simulationState.alarmCount = stats.alarmCount;
    }
    if (stats.elapsedTime !== undefined) {
      simulationState.elapsedTime = stats.elapsedTime;
    }
  }

  // 清理
  onUnmounted(() => {
    stopTimer();
  });

  return {
    // 状态
    sessionId,
    simulationState,
    isRunning,
    isPaused,
    isStopped,
    isIdle,
    currentTime,
    speed,
    formattedTime,

    // 方法
    createSession,
    start,
    pause,
    resume,
    stop,
    step,
    setSpeed,
    updateTime,
    syncStatus,
    reset,
    updateStats,
  };
}

export default useSimulationControl;
