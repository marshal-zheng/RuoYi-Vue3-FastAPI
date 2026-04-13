import type { DemoOfflineDb } from '@/demo/db';
import type { DemoProjectVersion } from '@/demo/scenarios';

import { DexieDemoRepository } from './base';
import { nextDemoSequence } from './sequences';

export class ProjectVersionRepository extends DexieDemoRepository<DemoProjectVersion, number> {
  constructor(private readonly db: DemoOfflineDb) {
    super(db.projectVersions, 'versionId');
  }

  async listByProject(projectId: number): Promise<DemoProjectVersion[]> {
    return this.db.projectVersions.where('projectId').equals(projectId).toArray();
  }

  async removeByProject(projectId: number): Promise<void> {
    await this.db.projectVersions.where('projectId').equals(projectId).delete();
  }

  override async create(input: Partial<DemoProjectVersion>): Promise<DemoProjectVersion> {
    if (input.projectId === undefined) {
      throw new Error('Demo project version requires projectId.');
    }

    const now = new Date().toISOString();
    const versionId = input.versionId ?? (await nextDemoSequence(this.db, 'projectVersions', 1));
    const record: DemoProjectVersion = {
      ...input,
      versionId,
      projectId: Number(input.projectId),
      versionName: String(input.versionName ?? `演示版本-${versionId}`),
      locked: Boolean(input.locked ?? false),
      status: input.status ?? '0',
      createTime: String(input.createTime ?? now),
      updateTime: String(input.updateTime ?? now),
    };

    await this.db.projectVersions.add(record);
    return record;
  }

  override async update(
    versionId: number,
    patch: Partial<DemoProjectVersion>
  ): Promise<DemoProjectVersion> {
    return super.update(versionId, {
      ...patch,
      updateTime: String(patch.updateTime ?? new Date().toISOString()),
    });
  }
}
