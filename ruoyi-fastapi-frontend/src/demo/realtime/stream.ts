import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import { DemoSimulationService } from '@/demo/services';

export interface DemoRealtimeClient {
  url: URL;
  send(data: string): void;
  close(code?: number, reason?: string): void;
  addEventListener(
    type: 'message',
    listener: (event: MessageEvent) => void,
    options?: AddEventListenerOptions | boolean
  ): void;
  addEventListener(
    type: 'close',
    listener: (event: CloseEvent) => void,
    options?: AddEventListenerOptions | boolean
  ): void;
}

type DemoRealtimeTimer = ReturnType<typeof setTimeout>;

export class DemoRealtimeStream {
  private readonly timers = new WeakMap<DemoRealtimeClient, Set<DemoRealtimeTimer>>();

  constructor(
    private readonly simulationService: DemoSimulationService,
    private readonly logger: DemoRuntimeLogger
  ) {}

  async start(client: DemoRealtimeClient, sessionId: string): Promise<void> {
    const clientTimers = new Set<DemoRealtimeTimer>();
    this.timers.set(client, clientTimers);

    client.addEventListener('message', (event) => {
      this.handleClientMessage(client, event);
    });
    client.addEventListener('close', () => this.stop(client), {
      once: true,
    });

    const frames = await this.simulationService.listStreamFrames(sessionId);
    frames.forEach((frame) => {
      const timer = setTimeout(() => {
        const activeTimers = this.timers.get(client);
        if (!activeTimers) {
          return;
        }

        activeTimers.delete(timer);
        client.send(
          JSON.stringify({
            type: frame.type,
            data: frame.payload,
          })
        );
      }, frame.delayMs);

      clientTimers.add(timer);
    });

    this.logger.debug('demo-offline 已启动仿真只读事件流。', {
      sessionId,
      frameCount: frames.length,
      url: client.url.toString(),
    });
  }

  stop(client: DemoRealtimeClient): void {
    const clientTimers = this.timers.get(client);
    if (!clientTimers) {
      return;
    }

    clientTimers.forEach((timer) => clearTimeout(timer));
    clientTimers.clear();
    this.timers.delete(client);
  }

  private handleClientMessage(client: DemoRealtimeClient, event: MessageEvent): void {
    let payload: unknown;
    try {
      payload = JSON.parse(String(event.data));
    } catch {
      payload = event.data;
    }

    if (payload && typeof payload === 'object' && (payload as { type?: unknown }).type === 'ping') {
      client.send(
        JSON.stringify({
          type: 'pong',
          data: {},
        })
      );
    }
  }
}
