import request from '@/utils/request';

export interface DevMenuSignaturePayload {
  signature: string;
  syncedAt: string | null;
  lastSyncStatus: 'idle' | 'ok' | 'failed' | string;
}

export function getDevMenuSignature() {
  return request<DevMenuSignaturePayload>({
    url: '/dev/menu/signature',
    method: 'get',
    headers: {
      silentError: true,
    },
  });
}

export interface DevMenuSyncPayload {
  trigger?: string;
  dryRun?: boolean;
}

export function postDevMenuSync(payload: DevMenuSyncPayload) {
  return request({
    url: '/dev/menu/sync',
    method: 'post',
    data: payload,
  });
}
