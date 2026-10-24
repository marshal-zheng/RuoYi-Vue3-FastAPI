/**
 * Unit tests for useBandwidthData composable
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref } from 'vue'
import { useBandwidthData } from '@/views/project/simulation/composables/useBandwidthData'

describe('useBandwidthData', () => {
  let bandwidthData: ReturnType<typeof useBandwidthData>

  beforeEach(() => {
    vi.clearAllMocks()
    bandwidthData = useBandwidthData()
  })

  describe('Initial State', () => {
    it('should initialize with empty data', () => {
      expect(bandwidthData.bandwidthHistory.value).toEqual([])
      expect(bandwidthData.currentBandwidth.value).toBe(0)
      expect(bandwidthData.peakBandwidth.value).toBe(0)
      expect(bandwidthData.averageBandwidth.value).toBe(0)
    })

    it('should have all required methods', () => {
      expect(typeof bandwidthData.addDataPoint).toBe('function')
      expect(typeof bandwidthData.clear).toBe('function')
      expect(typeof bandwidthData.getUtilization).toBe('function')
    })
  })

  describe('Add Data Point', () => {
    it('should add bandwidth data point', () => {
      const dataPoint = {
        timestamp: Date.now(),
        bandwidth: 1000,
        protocol: '1553B'
      }

      bandwidthData.addDataPoint(dataPoint)

      expect(bandwidthData.bandwidthHistory.value.length).toBe(1)
      expect(bandwidthData.currentBandwidth.value).toBe(1000)
    })

    it('should update peak bandwidth', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 1500 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 800 })

      expect(bandwidthData.peakBandwidth.value).toBe(1500)
    })

    it('should calculate average bandwidth', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 1000 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 2000 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 3000 })

      expect(bandwidthData.averageBandwidth.value).toBe(2000)
    })

    it('should limit history size', () => {
      // Add more than max history size
      for (let i = 0; i < 150; i++) {
        bandwidthData.addDataPoint({
          timestamp: i * 1000,
          bandwidth: i * 100
        })
      }

      // Should keep only last 100 points
      expect(bandwidthData.bandwidthHistory.value.length).toBeLessThanOrEqual(100)
    })

    it('should handle zero bandwidth', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 0 })

      expect(bandwidthData.currentBandwidth.value).toBe(0)
      expect(bandwidthData.peakBandwidth.value).toBe(0)
    })

    it('should handle negative bandwidth gracefully', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: -100 })

      // Should treat as 0 or throw error
      expect(bandwidthData.currentBandwidth.value).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Protocol-specific Bandwidth', () => {
    it('should track bandwidth by protocol', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500, protocol: '1553B' })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 300, protocol: 'CAN' })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 200, protocol: '1553B' })

      const protocolStats = bandwidthData.getProtocolStats()

      expect(protocolStats['1553B'].total).toBe(700)
      expect(protocolStats['CAN'].total).toBe(300)
    })

    it('should calculate protocol utilization', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500, protocol: '1553B' })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 500, protocol: 'CAN' })

      const utilization = bandwidthData.getProtocolUtilization('1553B')

      expect(utilization).toBe(50) // 500 out of 1000 total
    })
  })

  describe('Bandwidth Utilization', () => {
    it('should calculate utilization percentage', () => {
      const maxBandwidth = 10000

      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 5000 })

      const utilization = bandwidthData.getUtilization(maxBandwidth)

      expect(utilization).toBe(50)
    })

    it('should handle 100% utilization', () => {
      const maxBandwidth = 1000

      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 1000 })

      const utilization = bandwidthData.getUtilization(maxBandwidth)

      expect(utilization).toBe(100)
    })

    it('should handle over-utilization', () => {
      const maxBandwidth = 1000

      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 1500 })

      const utilization = bandwidthData.getUtilization(maxBandwidth)

      expect(utilization).toBeGreaterThan(100)
    })

    it('should handle zero max bandwidth', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500 })

      expect(() => bandwidthData.getUtilization(0)).toThrow()
    })
  })

  describe('Time Window Analysis', () => {
    it('should get bandwidth in time window', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 300 })
      bandwidthData.addDataPoint({ timestamp: 4000, bandwidth: 400 })

      const windowData = bandwidthData.getTimeWindow(2000, 3500)

      expect(windowData.length).toBe(2)
      expect(windowData[0].bandwidth).toBe(200)
      expect(windowData[1].bandwidth).toBe(300)
    })

    it('should calculate average in time window', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 300 })

      const average = bandwidthData.getWindowAverage(1000, 3000)

      expect(average).toBe(200)
    })

    it('should find peak in time window', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 500 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 200 })

      const peak = bandwidthData.getWindowPeak(1000, 3000)

      expect(peak).toBe(500)
    })
  })

  describe('Statistics', () => {
    it('should calculate standard deviation', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 300 })

      const stdDev = bandwidthData.getStandardDeviation()

      expect(stdDev).toBeGreaterThan(0)
      expect(stdDev).toBeLessThan(100)
    })

    it('should calculate variance', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 300 })

      const variance = bandwidthData.getVariance()

      expect(variance).toBeGreaterThan(0)
    })

    it('should detect bandwidth spikes', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 1000 }) // Spike
      bandwidthData.addDataPoint({ timestamp: 4000, bandwidth: 100 })

      const spikes = bandwidthData.detectSpikes(2) // 2x standard deviation

      expect(spikes.length).toBeGreaterThan(0)
      expect(spikes[0].bandwidth).toBe(1000)
    })
  })

  describe('Clear Data', () => {
    it('should clear all data', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 600 })

      bandwidthData.clear()

      expect(bandwidthData.bandwidthHistory.value).toEqual([])
      expect(bandwidthData.currentBandwidth.value).toBe(0)
      expect(bandwidthData.peakBandwidth.value).toBe(0)
      expect(bandwidthData.averageBandwidth.value).toBe(0)
    })

    it('should reset statistics after clear', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500 })
      
      const beforeClear = bandwidthData.getStandardDeviation()
      
      bandwidthData.clear()
      
      const afterClear = bandwidthData.getStandardDeviation()

      expect(afterClear).toBe(0)
    })
  })

  describe('Data Export', () => {
    it('should export data as CSV', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100, protocol: '1553B' })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200, protocol: 'CAN' })

      const csv = bandwidthData.exportCSV()

      expect(csv).toContain('timestamp,bandwidth,protocol')
      expect(csv).toContain('1000,100,1553B')
      expect(csv).toContain('2000,200,CAN')
    })

    it('should export data as JSON', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })

      const json = bandwidthData.exportJSON()
      const data = JSON.parse(json)

      expect(data.length).toBe(2)
      expect(data[0].bandwidth).toBe(100)
    })
  })

  describe('Real-time Updates', () => {
    it('should handle rapid updates', () => {
      const startTime = Date.now()

      for (let i = 0; i < 100; i++) {
        bandwidthData.addDataPoint({
          timestamp: startTime + i * 10,
          bandwidth: Math.random() * 1000
        })
      }

      expect(bandwidthData.bandwidthHistory.value.length).toBeLessThanOrEqual(100)
      expect(bandwidthData.currentBandwidth.value).toBeGreaterThanOrEqual(0)
    })

    it('should maintain chronological order', () => {
      bandwidthData.addDataPoint({ timestamp: 3000, bandwidth: 300 })
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 100 })
      bandwidthData.addDataPoint({ timestamp: 2000, bandwidth: 200 })

      const history = bandwidthData.bandwidthHistory.value

      for (let i = 1; i < history.length; i++) {
        expect(history[i].timestamp).toBeGreaterThanOrEqual(history[i - 1].timestamp)
      }
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty history', () => {
      expect(bandwidthData.averageBandwidth.value).toBe(0)
      expect(bandwidthData.peakBandwidth.value).toBe(0)
      expect(bandwidthData.getStandardDeviation()).toBe(0)
    })

    it('should handle single data point', () => {
      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: 500 })

      expect(bandwidthData.averageBandwidth.value).toBe(500)
      expect(bandwidthData.peakBandwidth.value).toBe(500)
      expect(bandwidthData.getStandardDeviation()).toBe(0)
    })

    it('should handle very large bandwidth values', () => {
      const largeBandwidth = 1e9 // 1 Gbps

      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: largeBandwidth })

      expect(bandwidthData.currentBandwidth.value).toBe(largeBandwidth)
    })

    it('should handle very small bandwidth values', () => {
      const smallBandwidth = 0.001

      bandwidthData.addDataPoint({ timestamp: 1000, bandwidth: smallBandwidth })

      expect(bandwidthData.currentBandwidth.value).toBe(smallBandwidth)
    })
  })
})
