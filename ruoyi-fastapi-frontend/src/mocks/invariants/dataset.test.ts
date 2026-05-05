import { describe, expect, it } from 'vitest';

import { MOCK_DATASET_VERSION, MOCK_REFERENCE_TIME, mockDataset } from '../data';
import { fingerprintDataset } from '../store';

describe('mock dataset invariants', () => {
  it('uses the fixed dataset version and reference time', () => {
    expect(mockDataset.version).toBe(MOCK_DATASET_VERSION);
    expect(mockDataset.referenceTime).toBe(MOCK_REFERENCE_TIME);
    expect(fingerprintDataset(mockDataset)).toMatch(/^fnv1a-[a-f0-9]{8}$/);
  });

  it('contains the first-batch domains', () => {
    expect(mockDataset.auth.accounts.length).toBeGreaterThan(0);
    expect(mockDataset.system.menus.length).toBeGreaterThan(0);
    expect(mockDataset.project.projects.length).toBeGreaterThan(0);
    expect(mockDataset.project.versions.length).toBeGreaterThan(0);
    expect(mockDataset.project.topologies.length).toBeGreaterThan(0);
    expect(mockDataset.simulation.sessions.length).toBeGreaterThan(0);
  });
});
