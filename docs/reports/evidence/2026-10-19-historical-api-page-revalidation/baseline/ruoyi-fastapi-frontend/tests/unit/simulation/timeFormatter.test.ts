/**
 * 时间格式化工具属性测试
 * 
 * **Feature: simulation-refactoring, Property 1: 时间格式化一致性**
 * **Validates: Requirements 1.2**
 */
import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import {
  formatSimulationTime,
  parseSimulationTime,
  formatTimestamp,
  formatDuration,
  formatReadableDuration
} from '@/views/project/simulation/utils/timeFormatter'

describe('timeFormatter', () => {
  // ============================================
  // 单元测试
  // ============================================
  describe('formatSimulationTime - Unit Tests', () => {
    it('should format 0 seconds correctly', () => {
      expect(formatSimulationTime(0)).toBe('00:00:00.000')
    })

    it('should format 1 second correctly', () => {
      expect(formatSimulationTime(1)).toBe('00:00:01.000')
    })

    it('should format 1 minute correctly', () => {
      expect(formatSimulationTime(60)).toBe('00:01:00.000')
    })

    it('should format 1 hour correctly', () => {
      expect(formatSimulationTime(3600)).toBe('01:00:00.000')
    })

    it('should format complex time correctly', () => {
      expect(formatSimulationTime(3661.123)).toBe('01:01:01.123')
    })

    it('should format 24 hours correctly', () => {
      expect(formatSimulationTime(86400)).toBe('24:00:00.000')
    })

    it('should handle negative values', () => {
      expect(formatSimulationTime(-1)).toBe('00:00:00.000')
    })

    it('should handle NaN', () => {
      expect(formatSimulationTime(NaN)).toBe('00:00:00.000')
    })

    it('should handle non-number input', () => {
      expect(formatSimulationTime('invalid' as any)).toBe('00:00:00.000')
    })
  })

  describe('parseSimulationTime - Unit Tests', () => {
    it('should parse 00:00:00.000 correctly', () => {
      expect(parseSimulationTime('00:00:00.000')).toBe(0)
    })

    it('should parse 01:01:01.123 correctly', () => {
      expect(parseSimulationTime('01:01:01.123')).toBe(3661.123)
    })

    it('should parse 24:00:00.000 correctly', () => {
      expect(parseSimulationTime('24:00:00.000')).toBe(86400)
    })

    it('should return 0 for invalid format', () => {
      expect(parseSimulationTime('invalid')).toBe(0)
    })

    it('should return 0 for non-string input', () => {
      expect(parseSimulationTime(123 as any)).toBe(0)
    })
  })

  // ============================================
  // 属性测试 (Property-Based Testing)
  // ============================================
  
  /**
   * **Feature: simulation-refactoring, Property 1: 时间格式化一致性**
   * **Validates: Requirements 1.2**
   * 
   * *For any* 仿真时间值（非负浮点数），格式化函数应返回符合 `HH:MM:SS.mmm` 格式的字符串，
   * 且解析后能还原为原始时间值（误差小于1毫秒）
   */
  describe('Property 1: Time Format Round Trip', () => {
    it('should round-trip time values correctly (0-24 hours)', () => {
      fc.assert(
        fc.property(
          // 生成 0 到 86400 秒（24小时）的浮点数，精度到毫秒
          fc.float({ min: 0, max: 86400, noNaN: true, noDefaultInfinity: true }),
          (timeValue) => {
            // 将时间值四舍五入到毫秒精度
            const roundedTime = Math.round(timeValue * 1000) / 1000
            
            const formatted = formatSimulationTime(roundedTime)
            const parsed = parseSimulationTime(formatted)
            
            // 验证往返一致性，误差小于1毫秒
            return Math.abs(parsed - roundedTime) < 0.001
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should produce valid HH:MM:SS.mmm format', () => {
      fc.assert(
        fc.property(
          fc.float({ min: 0, max: 86400, noNaN: true, noDefaultInfinity: true }),
          (timeValue) => {
            const formatted = formatSimulationTime(timeValue)
            
            // 验证格式符合 HH:MM:SS.mmm
            const pattern = /^\d{2}:\d{2}:\d{2}\.\d{3}$/
            return pattern.test(formatted)
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should handle values up to 99 hours (max supported by HH format)', () => {
      fc.assert(
        fc.property(
          // 生成 0 到 356400 秒（99小时）的浮点数，确保小时不超过两位数
          fc.float({ min: 0, max: 356400, noNaN: true, noDefaultInfinity: true }),
          (timeValue) => {
            const roundedTime = Math.round(timeValue * 1000) / 1000
            
            const formatted = formatSimulationTime(roundedTime)
            const parsed = parseSimulationTime(formatted)
            
            // 验证往返一致性
            return Math.abs(parsed - roundedTime) < 0.001
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should preserve millisecond precision', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 86400 }),  // 整数秒
          fc.integer({ min: 0, max: 999 }),    // 毫秒
          (seconds, milliseconds) => {
            const timeValue = seconds + milliseconds / 1000
            
            const formatted = formatSimulationTime(timeValue)
            const parsed = parseSimulationTime(formatted)
            
            // 验证毫秒精度保持
            return Math.abs(parsed - timeValue) < 0.001
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property: Format Components Correctness', () => {
    it('should correctly extract hours, minutes, seconds', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 99 }),   // 小时
          fc.integer({ min: 0, max: 59 }),   // 分钟
          fc.integer({ min: 0, max: 59 }),   // 秒
          fc.integer({ min: 0, max: 999 }),  // 毫秒
          (hours, minutes, seconds, milliseconds) => {
            const timeValue = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            
            const formatted = formatSimulationTime(timeValue)
            const parts = formatted.split(/[:.]/);
            
            const parsedHours = parseInt(parts[0], 10)
            const parsedMinutes = parseInt(parts[1], 10)
            const parsedSeconds = parseInt(parts[2], 10)
            const parsedMilliseconds = parseInt(parts[3], 10)
            
            return (
              parsedHours === hours &&
              parsedMinutes === minutes &&
              parsedSeconds === seconds &&
              parsedMilliseconds === milliseconds
            )
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  // ============================================
  // 其他工具函数测试
  // ============================================
  describe('formatDuration', () => {
    it('should calculate duration correctly', () => {
      expect(formatDuration(0, 3661.123)).toBe('01:01:01.123')
    })

    it('should handle reversed timestamps', () => {
      expect(formatDuration(3661.123, 0)).toBe('01:01:01.123')
    })
  })

  describe('formatReadableDuration', () => {
    it('should format milliseconds', () => {
      expect(formatReadableDuration(500)).toBe('500ms')
    })

    it('should format seconds', () => {
      expect(formatReadableDuration(1500)).toBe('1.5s')
    })

    it('should format minutes and seconds', () => {
      expect(formatReadableDuration(65000)).toBe('1m 5s')
    })

    it('should format hours and minutes', () => {
      expect(formatReadableDuration(3660000)).toBe('1h 1m')
    })
  })
})
