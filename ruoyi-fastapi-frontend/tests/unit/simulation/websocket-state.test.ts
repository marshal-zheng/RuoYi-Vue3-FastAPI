import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent } from 'vue';
import { mount } from '@vue/test-utils';
import { useSimulationWebSocket } from '@/views/project/simulation/composables/useSimulationWebSocket';
import request from '@/utils/request';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));
vi.mock('element-plus', () => ({ ElMessage: Object.assign(vi.fn(), { error: vi.fn() }) }));

class TestSocket {
  static OPEN = 1;
  static instances: TestSocket[] = [];
  readyState = 1;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  send = vi.fn<(data: string) => void>();
  close = vi.fn();
  constructor(public url: string) {
    TestSocket.instances.push(this);
  }
}

const mountStream = () => {
  let stream: ReturnType<typeof useSimulationWebSocket> | undefined;
  const wrapper = mount(
    defineComponent({
      setup() {
        stream = useSimulationWebSocket();
      },
      render: () => null,
    })
  );
  if (!stream) throw new Error('Stream setup failed');
  return { stream, wrapper };
};

describe('simulation WebSocket state', () => {
  beforeEach(() => {
    TestSocket.instances = [];
    vi.stubGlobal('WebSocket', TestSocket);
    vi.mocked(request).mockResolvedValue({ wsTicket: 'ticket-1' });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('publishes valid deltas and exposes malformed frames as state without replacing prior data', async () => {
    const { stream, wrapper } = mountStream();
    stream.connect('session-1');
    await Promise.resolve();
    const socket = TestSocket.instances[0];
    socket.onmessage?.(
      new MessageEvent('message', {
        data: JSON.stringify({
          type: 'messages',
          data: [{ messageId: 'message-1', sendTimestamp: 1000, payloadHex: 'AA' }],
        }),
      })
    );
    expect(stream.messagesData.value).toHaveLength(1);
    socket.onmessage?.(new MessageEvent('message', { data: '{' }));
    expect(stream.lastError.value).toBeTruthy();
    expect(stream.messagesData.value).toHaveLength(1);
    socket.onmessage?.(
      new MessageEvent('message', { data: JSON.stringify({ type: 'messages', data: {} }) })
    );
    expect(stream.lastError.value).toBe('实时消息格式无效');
    expect(stream.messagesData.value).toHaveLength(1);
    wrapper.unmount();
    expect(socket.close).toHaveBeenCalledOnce();
  });

  it('reports ticket acquisition errors through its reactive error state', async () => {
    vi.mocked(request).mockRejectedValueOnce(new Error('ticket unavailable'));
    const { stream, wrapper } = mountStream();
    stream.connect('session-1');
    await Promise.resolve();
    expect(stream.lastError.value).toBe('ticket unavailable');
    expect(TestSocket.instances).toHaveLength(0);
    wrapper.unmount();
  });
});
