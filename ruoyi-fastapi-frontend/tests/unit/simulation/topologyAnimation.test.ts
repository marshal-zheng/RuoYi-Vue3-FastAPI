/**
 * 拓扑动画工具属性测试
 * 
 * **Feature: simulation-refactoring, Property 2: 协议颜色映射完整性**
 * **Validates: Requirements 2.1**
 */
import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import {
  PROTOCOL_COLORS,
  getProtocolColor,
  validateProtocolColors
} from '@/views/project/simulation/composables/useTopologyAnimation'

describe('topologyAnimation', () => {
  // ============================================
  // 单元测试
  // ============================================
  describe('getProtocolColor - Unit Tests', () => {
    it('should return orange for 1553B protocol', () => {
      expect(getProtocolColor('1553B')).toBe('#f97316')
    })

    it('should return orange for MIL-STD-1553B protocol', () => {
      expect(getProtocolColor('MIL-STD-1553B')).toBe('#f97316')
    })

    it('should return blue for CAN protocol', () => {
      expect(getProtocolColor('CAN')).toBe('#3b82f6')
    })

    it('should return green for RS422 protocol', () => {
      expect(getProtocolColor('RS422')).toBe('#22c55e')
    })

    it('should return green for RS485 protocol', () => {
      expect(getProtocolColor('RS485')).toBe('#22c55e')
    })

    it('should return white for LAN protocol', () => {
      expect(getProtocolColor('LAN')).toBe('#e2e8f0')
    })

    it('should return white for Ethernet protocol', () => {
      expect(getProtocolColor('Ethernet')).toBe('#e2e8f0')
    })

    it('should return default color for unknown protocol', () => {
      expect(getProtocolColor('UNKNOWN')).toBe(PROTOCOL_COLORS.default)
    })


    it('should return default color for null/undefined', () => {
      expect(getProtocolColor(null as any)).toBe(PROTOCOL_COLORS.default)
      expect(getProtocolColor(undefined as any)).toBe(PROTOCOL_COLORS.default)
    })

    it('should handle case-insensitive matching', () => {
      expect(getProtocolColor('can')).toBe('#3b82f6')
      expect(getProtocolColor('CAN')).toBe('#3b82f6')
      expect(getProtocolColor('Can')).toBe('#3b82f6')
    })
  })

  // ============================================
  // 属性测试 (Property-Based Testing)
  // ============================================
  
  /**
   * **Feature: simulation-refactoring, Property 2: 协议颜色映射完整性**
   * **Validates: Requirements 2.1**
   */
  describe('Property 2: Protocol Color Mapping Completeness', () => {
    const CORE_PROTOCOLS = ['1553B', 'CAN', 'RS422', 'RS485', 'LAN']
    
    const PROTOCOL_VARIANTS: Record<string, string[]> = {
      '1553B': ['1553B', 'MIL-STD-1553B', 'mil-std-1553b', '1553b'],
      'CAN': ['CAN', 'can', 'Can'],
      'RS422': ['RS422', 'rs422', 'RS-422'],
      'RS485': ['RS485', 'rs485', 'RS-485'],
      'LAN': ['LAN', 'lan', 'Ethernet', 'ethernet']
    }

    it('should map all core protocols to predefined colors', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(...CORE_PROTOCOLS),
          (protocol) => {
            const color = getProtocolColor(protocol)
            return color !== PROTOCOL_COLORS.default
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should map different protocol types to different colors', () => {
      const colorMap = new Map<string, string>()
      for (const protocol of CORE_PROTOCOLS) {
        colorMap.set(protocol, getProtocolColor(protocol))
      }
      const uniqueColors = new Set([
        colorMap.get('1553B'),
        colorMap.get('CAN'),
        colorMap.get('RS422'),
        colorMap.get('LAN')
      ])
      expect(uniqueColors.size).toBe(4)
    })


    it('should handle protocol variants consistently', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(...Object.keys(PROTOCOL_VARIANTS)),
          (baseProtocol) => {
            const variants = PROTOCOL_VARIANTS[baseProtocol]
            const colors = variants.map(v => getProtocolColor(v))
            return colors.every(c => c === colors[0])
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should return valid hex color format', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(...CORE_PROTOCOLS, 'UNKNOWN', ''),
          (protocol) => {
            const color = getProtocolColor(protocol)
            return /^#[0-9a-fA-F]{6}$/.test(color)
          }
        ),
        { numRuns: 100 }
      )
    })

    it('should match expected colors for each protocol', () => {
      const expectedColors: Record<string, string> = {
        '1553B': '#f97316',
        'CAN': '#3b82f6',
        'RS422': '#22c55e',
        'RS485': '#22c55e',
        'LAN': '#e2e8f0',
      }
      fc.assert(
        fc.property(
          fc.constantFrom(...Object.keys(expectedColors)),
          (protocol) => {
            return getProtocolColor(protocol) === expectedColors[protocol]
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('validateProtocolColors', () => {
    it('should return true for valid protocol list', () => {
      expect(validateProtocolColors(['1553B', 'CAN', 'RS422', 'LAN'])).toBe(true)
    })

    it('should return false if unknown protocol is included', () => {
      expect(validateProtocolColors(['1553B', 'UNKNOWN'])).toBe(false)
    })
  })
})
