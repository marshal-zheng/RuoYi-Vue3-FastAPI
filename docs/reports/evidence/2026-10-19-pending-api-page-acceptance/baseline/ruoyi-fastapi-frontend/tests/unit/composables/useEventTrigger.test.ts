import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { ref, type Ref } from 'vue';
import type { SimulationEvent } from '@/api/simulation/types';
import {
  useEventTrigger,
  matchCondition,
  ConditionType,
  ActionType,
  CONDITION_TYPE_CONFIG,
  ACTION_TYPE_CONFIG,
} from '@/views/project/simulation/composables/useEventTrigger';
import * as simulationApi from '@/api/simulation/simulation';

// Mock API
vi.mock('@/api/simulation/simulation', () => ({
  createEvent: vi.fn(),
  updateEvent: vi.fn(),
  deleteEvent: vi.fn(),
  triggerEvent: vi.fn(),
  getEvents: vi.fn(),
}));

describe('useEventTrigger', () => {
  let sessionId: Ref<string | null>;

  beforeEach(() => {
    sessionId = ref('test-session-123');
    vi.clearAllMocks();
    vi.mocked(simulationApi.getEvents).mockResolvedValue({ items: [] });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with empty event list', async () => {
      const { eventList, loading } = useEventTrigger(sessionId);
      await Promise.resolve();

      expect(eventList.value).toEqual([]);
      expect(loading.value).toBe(false);
    });

    it('should load events when sessionId is provided', async () => {
      const mockEvents: SimulationEvent[] = [
        { eventId: '1', name: 'Event 1', status: 'pending' },
        { eventId: '2', name: 'Event 2', status: 'triggered' },
      ];

      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: mockEvents,
      });

      const { eventList, loadEvents } = useEventTrigger(sessionId);

      await loadEvents();

      expect(eventList.value).toEqual(mockEvents);
      expect(simulationApi.getEvents).toHaveBeenCalledWith('test-session-123');
    });

    it('should not load events when sessionId is empty', async () => {
      sessionId.value = '';
      const { eventList, loadEvents } = useEventTrigger(sessionId);

      await loadEvents();

      expect(eventList.value).toEqual([]);
      expect(simulationApi.getEvents).not.toHaveBeenCalled();
    });
  });

  describe('Computed Properties', () => {
    it('should calculate pending event count correctly', async () => {
      const mockEvents: SimulationEvent[] = [
        { eventId: '1', name: 'Event 1', status: 'pending' },
        { eventId: '2', name: 'Event 2', status: 'pending' },
        { eventId: '3', name: 'Event 3', status: 'triggered' },
      ];

      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: mockEvents,
      });

      const { pendingEventCount, loadEvents } = useEventTrigger(sessionId);

      await loadEvents();

      expect(pendingEventCount.value).toBe(2);
    });

    it('should calculate triggered event count correctly', async () => {
      const mockEvents: SimulationEvent[] = [
        { eventId: '1', name: 'Event 1', status: 'pending' },
        { eventId: '2', name: 'Event 2', status: 'triggered' },
        { eventId: '3', name: 'Event 3', status: 'triggered' },
      ];

      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: mockEvents,
      });

      const { triggeredEventCount, loadEvents } = useEventTrigger(sessionId);

      await loadEvents();

      expect(triggeredEventCount.value).toBe(2);
    });
  });

  describe('createEvent', () => {
    it('should create event successfully', async () => {
      vi.mocked(simulationApi.createEvent).mockResolvedValue({
        eventId: 'new-event-123',
        name: 'Test Event',
        status: 'pending',
      });

      vi.mocked(simulationApi.getEvents).mockResolvedValue({ items: [] });

      const { createEvent } = useEventTrigger(sessionId);

      const config = {
        name: 'Test Event',
        condition: {
          type: ConditionType.TIME,
          value: { time: 10 },
        },
        action: {
          type: ActionType.LOG,
          params: { message: 'Test log' },
        },
      };

      await createEvent(config);

      expect(simulationApi.createEvent).toHaveBeenCalledWith('test-session-123', {
        name: 'Test Event',
        conditionType: ConditionType.TIME,
        conditionValue: { time: 10 },
        actionType: ActionType.LOG,
        actionParams: { message: 'Test log' },
      });
    });

    it('should throw error when sessionId is empty', async () => {
      sessionId.value = '';
      const { createEvent } = useEventTrigger(sessionId);

      const config = {
        name: 'Test',
        condition: { type: ConditionType.TIME, value: { time: 10 } },
        action: { type: ActionType.LOG, params: {} },
      };

      await expect(createEvent(config)).rejects.toThrow('仿真会话不存在');
    });

    it('should throw error for invalid condition type', async () => {
      const { createEvent } = useEventTrigger(sessionId);

      const config = {
        name: 'Test',
        condition: { type: 'invalid_type', value: {} },
        action: { type: ActionType.LOG, params: {} },
      };

      await expect(createEvent(config)).rejects.toThrow('不支持的条件类型');
    });

    it('should throw error for invalid action type', async () => {
      const { createEvent } = useEventTrigger(sessionId);

      const config = {
        name: 'Test',
        condition: { type: ConditionType.TIME, value: { time: 10 } },
        action: { type: 'invalid_action', params: {} },
      };

      await expect(createEvent(config)).rejects.toThrow('不支持的动作类型');
    });
  });

  describe('updateEvent', () => {
    it('should update event successfully', async () => {
      vi.mocked(simulationApi.updateEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: [{ eventId: 'event-1', name: 'Updated Event', status: 'pending' }],
      });

      const { updateEvent, loadEvents } = useEventTrigger(sessionId);

      await loadEvents();
      await updateEvent('event-1', { name: 'Updated Event' });

      expect(simulationApi.updateEvent).toHaveBeenCalledWith('test-session-123', 'event-1', {
        name: 'Updated Event',
      });
    });

    it('should throw error when sessionId is empty', async () => {
      sessionId.value = '';
      const { updateEvent } = useEventTrigger(sessionId);

      await expect(updateEvent('event-1', {})).rejects.toThrow('仿真会话不存在');
    });
  });

  describe('deleteEvent', () => {
    it('should delete event successfully', async () => {
      vi.mocked(simulationApi.deleteEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({ items: [] });

      const { deleteEvent, eventList } = useEventTrigger(sessionId);

      // Add event first
      eventList.value = [{ eventId: 'event-1', name: 'Test', status: 'pending' }];

      await deleteEvent('event-1');

      expect(simulationApi.deleteEvent).toHaveBeenCalledWith('test-session-123', 'event-1');
    });

    it('should throw error when sessionId is empty', async () => {
      sessionId.value = '';
      const { deleteEvent } = useEventTrigger(sessionId);

      await expect(deleteEvent('event-1')).rejects.toThrow('仿真会话不存在');
    });
  });

  describe('triggerEvent', () => {
    it('should trigger event successfully', async () => {
      vi.mocked(simulationApi.triggerEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: [
          {
            eventId: 'event-1',
            name: 'Test',
            status: 'triggered',
            triggerCount: 1,
          },
        ],
      });

      const { triggerEvent, eventList } = useEventTrigger(sessionId);

      eventList.value = [
        {
          eventId: 'event-1',
          name: 'Test',
          status: 'pending',
          triggerCount: 0,
        },
      ];

      await triggerEvent('event-1');

      expect(simulationApi.triggerEvent).toHaveBeenCalledWith('test-session-123', 'event-1');
    });

    it('should throw error when sessionId is empty', async () => {
      sessionId.value = '';
      const { triggerEvent } = useEventTrigger(sessionId);

      await expect(triggerEvent('event-1')).rejects.toThrow('仿真会话不存在');
    });
  });

  describe('setEventEnabled', () => {
    it('should enable event', async () => {
      vi.mocked(simulationApi.updateEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: [{ eventId: 'event-1', name: 'Test', status: 'pending' }],
      });

      const { setEventEnabled, eventList } = useEventTrigger(sessionId);

      eventList.value = [{ eventId: 'event-1', name: 'Test', status: 'disabled' }];

      await setEventEnabled('event-1', true);

      expect(eventList.value[0].status).toBe('pending');
    });

    it('should disable event', async () => {
      vi.mocked(simulationApi.updateEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: [{ eventId: 'event-1', name: 'Test', status: 'disabled' }],
      });

      const { setEventEnabled, eventList } = useEventTrigger(sessionId);

      eventList.value = [{ eventId: 'event-1', name: 'Test', status: 'pending' }];

      await setEventEnabled('event-1', false);

      expect(eventList.value[0].status).toBe('disabled');
    });
  });

  describe('checkAndTriggerEvents', () => {
    it('keeps automatic triggers pending per event while allowing other events in parallel', async () => {
      const releases: Array<() => void> = [];
      vi.mocked(simulationApi.triggerEvent).mockImplementation(
        () =>
          new Promise<void>((resolve) => {
            releases.push(resolve);
          })
      );
      const { checkAndTriggerEvents, eventList } = useEventTrigger(sessionId);
      await Promise.resolve();
      eventList.value = ['first', 'second'].map((eventId) => ({
        eventId,
        name: eventId,
        status: 'pending',
        condition: { type: ConditionType.TIME, value: { time: 10 } },
        action: { type: ActionType.LOG, params: {} },
      }));
      checkAndTriggerEvents({ elapsedTime: 15 });
      checkAndTriggerEvents({ elapsedTime: 16 });
      expect(simulationApi.triggerEvent).toHaveBeenCalledTimes(2);
      releases.forEach((release) => release());
    });

    it('should trigger matching events', async () => {
      vi.mocked(simulationApi.triggerEvent).mockResolvedValue({});
      vi.mocked(simulationApi.getEvents).mockResolvedValue({ items: [] });

      const { checkAndTriggerEvents, eventList } = useEventTrigger(sessionId);

      eventList.value = [
        {
          eventId: 'event-1',
          name: 'Time Event',
          status: 'pending',
          condition: {
            type: ConditionType.TIME,
            value: { time: 10 },
          },
          action: { type: ActionType.LOG, params: {} },
        },
      ];

      const state = { elapsedTime: 15 };

      checkAndTriggerEvents(state);

      // Wait for async trigger
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(simulationApi.triggerEvent).toHaveBeenCalledWith('test-session-123', 'event-1');
    });

    it('should not trigger non-matching events', () => {
      const { checkAndTriggerEvents, eventList } = useEventTrigger(sessionId);

      eventList.value = [
        {
          eventId: 'event-1',
          name: 'Time Event',
          status: 'pending',
          condition: {
            type: ConditionType.TIME,
            value: { time: 10 },
          },
          action: { type: ActionType.LOG, params: {} },
        },
      ];

      const state = { elapsedTime: 5 };

      checkAndTriggerEvents(state);

      expect(simulationApi.triggerEvent).not.toHaveBeenCalled();
    });
  });

  describe('reset', () => {
    it('should reset event list', async () => {
      vi.mocked(simulationApi.getEvents).mockResolvedValue({
        items: [{ eventId: '1', name: 'Event 1', status: 'pending' }],
      });

      const { eventList, loadEvents, reset } = useEventTrigger(sessionId);

      await loadEvents();
      expect(eventList.value.length).toBe(1);

      reset();
      expect(eventList.value).toEqual([]);
    });
  });
});

describe('matchCondition', () => {
  describe('TIME condition', () => {
    it('should match when elapsed time exceeds threshold', () => {
      const condition = {
        type: ConditionType.TIME,
        value: { time: 10 },
      };
      const state = { elapsedTime: 15 };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should not match when elapsed time is below threshold', () => {
      const condition = {
        type: ConditionType.TIME,
        value: { time: 10 },
      };
      const state = { elapsedTime: 5 };

      expect(matchCondition(condition, state)).toBe(false);
    });
  });

  describe('MESSAGE_COUNT condition', () => {
    it('should match when message count exceeds threshold', () => {
      const condition = {
        type: ConditionType.MESSAGE_COUNT,
        value: { count: 100 },
      };
      const state = { messageCount: 150 };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should not match when message count is below threshold', () => {
      const condition = {
        type: ConditionType.MESSAGE_COUNT,
        value: { count: 100 },
      };
      const state = { messageCount: 50 };

      expect(matchCondition(condition, state)).toBe(false);
    });
  });

  describe('BANDWIDTH_THRESHOLD condition', () => {
    it('should match when specific port bandwidth exceeds threshold', () => {
      const condition = {
        type: ConditionType.BANDWIDTH_THRESHOLD,
        value: { threshold: 80, portId: 'port-1' },
      };
      const state = {
        bandwidthByPort: {
          'port-1': { loadPercent: 85 },
        },
      };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should match when any port bandwidth exceeds threshold', () => {
      const condition = {
        type: ConditionType.BANDWIDTH_THRESHOLD,
        value: { threshold: 80 },
      };
      const state = {
        bandwidthByPort: {
          'port-1': { loadPercent: 70 },
          'port-2': { loadPercent: 90 },
        },
      };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should not match when bandwidth is below threshold', () => {
      const condition = {
        type: ConditionType.BANDWIDTH_THRESHOLD,
        value: { threshold: 80, portId: 'port-1' },
      };
      const state = {
        bandwidthByPort: {
          'port-1': { loadPercent: 70 },
        },
      };

      expect(matchCondition(condition, state)).toBe(false);
    });
  });

  describe('MESSAGE_CONTENT condition', () => {
    it('should match when message contains pattern', () => {
      const condition = {
        type: ConditionType.MESSAGE_CONTENT,
        value: { pattern: 'AA55' },
      };
      const state = {
        latestMessage: {
          payloadHex: 'AA5501020304',
        },
      };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should match when protocol type matches', () => {
      const condition = {
        type: ConditionType.MESSAGE_CONTENT,
        value: { protocolType: 'CAN', pattern: '' },
      };
      const state = {
        latestMessage: {
          protocolType: 'CAN',
          payloadHex: '12345678',
        },
      };

      expect(matchCondition(condition, state)).toBe(true);
    });

    it('should not match when protocol type differs', () => {
      const condition = {
        type: ConditionType.MESSAGE_CONTENT,
        value: { protocolType: 'CAN' },
      };
      const state = {
        latestMessage: {
          protocolType: '1553B',
          payloadHex: '12345678',
        },
      };

      expect(matchCondition(condition, state)).toBe(false);
    });

    it('should not match when no latest message', () => {
      const condition = {
        type: ConditionType.MESSAGE_CONTENT,
        value: { pattern: 'AA55' },
      };
      const state = {};

      expect(matchCondition(condition, state)).toBe(false);
    });
  });

  describe('Edge cases', () => {
    it('should return false for null condition', () => {
      expect(matchCondition(null, { elapsedTime: 10 })).toBe(false);
    });

    it('should return false for null state', () => {
      const condition = {
        type: ConditionType.TIME,
        value: { time: 10 },
      };
      expect(matchCondition(condition, null)).toBe(false);
    });

    it('should return false for unknown condition type', () => {
      const condition = {
        type: 'unknown_type',
        value: {},
      };
      const state = { elapsedTime: 10 };

      expect(matchCondition(condition, state)).toBe(false);
    });
  });
});

describe('Configuration Constants', () => {
  it('should have all condition type configs', () => {
    expect(CONDITION_TYPE_CONFIG).toHaveProperty('manual');
    expect(CONDITION_TYPE_CONFIG).toHaveProperty(ConditionType.TIME);
    expect(CONDITION_TYPE_CONFIG).toHaveProperty(ConditionType.MESSAGE_COUNT);
    expect(CONDITION_TYPE_CONFIG).toHaveProperty(ConditionType.BANDWIDTH_THRESHOLD);
    expect(CONDITION_TYPE_CONFIG).toHaveProperty(ConditionType.MESSAGE_CONTENT);
  });

  it('should have all action type configs', () => {
    expect(ACTION_TYPE_CONFIG).toHaveProperty(ActionType.SEND_COMMAND);
    expect(ACTION_TYPE_CONFIG).toHaveProperty(ActionType.SEND_MESSAGE);
    expect(ACTION_TYPE_CONFIG).toHaveProperty(ActionType.INJECT_FAULT);
    expect(ACTION_TYPE_CONFIG).toHaveProperty(ActionType.PAUSE);
    expect(ACTION_TYPE_CONFIG).toHaveProperty(ActionType.LOG);
  });
});
