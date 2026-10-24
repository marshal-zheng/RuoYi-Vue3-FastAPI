import request from '@/utils/request';
import type {
  DashboardPersistenceAdapter,
  DashboardStoredDocument,
} from '@zxio/dashboard/persistence';

export type DashboardScope = 'account' | 'scene';

function conflict(error: unknown): {
  status: 'conflict';
  remote: DashboardStoredDocument | null;
} {
  const problem = (
    error as {
      problem?: {
        status?: number;
        errorCode?: string;
        errors?: { code?: string; remote?: DashboardStoredDocument | null }[];
      };
    }
  )?.problem;
  const detail = problem?.errors?.find((item) => item.code === 'conflict');
  if (
    problem?.status !== 409 ||
    problem.errorCode !== 'dashboard_revision_conflict' ||
    !detail ||
    !('remote' in detail)
  )
    throw error;
  return { status: 'conflict', remote: detail.remote ?? null };
}

/** Identity and permissions are enforced by the server, never supplied in the document. */
export function createDashboardHttpAdapter(scope: DashboardScope): DashboardPersistenceAdapter {
  const url = (key: string) => `/system/dashboard/${scope}/${encodeURIComponent(key)}`;
  const quiet = { silentSuccess: true, silentError: true };
  return {
    load: (key) => request<DashboardStoredDocument | null>({ url: url(key), ...quiet }),
    async save(key, document, expectedRevision) {
      try {
        const snapshot = await request<DashboardStoredDocument>({
          url: url(key),
          method: 'put',
          data: { document, expectedRevision },
          ...quiet,
        });
        return { status: 'saved', snapshot };
      } catch (error) {
        return conflict(error);
      }
    },
    async remove(key, expectedRevision) {
      try {
        await request({
          url: url(key),
          method: 'delete',
          params: { expectedRevision },
          ...quiet,
        });
        return { status: 'removed' };
      } catch (error) {
        return conflict(error);
      }
    },
  };
}
