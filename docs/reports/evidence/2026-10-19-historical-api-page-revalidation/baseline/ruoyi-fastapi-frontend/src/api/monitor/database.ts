import request from '@/utils/request';

export interface DatabasePoolHealth {
  status: 'healthy' | 'warning' | 'critical';
  message: string;
  poolSize: number;
  checkedOut: number;
  overflow: number;
  totalCapacity: number;
  usageRate: number;
  available: number;
}
export interface DatabaseQueryStats {
  totalQueries: number;
  slowQueries: number;
  slowQueryRate: string;
  avgTimeMs: string;
  maxTimeMs: string;
  nPlusOneDetected: number;
}
export function getDatabasePoolHealth(signal: AbortSignal) {
  return request<DatabasePoolHealth>({ url: '/health/db', signal, feedback: { mode: 'silent' } });
}
export function getDatabaseQueryStats(signal: AbortSignal) {
  return request<DatabaseQueryStats>({
    url: '/health/query-stats',
    signal,
    feedback: { mode: 'silent' },
  });
}
