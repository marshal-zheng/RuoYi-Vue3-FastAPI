/**
 * 设备端口颜色配置，供拓扑和设备配置界面共用
 */

export const PORT_COLOR_MAP = {
  RS422: '#f59e0b', // 琥珀色 - 串口通信
  RS485: '#f97316', // 橙色 - 工业串口
  CAN: '#3b82f6', // 蓝色 - CAN总线
  LAN: '#10b981', // 绿色 - 以太网
  '1553B': '#8b5cf6', // 紫色 - 军用总线
};

export const DEFAULT_PORT_COLOR = '#6b7280'; // 默认灰色

/**
 * 根据端口信息获取颜色
 * @param {string|Object} portInfo - 端口类型字符串或端口对象
 * @returns {string} 颜色值
 */
export function getPortColor(portInfo) {
  const candidates = [];
  if (typeof portInfo === 'string') {
    candidates.push(portInfo);
  } else if (portInfo && typeof portInfo === 'object') {
    const { busType, interfaceType, type } = portInfo;
    candidates.push(busType, interfaceType, type);
  }

  for (const candidate of candidates) {
    if (!candidate) continue;
    const key = String(candidate).trim().toUpperCase();
    if (key && PORT_COLOR_MAP[key]) {
      return PORT_COLOR_MAP[key];
    }
  }

  return DEFAULT_PORT_COLOR;
}
