import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import {
  ProjectRepository,
  ProjectVersionRepository,
  ScenarioRepository,
  TopologyRepository,
} from '@/demo/repositories';
import { defaultDemoScenario } from '@/demo/scenarios';

import { DemoProjectService } from './project';

let db: DemoOfflineDb;
let projectService: DemoProjectService;

describe('DemoProjectService', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-project-service-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    projectService = new DemoProjectService(
      new ProjectRepository(db),
      new ProjectVersionRepository(db),
      new TopologyRepository(db)
    );
  });

  afterEach(async () => {
    await db.delete();
  });

  it('normalizes project fields and persists project CRUD to IndexedDB', async () => {
    await expect(projectService.listProjects({ projectName: '星载' })).resolves.toMatchObject({
      items: [
        expect.objectContaining({
          projectId: 1001,
          projectName: '星载总线演示项目',
          projectDesc: '默认 demo-offline 项目，可被客户本地修改。',
          createBy: '售前演示组',
        }),
      ],
      total: 1,
    });

    const created = await projectService.createProject(
      {
        projectName: '客户新增工程',
        projectDesc: '离线演示新增',
      },
      'admin'
    );

    expect(created).toMatchObject({
      projectName: '客户新增工程',
      projectDesc: '离线演示新增',
      createBy: 'admin',
      projectCode: expect.stringMatching(/^PRJ-\d+$/),
    });

    const updated = await projectService.updateProject(
      {
        projectId: created.projectId,
        projectName: '客户新增工程-已修改',
        projectDesc: '修改后的描述',
      },
      'admin'
    );

    expect(updated).toMatchObject({
      projectId: created.projectId,
      projectName: '客户新增工程-已修改',
      projectDesc: '修改后的描述',
      updateBy: 'admin',
    });

    await expect(projectService.getProject(created.projectId)).resolves.toMatchObject({
      projectName: '客户新增工程-已修改',
      projectDesc: '修改后的描述',
    });

    await projectService.deleteProjects(created.projectId);

    await expect(projectService.getProject(created.projectId)).rejects.toEqual(
      expect.objectContaining({
        name: 'DemoProjectError',
        status: 404,
      })
    );
  });

  it('supports version clone, lock lifecycle, and topology persistence', async () => {
    await expect(projectService.listProjectVersions({ projectId: 1001 })).resolves.toMatchObject({
      items: [
        expect.objectContaining({
          versionId: 2001,
          projectId: 1001,
          versionName: 'V1.0 演示基线',
          isLocked: '1',
        }),
      ],
      total: 1,
    });

    const cloned = await projectService.cloneProjectVersion(
      {
        sourceVersionId: 2001,
        versionNumber: 'v1.0.1',
        versionName: 'V1.0 演示基线-副本',
        description: '从默认版本克隆',
      },
      'admin'
    );

    expect(cloned).toMatchObject({
      projectId: 1001,
      versionName: 'V1.0 演示基线-副本',
      versionNumber: 'v1.0.1',
      isLocked: '0',
      createBy: 'admin',
    });

    await expect(projectService.getProjectTopology(1001, cloned.versionId)).resolves.toMatchObject({
      projectId: 1001,
      versionId: cloned.versionId,
      topologyData: {
        graph: expect.objectContaining({
          nodes: expect.any(Array),
          edges: expect.any(Array),
        }),
      },
    });

    const locked = await projectService.lockProjectVersion(cloned.versionId, '1', 'admin');
    expect(locked).toMatchObject({
      versionId: cloned.versionId,
      isLocked: '1',
      lockedBy: 'admin',
    });

    await expect(
      projectService.saveProjectTopology(
        {
          projectId: 1001,
          versionId: cloned.versionId,
          topologyData: {
            graph: {
              cells: [{ id: 'locked-node' }],
            },
          },
        },
        'admin'
      )
    ).rejects.toEqual(
      expect.objectContaining({
        name: 'DemoProjectError',
        status: 400,
      })
    );

    await projectService.unlockProjectVersions(1001, 'admin');

    const savedTopology = await projectService.saveProjectTopology(
      {
        projectId: 1001,
        versionId: cloned.versionId,
        topologyData: {
          version: '3.9.0',
          graph: {
            cells: [{ id: 'node-1', shape: 'demo-node' }],
          },
          nodes: [{ id: 'node-1' }],
          edges: [],
        },
      },
      'admin'
    );

    expect(savedTopology).toMatchObject({
      projectId: 1001,
      versionId: cloned.versionId,
      topologyData: {
        graph: {
          cells: [{ id: 'node-1', shape: 'demo-node' }],
        },
      },
    });

    await expect(projectService.getProjectTopology(1001, cloned.versionId)).resolves.toMatchObject({
      topologyData: {
        graph: {
          cells: [{ id: 'node-1', shape: 'demo-node' }],
        },
      },
    });
  });

  it('builds deterministic export placeholder files', async () => {
    const projectFile = await projectService.exportProject(1001);
    const versionFile = await projectService.exportProjectVersion(2001, 'xml');

    expect(projectFile).toMatchObject({
      filename: '星载总线演示项目.zip',
      contentType: 'application/zip',
    });
    expect(projectFile.body).toContain('demo-project-export');

    expect(versionFile).toMatchObject({
      filename: 'V1.0_演示基线_接口控制文件.xml',
      contentType: 'application/xml',
    });
    expect(versionFile.body).toContain('<demoOfflineVersionExport>');
  });
});
