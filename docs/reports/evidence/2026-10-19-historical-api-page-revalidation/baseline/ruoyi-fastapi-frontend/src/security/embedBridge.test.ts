import { describe, expect, it, vi } from 'vitest';
import { attachEmbedGrantListener, sendEmbedGrantMessage } from '@/security/embedBridge';

describe('embedBridge', () => {
  it('sends grant by postMessage with strict targetOrigin', () => {
    const postMessage = vi.fn();
    const fakeWindow = { postMessage } as unknown as Window;

    sendEmbedGrantMessage(fakeWindow, 'https://parent.example.com', 'grant-1');

    expect(postMessage).toHaveBeenCalledTimes(1);
    const [payload, targetOrigin] = postMessage.mock.calls[0];
    expect(targetOrigin).toBe('https://parent.example.com');
    expect(payload.type).toBe('RUOYI_EMBED_GRANT');
    expect(payload.grant).toBe('grant-1');
  });

  it('accepts only whitelisted origin and message shape', () => {
    const handler = vi.fn();
    const detach = attachEmbedGrantListener(['https://parent.example.com'], handler);

    window.dispatchEvent(
      new MessageEvent('message', {
        origin: 'https://evil.example.com',
        data: { type: 'RUOYI_EMBED_GRANT', grant: 'grant-evil', issuedAt: Date.now() },
      })
    );
    expect(handler).not.toHaveBeenCalled();

    window.dispatchEvent(
      new MessageEvent('message', {
        origin: 'https://parent.example.com',
        data: { type: 'RUOYI_EMBED_GRANT', grant: 'grant-ok', issuedAt: Date.now() },
      })
    );
    expect(handler).toHaveBeenCalledWith('grant-ok', 'https://parent.example.com');

    detach();
  });
});
