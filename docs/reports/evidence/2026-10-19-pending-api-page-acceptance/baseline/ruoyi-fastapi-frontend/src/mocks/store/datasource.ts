import type { CloneProjectVersionModel } from '@/api/_generated/types.gen';
import type { MockListQuery, MockPage } from '../contracts';
import type {
  MockAccount,
  MockDataset,
  MockDepartment,
  MockDictData,
  MockMenu,
  MockProject,
  MockProjectVersion,
  MockRole,
  MockSimulationEvent,
  MockSimulationFrame,
  MockSimulationMessage,
  MockSimulationSession,
  MockTopology,
} from '../data';
import { MOCK_REFERENCE_TIME, MOCK_TOKEN_ISSUED_AT, mockDataset, offsetMockTime } from '../data';
import { getMockDemoDb, type MockDemoDb } from './db';
import type {
  MockAuthRepository,
  MockAuthSession,
  MockProjectRepository,
  MockProjectVersionRepository,
  MockSimulationReadRepository,
  MockSystemRepository,
  MockTopologyRepository,
} from './repositories';
import { resetMockDemoDb } from './reset';
import { ensureMockDemoDbSeeded } from './seed';

export interface MockDataSource {
  init(): Promise<void>;
  reset(): Promise<void>;
  auth: MockAuthRepository;
  system: MockSystemRepository;
  project: MockProjectRepository;
  version: MockProjectVersionRepository;
  topology: MockTopologyRepository;
  simulation: MockSimulationReadRepository;
}

function toNumber(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function toText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function pageResult<T>(items: T[], query?: MockListQuery): MockPage<T> {
  const page = toNumber(query?.page, 1);
  const pageSize = toNumber(query?.pageSize ?? query?.page_size, 10);
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    pageSize,
  };
}

export class MockRepositoryError extends Error {
  readonly status: number;

  constructor(message: string, status = 400) {
    super(message);
    this.name = 'MockRepositoryError';
    this.status = status;
  }
}

function isVersionLocked(version: MockProjectVersion): boolean {
  return version.locked || version.isLocked === '1';
}

function cloneMockValue<T>(value: T): T {
  if (typeof structuredClone === 'function') {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value)) as T;
}

async function nextSequence(db: MockDemoDb, name: string): Promise<number> {
  const current = await db.sequences.get(name);
  const value = current?.value ?? 1;
  await db.sequences.put({ name, value: value + 1 });
  return value;
}

class DexieAuthRepository implements MockAuthRepository {
  constructor(private readonly db: MockDemoDb) {}

  findAccountByUsername(username: string): Promise<MockAccount | undefined> {
    return this.db.accounts.get(username);
  }

  findSessionByToken(token: string): Promise<MockAuthSession | undefined> {
    return this.db.authSessions.get(token);
  }

  async createSession(username: string): Promise<MockAuthSession> {
    const session = {
      token: `mock-session-${username}-${MOCK_TOKEN_ISSUED_AT}`,
      username,
      expiresAt: offsetMockTime(1),
    } satisfies MockAuthSession;
    await this.db.authSessions.put(session);
    return session;
  }

  async deleteSession(token: string): Promise<void> {
    await this.db.authSessions.delete(token);
  }
}

class DexieSystemRepository implements MockSystemRepository {
  constructor(private readonly db: MockDemoDb) {}

  listMenus(): Promise<MockMenu[]> {
    return this.db.menus.toArray().then((menus) =>
      menus.sort((left, right) => {
        const orderDiff = (left.orderNum ?? left.menuId) - (right.orderNum ?? right.menuId);
        if (orderDiff !== 0) {
          return orderDiff;
        }
        return left.menuId - right.menuId;
      })
    );
  }

  listRoles(): Promise<MockRole[]> {
    return this.db.roles.orderBy('roleId').toArray();
  }

  async listDictData(dictType?: string): Promise<MockDictData[]> {
    if (!dictType) return this.db.dicts.orderBy('id').toArray();
    return this.db.dicts.where('dictType').equals(dictType).sortBy('id');
  }

  listDepartments(): Promise<MockDepartment[]> {
    return this.db.departments.orderBy('deptId').toArray();
  }
}

class DexieProjectRepository implements MockProjectRepository {
  constructor(private readonly db: MockDemoDb) {}

  async list(query?: MockListQuery): Promise<MockPage<MockProject>> {
    const name = toText(query?.projectName ?? query?.project_name);
    const status = toText(query?.status);
    const projects = await this.db.projects.orderBy('projectId').toArray();
    const filtered = projects.filter((project) => {
      if (name && !project.projectName.includes(name)) return false;
      if (status && project.status !== status) return false;
      return true;
    });
    return pageResult(filtered, query);
  }

  get(projectId: number): Promise<MockProject | undefined> {
    return this.db.projects.get(projectId);
  }

  async create(input: Partial<MockProject>): Promise<MockProject> {
    const project = {
      projectId: input.projectId ?? (await nextSequence(this.db, 'projectId')),
      projectName: input.projectName ?? '未命名演示项目',
      status: input.status ?? 'active',
      createTime: input.createTime ?? MOCK_REFERENCE_TIME,
      updateTime: input.updateTime ?? MOCK_REFERENCE_TIME,
    } satisfies MockProject;
    await this.db.projects.put(project);
    return project;
  }

  async update(projectId: number, input: Partial<MockProject>): Promise<MockProject> {
    const current = await this.db.projects.get(projectId);
    if (!current) {
      throw new MockRepositoryError(`工程不存在或已被删除: ${projectId}`, 404);
    }
    const next = {
      ...current,
      ...input,
      projectId,
      updateTime: input.updateTime ?? MOCK_REFERENCE_TIME,
    } satisfies MockProject;
    await this.db.projects.put(next);
    return next;
  }

  async delete(projectId: number): Promise<void> {
    const versions = await this.db.projectVersions.where('projectId').equals(projectId).toArray();
    await this.db.transaction(
      'rw',
      [this.db.projects, this.db.projectVersions, this.db.topologies],
      async () => {
        await this.db.projects.delete(projectId);
        await Promise.all(
          versions.map((version) => this.db.projectVersions.delete(version.versionId))
        );
        await this.db.topologies.where('projectId').equals(projectId).delete();
      }
    );
  }
}

class DexieProjectVersionRepository implements MockProjectVersionRepository {
  constructor(private readonly db: MockDemoDb) {}

  async list(projectId?: number, query?: MockListQuery): Promise<MockPage<MockProjectVersion>> {
    const versions = projectId
      ? await this.db.projectVersions.where('projectId').equals(projectId).sortBy('versionId')
      : await this.db.projectVersions.orderBy('versionId').toArray();
    return pageResult(versions, query);
  }

  get(versionId: number): Promise<MockProjectVersion | undefined> {
    return this.db.projectVersions.get(versionId);
  }

  async create(input: Partial<MockProjectVersion>): Promise<MockProjectVersion> {
    const projectId = Number(input.projectId);
    if (!Number.isFinite(projectId) || projectId <= 0) {
      throw new MockRepositoryError('Mock project version requires projectId', 400);
    }
    const project = await this.db.projects.get(projectId);
    if (!project) {
      throw new MockRepositoryError(`工程不存在或已被删除: ${projectId}`, 404);
    }
    const versionId = input.versionId ?? (await nextSequence(this.db, 'versionId'));
    const locked = input.locked ?? input.isLocked === '1';
    const version = {
      versionId,
      projectId,
      versionName: input.versionName ?? '未命名版本',
      versionNumber: input.versionNumber ?? `V${versionId}`,
      description: input.description ?? input.versionName ?? '未命名版本',
      locked,
      isLocked: locked ? '1' : '0',
      lockedBy: input.lockedBy ?? '',
      lockedTime: input.lockedTime ?? '',
      status: input.status ?? 'draft',
      createTime: input.createTime ?? MOCK_REFERENCE_TIME,
      updateTime: input.updateTime ?? MOCK_REFERENCE_TIME,
    } satisfies MockProjectVersion;
    await this.db.projectVersions.put(version);
    return version;
  }

  async update(versionId: number, input: Partial<MockProjectVersion>): Promise<MockProjectVersion> {
    const current = await this.db.projectVersions.get(versionId);
    if (!current) {
      throw new MockRepositoryError(`版本不存在或已被删除: ${versionId}`, 404);
    }
    if (isVersionLocked(current)) {
      throw new MockRepositoryError('固化版本不允许编辑', 409);
    }
    const nextProjectId = input.projectId ? Number(input.projectId) : current.projectId;
    if (nextProjectId !== current.projectId) {
      const project = await this.db.projects.get(nextProjectId);
      if (!project) {
        throw new MockRepositoryError(`工程不存在或已被删除: ${nextProjectId}`, 404);
      }
    }
    const nextLocked = input.locked ?? (input.isLocked ? input.isLocked === '1' : current.locked);
    const next = {
      ...current,
      ...input,
      versionId,
      projectId: nextProjectId,
      locked: nextLocked,
      isLocked: nextLocked ? '1' : '0',
      updateTime: input.updateTime ?? MOCK_REFERENCE_TIME,
    } satisfies MockProjectVersion;
    await this.db.projectVersions.put(next);
    return next;
  }

  async clone(input: CloneProjectVersionModel): Promise<MockProjectVersion> {
    const current = await this.db.projectVersions.get(input.sourceVersionId);
    if (!current) {
      throw new MockRepositoryError(`版本不存在或已被删除: ${input.sourceVersionId}`, 404);
    }
    const duplicate = await this.db.projectVersions
      .where('projectId')
      .equals(current.projectId)
      .filter((version) => version.versionNumber === input.versionNumber)
      .first();
    if (duplicate) throw new MockRepositoryError(`版本号 ${input.versionNumber} 已存在`, 409);
    const nextVersionId = await nextSequence(this.db, 'versionId');
    const cloned = {
      ...current,
      versionId: nextVersionId,
      versionName: input.versionName,
      versionNumber: input.versionNumber,
      ...(input.description ? { description: input.description } : {}),
      locked: false,
      isLocked: '0',
      lockedBy: '',
      lockedTime: '',
      status: 'draft',
      createTime: MOCK_REFERENCE_TIME,
      updateTime: MOCK_REFERENCE_TIME,
    } satisfies MockProjectVersion;
    await this.db.projectVersions.put(cloned);
    const sourceTopology = await this.db.topologies
      .where('[projectId+versionId]')
      .equals([current.projectId, current.versionId])
      .first();
    if (sourceTopology) {
      await this.db.topologies.put({
        ...sourceTopology,
        id: `topology-${cloned.projectId}-${cloned.versionId}`,
        versionId: cloned.versionId,
        graph: cloneMockValue(sourceTopology.graph),
        updateTime: MOCK_REFERENCE_TIME,
      });
    }
    return cloned;
  }

  async lock(versionId: number): Promise<MockProjectVersion> {
    return this.updateLock(versionId, true);
  }

  async unlock(versionId: number): Promise<MockProjectVersion> {
    return this.updateLock(versionId, false);
  }

  async unlockByProject(projectId: number): Promise<number> {
    const versions = await this.db.projectVersions.where('projectId').equals(projectId).toArray();
    const lockedVersions = versions.filter((version) => version.locked);
    await Promise.all(
      lockedVersions.map((version) =>
        this.db.projectVersions.put({
          ...version,
          locked: false,
          isLocked: '0',
          lockedBy: '',
          lockedTime: '',
          updateTime: MOCK_REFERENCE_TIME,
        })
      )
    );
    return lockedVersions.length;
  }

  async delete(versionId: number): Promise<void> {
    const current = await this.db.projectVersions.get(versionId);
    if (!current) {
      throw new MockRepositoryError(`版本不存在或已被删除: ${versionId}`, 404);
    }
    if (isVersionLocked(current)) {
      throw new MockRepositoryError(`版本"${current.versionName}"已固化，不能删除`, 409);
    }
    await this.db.transaction('rw', [this.db.projectVersions, this.db.topologies], async () => {
      await this.db.projectVersions.delete(versionId);
      await this.db.topologies.where('versionId').equals(versionId).delete();
    });
  }

  private async updateLock(versionId: number, locked: boolean): Promise<MockProjectVersion> {
    const current = await this.db.projectVersions.get(versionId);
    if (!current) {
      throw new MockRepositoryError(`版本不存在或已被删除: ${versionId}`, 404);
    }
    const next = {
      ...current,
      locked,
      isLocked: locked ? '1' : '0',
      lockedBy: locked ? 'mock' : '',
      lockedTime: locked ? MOCK_REFERENCE_TIME : '',
      updateTime: MOCK_REFERENCE_TIME,
    } satisfies MockProjectVersion;
    await this.db.projectVersions.put(next);
    return next;
  }
}

class DexieTopologyRepository implements MockTopologyRepository {
  constructor(private readonly db: MockDemoDb) {}

  getByProjectVersion(projectId: number, versionId: number): Promise<MockTopology | undefined> {
    return this.db.topologies
      .where('[projectId+versionId]')
      .equals([projectId, versionId])
      .first()
      .catch(() =>
        this.db.topologies
          .filter(
            (topology) => topology.projectId === projectId && topology.versionId === versionId
          )
          .first()
      );
  }

  async save(projectId: number, versionId: number, graph: unknown): Promise<MockTopology> {
    const [project, version] = await Promise.all([
      this.db.projects.get(projectId),
      this.db.projectVersions.get(versionId),
    ]);
    if (!project) {
      throw new MockRepositoryError(`工程不存在或已被删除: ${projectId}`, 404);
    }
    if (!version) {
      throw new MockRepositoryError(`版本不存在或已被删除: ${versionId}`, 404);
    }
    if (version.projectId !== projectId) {
      throw new MockRepositoryError('版本不属于当前工程', 404);
    }
    if (isVersionLocked(version)) {
      throw new MockRepositoryError('固化版本不允许保存拓扑', 409);
    }
    if (!graph || typeof graph !== 'object') {
      throw new MockRepositoryError('拓扑数据不能为空', 400);
    }
    const graphData = graph as MockTopology['graph'];
    const existing = await this.getByProjectVersion(projectId, versionId);
    const topology = {
      id: existing?.id ?? `topology-${projectId}-${versionId}`,
      projectId,
      versionId,
      graph: cloneMockValue(graphData),
      updateTime: MOCK_REFERENCE_TIME,
    } satisfies MockTopology;
    await this.db.topologies.put(topology);
    return topology;
  }
}

class DexieSimulationReadRepository implements MockSimulationReadRepository {
  constructor(private readonly db: MockDemoDb) {}

  listSessions(): Promise<MockSimulationSession[]> {
    return this.db.simulationSessions.orderBy('sessionId').toArray();
  }

  getSession(sessionId: string): Promise<MockSimulationSession | undefined> {
    return this.db.simulationSessions.get(sessionId);
  }

  listFrames(sessionId: string): Promise<MockSimulationFrame[]> {
    return this.db.simulationFrames.where('sessionId').equals(sessionId).sortBy('timestamp');
  }

  listMessages(sessionId: string): Promise<MockSimulationMessage[]> {
    return this.db.simulationMessages.where('sessionId').equals(sessionId).sortBy('timestamp');
  }

  listEvents(sessionId: string): Promise<MockSimulationEvent[]> {
    return this.db.simulationEvents.where('sessionId').equals(sessionId).sortBy('triggerTime');
  }
}

export class DexieMockDataSource implements MockDataSource {
  readonly auth: MockAuthRepository;
  readonly system: MockSystemRepository;
  readonly project: MockProjectRepository;
  readonly version: MockProjectVersionRepository;
  readonly topology: MockTopologyRepository;
  readonly simulation: MockSimulationReadRepository;

  constructor(
    private readonly db: MockDemoDb = getMockDemoDb(),
    private readonly dataset: MockDataset = mockDataset
  ) {
    this.auth = new DexieAuthRepository(db);
    this.system = new DexieSystemRepository(db);
    this.project = new DexieProjectRepository(db);
    this.version = new DexieProjectVersionRepository(db);
    this.topology = new DexieTopologyRepository(db);
    this.simulation = new DexieSimulationReadRepository(db);
  }

  init(): Promise<void> {
    return ensureMockDemoDbSeeded(this.db, this.dataset);
  }

  reset(): Promise<void> {
    return resetMockDemoDb(this.db, this.dataset);
  }
}

let mockDataSource: MockDataSource | undefined;

export function createMockDataSource(
  db: MockDemoDb = getMockDemoDb(),
  dataset: MockDataset = mockDataset
) {
  return new DexieMockDataSource(db, dataset);
}

export function getMockDataSource(): MockDataSource {
  if (!mockDataSource) {
    mockDataSource = createMockDataSource();
  }
  return mockDataSource;
}

export function replaceMockDataSource(dataSource: MockDataSource | undefined) {
  mockDataSource = dataSource;
}
