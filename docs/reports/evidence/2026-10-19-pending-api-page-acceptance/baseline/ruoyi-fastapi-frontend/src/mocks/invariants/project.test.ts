import { describe, expect, it } from 'vitest';

import { mockDataset } from '../data';

describe('project mock invariants', () => {
  it('keeps project, version, and topology keys unique', () => {
    const projectIds = mockDataset.project.projects.map((project) => project.projectId);
    const versionIds = mockDataset.project.versions.map((version) => version.versionId);
    const topologyIds = mockDataset.project.topologies.map((topology) => topology.id);

    expect(new Set(projectIds).size).toBe(projectIds.length);
    expect(new Set(versionIds).size).toBe(versionIds.length);
    expect(new Set(topologyIds).size).toBe(topologyIds.length);
  });

  it('keeps versions and topologies traceable to projects', () => {
    const projectIds = new Set(mockDataset.project.projects.map((project) => project.projectId));
    const versionIds = new Set(mockDataset.project.versions.map((version) => version.versionId));

    mockDataset.project.projects.forEach((project) => {
      expect(project.projectName).toBeTruthy();
      expect(project.createTime).toBeTruthy();
    });

    mockDataset.project.versions.forEach((version) => {
      expect(projectIds.has(version.projectId)).toBe(true);
      expect(version.versionName).toBeTruthy();
    });

    mockDataset.project.topologies.forEach((topology) => {
      expect(projectIds.has(topology.projectId)).toBe(true);
      expect(versionIds.has(topology.versionId)).toBe(true);
      expect(topology.graph).toBeTruthy();
    });
  });
});
