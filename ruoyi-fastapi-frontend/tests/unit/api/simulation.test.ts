/**
 * Unit tests for simulation API service
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as simulationApi from '@/api/simulation/simulation'
import request from '@/utils/request'

// Mock request utility
vi.mock('@/utils/request')

describe('Simulation API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('startSimulation', () => {
    it('should start simulation successfully', async () => {
      const mockResponse = {
        code: 200,
        data: {
          simulation_id: 1,
          status: 'running',
          start_time: Date.now()
        }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.startSimulation(1, { speed: 1.0 })

      expect(request.post).toHaveBeenCalledWith('/simulation/start', {
        project_id: 1,
        config: { speed: 1.0 }
      })
      expect(result.data.status).toBe('running')
    })

    it('should handle start simulation error', async () => {
      vi.mocked(request.post).mockRejectedValue(new Error('仿真已在运行中'))

      await expect(simulationApi.startSimulation(1)).rejects.toThrow('仿真已在运行中')
    })
  })

  describe('pauseSimulation', () => {
    it('should pause simulation', async () => {
      const mockResponse = {
        code: 200,
        data: { status: 'paused' }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.pauseSimulation(1)

      expect(request.post).toHaveBeenCalledWith('/simulation/1/pause')
      expect(result.data.status).toBe('paused')
    })
  })

  describe('resumeSimulation', () => {
    it('should resume simulation', async () => {
      const mockResponse = {
        code: 200,
        data: { status: 'running' }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.resumeSimulation(1)

      expect(request.post).toHaveBeenCalledWith('/simulation/1/resume')
      expect(result.data.status).toBe('running')
    })
  })

  describe('stopSimulation', () => {
    it('should stop simulation', async () => {
      const mockResponse = {
        code: 200,
        data: {
          status: 'stopped',
          duration: 100.5,
          total_messages: 1000
        }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.stopSimulation(1)

      expect(request.post).toHaveBeenCalledWith('/simulation/1/stop')
      expect(result.data.status).toBe('stopped')
      expect(result.data.duration).toBe(100.5)
    })
  })

  describe('getSimulationStatus', () => {
    it('should get simulation status', async () => {
      const mockStatus = {
        code: 200,
        data: {
          status: 'running',
          current_time: 50.5,
          speed: 1.0,
          messages_sent: 500
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockStatus)

      const result = await simulationApi.getSimulationStatus(1)

      expect(request.get).toHaveBeenCalledWith('/simulation/1/status')
      expect(result.data.status).toBe('running')
      expect(result.data.current_time).toBe(50.5)
    })

    it('should handle status fetch error', async () => {
      vi.mocked(request.get).mockRejectedValue(new Error('仿真不存在'))

      await expect(simulationApi.getSimulationStatus(999)).rejects.toThrow('仿真不存在')
    })
  })

  describe('setSimulationSpeed', () => {
    it('should set simulation speed', async () => {
      const mockResponse = {
        code: 200,
        data: { speed: 2.0 }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.setSimulationSpeed(1, 2.0)

      expect(request.post).toHaveBeenCalledWith('/simulation/1/speed', { speed: 2.0 })
      expect(result.data.speed).toBe(2.0)
    })

    it('should validate speed range', async () => {
      vi.mocked(request.post).mockRejectedValue(new Error('速度必须在0.1-10之间'))

      await expect(simulationApi.setSimulationSpeed(1, 100)).rejects.toThrow('速度必须在0.1-10之间')
    })
  })

  describe('getSimulationStatistics', () => {
    it('should get simulation statistics', async () => {
      const mockStats = {
        code: 200,
        data: {
          total_messages: 10000,
          messages_by_protocol: {
            '1553B': 6000,
            'CAN': 4000
          },
          bandwidth_usage: {
            peak: 950000,
            average: 500000
          },
          alarms: {
            total: 5,
            by_level: {
              error: 2,
              warning: 3
            }
          }
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockStats)

      const result = await simulationApi.getSimulationStatistics(1)

      expect(request.get).toHaveBeenCalledWith('/simulation/1/statistics')
      expect(result.data.total_messages).toBe(10000)
      expect(result.data.messages_by_protocol['1553B']).toBe(6000)
    })
  })

  describe('triggerEvent', () => {
    it('should trigger simulation event', async () => {
      const eventData = {
        event_type: 'fault_injection',
        target_device: 'device_1',
        fault_type: 'communication_loss'
      }

      const mockResponse = {
        code: 200,
        data: { success: true, event_id: 1 }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await simulationApi.triggerEvent(1, eventData)

      expect(request.post).toHaveBeenCalledWith('/simulation/1/event', eventData)
      expect(result.data.success).toBe(true)
    })

    it('should handle invalid event type', async () => {
      vi.mocked(request.post).mockRejectedValue(new Error('不支持的事件类型'))

      await expect(
        simulationApi.triggerEvent(1, { event_type: 'invalid' })
      ).rejects.toThrow('不支持的事件类型')
    })
  })

  describe('getSimulationMessages', () => {
    it('should get simulation messages', async () => {
      const mockMessages = {
        code: 200,
        data: {
          messages: [
            { id: 1, timestamp: 1.0, protocol: '1553B' },
            { id: 2, timestamp: 2.0, protocol: 'CAN' }
          ],
          total: 2
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockMessages)

      const result = await simulationApi.getSimulationMessages(1, {
        start_time: 0,
        end_time: 10
      })

      expect(request.get).toHaveBeenCalledWith('/simulation/1/messages', {
        params: { start_time: 0, end_time: 10 }
      })
      expect(result.data.messages.length).toBe(2)
    })

    it('should filter messages by protocol', async () => {
      const mockMessages = {
        code: 200,
        data: {
          messages: [
            { id: 1, protocol: '1553B' }
          ],
          total: 1
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockMessages)

      const result = await simulationApi.getSimulationMessages(1, {
        protocol: '1553B'
      })

      expect(result.data.messages[0].protocol).toBe('1553B')
    })
  })

  describe('getSimulationAlarms', () => {
    it('should get simulation alarms', async () => {
      const mockAlarms = {
        code: 200,
        data: {
          alarms: [
            { id: 1, level: 'error', type: 'message_loss' },
            { id: 2, level: 'warning', type: 'timing_violation' }
          ],
          total: 2
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockAlarms)

      const result = await simulationApi.getSimulationAlarms(1)

      expect(request.get).toHaveBeenCalledWith('/simulation/1/alarms')
      expect(result.data.alarms.length).toBe(2)
    })

    it('should filter alarms by level', async () => {
      const mockAlarms = {
        code: 200,
        data: {
          alarms: [{ id: 1, level: 'error' }],
          total: 1
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockAlarms)

      const result = await simulationApi.getSimulationAlarms(1, { level: 'error' })

      expect(result.data.alarms[0].level).toBe('error')
    })
  })

  describe('exportSimulationResults', () => {
    it('should export simulation results', async () => {
      const mockBlob = new Blob(['simulation data'], { type: 'application/json' })
      const mockResponse = { data: mockBlob }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await simulationApi.exportSimulationResults(1, 'json')

      expect(request.get).toHaveBeenCalledWith('/simulation/1/export', {
        params: { format: 'json' },
        responseType: 'blob'
      })
      expect(result.data).toBeInstanceOf(Blob)
    })

    it('should support CSV export', async () => {
      const mockBlob = new Blob(['csv data'], { type: 'text/csv' })
      const mockResponse = { data: mockBlob }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await simulationApi.exportSimulationResults(1, 'csv')

      expect(result.data).toBeInstanceOf(Blob)
    })
  })

  describe('WebSocket Connection', () => {
    it('should connect to simulation WebSocket', () => {
      const mockWs = {
        onopen: vi.fn(),
        onmessage: vi.fn(),
        onerror: vi.fn(),
        onclose: vi.fn()
      }

      // Mock WebSocket
      global.WebSocket = vi.fn(() => mockWs) as any

      const ws = simulationApi.connectSimulationWebSocket(1)

      expect(WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('/simulation/1/ws')
      )
    })

    it('should handle WebSocket messages', () => {
      const mockWs = {
        onopen: vi.fn(),
        onmessage: vi.fn(),
        onerror: vi.fn(),
        onclose: vi.fn()
      }

      global.WebSocket = vi.fn(() => mockWs) as any

      const ws = simulationApi.connectSimulationWebSocket(1)
      const messageHandler = vi.fn()

      ws.onmessage = messageHandler

      // Simulate message
      const mockEvent = {
        data: JSON.stringify({ type: 'message', data: {} })
      }

      ws.onmessage(mockEvent)

      expect(messageHandler).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      vi.mocked(request.post).mockRejectedValue(new Error('Network error'))

      await expect(simulationApi.startSimulation(1)).rejects.toThrow('Network error')
    })

    it('should handle 404 errors', async () => {
      const error = {
        response: { status: 404, data: { msg: 'Simulation not found' } }
      }

      vi.mocked(request.get).mockRejectedValue(error)

      await expect(simulationApi.getSimulationStatus(999)).rejects.toMatchObject(error)
    })

    it('should handle timeout errors', async () => {
      vi.mocked(request.post).mockRejectedValue(new Error('timeout'))

      await expect(simulationApi.startSimulation(1)).rejects.toThrow('timeout')
    })
  })
})
