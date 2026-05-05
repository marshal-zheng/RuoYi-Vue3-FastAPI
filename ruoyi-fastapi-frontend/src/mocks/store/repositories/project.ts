import type { MockPage } from '../../contracts';
import type { MockListQuery } from '../../contracts/local';
import type { MockProject } from '../../data';

export interface MockProjectRepository {
  list(query?: MockListQuery): Promise<MockPage<MockProject>>;
  get(projectId: number): Promise<MockProject | undefined>;
  create(input: Partial<MockProject>): Promise<MockProject>;
  update(projectId: number, input: Partial<MockProject>): Promise<MockProject>;
  delete(projectId: number): Promise<void>;
}
