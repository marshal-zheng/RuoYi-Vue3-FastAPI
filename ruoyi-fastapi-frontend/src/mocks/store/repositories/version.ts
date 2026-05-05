import type { MockPage } from '../../contracts';
import type { MockListQuery } from '../../contracts/local';
import type { MockProjectVersion } from '../../data';

export interface MockProjectVersionRepository {
  list(projectId?: number, query?: MockListQuery): Promise<MockPage<MockProjectVersion>>;
  get(versionId: number): Promise<MockProjectVersion | undefined>;
  create(input: Partial<MockProjectVersion>): Promise<MockProjectVersion>;
  update(versionId: number, input: Partial<MockProjectVersion>): Promise<MockProjectVersion>;
  clone(versionId: number, name?: string): Promise<MockProjectVersion>;
  lock(versionId: number): Promise<MockProjectVersion>;
  unlock(versionId: number): Promise<MockProjectVersion>;
  unlockByProject(projectId: number): Promise<number>;
  delete(versionId: number): Promise<void>;
}
