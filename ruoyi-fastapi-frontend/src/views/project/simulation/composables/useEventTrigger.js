/**
 * 事件触发 Composable
 *
 * 管理仿真过程中的自定义事件触发功能
 */
import { ref, computed } from "vue";
import {
  createEvent as createEventApi,
  updateEvent as updateEventApi,
  deleteEvent as deleteEventApi,
  triggerEvent as triggerEventApi,
  getEvents as getEventsApi,
} from "@/api/simulation/simulation";

/**
 * 事件条件类型
 */
export const ConditionType = {
  TIME: "time", // 时间点
  MESSAGE_COUNT: "message_count", // 报文数量
  BANDWIDTH_THRESHOLD: "bandwidth_threshold", // 带宽阈值
  MESSAGE_CONTENT: "message_content", // 特定报文内容
};

/**
 * 事件动作类型
 */
export const ActionType = {
  SEND_COMMAND: "send_command", // 发送指令（A设备给B设备发指令，如自检、上电等）
  SEND_MESSAGE: "send_message", // 发送特定报文
  INJECT_FAULT: "inject_fault", // 注入故障
  PAUSE: "pause", // 暂停仿真
  LOG: "log", // 记录日志
};

/**
 * 条件类型配置
 */
export const CONDITION_TYPE_CONFIG = {
  manual: {
    label: "手动触发",
    description: "无自动条件，需要手动触发",
    params: [],
  },
  [ConditionType.TIME]: {
    label: "时间点",
    description: "在指定仿真时间触发",
    params: [
      {
        name: "time",
        label: "触发时间(秒)",
        type: "number",
        default: 10,
        min: 0,
      },
    ],
  },
  [ConditionType.MESSAGE_COUNT]: {
    label: "报文数量",
    description: "当报文数量达到指定值时触发",
    params: [
      {
        name: "count",
        label: "报文数量",
        type: "number",
        default: 100,
        min: 1,
      },
    ],
  },
  [ConditionType.BANDWIDTH_THRESHOLD]: {
    label: "带宽阈值",
    description: "当带宽超过指定阈值时触发",
    params: [
      {
        name: "threshold",
        label: "阈值(%)",
        type: "number",
        default: 80,
        min: 0,
        max: 100,
      },
      { name: "portId", label: "端口ID", type: "string", default: "" },
    ],
  },
  [ConditionType.MESSAGE_CONTENT]: {
    label: "报文内容",
    description: "当收到包含指定内容的报文时触发",
    params: [
      { name: "pattern", label: "匹配模式", type: "string", default: "" },
      {
        name: "protocolType",
        label: "协议类型",
        type: "select",
        options: ["1553B", "CAN", "RS422", "LAN"],
      },
    ],
  },
};

/**
 * 动作类型配置
 */
export const ACTION_TYPE_CONFIG = {
  [ActionType.SEND_COMMAND]: {
    label: "发送指令",
    description: "A设备给B设备发送指令（自检、上电、复位等）",
    params: [
      {
        name: "sourceNodeId",
        label: "源设备",
        type: "node",
        description: "发送指令的设备",
      },
      {
        name: "targetNodeId",
        label: "目标设备",
        type: "node",
        description: "接收指令的设备",
      },
      {
        name: "commandType",
        label: "指令类型",
        type: "select",
        options: [
          { value: "self_check", label: "自检指令" },
          { value: "power_on", label: "上电指令" },
          { value: "power_off", label: "断电指令" },
          { value: "reset", label: "复位指令" },
          { value: "status_query", label: "状态查询" },
          { value: "heartbeat", label: "心跳" },
          { value: "custom", label: "自定义报文" },
        ],
        default: "self_check",
      },
      {
        name: "payload",
        label: "报文内容(Hex)",
        type: "string",
        description: "自定义报文时填写，如: AA55010100",
        condition: 'commandType === "custom"',
      },
      {
        name: "protocolType",
        label: "协议类型",
        type: "select",
        options: ["1553B", "CAN", "RS422", "RS485", "LAN"],
        default: "LAN",
      },
    ],
  },
  [ActionType.SEND_MESSAGE]: {
    label: "发送报文",
    description: "发送指定的报文",
    params: [
      { name: "sourceNodeId", label: "源节点", type: "node" },
      { name: "targetNodeId", label: "目标节点", type: "node" },
      { name: "payload", label: "报文内容(Hex)", type: "string" },
      {
        name: "protocolType",
        label: "协议类型",
        type: "select",
        options: ["1553B", "CAN", "RS422", "RS485", "LAN"],
        default: "LAN",
      },
    ],
  },
  [ActionType.INJECT_FAULT]: {
    label: "注入故障",
    description: "注入指定类型的故障",
    params: [
      {
        name: "faultType",
        label: "故障类型",
        type: "select",
        options: [
          { value: "disconnect", label: "链路断开" },
          { value: "error_frame", label: "错误帧" },
          { value: "packet_loss", label: "丢包" },
          { value: "delay", label: "延迟" },
          { value: "device_failure", label: "设备故障" },
        ],
      },
      {
        name: "targetId",
        label: "目标ID",
        type: "string",
        description: "链路ID或节点ID",
      },
    ],
  },
  [ActionType.PAUSE]: {
    label: "暂停仿真",
    description: "暂停仿真运行",
    params: [],
  },
  [ActionType.LOG]: {
    label: "记录日志",
    description: "记录自定义日志信息",
    params: [
      { name: "message", label: "日志内容", type: "string" },
      {
        name: "level",
        label: "日志级别",
        type: "select",
        options: [
          { value: "info", label: "信息" },
          { value: "warning", label: "警告" },
          { value: "error", label: "错误" },
        ],
        default: "info",
      },
    ],
  },
};

/**
 * 检查事件条件是否匹配
 * @param {Object} condition - 条件配置
 * @param {Object} state - 当前仿真状态
 * @returns {boolean} 是否匹配
 */
export function matchCondition(condition, state) {
  if (!condition || !state) {
    return false;
  }

  const { type, value } = condition;

  switch (type) {
    case ConditionType.TIME:
      return state.elapsedTime >= value.time;

    case ConditionType.MESSAGE_COUNT:
      return state.messageCount >= value.count;

    case ConditionType.BANDWIDTH_THRESHOLD:
      if (value.portId) {
        const portBandwidth = state.bandwidthByPort?.[value.portId];
        return portBandwidth && portBandwidth.loadPercent >= value.threshold;
      }
      // 检查任意端口
      return Object.values(state.bandwidthByPort || {}).some(
        (b) => b.loadPercent >= value.threshold,
      );

    case ConditionType.MESSAGE_CONTENT:
      if (!state.latestMessage) return false;
      if (
        value.protocolType &&
        state.latestMessage.protocolType !== value.protocolType
      ) {
        return false;
      }
      if (value.pattern) {
        const content = state.latestMessage.payloadHex || "";
        return content.includes(value.pattern);
      }
      return true;

    default:
      return false;
  }
}

/**
 * 事件触发 Composable
 * @param {Ref<string>} sessionId - 会话ID
 * @returns {Object} 事件触发方法和状态
 */
export function useEventTrigger(sessionId) {
  // 事件列表
  const eventList = ref([]);

  // 加载中状态
  const loading = ref(false);

  // 计算属性：待触发事件数量
  const pendingEventCount = computed(() => {
    return eventList.value.filter((e) => e.status === "pending").length;
  });

  // 计算属性：已触发事件数量
  const triggeredEventCount = computed(() => {
    return eventList.value.filter((e) => e.status === "triggered").length;
  });

  /**
   * 加载事件列表
   */
  async function loadEvents() {
    if (!sessionId.value) return;

    loading.value = true;
    try {
      const response = await getEventsApi(sessionId.value);
      eventList.value = response.data || [];
    } catch (error) {
      console.error("加载事件列表失败:", error);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 创建事件
   * @param {Object} config - 事件配置
   * @returns {Promise<Object>} 事件信息
   */
  async function createEvent(config) {
    if (!sessionId.value) {
      throw new Error("仿真会话不存在");
    }

    const { name, condition, action } = config;

    // 验证条件类型
    if (!CONDITION_TYPE_CONFIG[condition.type]) {
      throw new Error(`不支持的条件类型: ${condition.type}`);
    }

    // 验证动作类型
    if (!ACTION_TYPE_CONFIG[action.type]) {
      throw new Error(`不支持的动作类型: ${action.type}`);
    }

    const response = await createEventApi(sessionId.value, {
      name,
      conditionType: condition.type,
      conditionValue: condition.value,
      actionType: action.type,
      actionParams: action.params,
    });

    const event = {
      eventId: response.data?.eventId || `event-${Date.now()}`,
      name,
      condition,
      action,
      status: "pending",
      triggerCount: 0,
      createTime: Date.now(),
    };

    eventList.value.push(event);

    return event;
  }

  /**
   * 更新事件
   * @param {string} eventId - 事件ID
   * @param {Object} config - 事件配置
   */
  async function updateEvent(eventId, config) {
    if (!sessionId.value) {
      throw new Error("仿真会话不存在");
    }

    await updateEventApi(sessionId.value, eventId, config);

    // 更新本地状态
    const event = eventList.value.find((e) => e.eventId === eventId);
    if (event) {
      Object.assign(event, config);
    }
  }

  /**
   * 删除事件
   * @param {string} eventId - 事件ID
   */
  async function deleteEvent(eventId) {
    if (!sessionId.value) {
      throw new Error("仿真会话不存在");
    }

    await deleteEventApi(sessionId.value, eventId);

    // 从本地列表移除
    const index = eventList.value.findIndex((e) => e.eventId === eventId);
    if (index !== -1) {
      eventList.value.splice(index, 1);
    }
  }

  /**
   * 手动触发事件
   * @param {string} eventId - 事件ID
   */
  async function triggerEvent(eventId) {
    if (!sessionId.value) {
      throw new Error("仿真会话不存在");
    }

    await triggerEventApi(sessionId.value, eventId);

    // 更新本地状态
    const event = eventList.value.find((e) => e.eventId === eventId);
    if (event) {
      event.status = "triggered";
      event.triggerCount += 1;
      event.lastTriggerTime = Date.now();
    }
  }

  /**
   * 启用/禁用事件
   * @param {string} eventId - 事件ID
   * @param {boolean} enabled - 是否启用
   */
  async function setEventEnabled(eventId, enabled) {
    const event = eventList.value.find((e) => e.eventId === eventId);
    if (event) {
      event.status = enabled ? "pending" : "disabled";
      await updateEvent(eventId, { status: event.status });
    }
  }

  /**
   * 检查并触发匹配的事件
   * @param {Object} state - 当前仿真状态
   */
  function checkAndTriggerEvents(state) {
    const pendingEvents = eventList.value.filter((e) => e.status === "pending");

    for (const event of pendingEvents) {
      if (matchCondition(event.condition, state)) {
        triggerEvent(event.eventId).catch(console.error);
      }
    }
  }

  /**
   * 重置事件列表
   */
  function reset() {
    eventList.value = [];
  }

  return {
    // 状态
    eventList,
    loading,
    pendingEventCount,
    triggeredEventCount,

    // 方法
    loadEvents,
    createEvent,
    updateEvent,
    deleteEvent,
    triggerEvent,
    setEventEnabled,
    checkAndTriggerEvents,
    reset,
  };
}

export default useEventTrigger;
