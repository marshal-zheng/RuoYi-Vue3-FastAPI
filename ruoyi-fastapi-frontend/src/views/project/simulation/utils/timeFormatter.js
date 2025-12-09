/**
 * 仿真时间格式化工具
 * 
 * 提供时间格式化和解析功能，支持毫秒级精度
 */

/**
 * 将秒数格式化为 HH:MM:SS.mmm 格式
 * @param {number} seconds - 秒数（支持小数）
 * @returns {string} 格式化后的时间字符串
 * 
 * @example
 * formatSimulationTime(0) // '00:00:00.000'
 * formatSimulationTime(3661.123) // '01:01:01.123'
 * formatSimulationTime(86400) // '24:00:00.000'
 */
export function formatSimulationTime(seconds) {
  if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
    return '00:00:00.000'
  }

  // 提取整数秒和毫秒
  const totalSeconds = Math.floor(seconds)
  const milliseconds = Math.round((seconds - totalSeconds) * 1000)

  // 计算时分秒
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60

  // 格式化为两位数（时分秒）和三位数（毫秒）
  const hh = String(hours).padStart(2, '0')
  const mm = String(minutes).padStart(2, '0')
  const ss = String(secs).padStart(2, '0')
  const mmm = String(milliseconds).padStart(3, '0')

  return `${hh}:${mm}:${ss}.${mmm}`
}

/**
 * 将 HH:MM:SS.mmm 格式的时间字符串解析为秒数
 * @param {string} timeStr - 时间字符串
 * @returns {number} 秒数（包含小数部分）
 * 
 * @example
 * parseSimulationTime('00:00:00.000') // 0
 * parseSimulationTime('01:01:01.123') // 3661.123
 * parseSimulationTime('24:00:00.000') // 86400
 */
export function parseSimulationTime(timeStr) {
  if (typeof timeStr !== 'string') {
    return 0
  }

  // 匹配 HH:MM:SS.mmm 格式（小时支持2位或更多位数）
  const match = timeStr.match(/^(\d{2,}):(\d{2}):(\d{2})\.(\d{3})$/)
  if (!match) {
    return 0
  }

  const hours = parseInt(match[1], 10)
  const minutes = parseInt(match[2], 10)
  const seconds = parseInt(match[3], 10)
  const milliseconds = parseInt(match[4], 10)

  return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
}

/**
 * 格式化时间戳为可读的日期时间字符串
 * @param {number} timestamp - Unix 时间戳（秒或毫秒）
 * @param {boolean} includeDate - 是否包含日期部分
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatTimestamp(timestamp, includeDate = false) {
  if (!timestamp) return ''

  // 如果是秒级时间戳，转换为毫秒
  const ms = timestamp > 1e12 ? timestamp : timestamp * 1000
  const date = new Date(ms)

  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  const milliseconds = String(date.getMilliseconds()).padStart(3, '0')

  const timeStr = `${hours}:${minutes}:${seconds}.${milliseconds}`

  if (includeDate) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day} ${timeStr}`
  }

  return timeStr
}

/**
 * 计算两个时间戳之间的持续时间
 * @param {number} startTime - 开始时间戳
 * @param {number} endTime - 结束时间戳
 * @returns {string} 格式化后的持续时间
 */
export function formatDuration(startTime, endTime) {
  const durationSeconds = Math.abs(endTime - startTime)
  return formatSimulationTime(durationSeconds)
}

/**
 * 将毫秒数格式化为人类可读的时间描述
 * @param {number} ms - 毫秒数
 * @returns {string} 人类可读的时间描述
 * 
 * @example
 * formatReadableDuration(500) // '500ms'
 * formatReadableDuration(1500) // '1.5s'
 * formatReadableDuration(65000) // '1m 5s'
 */
export function formatReadableDuration(ms) {
  if (ms < 1000) {
    return `${ms}ms`
  }

  const seconds = ms / 1000
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)

  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

export default {
  formatSimulationTime,
  parseSimulationTime,
  formatTimestamp,
  formatDuration,
  formatReadableDuration,
}
