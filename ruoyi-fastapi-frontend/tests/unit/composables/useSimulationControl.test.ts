/**
 * Unit tests for useSimulationControl composable
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref } from 'vue'
import { useSimulationControl } from '@/views/project/simulation/composables/useSimulationControl'

// Mock API
vi.mock('@/api/simulation/simulation', () => ({
  startSimulation: vi.fn(),
  pauseSimulation: vi.fn(),
  stopSimulation: vi.fn(),
  resumeSimulation: vi.fn(),
  getSimulationStatus: vi.fn()
}))

describe('useSimulationControl', () => {
  let simulationControl: ReturnType<typeof useSimulationControl>

  beforeEach(() => {
    vi.clearAllMocks()
    simulationControl = useSimulationControl(1)
  })

  describe('Initial State', () => {
    it('should initialize with correct default values', () => {
      expect(simulationControl.isRunning.value).toBe(false)
      expect(simulationControl.isPaused.value).toBe(false)
      expect(simulationControl.currentTime.value).toBe(0)
      expect(simulationControl.speed.value).toBe(1)
    })

    it('should have all required methods', () => {
      expect(typeof simulationControl.start).toBe('function')
      expect(typeof simulationControl.pause).toBe('function')
      expect(typeof simulationControl.resume).toBe('function')
      expect(typeof simulationControl.stop).toBe('function')
      expect(typeof simulationControl.setSpeed).toBe('function')
    })
  })

  describe('Start Simulation', () => {
    it('should start simulation successfully', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })

      await simulationControl.start()

      expect(simulationControl.isRunning.value).toBe(true)
      expect(simulationControl.isPaused.value).toBe(false)
      expect(startSimulation).toHaveBeenCalledWith(1)
    })

    it('should handle start simulation error', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockRejectedValue(new Error('Start failed'))

      await expect(simulationControl.start()).rejects.toThrow('Start failed')
      expect(simulationControl.isRunning.value).toBe(false)
    })

    it('should not start if already running', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })

      await simulationControl.start()
      const callCount = vi.mocked(startSimulation).mock.calls.length

      await simulationControl.start()

      expect(vi.mocked(startSimulation).mock.calls.length).toBe(callCount)
    })
  })

  describe('Pause Simulation', () => {
    it('should pause running simulation', async () => {
      const { startSimulation, pauseSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(pauseSimulation).mockResolvedValue({ code: 200, data: { status: 'paused' } })

      await simulationControl.start()
      await simulationControl.pause()

      expect(simulationControl.isPaused.value).toBe(true)
      expect(simulationControl.isRunning.value).toBe(true)
      expect(pauseSimulation).toHaveBeenCalledWith(1)
    })

    it('should not pause if not running', async () => {
      const { pauseSimulation } = await import('@/api/simulation/simulation')

      await simulationControl.pause()

      expect(pauseSimulation).not.toHaveBeenCalled()
    })
  })

  describe('Resume Simulation', () => {
    it('should resume paused simulation', async () => {
      const { startSimulation, pauseSimulation, resumeSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(pauseSimulation).mockResolvedValue({ code: 200, data: { status: 'paused' } })
      vi.mocked(resumeSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })

      await simulationControl.start()
      await simulationControl.pause()
      await simulationControl.resume()

      expect(simulationControl.isPaused.value).toBe(false)
      expect(simulationControl.isRunning.value).toBe(true)
      expect(resumeSimulation).toHaveBeenCalledWith(1)
    })

    it('should not resume if not paused', async () => {
      const { resumeSimulation } = await import('@/api/simulation/simulation')

      await simulationControl.resume()

      expect(resumeSimulation).not.toHaveBeenCalled()
    })
  })

  describe('Stop Simulation', () => {
    it('should stop running simulation', async () => {
      const { startSimulation, stopSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(stopSimulation).mockResolvedValue({ code: 200, data: { status: 'stopped' } })

      await simulationControl.start()
      await simulationControl.stop()

      expect(simulationControl.isRunning.value).toBe(false)
      expect(simulationControl.isPaused.value).toBe(false)
      expect(simulationControl.currentTime.value).toBe(0)
      expect(stopSimulation).toHaveBeenCalledWith(1)
    })

    it('should reset state when stopping', async () => {
      const { startSimulation, stopSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(stopSimulation).mockResolvedValue({ code: 200, data: { status: 'stopped' } })

      await simulationControl.start()
      simulationControl.currentTime.value = 100
      simulationControl.speed.value = 2

      await simulationControl.stop()

      expect(simulationControl.currentTime.value).toBe(0)
      expect(simulationControl.speed.value).toBe(1)
    })
  })

  describe('Speed Control', () => {
    it('should set simulation speed', () => {
      simulationControl.setSpeed(2)
      expect(simulationControl.speed.value).toBe(2)
    })

    it('should validate speed range', () => {
      simulationControl.setSpeed(0.5)
      expect(simulationControl.speed.value).toBe(0.5)

      simulationControl.setSpeed(10)
      expect(simulationControl.speed.value).toBe(10)
    })

    it('should reject invalid speed values', () => {
      expect(() => simulationControl.setSpeed(0)).toThrow()
      expect(() => simulationControl.setSpeed(-1)).toThrow()
      expect(() => simulationControl.setSpeed(100)).toThrow()
    })

    it('should handle speed presets', () => {
      const presets = [0.5, 1, 2, 5, 10]
      
      presets.forEach(speed => {
        simulationControl.setSpeed(speed)
        expect(simulationControl.speed.value).toBe(speed)
      })
    })
  })

  describe('Time Management', () => {
    it('should update current time', () => {
      simulationControl.updateTime(100)
      expect(simulationControl.currentTime.value).toBe(100)
    })

    it('should not allow negative time', () => {
      expect(() => simulationControl.updateTime(-1)).toThrow()
    })

    it('should format time correctly', () => {
      simulationControl.updateTime(3661.5)
      const formatted = simulationControl.formattedTime.value
      expect(formatted).toMatch(/\d{2}:\d{2}:\d{2}\.\d{3}/)
    })
  })

  describe('State Transitions', () => {
    it('should handle complete lifecycle', async () => {
      const { startSimulation, pauseSimulation, resumeSimulation, stopSimulation } = 
        await import('@/api/simulation/simulation')
      
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(pauseSimulation).mockResolvedValue({ code: 200, data: { status: 'paused' } })
      vi.mocked(resumeSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(stopSimulation).mockResolvedValue({ code: 200, data: { status: 'stopped' } })

      // Start
      await simulationControl.start()
      expect(simulationControl.isRunning.value).toBe(true)

      // Pause
      await simulationControl.pause()
      expect(simulationControl.isPaused.value).toBe(true)

      // Resume
      await simulationControl.resume()
      expect(simulationControl.isPaused.value).toBe(false)

      // Stop
      await simulationControl.stop()
      expect(simulationControl.isRunning.value).toBe(false)
    })

    it('should maintain state consistency', async () => {
      const { startSimulation, stopSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockResolvedValue({ code: 200, data: { status: 'running' } })
      vi.mocked(stopSimulation).mockResolvedValue({ code: 200, data: { status: 'stopped' } })

      await simulationControl.start()
      expect(simulationControl.isRunning.value).toBe(true)
      expect(simulationControl.isPaused.value).toBe(false)

      await simulationControl.stop()
      expect(simulationControl.isRunning.value).toBe(false)
      expect(simulationControl.isPaused.value).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockRejectedValue(new Error('Network error'))

      await expect(simulationControl.start()).rejects.toThrow('Network error')
      expect(simulationControl.isRunning.value).toBe(false)
    })

    it('should handle timeout errors', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      vi.mocked(startSimulation).mockRejectedValue(new Error('Timeout'))

      await expect(simulationControl.start()).rejects.toThrow('Timeout')
    })

    it('should recover from errors', async () => {
      const { startSimulation } = await import('@/api/simulation/simulation')
      
      // First call fails
      vi.mocked(startSimulation).mockRejectedValueOnce(new Error('Error'))
      await expect(simulationControl.start()).rejects.toThrow()

      // Second call succeeds
      vi.mocked(startSimulation).mockResolvedValueOnce({ code: 200, data: { status: 'running' } })
      await simulationControl.start()
      expect(simulationControl.isRunning.value).toBe(true)
    })
  })
})
