/**
 * 仿真数据管理 Composable
 * 优化 WebSocket 数据更新性能
 */
import { shallowRef, onUnmounted } from 'vue';

// 数据限制配置
const MAX_BANDWIDTH_POINTS = 120; // 最多保留120个数据点（2分钟，每秒1个）
const MAX_MESSAGES = 50; // 最多保留50条报文
const MAX_ALARMS = 50; // 最多保留50条告警
const BANDWIDTH_TIME_WINDOW = 120; // 120秒时间窗口

export function useSimulationDataManager() {
  // 使用 shallowRef 减少深度监听开销
  const bandwidthData = shallowRef([]);
  const messageData = shallowRef([]);
  const alarmData = shallowRef([]);

  // 用于去重的Set
  const seenMessageIds = new Set();
  const seenBandwidthKeys = new Set();

  /**
   * 更新带宽数据（增量追加，自动去重和清理）
   */
  function updateBandwidthData(newData) {
    if (!newData || newData.length === 0) return;

    const now = Date.now() / 1000;
    const cutoffTime = now - BANDWIDTH_TIME_WINDOW;

    // 过滤重复数据
    const uniqueNew = newData.filter((item) => {
      const key = `${item.timestamp}-${item.portId || 'all'}`;
      if (seenBandwidthKeys.has(key)) return false;
      seenBandwidthKeys.add(key);
      return true;
    });

    if (uniqueNew.length === 0) return;

    // 合并新数据
    const merged = [...bandwidthData.value, ...uniqueNew];

    // 过滤旧数据并限制数量
    const filtered = merged
      .filter((item) => item.timestamp >= cutoffTime)
      .slice(-MAX_BANDWIDTH_POINTS);

    // 清理去重集合中的旧键
    if (seenBandwidthKeys.size > MAX_BANDWIDTH_POINTS * 2) {
      seenBandwidthKeys.clear();
      filtered.forEach((item) => {
        seenBandwidthKeys.add(`${item.timestamp}-${item.portId || 'all'}`);
      });
    }

    bandwidthData.value = filtered;
  }

  /**
   * 更新报文数据（增量追加，自动去重）
   */
  function updateMessageData(newData) {
    if (!newData || newData.length === 0) return;

    // 过滤重复数据并格式化
    const uniqueNew = newData
      .filter((msg) => {
        if (!msg.messageId || seenMessageIds.has(msg.messageId)) return false;
        seenMessageIds.add(msg.messageId);
        return true;
      })
      .map((msg) => ({
        messageId: msg.messageId,
        sendTimestamp: msg.sendTimestamp || msg.timestamp,
        senderNodeId: msg.senderNodeId || msg.sender,
        senderPortId: msg.senderPortId,
        receiverNodeId: msg.receiverNodeId || msg.receiver,
        receiverPortId: msg.receiverPortId,
        protocolType: msg.protocolType || msg.protocol,
        sizeBytes: msg.sizeBytes || msg.size,
        receiveTimestamp: msg.receiveTimestamp,
      }));

    if (uniqueNew.length === 0) return;

    // 追加并限制数量
    const merged = [...messageData.value, ...uniqueNew].slice(-MAX_MESSAGES);

    // 清理去重集合
    if (seenMessageIds.size > MAX_MESSAGES * 2) {
      seenMessageIds.clear();
      merged.forEach((msg) => seenMessageIds.add(msg.messageId));
    }

    messageData.value = merged;
  }

  /**
   * 更新告警数据
   */
  function updateAlarmData(newData) {
    if (!newData || newData.length === 0) return;

    // 追加并限制数量
    alarmData.value = [...alarmData.value, ...newData].slice(-MAX_ALARMS);
  }

  /**
   * 清空所有数据
   */
  function clearAllData() {
    bandwidthData.value = [];
    messageData.value = [];
    alarmData.value = [];
    seenMessageIds.clear();
    seenBandwidthKeys.clear();
  }

  // 组件卸载时清理
  onUnmounted(() => {
    clearAllData();
  });

  return {
    bandwidthData,
    messageData,
    alarmData,
    updateBandwidthData,
    updateMessageData,
    updateAlarmData,
    clearAllData,
  };
}
