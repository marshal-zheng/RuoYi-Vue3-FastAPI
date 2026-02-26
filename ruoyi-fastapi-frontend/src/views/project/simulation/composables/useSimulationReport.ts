/**
 * 仿真报告 Composable
 *
 * 管理仿真报告的生成和格式化
 */
import type { Ref } from 'vue';

interface MessageItem {
  messageId?: string;
  [key: string]: any;
}

interface AlarmItem {
  alarmType?: string;
  type?: string;
  severity?: string;
  level?: string;
  [key: string]: any;
}

interface BandwidthItem {
  protocolType?: string;
  protocol_type?: string;
  bandwidthMbps?: number;
  bandwidth_mbps?: number;
  loadPercent?: number;
  load_percent?: number;
  [key: string]: any;
}

interface SimulationState {
  elapsedTime: number;
  startTime: number | string | Date;
  [key: string]: any;
}

interface BandwidthStat {
  protocol: string;
  avgBandwidth: string;
  maxBandwidth: string;
  avgLoad: string;
}

interface AlarmStat {
  type: string;
  level: string;
  count: number;
}

interface SimulationSummary {
  duration: string;
  messageCount: number;
  alarmCount: number;
  bandwidthStats: BandwidthStat[];
  alarmStats: AlarmStat[];
  startTime: string;
}

/**
 * 格式化持续时间
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时间字符串
 */
export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const parts: string[] = [];
  if (h > 0) parts.push(`${h}小时`);
  if (m > 0) parts.push(`${m}分`);
  parts.push(`${s}秒`);
  return parts.join('');
}

/**
 * 格式化日期时间
 * @param {number|string|Date} ts - 时间戳
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(ts: number | string | Date): string {
  if (!ts) return '-';
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return '-';
  const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

interface UseSimulationReportOptions {
  messageData: Ref<MessageItem[]>;
  alarmData: Ref<AlarmItem[]>;
  bandwidthData: Ref<BandwidthItem[]>;
  simulationState: SimulationState;
}

/**
 * 仿真报告 Composable
 * @param {Object} options 配置选项
 * @param {Ref} options.messageData - 报文数据
 * @param {Ref} options.alarmData - 告警数据
 * @param {Ref} options.bandwidthData - 带宽数据
 * @param {Object} options.simulationState - 仿真状态
 */
export function useSimulationReport(options: UseSimulationReportOptions) {
  const { messageData, alarmData, bandwidthData, simulationState } = options;

  /**
   * 构建仿真摘要报告
   * @returns {Object} 仿真摘要
   */
  function buildSimulationSummary(): SimulationSummary {
    const messageCount = messageData.value.length;
    const alarmCount = alarmData.value.length;
    const duration = formatDuration(simulationState.elapsedTime);
    const startTime = formatDateTime(simulationState.startTime);

    // 带宽统计
    const bandwidthStatsMap: Record<
      string,
      {
        protocol: string;
        total: number;
        max: number;
        loadTotal: number;
        count: number;
      }
    > = {};

    bandwidthData.value.forEach((item) => {
      const protocol = item.protocolType || item.protocol_type || '未知协议';
      if (!bandwidthStatsMap[protocol]) {
        bandwidthStatsMap[protocol] = {
          protocol,
          total: 0,
          max: 0,
          loadTotal: 0,
          count: 0,
        };
      }
      const stat = bandwidthStatsMap[protocol];
      const bw = Number(item.bandwidthMbps || item.bandwidth_mbps || 0);
      const load = Number(item.loadPercent || item.load_percent || 0);
      stat.total += bw;
      stat.loadTotal += load;
      stat.count += 1;
      stat.max = Math.max(stat.max, bw);
    });

    const bandwidthStats: BandwidthStat[] = Object.values(bandwidthStatsMap).map((item) => ({
      protocol: item.protocol,
      avgBandwidth: `${(item.total / item.count || 0).toFixed(3)} Mbps`,
      maxBandwidth: `${item.max.toFixed(3)} Mbps`,
      avgLoad: `${(item.loadTotal / item.count || 0).toFixed(1)}%`,
    }));

    // 告警统计
    const alarmStatsMap: Record<string, AlarmStat> = {};
    alarmData.value.forEach((alarm) => {
      const type = alarm.alarmType || alarm.type || '未知类型';
      const level = alarm.severity || alarm.level || 'info';
      const key = `${type}-${level}`;
      if (!alarmStatsMap[key]) {
        alarmStatsMap[key] = { type, level, count: 0 };
      }
      alarmStatsMap[key].count += 1;
    });
    const alarmStats = Object.values(alarmStatsMap);

    return {
      duration,
      messageCount,
      alarmCount,
      bandwidthStats,
      alarmStats,
      startTime,
    };
  }

  return {
    // 工具函数
    formatDuration,
    formatDateTime,

    // 方法
    buildSimulationSummary,
  };
}

export default useSimulationReport;
