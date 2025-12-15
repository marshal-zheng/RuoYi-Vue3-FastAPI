/**
 * 事件触发相关下拉框选项配置
 * 用于 EventFormDialog、EventTriggerPanel 等组件
 */

// 触发条件类型选项
export const conditionTypeOptions = [
  { value: "manual", label: "手动触发（无自动条件）" },
  { value: "time", label: "时间点" },
  { value: "message_count", label: "报文数量" },
  { value: "bandwidth_threshold", label: "带宽阈值" },
];

// 动作类型选项
export const actionTypeOptions = [
  { value: "send_command", label: "发送指令（设备间通信）" },
  { value: "send_message", label: "发送报文" },
  { value: "inject_fault", label: "注入故障" },
  { value: "pause", label: "暂停仿真" },
  { value: "log", label: "记录日志" },
];

// 指令类型选项
export const commandTypeOptions = [
  { value: "self_check", label: "自检指令" },
  { value: "power_on", label: "上电指令" },
  { value: "power_off", label: "断电指令" },
  { value: "reset", label: "复位指令" },
  { value: "status_query", label: "状态查询" },
  { value: "heartbeat", label: "心跳" },
  { value: "custom", label: "自定义报文" },
];

// 协议类型选项
export const protocolTypeOptions = [
  { value: "LAN", label: "以太网(LAN)" },
  { value: "1553B", label: "1553B" },
  { value: "CAN", label: "CAN" },
  { value: "RS422", label: "RS422" },
  { value: "RS485", label: "RS485" },
];

// 故障类型选项
export const faultTypeOptions = [
  { value: "disconnect", label: "链路断开" },
  { value: "error_frame", label: "错误帧" },
  { value: "packet_loss", label: "丢包" },
  { value: "delay", label: "延迟" },
  { value: "device_failure", label: "设备故障" },
];

// 日志级别选项
export const logLevelOptions = [
  { value: "info", label: "信息" },
  { value: "warning", label: "警告" },
  { value: "error", label: "错误" },
];

// 指令类型映射（用于显示）
export const commandTypeLabels = {
  self_check: "自检",
  power_on: "上电",
  power_off: "断电",
  reset: "复位",
  status_query: "状态查询",
  heartbeat: "心跳",
  custom: "自定义报文",
};

// 事件状态映射
export const eventStatusMap = {
  pending: { type: "info", label: "待触发" },
  triggered: { type: "success", label: "已触发" },
  disabled: { type: "warning", label: "已禁用" },
};

export default {
  conditionTypeOptions,
  actionTypeOptions,
  commandTypeOptions,
  protocolTypeOptions,
  faultTypeOptions,
  logLevelOptions,
  commandTypeLabels,
  eventStatusMap,
};
