import type { MockTopology } from '../../data';

export interface MockTopologyRepository {
  getByProjectVersion(projectId: number, versionId: number): Promise<MockTopology | undefined>;
  save(projectId: number, versionId: number, graph: unknown): Promise<MockTopology>;
}
