/**
 * Unit tests for useSimulationControl composable
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';
import { useSimulationControl } from '@/views/project/simulation/composables/useSimulationControl';
import * as simulationApi from '@/api/simulation/simulation';

vi.mock('@/api/simulation/simulation', () => ({
  createSimulationSession: vi.fn(),
  startSimulationSession: vi.fn(),
  pauseSimulationSession: vi.fn(),
  resumeSimulationSession: vi.fn(),
  stopSimulationSession: vi.fn(),
  stepSimulationSession: vi.fn(),
  setSimulationSpeed: vi.fn(),
}));

describe('useSimulationControl', () => {
  let simulationControl: ReturnType<typeof useSimulationControl>;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(simulationApi.createSimulationSession).mockResolvedValue({
      sessionId: 'session-1',
      status: 'created',
      message: '仿真会话创建成功',
    });
    vi.mocked(simulationApi.startSimulationSession).mockResolvedValue({
      sessionId: 'session-1',
      action: 'start',
      status: 'accepted',
    });
    vi.mocked(simulationApi.pauseSimulationSession).mockResolvedValue(null);
    vi.mocked(simulationApi.resumeSimulationSession).mockResolvedValue(null);
    vi.mocked(simulationApi.stopSimulationSession).mockResolvedValue({
      sessionId: 'session-1',
      action: 'stop',
      status: 'accepted',
    });
    vi.mocked(simulationApi.setSimulationSpeed).mockResolvedValue(null);
    simulationControl = useSimulationControl(ref(1));
  });

  describe('Initial State', () => {
    it('should initialize with correct default values', () => {
      expect(simulationControl.isRunning.value).toBe(false);
      expect(simulationControl.isPaused.value).toBe(false);
      expect(simulationControl.currentTime.value).toBe(0);
      expect(simulationControl.speed.value).toBe(1);
    });

    it('should have all required methods', () => {
      expect(typeof simulationControl.start).toBe('function');
      expect(typeof simulationControl.pause).toBe('function');
      expect(typeof simulationControl.resume).toBe('function');
      expect(typeof simulationControl.stop).toBe('function');
      expect(typeof simulationControl.setSpeed).toBe('function');
    });
  });

  describe('Start Simulation', () => {
    it('should start simulation successfully', async () => {
      await simulationControl.start();

      expect(simulationControl.isRunning.value).toBe(true);
      expect(simulationControl.isPaused.value).toBe(false);
      expect(simulationApi.createSimulationSession).toHaveBeenCalledWith(
        expect.objectContaining({ projectId: 1 })
      );
      expect(simulationApi.startSimulationSession).toHaveBeenCalledWith('session-1', {
        speed: 1,
      });
    });

    it('should handle start simulation error', async () => {
      vi.mocked(simulationApi.createSimulationSession).mockRejectedValue(new Error('Start failed'));

      await expect(simulationControl.start()).rejects.toThrow('Start failed');
      expect(simulationControl.isRunning.value).toBe(false);
    });

    it('should reject start if already running', async () => {
      await simulationControl.start();

      await expect(simulationControl.start()).rejects.toThrow('当前状态不允许启动仿真');
    });
  });

  describe('Pause Simulation', () => {
    it('should pause running simulation', async () => {
      await simulationControl.start();
      await simulationControl.pause();

      expect(simulationControl.isPaused.value).toBe(true);
      expect(simulationControl.isRunning.value).toBe(false);
      expect(simulationApi.pauseSimulationSession).toHaveBeenCalledWith('session-1');
    });

    it('should reject pause if not running', async () => {
      await expect(simulationControl.pause()).rejects.toThrow('当前状态不允许暂停仿真');
      expect(simulationApi.pauseSimulationSession).not.toHaveBeenCalled();
    });
  });

  describe('Resume Simulation', () => {
    it('should resume paused simulation', async () => {
      await simulationControl.start();
      await simulationControl.pause();
      await simulationControl.resume();

      expect(simulationControl.isPaused.value).toBe(false);
      expect(simulationControl.isRunning.value).toBe(true);
      expect(simulationApi.resumeSimulationSession).toHaveBeenCalledWith('session-1');
    });

    it('should reject resume if not paused', async () => {
      await expect(simulationControl.resume()).rejects.toThrow('仿真会话不存在');
      expect(simulationApi.resumeSimulationSession).not.toHaveBeenCalled();
    });
  });

  describe('Stop Simulation', () => {
    it('should stop running simulation', async () => {
      await simulationControl.start();
      await simulationControl.stop();

      expect(simulationControl.isRunning.value).toBe(false);
      expect(simulationControl.isPaused.value).toBe(false);
      expect(simulationControl.isStopped.value).toBe(true);
      expect(simulationApi.stopSimulationSession).toHaveBeenCalledWith('session-1');
    });

    it('should preserve elapsed time and speed when stopping', async () => {
      await simulationControl.start();
      simulationControl.currentTime.value = 100;
      simulationControl.speed.value = 2;

      await simulationControl.stop();

      expect(simulationControl.currentTime.value).toBe(100);
      expect(simulationControl.speed.value).toBe(2);
    });
  });

  describe('Speed Control', () => {
    it('should set simulation speed', async () => {
      await simulationControl.setSpeed(2);
      expect(simulationControl.speed.value).toBe(2);
    });

    it('should clamp speed range', async () => {
      await simulationControl.setSpeed(0.5);
      expect(simulationControl.speed.value).toBe(0.5);

      await simulationControl.setSpeed(10);
      expect(simulationControl.speed.value).toBe(4);
    });

    it('should clamp invalid speed values', async () => {
      await simulationControl.setSpeed(0);
      expect(simulationControl.speed.value).toBe(0.5);

      await simulationControl.setSpeed(-1);
      expect(simulationControl.speed.value).toBe(0.5);

      await simulationControl.setSpeed(100);
      expect(simulationControl.speed.value).toBe(4);
    });

    it('should handle supported speed presets', async () => {
      const presets = [0.5, 1, 2, 4];

      for (const speed of presets) {
        await simulationControl.setSpeed(speed);
        expect(simulationControl.speed.value).toBe(speed);
      }
    });
  });

  describe('Time Management', () => {
    it('should update current time', () => {
      simulationControl.updateTime(100);
      expect(simulationControl.currentTime.value).toBe(100);
    });

    it('should not allow negative time', () => {
      expect(() => simulationControl.updateTime(-1)).toThrow();
    });

    it('should format time correctly', () => {
      simulationControl.updateTime(3661.5);
      const formatted = simulationControl.formattedTime.value;
      expect(formatted).toMatch(/\d{2}:\d{2}:\d{2}\.\d{3}/);
    });
  });

  describe('State Transitions', () => {
    it('should handle complete lifecycle', async () => {
      await simulationControl.start();
      expect(simulationControl.isRunning.value).toBe(true);

      await simulationControl.pause();
      expect(simulationControl.isPaused.value).toBe(true);

      await simulationControl.resume();
      expect(simulationControl.isPaused.value).toBe(false);

      await simulationControl.stop();
      expect(simulationControl.isRunning.value).toBe(false);
      expect(simulationControl.isStopped.value).toBe(true);
    });

    it('should maintain state consistency', async () => {
      await simulationControl.start();
      expect(simulationControl.isRunning.value).toBe(true);
      expect(simulationControl.isPaused.value).toBe(false);

      await simulationControl.stop();
      expect(simulationControl.isRunning.value).toBe(false);
      expect(simulationControl.isPaused.value).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      vi.mocked(simulationApi.createSimulationSession).mockRejectedValue(
        new Error('Network error')
      );

      await expect(simulationControl.start()).rejects.toThrow('Network error');
      expect(simulationControl.isRunning.value).toBe(false);
    });

    it('should handle timeout errors', async () => {
      vi.mocked(simulationApi.createSimulationSession).mockRejectedValue(new Error('Timeout'));

      await expect(simulationControl.start()).rejects.toThrow('Timeout');
    });

    it('should recover from errors', async () => {
      vi.mocked(simulationApi.createSimulationSession)
        .mockRejectedValueOnce(new Error('Error'))
        .mockResolvedValueOnce({
          sessionId: 'session-1',
          status: 'created',
          message: '仿真会话创建成功',
        });

      await expect(simulationControl.start()).rejects.toThrow();

      await simulationControl.start();
      expect(simulationControl.isRunning.value).toBe(true);
    });
  });
});
