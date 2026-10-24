import { describe, expect, it } from 'vitest';
import { decodeWebSocketMessage } from '@/views/project/simulation/composables/websocket-contract';

/** Frames use the backend's decoded resource shape, without an HTTP envelope. */
describe('simulation WebSocket transport contract', () => {
  it('keeps actual protocol message timestamps and nested protocol values', () => {
    const message = {
      messageId: 'message-1',
      senderNodeId: 'node-1',
      receiverNodeId: 'node-2',
      protocolType: 'CAN',
      sendTimestamp: 1000,
      receiveTimestamp: 1000.1,
      fieldValues: { sequence: 1, metadata: { valid: true }, bytes: [1, 2, null] },
      payloadHex: '0102',
    };
    expect(decodeWebSocketMessage({ type: 'messages', data: [message] })).toEqual({
      type: 'messages',
      data: [message],
    });
  });

  it('accepts nullable fault metadata emitted for an active indefinite fault', () => {
    const fault = {
      fault_id: 'fault-1',
      fault_type: 'disconnect',
      target_id: 'edge-1',
      target_name: null,
      start_at: 1000,
      end_at: null,
      params: { target_name: null },
    };
    const frame = { type: 'faults', data: [{ action: 'created', fault }] };
    expect(decodeWebSocketMessage(frame)).toEqual(frame);
  });

  it.each([
    {
      type: 'status',
      data: { sessionId: 'session-1', status: 'created', messageCount: 0, alarmCount: 0 },
    },
    { type: 'messages', data: [{ timestamp: 1, data: [1, 2] }] },
    { type: 'bandwidth', data: [{ timestamp: 1, bandwidthMbps: 2, loadPercent: 3 }] },
    {
      type: 'alarms',
      data: [
        { alarmId: 'alarm-1', timestamp: 1, severity: 'warning', details: { portId: 'port-1' } },
      ],
    },
    { type: 'animation', data: [{ type: 'traffic', edgeId: 'edge-1' }] },
    { type: 'faults', data: [] },
    { type: 'pong' },
  ])('decodes the $type variant', (frame) => {
    expect(decodeWebSocketMessage(frame)).toEqual(frame);
  });

  it.each([
    null,
    { type: 'unknown', data: [] },
    { type: 'messages', data: {} },
    { type: 'messages', data: [{ payloadHex: 123 }] },
    { type: 'messages', data: [{ fieldValues: { callback: () => true } }] },
    { type: 'bandwidth', data: [{ timestamp: 'bad' }] },
    { type: 'alarms', data: [{ timestamp: 1, details: { connections: [123] } }] },
    { type: 'animation', data: [{ type: 'unknown' }] },
    { type: 'faults', data: [{ fault: { fault_id: 123 } }] },
    {
      type: 'status',
      data: { sessionId: 'session-1', status: 'running', messageCount: 'bad', alarmCount: 0 },
    },
  ])('rejects invalid fields before publishing to reactive consumers', (frame) => {
    expect(decodeWebSocketMessage(frame)).toBeNull();
  });
});
