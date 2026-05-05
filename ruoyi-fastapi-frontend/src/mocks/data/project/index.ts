import type { ProjectMockData } from '../types';
import { mockProjects } from './projects';
import { mockProjectVersions } from './versions';
import { mockTopologies } from './topologies';

export const projectMockData = {
  projects: mockProjects,
  versions: mockProjectVersions,
  topologies: mockTopologies,
} satisfies ProjectMockData;

export * from './projects';
export * from './topologies';
export * from './versions';
