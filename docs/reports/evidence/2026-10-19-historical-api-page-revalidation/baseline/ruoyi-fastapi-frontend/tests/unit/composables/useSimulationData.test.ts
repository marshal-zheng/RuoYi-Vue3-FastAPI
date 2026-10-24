/**
 * Unit tests for useSimulationData composable
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSimulationData } from '@/views/project/simulation/composables/useSimulationData';

describe('useSimulationData', () => {
  let simulationData: ReturnType<typeof useSimulationData>;

  beforeEach(() => {
    vi.clearAllMocks();
    simulationData = useSimulationData();
  });

  describe('Initial State', () => {
    it('should initialize with empty data', () => {
      expect(simulationData.messages.value).toEqual([]);
      expect(simulationData.alarms.value).toEqual([]);
      expect(simulationData.statistics.value).toEqual({});
    });

    it('should have all required methods', () => {
      expect(typeof simulationData.addMessage).toBe('function');
      expect(typeof simulationData.addAlarm).toBe('function');
      expect(typeof simulationData.updateStatistics).toBe('function');
      expect(typeof simulationData.clear).toBe('function');
    });
  });

  describe('Message Management', () => {
    it('should add message', () => {
      const message = {
        id: 1,
        timestamp: 1000,
        protocol: '1553B',
        source: 'Device1',
        target: 'Device2',
        data: [0x01, 0x02, 0x03],
      };

      simulationData.addMessage(message);

      expect(simulationData.messages.value.length).toBe(1);
      expect(simulationData.messages.value[0]).toEqual(message);
    });

    it('should limit message history size', () => {
      // Add more than max size
      for (let i = 0; i < 1500; i++) {
        simulationData.addMessage({
          id: i,
          timestamp: i * 1000,
          protocol: '1553B',
        });
      }

      // Should keep only last 1000 messages
      expect(simulationData.messages.value.length).toBeLessThanOrEqual(1000);
    });

    it('should filter messages by protocol', () => {
      simulationData.addMessage({ id: 1, protocol: '1553B' });
      simulationData.addMessage({ id: 2, protocol: 'CAN' });
      simulationData.addMessage({ id: 3, protocol: '1553B' });

      const filtered = simulationData.getMessagesByProtocol('1553B');

      expect(filtered.length).toBe(2);
      expect(filtered.every((m) => m.protocol === '1553B')).toBe(true);
    });

    it('should filter messages by time range', () => {
      simulationData.addMessage({ id: 1, timestamp: 1000 });
      simulationData.addMessage({ id: 2, timestamp: 2000 });
      simulationData.addMessage({ id: 3, timestamp: 3000 });

      const filtered = simulationData.getMessagesByTimeRange(1500, 2500);

      expect(filtered.length).toBe(1);
      expect(filtered[0].id).toBe(2);
    });

    it('should get latest messages', () => {
      for (let i = 0; i < 10; i++) {
        simulationData.addMessage({ id: i, timestamp: i * 1000 });
      }

      const latest = simulationData.getLatestMessages(5);

      expect(latest.length).toBe(5);
      expect(latest[0].id).toBe(9); // Most recent first
    });
  });

  describe('Alarm Management', () => {
    it('should add alarm', () => {
      const alarm = {
        id: 1,
        timestamp: 1000,
        level: 'error',
        type: 'message_loss',
        message: 'Message lost',
        device: 'Device1',
      };

      simulationData.addAlarm(alarm);

      expect(simulationData.alarms.value.length).toBe(1);
      expect(simulationData.alarms.value[0]).toEqual(alarm);
    });

    it('should filter alarms by level', () => {
      simulationData.addAlarm({ id: 1, level: 'error' });
      simulationData.addAlarm({ id: 2, level: 'warning' });
      simulationData.addAlarm({ id: 3, level: 'error' });

      const errors = simulationData.getAlarmsByLevel('error');

      expect(errors.length).toBe(2);
      expect(errors.every((a) => a.level === 'error')).toBe(true);
    });

    it('should filter alarms by type', () => {
      simulationData.addAlarm({ id: 1, type: 'message_loss' });
      simulationData.addAlarm({ id: 2, type: 'timing_violation' });
      simulationData.addAlarm({ id: 3, type: 'message_loss' });

      const filtered = simulationData.getAlarmsByType('message_loss');

      expect(filtered.length).toBe(2);
    });

    it('should count alarms by level', () => {
      simulationData.addAlarm({ id: 1, level: 'error' });
      simulationData.addAlarm({ id: 2, level: 'error' });
      simulationData.addAlarm({ id: 3, level: 'warning' });

      const counts = simulationData.getAlarmCounts();

      expect(counts.error).toBe(2);
      expect(counts.warning).toBe(1);
    });

    it('should clear acknowledged alarms', () => {
      simulationData.addAlarm({ id: 1, acknowledged: false });
      simulationData.addAlarm({ id: 2, acknowledged: true });
      simulationData.addAlarm({ id: 3, acknowledged: false });

      simulationData.clearAcknowledgedAlarms();

      expect(simulationData.alarms.value.length).toBe(2);
      expect(simulationData.alarms.value.every((a) => !a.acknowledged)).toBe(true);
    });
  });

  describe('Statistics Management', () => {
    it('should update statistics', () => {
      const stats = {
        total_messages: 1000,
        messages_by_protocol: {
          '1553B': 600,
          CAN: 400,
        },
        bandwidth_usage: {
          peak: 950000,
          average: 500000,
        },
      };

      simulationData.updateStatistics(stats);

      expect(simulationData.statistics.value).toEqual(stats);
    });

    it('should calculate message rate', () => {
      simulationData.updateStatistics({
        total_messages: 1000,
        duration: 10,
      });

      const rate = simulationData.getMessageRate();

      expect(rate).toBe(100); // 1000 messages / 10 seconds
    });

    it('should get protocol distribution', () => {
      simulationData.updateStatistics({
        messages_by_protocol: {
          '1553B': 600,
          CAN: 300,
          RS422: 100,
        },
      });

      const distribution = simulationData.getProtocolDistribution();

      expect(distribution['1553B']).toBe(60); // 60%
      expect(distribution['CAN']).toBe(30); // 30%
      expect(distribution['RS422']).toBe(10); // 10%
    });
  });

  describe('Data Analysis', () => {
    it('should calculate message latency', () => {
      const messages = [
        { id: 1, sent_time: 1000, received_time: 1005 },
        { id: 2, sent_time: 2000, received_time: 2010 },
        { id: 3, sent_time: 3000, received_time: 3003 },
      ];

      messages.forEach((m) => simulationData.addMessage(m));

      const avgLatency = simulationData.getAverageLatency();

      expect(avgLatency).toBeCloseTo(6, 1); // (5 + 10 + 3) / 3
    });

    it('should detect message patterns', () => {
      // Add periodic messages
      for (let i = 0; i < 10; i++) {
        simulationData.addMessage({
          id: i,
          timestamp: i * 100, // Every 100ms
          protocol: '1553B',
        });
      }

      const pattern = simulationData.detectPattern('1553B');

      expect(pattern.isPeriodic).toBe(true);
      expect(pattern.period).toBeCloseTo(100, 1);
    });

    it('should identify communication pairs', () => {
      simulationData.addMessage({ source: 'A', target: 'B' });
      simulationData.addMessage({ source: 'A', target: 'B' });
      simulationData.addMessage({ source: 'B', target: 'C' });

      const pairs = simulationData.getCommunicationPairs();

      expect(pairs['A->B']).toBe(2);
      expect(pairs['B->C']).toBe(1);
    });
  });

  describe('Data Export', () => {
    it('should export messages as CSV', () => {
      simulationData.addMessage({
        id: 1,
        timestamp: 1000,
        protocol: '1553B',
        source: 'A',
        target: 'B',
      });

      const csv = simulationData.exportMessagesCSV();

      expect(csv).toContain('id,timestamp,protocol,source,target');
      expect(csv).toContain('1,1000,1553B,A,B');
    });

    it('should export alarms as JSON', () => {
      simulationData.addAlarm({
        id: 1,
        level: 'error',
        message: 'Test alarm',
      });

      const json = simulationData.exportAlarmsJSON();
      const data = JSON.parse(json);

      expect(data.length).toBe(1);
      expect(data[0].level).toBe('error');
    });

    it('should export statistics summary', () => {
      simulationData.updateStatistics({
        total_messages: 1000,
        total_alarms: 5,
      });

      const summary = simulationData.exportSummary();

      expect(summary.total_messages).toBe(1000);
      expect(summary.total_alarms).toBe(5);
    });
  });

  describe('Clear Data', () => {
    it('should clear all data', () => {
      simulationData.addMessage({ id: 1 });
      simulationData.addAlarm({ id: 1 });
      simulationData.updateStatistics({ total: 100 });

      simulationData.clear();

      expect(simulationData.messages.value).toEqual([]);
      expect(simulationData.alarms.value).toEqual([]);
      expect(simulationData.statistics.value).toEqual({});
    });

    it('should clear only messages', () => {
      simulationData.addMessage({ id: 1 });
      simulationData.addAlarm({ id: 1 });

      simulationData.clearMessages();

      expect(simulationData.messages.value).toEqual([]);
      expect(simulationData.alarms.value.length).toBe(1);
    });

    it('should clear only alarms', () => {
      simulationData.addMessage({ id: 1 });
      simulationData.addAlarm({ id: 1 });

      simulationData.clearAlarms();

      expect(simulationData.messages.value.length).toBe(1);
      expect(simulationData.alarms.value).toEqual([]);
    });
  });

  describe('Real-time Updates', () => {
    it('should handle rapid message additions', () => {
      const startTime = Date.now();

      for (let i = 0; i < 100; i++) {
        simulationData.addMessage({
          id: i,
          timestamp: startTime + i,
        });
      }

      expect(simulationData.messages.value.length).toBe(100);
    });

    it('should maintain chronological order', () => {
      simulationData.addMessage({ id: 3, timestamp: 3000 });
      simulationData.addMessage({ id: 1, timestamp: 1000 });
      simulationData.addMessage({ id: 2, timestamp: 2000 });

      const messages = simulationData.messages.value;

      for (let i = 1; i < messages.length; i++) {
        expect(messages[i].timestamp).toBeGreaterThanOrEqual(messages[i - 1].timestamp ?? 0);
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message list', () => {
      expect(simulationData.getLatestMessages(10)).toEqual([]);
      expect(simulationData.getAverageLatency()).toBe(0);
    });

    it('should handle invalid protocol filter', () => {
      simulationData.addMessage({ id: 1, protocol: '1553B' });

      const filtered = simulationData.getMessagesByProtocol('INVALID');

      expect(filtered).toEqual([]);
    });

    it('should handle invalid time range', () => {
      simulationData.addMessage({ id: 1, timestamp: 1000 });

      const filtered = simulationData.getMessagesByTimeRange(2000, 3000);

      expect(filtered).toEqual([]);
    });

    it('should handle duplicate message IDs', () => {
      simulationData.addMessage({ id: 1, data: 'first' });
      simulationData.addMessage({ id: 1, data: 'second' });

      // Should keep both or handle appropriately
      expect(simulationData.messages.value.length).toBeGreaterThan(0);
    });
  });

  describe('Performance', () => {
    it('should handle large message volumes efficiently', () => {
      const startTime = performance.now();

      for (let i = 0; i < 10000; i++) {
        simulationData.addMessage({ id: i, timestamp: i });
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should complete in reasonable time (< 1 second)
      expect(duration).toBeLessThan(1000);
    });

    it('should filter large datasets efficiently', () => {
      for (let i = 0; i < 1000; i++) {
        simulationData.addMessage({
          id: i,
          protocol: i % 2 === 0 ? '1553B' : 'CAN',
        });
      }

      const startTime = performance.now();
      const filtered = simulationData.getMessagesByProtocol('1553B');
      const endTime = performance.now();

      expect(filtered.length).toBe(500);
      expect(endTime - startTime).toBeLessThan(100); // < 100ms
    });
  });
});
