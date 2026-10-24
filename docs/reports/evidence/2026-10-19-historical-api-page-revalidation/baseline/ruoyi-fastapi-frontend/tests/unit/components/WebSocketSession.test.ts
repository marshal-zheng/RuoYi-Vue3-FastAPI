import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import { setQuerySession, endQuerySession } from '@/queries/context';
import { useSimulationWebSocket } from '@/views/project/simulation/composables/useSimulationWebSocket';
const requestMock = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: requestMock }));
class Socket {
  static instances: Socket[] = [];
  static OPEN = 1;
  static CONNECTING = 0;
  readyState = 0;
  onopen?: () => void;
  onclose?: () => void;
  onerror?: () => void;
  onmessage?: (event: unknown) => void;
  send = vi.fn();
  constructor(public url: string) {
    Socket.instances.push(this);
  }
  close() {
    this.readyState = 3;
    this.onclose?.();
  }
}
let instance: ReturnType<typeof useSimulationWebSocket>;
let wrapper: ReturnType<typeof mount>;
beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  vi.stubGlobal('WebSocket', Socket);
  Socket.instances = [];
  setQuerySession('qa', ['admin'], []);
  requestMock.mockResolvedValue({ wsTicket: 'ticket' });
  wrapper = mount(
    defineComponent({
      setup() {
        instance = useSimulationWebSocket();
        return () => null;
      },
    })
  );
});
afterEach(() => {
  wrapper.unmount();
  endQuerySession();
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
describe('WebSocket session ownership', () => {
  it('does not reconnect after an explicit disconnect', async () => {
    instance.connect('qa-target');
    await flushPromises();
    instance.disconnect();
    await vi.advanceTimersByTimeAsync(10000);
    expect(Socket.instances).toHaveLength(1);
    expect(requestMock).toHaveBeenCalledOnce();
  });
  it('requests a new ticket after an unexpected close', async () => {
    instance.connect('qa-target');
    await flushPromises();
    Socket.instances[0].close();
    await vi.advanceTimersByTimeAsync(10000);
    await flushPromises();
    expect(requestMock).toHaveBeenCalledTimes(2);
    expect(Socket.instances).toHaveLength(2);
  });
  it('closes when authentication ends and ignores old socket callbacks', async () => {
    instance.connect('qa-target');
    await flushPromises();
    const old = Socket.instances[0];
    endQuerySession();
    old.onopen?.();
    old.onerror?.();
    old.onclose?.();
    await vi.advanceTimersByTimeAsync(10000);
    expect(instance.connected.value).toBe(false);
    expect(Socket.instances).toHaveLength(1);
  });
  it('does not create a socket from a ticket returned after logout', async () => {
    let resolve!: (value: unknown) => void;
    requestMock.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    instance.connect('qa-target');
    endQuerySession();
    resolve({ wsTicket: 'late' });
    await flushPromises();
    expect(Socket.instances).toHaveLength(0);
  });
});
