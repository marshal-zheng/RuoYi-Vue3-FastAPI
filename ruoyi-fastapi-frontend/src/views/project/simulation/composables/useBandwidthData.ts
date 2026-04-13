/**
 * 带宽数据管理Composable
 * 管理带宽数据缓存（600秒滑动窗口）
 * 提供数据聚合和计算功能
 */
import { ref, computed, watch, type Ref, type ComputedRef } from 'vue';

interface BandwidthDataPoint {
  timestamp: number;
  portId: string;
  bandwidthMbps: number;
  bandwidth?: number;
  protocol?: string;
  messageCount?: number;
}

interface PortStats {
  portId: string;
  dataPoints: number;
  averageBandwidth: string;
  peakBandwidth: string;
  messageCount: number;
}

interface OverallStats {
  totalDataPoints: number;
  totalPorts: number;
  averageBandwidth: string;
  peakBandwidth: string;
  totalMessages: number;
}

interface ChartData {
  xData: string[];
  yData: number[];
}

interface MultiPortSeries {
  name: string;
  data: number[];
  xData: string[];
}

export function useBandwidthData() {
  const rawData: Ref<BandwidthDataPoint[]> = ref([]); // 原始带宽数据
  const timeWindow = 600; // 600秒时间窗口
  const selectedPortId: Ref<string | null> = ref(null); // 当前选择的端口
  const autoCleanInterval: Ref<number | null> = ref(null); // 自动清理定时器

  /**
   * 添加带宽数据
   */
  const addBandwidthData = (data: BandwidthDataPoint | BandwidthDataPoint[]) => {
    if (Array.isArray(data)) {
      rawData.value = [...rawData.value, ...data];
    } else {
      rawData.value.push(data);
    }

    // 清理超过时间窗口的数据
    cleanOldData();
  };

  /**
   * 清理超过时间窗口的数据
   */
  const cleanOldData = () => {
    const now = Date.now() / 1000;
    const cutoffTime = now - timeWindow;

    rawData.value = rawData.value.filter((item) => item.timestamp >= cutoffTime);
  };

  /**
   * 获取所有端口列表
   */
  const portList: ComputedRef<string[]> = computed(() => {
    const ports = new Set<string>();
    rawData.value.forEach((item) => {
      if (item.portId) {
        ports.add(item.portId);
      }
    });
    return Array.from(ports);
  });

  /**
   * 获取指定端口的数据
   */
  const getPortData = (portId: string): BandwidthDataPoint[] => {
    return rawData.value.filter((item) => item.portId === portId);
  };

  /**
   * 获取当前选择端口的数据
   */
  const currentPortData: ComputedRef<BandwidthDataPoint[]> = computed(() => {
    if (!selectedPortId.value) {
      return [];
    }
    return getPortData(selectedPortId.value);
  });

  /**
   * 格式化为ECharts数据格式
   */
  const formatForChart = (portId: string | null = null): ChartData => {
    const targetPortId = portId || selectedPortId.value;
    if (!targetPortId) {
      return { xData: [], yData: [] };
    }

    const portData = getPortData(targetPortId);

    // 按时间戳排序
    const sortedData = portData.sort((a, b) => a.timestamp - b.timestamp);

    // 提取时间和带宽值
    const xData = sortedData.map((item) => {
      const date = new Date(item.timestamp * 1000);
      return date.toLocaleTimeString();
    });

    const yData = sortedData.map((item) => item.bandwidthMbps || 0);

    return { xData, yData };
  };

  /**
   * 获取多端口数据（用于多条曲线）
   */
  const formatMultiPortForChart = (portIds: string[]): MultiPortSeries[] => {
    const series: MultiPortSeries[] = [];

    portIds.forEach((portId) => {
      const { xData, yData } = formatForChart(portId);
      series.push({
        name: portId,
        data: yData,
        xData: xData,
      });
    });

    return series;
  };

  /**
   * 计算端口的平均带宽
   */
  const calculateAverageBandwidth = (portId: string): string => {
    const portData = getPortData(portId);
    if (portData.length === 0) return '0';

    const sum = portData.reduce((acc, item) => acc + (item.bandwidthMbps || 0), 0);
    return (sum / portData.length).toFixed(2);
  };

  /**
   * 计算端口的峰值带宽
   */
  const calculatePeakBandwidth = (portId: string): string => {
    const portData = getPortData(portId);
    if (portData.length === 0) return '0';

    const max = Math.max(...portData.map((item) => item.bandwidthMbps || 0));
    return max.toFixed(2);
  };

  /**
   * 获取端口统计信息
   */
  const getPortStats = (portId: string): PortStats => {
    const portData = getPortData(portId);

    return {
      portId,
      dataPoints: portData.length,
      averageBandwidth: calculateAverageBandwidth(portId),
      peakBandwidth: calculatePeakBandwidth(portId),
      messageCount: portData.reduce((acc, item) => acc + (item.messageCount || 0), 0),
    };
  };

  /**
   * 获取所有端口的统计信息
   */
  const getAllPortsStats: ComputedRef<PortStats[]> = computed(() => {
    return portList.value.map((portId) => getPortStats(portId));
  });

  /**
   * 获取总体统计信息
   */
  const overallStats: ComputedRef<OverallStats> = computed(() => {
    if (rawData.value.length === 0) {
      return {
        totalDataPoints: 0,
        totalPorts: 0,
        averageBandwidth: '0',
        peakBandwidth: '0',
        totalMessages: 0,
      };
    }

    const allBandwidths = rawData.value.map((item) => item.bandwidthMbps || 0);
    const sum = allBandwidths.reduce((acc, val) => acc + val, 0);
    const max = Math.max(...allBandwidths);

    return {
      totalDataPoints: rawData.value.length,
      totalPorts: portList.value.length,
      averageBandwidth: (sum / rawData.value.length).toFixed(2),
      peakBandwidth: max.toFixed(2),
      totalMessages: rawData.value.reduce((acc, item) => acc + (item.messageCount || 0), 0),
    };
  });

  /**
   * 启动自动清理
   */
  const startAutoClean = () => {
    if (autoCleanInterval.value) return;

    // 每10秒清理一次过期数据
    autoCleanInterval.value = window.setInterval(() => {
      cleanOldData();
    }, 10000);
  };

  /**
   * 停止自动清理
   */
  const stopAutoClean = () => {
    if (autoCleanInterval.value) {
      clearInterval(autoCleanInterval.value);
      autoCleanInterval.value = null;
    }
  };

  /**
   * 清空数据
   */
  const clearData = () => {
    rawData.value = [];
    selectedPortId.value = null;
    stopAutoClean();
  };

  const getBandwidthValue = (item: Partial<BandwidthDataPoint>): number => {
    return Math.max(0, Number(item.bandwidth ?? item.bandwidthMbps ?? 0));
  };

  const addDataPoint = (data: Partial<BandwidthDataPoint> & Record<string, any>) => {
    const bandwidth = getBandwidthValue(data);
    rawData.value.push({
      timestamp: Number(data.timestamp ?? Date.now()),
      portId: String(data.portId ?? data.protocol ?? 'default'),
      bandwidth,
      bandwidthMbps: bandwidth,
      protocol: data.protocol,
      messageCount: data.messageCount,
    });

    if (rawData.value.length > 100) {
      rawData.value = rawData.value.slice(-100);
    }
    rawData.value.sort((a, b) => a.timestamp - b.timestamp);
  };

  const bandwidthHistory = rawData;

  const currentBandwidth = computed(() => {
    const latest = rawData.value[rawData.value.length - 1];
    return latest ? getBandwidthValue(latest) : 0;
  });

  const peakBandwidth = computed(() => {
    return rawData.value.length ? Math.max(...rawData.value.map(getBandwidthValue)) : 0;
  });

  const averageBandwidth = computed(() => {
    if (!rawData.value.length) return 0;
    return (
      rawData.value.reduce((sum, item) => sum + getBandwidthValue(item), 0) / rawData.value.length
    );
  });

  const getProtocolStats = () => {
    return rawData.value.reduce<Record<string, { total: number; count: number }>>((stats, item) => {
      const protocol = item.protocol || 'unknown';
      stats[protocol] ||= { total: 0, count: 0 };
      stats[protocol].total += getBandwidthValue(item);
      stats[protocol].count += 1;
      return stats;
    }, {});
  };

  const getProtocolUtilization = (protocol: string): number => {
    const stats = getProtocolStats();
    const protocolTotal = stats[protocol]?.total || 0;
    const total = Object.values(stats).reduce((sum, item) => sum + item.total, 0);
    return total ? (protocolTotal / total) * 100 : 0;
  };

  const getUtilization = (maxBandwidth: number): number => {
    if (maxBandwidth <= 0) {
      throw new Error('最大带宽必须大于 0');
    }
    return (currentBandwidth.value / maxBandwidth) * 100;
  };

  const getTimeWindow = (startTime: number, endTime: number) => {
    return rawData.value.filter((item) => item.timestamp >= startTime && item.timestamp <= endTime);
  };

  const getWindowAverage = (startTime: number, endTime: number): number => {
    const windowData = getTimeWindow(startTime, endTime);
    if (!windowData.length) return 0;
    return windowData.reduce((sum, item) => sum + getBandwidthValue(item), 0) / windowData.length;
  };

  const getWindowPeak = (startTime: number, endTime: number): number => {
    const windowData = getTimeWindow(startTime, endTime);
    return windowData.length ? Math.max(...windowData.map(getBandwidthValue)) : 0;
  };

  const getVariance = (): number => {
    if (!rawData.value.length) return 0;
    const average = averageBandwidth.value;
    return (
      rawData.value.reduce((sum, item) => {
        const diff = getBandwidthValue(item) - average;
        return sum + diff * diff;
      }, 0) / rawData.value.length
    );
  };

  const getStandardDeviation = (): number => Math.sqrt(getVariance());

  const detectSpikes = (multiplier = 2) => {
    const average = averageBandwidth.value;
    const threshold = average * multiplier;
    return rawData.value.filter((item) => getBandwidthValue(item) >= threshold);
  };

  const exportCSV = (): string => {
    const lines = rawData.value.map(
      (item) => `${item.timestamp},${getBandwidthValue(item)},${item.protocol || ''}`
    );
    return ['timestamp,bandwidth,protocol', ...lines].join('\n');
  };

  const exportJSON = (): string => JSON.stringify(rawData.value);

  // 监听数据变化，自动启动清理
  watch(
    () => rawData.value.length,
    (newLength) => {
      if (newLength > 0 && !autoCleanInterval.value) {
        startAutoClean();
      } else if (newLength === 0) {
        stopAutoClean();
      }
    }
  );

  return {
    rawData,
    selectedPortId,
    portList,
    currentPortData,
    overallStats,
    getAllPortsStats,
    addBandwidthData,
    formatForChart,
    formatMultiPortForChart,
    getPortStats,
    clearData,
    startAutoClean,
    stopAutoClean,

    bandwidthHistory,
    currentBandwidth,
    peakBandwidth,
    averageBandwidth,
    addDataPoint,
    clear: clearData,
    getProtocolStats,
    getProtocolUtilization,
    getUtilization,
    getTimeWindow,
    getWindowAverage,
    getWindowPeak,
    getVariance,
    getStandardDeviation,
    detectSpikes,
    exportCSV,
    exportJSON,
  };
}
