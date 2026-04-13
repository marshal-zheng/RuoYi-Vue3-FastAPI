import type { DemoOfflineDb } from '@/demo/db';
import type { DemoProject } from '@/demo/scenarios';

import { DexieDemoRepository } from './base';
import { nextDemoSequence } from './sequences';

export class ProjectRepository extends DexieDemoRepository<DemoProject, number> {
  constructor(private readonly db: DemoOfflineDb) {
    super(db.projects, 'projectId');
  }

  override async create(input: Partial<DemoProject>): Promise<DemoProject> {
    const now = new Date().toISOString();
    const projectId = input.projectId ?? (await nextDemoSequence(this.db, 'projects', 1));
    const record: DemoProject = {
      ...input,
      projectId,
      projectName: String(input.projectName ?? `演示项目-${projectId}`),
      status: input.status ?? '0',
      createTime: String(input.createTime ?? now),
      updateTime: String(input.updateTime ?? now),
    };

    await this.db.projects.add(record);
    return record;
  }

  override async update(projectId: number, patch: Partial<DemoProject>): Promise<DemoProject> {
    return super.update(projectId, {
      ...patch,
      updateTime: String(patch.updateTime ?? new Date().toISOString()),
    });
  }
}
