import type { DemoOfflineDb } from '@/demo/db';
import type { DemoTopology } from '@/demo/scenarios';

import { DexieDemoRepository } from './base';

export function createTopologyId(projectId: number, versionId?: number): string {
  return `topology-${projectId}-${versionId ?? 'draft'}`;
}

export class TopologyRepository extends DexieDemoRepository<DemoTopology, string> {
  constructor(private readonly db: DemoOfflineDb) {
    super(db.topologies, 'id');
  }

  getByProject(projectId: number, versionId?: number): Promise<DemoTopology | undefined> {
    return this.db.topologies.get(createTopologyId(projectId, versionId));
  }

  listByProject(projectId: number): Promise<DemoTopology[]> {
    return this.db.topologies.where('projectId').equals(projectId).toArray();
  }

  async removeByProject(projectId: number): Promise<void> {
    await this.db.topologies.where('projectId').equals(projectId).delete();
  }

  async removeByVersion(versionId: number): Promise<void> {
    await this.db.topologies.where('versionId').equals(versionId).delete();
  }

  async saveTopology(input: Omit<DemoTopology, 'id' | 'updateTime'> & Partial<DemoTopology>) {
    const record: DemoTopology = {
      id: input.id ?? createTopologyId(input.projectId, input.versionId),
      projectId: input.projectId,
      versionId: input.versionId,
      graph: input.graph,
      updateTime: input.updateTime ?? new Date().toISOString(),
    };

    await this.db.topologies.put(record);
    return record;
  }
}
