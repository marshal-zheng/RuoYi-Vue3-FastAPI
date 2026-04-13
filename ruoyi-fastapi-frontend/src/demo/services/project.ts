import {
  ProjectRepository,
  ProjectVersionRepository,
  TopologyRepository,
  createTopologyId,
} from '@/demo/repositories';
import type { DemoProject, DemoProjectVersion, DemoRecord, DemoTopology } from '@/demo/scenarios';

import { DemoAuthError } from './auth';

const DEFAULT_PAGE_SIZE = 10;

export interface DemoProjectListQuery {
  pageNum?: number | string;
  pageSize?: number | string;
  projectName?: string;
  beginTime?: string;
  endTime?: string;
}

export interface DemoProjectVersionListQuery {
  pageNum?: number | string;
  pageSize?: number | string;
  projectId?: number | string;
  versionName?: string;
  beginTime?: string;
  endTime?: string;
}

export interface DemoProjectPayload {
  projectId?: number | string | null;
  projectName?: string;
  projectCode?: string;
  projectDesc?: string;
  description?: string;
  remark?: string;
  status?: '0' | '1';
}

export interface DemoProjectVersionPayload {
  versionId?: number | string | null;
  projectId?: number | string | null;
  versionNumber?: string;
  versionName?: string;
  description?: string;
  remark?: string;
  status?: '0' | '1';
  isLocked?: '0' | '1';
}

export interface DemoProjectVersionClonePayload {
  sourceVersionId?: number | string | null;
  versionNumber?: string;
  versionName?: string;
  description?: string;
}

export interface DemoProjectTopologyPayload {
  projectId?: number | string | null;
  versionId?: number | string | null;
  topologyData?: DemoRecord;
}

export interface DemoGeneratedFile {
  filename: string;
  contentType: string;
  body: string;
}

export interface DemoProjectDetail extends DemoProject {
  projectCode: string;
  projectDesc: string;
  description: string;
  createBy: string;
  updateBy: string;
}

export interface DemoProjectVersionDetail extends DemoProjectVersion {
  versionNumber: string;
  description: string;
  isLocked: '0' | '1';
  createBy: string;
  updateBy: string;
  lockedBy?: string;
  lockedTime?: string;
}

export interface DemoProjectTopologyDetail {
  topologyId: string;
  projectId: number;
  versionId?: number;
  topologyData: DemoRecord;
  updateTime: string;
}

export interface DemoPageResult<T> {
  rows: T[];
  total: number;
  pageNum: number;
  pageSize: number;
}

export class DemoProjectError extends DemoAuthError {
  constructor(message: string, status = 400, code = status) {
    super(message, status, code);
    this.name = 'DemoProjectError';
  }
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? null)) as T;
}

function hasText(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function normalizeText(value: unknown, fallback = ''): string {
  return hasText(value) ? value.trim() : fallback;
}

function resolvePage(value: number | string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }

  return Math.floor(parsed);
}

function resolveOptionalNumber(value: number | string | null | undefined): number | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new DemoProjectError('请求参数格式错误', 400);
  }

  return Math.floor(parsed);
}

function ensureNumber(value: number | string | null | undefined, fieldLabel: string): number {
  const parsed = resolveOptionalNumber(value);
  if (!parsed) {
    throw new DemoProjectError(`${fieldLabel}不能为空`, 400);
  }
  return parsed;
}

function withinDateRange(value: string, beginTime?: string, endTime?: string): boolean {
  if (!beginTime && !endTime) {
    return true;
  }

  const current = Date.parse(value);
  if (Number.isNaN(current)) {
    return true;
  }

  if (beginTime) {
    const begin = Date.parse(`${beginTime}T00:00:00`);
    if (!Number.isNaN(begin) && current < begin) {
      return false;
    }
  }

  if (endTime) {
    const end = Date.parse(`${endTime}T23:59:59.999`);
    if (!Number.isNaN(end) && current > end) {
      return false;
    }
  }

  return true;
}

function paginate<T>(rows: T[], pageNum: number, pageSize: number): DemoPageResult<T> {
  const start = (pageNum - 1) * pageSize;

  return {
    rows: rows.slice(start, start + pageSize),
    total: rows.length,
    pageNum,
    pageSize,
  };
}

function sortByUpdateTime<T extends { updateTime?: string; createTime?: string }>(
  left: T,
  right: T
): number {
  const leftTime = Date.parse(left.updateTime ?? left.createTime ?? '') || 0;
  const rightTime = Date.parse(right.updateTime ?? right.createTime ?? '') || 0;

  return rightTime - leftTime;
}

function parseIdList(value: string | number | Array<string | number>): number[] {
  const rawValues = Array.isArray(value) ? value : String(value).split(',');
  const ids = rawValues
    .map((item) => resolveOptionalNumber(item))
    .filter((item): item is number => Boolean(item));

  return Array.from(new Set(ids));
}

function safeFilename(value: string, fallback: string): string {
  const normalized = normalizeText(value, fallback).replace(/[\\/:*?"<>|\s]+/g, '_');
  return normalized || fallback;
}

function normalizeProject(project: DemoProject): DemoProjectDetail {
  const raw = project as DemoProject & Record<string, unknown>;
  const projectId = Number(project.projectId);
  const projectDesc = normalizeText(raw.projectDesc ?? raw.description ?? project.remark, '');
  const createBy = normalizeText(raw.createBy ?? project.owner, 'demo-offline');
  const updateBy = normalizeText(raw.updateBy ?? createBy, createBy);

  return {
    ...raw,
    projectId,
    projectName: normalizeText(project.projectName, `演示项目-${projectId}`),
    projectCode: normalizeText(raw.projectCode, `PRJ-${projectId}`),
    projectDesc,
    description: normalizeText(raw.description, projectDesc),
    remark: normalizeText(project.remark, projectDesc),
    owner: normalizeText(project.owner, createBy),
    createBy,
    updateBy,
    status: project.status ?? '0',
    createTime: normalizeText(project.createTime, new Date().toISOString()),
    updateTime: normalizeText(project.updateTime, project.createTime ?? new Date().toISOString()),
  };
}

function normalizeVersion(version: DemoProjectVersion): DemoProjectVersionDetail {
  const raw = version as DemoProjectVersion & Record<string, unknown>;
  const versionId = Number(version.versionId);
  const isLocked = raw.isLocked === '1' || version.locked ? '1' : '0';
  const description = normalizeText(raw.description ?? version.remark, '');
  const createBy = normalizeText(raw.createBy, 'demo-offline');
  const updateBy = normalizeText(raw.updateBy ?? createBy, createBy);

  return {
    ...raw,
    versionId,
    projectId: Number(version.projectId),
    versionName: normalizeText(version.versionName, `演示版本-${versionId}`),
    versionNumber: normalizeText(raw.versionNumber, `V${versionId}`),
    description,
    remark: normalizeText(version.remark, description),
    status: version.status ?? '0',
    locked: isLocked === '1',
    isLocked,
    createBy,
    updateBy,
    lockedBy: hasText(raw.lockedBy) ? raw.lockedBy.trim() : undefined,
    lockedTime: hasText(raw.lockedTime) ? raw.lockedTime.trim() : undefined,
    createTime: normalizeText(version.createTime, new Date().toISOString()),
    updateTime: normalizeText(version.updateTime, version.createTime ?? new Date().toISOString()),
  };
}

function normalizeTopologyData(graph: DemoRecord | undefined): DemoRecord {
  const raw = graph && typeof graph === 'object' ? deepClone(graph) : {};
  if ('graph' in raw) {
    return raw;
  }

  return {
    ...raw,
    graph: raw,
  };
}

function normalizeTopology(
  topology: DemoTopology | undefined,
  projectId: number,
  versionId?: number
): DemoProjectTopologyDetail {
  return {
    topologyId: topology?.id ?? createTopologyId(projectId, versionId),
    projectId,
    versionId,
    topologyData: normalizeTopologyData(topology?.graph),
    updateTime: normalizeText(topology?.updateTime, new Date().toISOString()),
  };
}

function buildProjectExportBody(
  project: DemoProjectDetail,
  versions: DemoProjectVersionDetail[],
  topologies: DemoProjectTopologyDetail[]
): string {
  return JSON.stringify(
    {
      kind: 'demo-project-export',
      generatedAt: new Date().toISOString(),
      note: 'demo-offline 导出占位文件，仅用于离线演示流程校验。',
      project,
      versions,
      topologies,
    },
    null,
    2
  );
}

function buildVersionExportBody(
  version: DemoProjectVersionDetail,
  topology: DemoProjectTopologyDetail,
  format: 'word' | 'excel' | 'xml',
  imageBase64?: string
): string {
  if (format === 'xml') {
    return [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<demoOfflineVersionExport>',
      `  <versionId>${version.versionId}</versionId>`,
      `  <versionNumber>${version.versionNumber}</versionNumber>`,
      `  <versionName>${version.versionName}</versionName>`,
      `  <description>${version.description}</description>`,
      `  <hasTopology>${String(Boolean(topology.topologyData?.graph))}</hasTopology>`,
      '</demoOfflineVersionExport>',
    ].join('\n');
  }

  return JSON.stringify(
    {
      kind: `demo-version-export-${format}`,
      generatedAt: new Date().toISOString(),
      note: 'demo-offline 导出占位文件，仅用于本地演示下载链路验证。',
      version,
      topology,
      imageBase64Provided: Boolean(imageBase64),
    },
    null,
    2
  );
}

export class DemoProjectService {
  constructor(
    private readonly projectRepository: ProjectRepository,
    private readonly projectVersionRepository: ProjectVersionRepository,
    private readonly topologyRepository: TopologyRepository
  ) {}

  async listProjects(query: DemoProjectListQuery = {}): Promise<DemoPageResult<DemoProjectDetail>> {
    const pageNum = resolvePage(query.pageNum, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const source = await this.projectRepository.list({
      pageNum: 1,
      pageSize: Number.MAX_SAFE_INTEGER,
      filters: {
        projectName: query.projectName,
      },
      sortBy: 'updateTime',
      sortOrder: 'desc',
    });

    const rows = source.rows
      .map(normalizeProject)
      .filter((item) => withinDateRange(item.createTime, query.beginTime, query.endTime))
      .sort(sortByUpdateTime);

    return paginate(rows, pageNum, pageSize);
  }

  async getProject(projectId: number): Promise<DemoProjectDetail> {
    const project = await this.projectRepository.get(projectId);

    if (!project) {
      throw new DemoProjectError('工程不存在或已被删除', 404);
    }

    return normalizeProject(project);
  }

  async createProject(payload: DemoProjectPayload, operator: string): Promise<DemoProjectDetail> {
    const projectName = normalizeText(payload.projectName);
    if (!projectName) {
      throw new DemoProjectError('工程名称不能为空', 400);
    }

    const now = new Date().toISOString();
    const projectDesc = normalizeText(payload.projectDesc ?? payload.description ?? payload.remark);
    const created = await this.projectRepository.create({
      projectName,
      projectCode: normalizeText(payload.projectCode),
      projectDesc,
      description: projectDesc,
      remark: projectDesc,
      owner: operator,
      createBy: operator,
      updateBy: operator,
      status: payload.status ?? '0',
      createTime: now,
      updateTime: now,
    });

    return normalizeProject(created);
  }

  async updateProject(payload: DemoProjectPayload, operator: string): Promise<DemoProjectDetail> {
    const projectId = ensureNumber(payload.projectId, '工程ID');
    const currentProject = await this.getProject(projectId);

    const projectDesc = normalizeText(payload.projectDesc ?? payload.description ?? payload.remark);
    const updated = await this.projectRepository.update(projectId, {
      projectName: normalizeText(payload.projectName, currentProject.projectName),
      projectCode: normalizeText(payload.projectCode, currentProject.projectCode),
      projectDesc: projectDesc || currentProject.projectDesc,
      description: projectDesc || currentProject.description,
      remark: projectDesc || currentProject.remark,
      updateBy: operator,
    });

    return normalizeProject(updated);
  }

  async deleteProjects(projectIds: string | number | Array<string | number>): Promise<void> {
    const ids = parseIdList(projectIds);
    if (!ids.length) {
      throw new DemoProjectError('请选择要删除的工程', 400);
    }

    for (const projectId of ids) {
      await this.getProject(projectId);
      await this.projectVersionRepository.removeByProject(projectId);
      await this.topologyRepository.removeByProject(projectId);
      await this.projectRepository.remove(projectId);
    }
  }

  async listProjectVersions(
    query: DemoProjectVersionListQuery = {}
  ): Promise<DemoPageResult<DemoProjectVersionDetail>> {
    const pageNum = resolvePage(query.pageNum, 1);
    const pageSize = resolvePage(query.pageSize, DEFAULT_PAGE_SIZE);
    const projectId = resolveOptionalNumber(query.projectId);

    if (!projectId) {
      return {
        rows: [],
        total: 0,
        pageNum,
        pageSize,
      };
    }

    await this.getProject(projectId);
    const rows = (await this.projectVersionRepository.listByProject(projectId))
      .map(normalizeVersion)
      .filter((item) =>
        query.versionName
          ? item.versionName.toLowerCase().includes(String(query.versionName).toLowerCase())
          : true
      )
      .filter((item) => withinDateRange(item.createTime, query.beginTime, query.endTime))
      .sort(sortByUpdateTime);

    return paginate(rows, pageNum, pageSize);
  }

  async getProjectVersion(versionId: number): Promise<DemoProjectVersionDetail> {
    const version = await this.projectVersionRepository.get(versionId);

    if (!version) {
      throw new DemoProjectError('版本不存在或已被删除', 404);
    }

    return normalizeVersion(version);
  }

  async createProjectVersion(
    payload: DemoProjectVersionPayload,
    operator: string
  ): Promise<DemoProjectVersionDetail> {
    const projectId = ensureNumber(payload.projectId, '工程ID');
    await this.getProject(projectId);

    const versionName = normalizeText(payload.versionName);
    if (!versionName) {
      throw new DemoProjectError('版本名称不能为空', 400);
    }

    const versionNumber = normalizeText(payload.versionNumber);
    if (!versionNumber) {
      throw new DemoProjectError('版本号不能为空', 400);
    }

    const now = new Date().toISOString();
    const description = normalizeText(payload.description ?? payload.remark);
    const created = await this.projectVersionRepository.create({
      projectId,
      versionName,
      versionNumber,
      description,
      remark: description,
      locked: false,
      isLocked: '0',
      status: payload.status ?? '0',
      createBy: operator,
      updateBy: operator,
      createTime: now,
      updateTime: now,
    });

    return normalizeVersion(created);
  }

  async updateProjectVersion(
    payload: DemoProjectVersionPayload,
    operator: string
  ): Promise<DemoProjectVersionDetail> {
    const versionId = ensureNumber(payload.versionId, '版本ID');
    const currentVersion = await this.getProjectVersion(versionId);
    if (currentVersion.isLocked === '1') {
      throw new DemoProjectError('固化版本不允许编辑', 400);
    }

    const versionName = normalizeText(payload.versionName);
    const versionNumber = normalizeText(payload.versionNumber);
    if (!versionName) {
      throw new DemoProjectError('版本名称不能为空', 400);
    }
    if (!versionNumber) {
      throw new DemoProjectError('版本号不能为空', 400);
    }

    const description = normalizeText(payload.description ?? payload.remark);
    const updated = await this.projectVersionRepository.update(versionId, {
      versionName: versionName || currentVersion.versionName,
      versionNumber: versionNumber || currentVersion.versionNumber,
      description: description || currentVersion.description,
      remark: description || currentVersion.remark,
      updateBy: operator,
    });

    return normalizeVersion(updated);
  }

  async deleteProjectVersions(versionIds: string | number | Array<string | number>): Promise<void> {
    const ids = parseIdList(versionIds);
    if (!ids.length) {
      throw new DemoProjectError('请选择要删除的版本', 400);
    }

    for (const versionId of ids) {
      const currentVersion = await this.getProjectVersion(versionId);
      if (currentVersion.isLocked === '1') {
        throw new DemoProjectError(`版本"${currentVersion.versionName}"已固化，不能删除`, 400);
      }

      await this.topologyRepository.removeByVersion(versionId);
      await this.projectVersionRepository.remove(versionId);
    }
  }

  async cloneProjectVersion(
    payload: DemoProjectVersionClonePayload,
    operator: string
  ): Promise<DemoProjectVersionDetail> {
    const sourceVersionId = ensureNumber(payload.sourceVersionId, '源版本ID');
    const sourceVersion = await this.getProjectVersion(sourceVersionId);
    const versionName = normalizeText(payload.versionName);
    const versionNumber = normalizeText(payload.versionNumber);

    if (!versionName) {
      throw new DemoProjectError('版本名称不能为空', 400);
    }

    if (!versionNumber) {
      throw new DemoProjectError('版本号不能为空', 400);
    }

    const description = normalizeText(payload.description, sourceVersion.description);
    const clonedVersion = await this.createProjectVersion(
      {
        projectId: sourceVersion.projectId,
        versionName,
        versionNumber,
        description,
        status: sourceVersion.status,
      },
      operator
    );

    const sourceTopology = await this.topologyRepository.getByProject(
      sourceVersion.projectId,
      sourceVersion.versionId
    );

    if (sourceTopology) {
      await this.topologyRepository.saveTopology({
        projectId: clonedVersion.projectId,
        versionId: clonedVersion.versionId,
        graph: deepClone(sourceTopology.graph),
      });
    }

    return clonedVersion;
  }

  async lockProjectVersion(
    versionId: number,
    isLocked: '0' | '1',
    operator: string
  ): Promise<DemoProjectVersionDetail> {
    const currentVersion = await this.getProjectVersion(versionId);
    const now = new Date().toISOString();
    const lockState = isLocked === '1';
    const updated = await this.projectVersionRepository.update(versionId, {
      locked: lockState,
      isLocked: lockState ? '1' : '0',
      lockedBy: lockState ? operator : '',
      lockedTime: lockState ? now : '',
      updateBy: operator,
      updateTime: now,
    });

    return normalizeVersion({
      ...updated,
      projectId: currentVersion.projectId,
    });
  }

  async unlockProjectVersions(projectId: number, operator: string): Promise<number> {
    await this.getProject(projectId);
    const versions = await this.projectVersionRepository.listByProject(projectId);

    for (const version of versions) {
      if (version.locked || (version as Record<string, unknown>).isLocked === '1') {
        await this.lockProjectVersion(version.versionId, '0', operator);
      }
    }

    return versions.length;
  }

  async getProjectTopology(
    projectId: number,
    versionId?: number
  ): Promise<DemoProjectTopologyDetail> {
    await this.getProject(projectId);
    if (versionId !== undefined) {
      const version = await this.getProjectVersion(versionId);
      if (version.projectId !== projectId) {
        throw new DemoProjectError('版本不属于当前工程', 400);
      }
    }

    return normalizeTopology(
      await this.topologyRepository.getByProject(projectId, versionId),
      projectId,
      versionId
    );
  }

  async saveProjectTopology(
    payload: DemoProjectTopologyPayload,
    _operator: string
  ): Promise<DemoProjectTopologyDetail> {
    void _operator;
    const projectId = ensureNumber(payload.projectId, '工程ID');
    const versionId = resolveOptionalNumber(payload.versionId);
    await this.getProject(projectId);

    if (!payload.topologyData || typeof payload.topologyData !== 'object') {
      throw new DemoProjectError('拓扑数据不能为空', 400);
    }

    if (versionId !== undefined) {
      const version = await this.getProjectVersion(versionId);
      if (version.projectId !== projectId) {
        throw new DemoProjectError('版本不属于当前工程', 400);
      }
      if (version.isLocked === '1') {
        throw new DemoProjectError('固化版本不允许保存拓扑', 400);
      }
    }

    const saved = await this.topologyRepository.saveTopology({
      projectId,
      versionId,
      graph: deepClone(payload.topologyData),
    });

    return normalizeTopology(saved, projectId, versionId);
  }

  async exportProject(projectId: number): Promise<DemoGeneratedFile> {
    const project = await this.getProject(projectId);
    const versions = (await this.projectVersionRepository.listByProject(projectId)).map(
      normalizeVersion
    );
    const topologies = (await this.topologyRepository.listByProject(projectId)).map((item) =>
      normalizeTopology(item, item.projectId, item.versionId)
    );

    return {
      filename: `${safeFilename(project.projectName, `project-${projectId}`)}.zip`,
      contentType: 'application/zip',
      body: buildProjectExportBody(project, versions, topologies),
    };
  }

  async exportProjects(projectIds: Array<string | number>): Promise<DemoGeneratedFile> {
    const ids = parseIdList(projectIds);
    if (!ids.length) {
      throw new DemoProjectError('请选择要导出的工程', 400);
    }

    const exports = await Promise.all(ids.map((projectId) => this.exportProject(projectId)));

    return {
      filename: `demo-project-batch-${ids.join('-')}.zip`,
      contentType: 'application/zip',
      body: JSON.stringify(
        {
          kind: 'demo-project-batch-export',
          generatedAt: new Date().toISOString(),
          note: 'demo-offline 批量导出占位文件。',
          files: exports.map((item) => ({
            filename: item.filename,
            preview: item.body.slice(0, 200),
          })),
        },
        null,
        2
      ),
    };
  }

  async exportProjectVersion(
    versionId: number,
    format: 'word' | 'excel' | 'xml',
    imageBase64?: string
  ): Promise<DemoGeneratedFile> {
    const version = await this.getProjectVersion(versionId);
    const topology = await this.getProjectTopology(version.projectId, versionId);
    const versionName = safeFilename(version.versionName, `version-${versionId}`);
    const body = buildVersionExportBody(version, topology, format, imageBase64);

    if (format === 'word') {
      return {
        filename: `${versionName}_接口控制文件.doc`,
        contentType: 'application/msword',
        body,
      };
    }

    if (format === 'excel') {
      return {
        filename: `${versionName}_附录表.zip`,
        contentType: 'application/zip',
        body,
      };
    }

    return {
      filename: `${versionName}_接口控制文件.xml`,
      contentType: 'application/xml',
      body,
    };
  }
}
