export interface EmbedGrantMessage {
  type: 'RUOYI_EMBED_GRANT';
  grant: string;
  issuedAt: number;
}

export interface EmbedAccessTokenResponse {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  subject?: string;
}

const EMBED_GRANT_MESSAGE_TYPE = 'RUOYI_EMBED_GRANT';

function isEmbedGrantMessage(data: unknown): data is EmbedGrantMessage {
  if (!data || typeof data !== 'object') return false;
  const candidate = data as Partial<EmbedGrantMessage>;
  return (
    candidate.type === EMBED_GRANT_MESSAGE_TYPE &&
    typeof candidate.grant === 'string' &&
    candidate.grant.length > 0 &&
    typeof candidate.issuedAt === 'number'
  );
}

export function sendEmbedGrantMessage(
  targetWindow: Window,
  targetOrigin: string,
  grant: string
): void {
  if (!targetOrigin) {
    throw new Error('targetOrigin 不能为空');
  }
  const payload: EmbedGrantMessage = {
    type: EMBED_GRANT_MESSAGE_TYPE,
    grant,
    issuedAt: Date.now(),
  };
  targetWindow.postMessage(payload, targetOrigin);
}

export function attachEmbedGrantListener(
  allowedOrigins: string[],
  onGrant: (grant: string, sourceOrigin: string) => void
): () => void {
  const whitelist = new Set((allowedOrigins || []).filter(Boolean));
  if (!whitelist.size) {
    throw new Error('allowedOrigins 不能为空');
  }

  const handler = (event: MessageEvent) => {
    if (!whitelist.has(event.origin)) {
      return;
    }
    if (!isEmbedGrantMessage(event.data)) {
      return;
    }
    onGrant(event.data.grant, event.origin);
  };

  window.addEventListener('message', handler);
  return () => {
    window.removeEventListener('message', handler);
  };
}

export async function exchangeEmbedGrant(grant: string): Promise<EmbedAccessTokenResponse> {
  if (!grant) {
    throw new Error('embed grant 不能为空');
  }
  const { default: request } = await import('@/utils/request');
  return request<EmbedAccessTokenResponse>({
    url: '/auth/embed/exchange',
    method: 'post',
    data: { embed_grant: grant },
  });
}
