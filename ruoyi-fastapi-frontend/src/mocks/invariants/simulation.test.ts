import { describe, expect, it } from 'vitest';

import { mockDataset } from '../data';

describe('simulation mock invariants', () => {
  it('keeps simulation records traceable to existing project versions', () => {
    const projectIds = new Set(mockDataset.project.projects.map((project) => project.projectId));
    const versionIds = new Set(mockDataset.project.versions.map((version) => version.versionId));

    mockDataset.simulation.sessions.forEach((session) => {
      expect(projectIds.has(session.projectId)).toBe(true);
      expect(versionIds.has(session.versionId)).toBe(true);
      expect(session.status).toBeTruthy();
    });
  });

  it('keeps frame, message, and event session references valid', () => {
    const sessionIds = new Set(mockDataset.simulation.sessions.map((session) => session.sessionId));

    mockDataset.simulation.frames.forEach((frame) => {
      expect(sessionIds.has(frame.sessionId)).toBe(true);
      expect(frame.timestamp).toBeTruthy();
      expect(frame.bandwidthMbps).toBeGreaterThan(0);
    });
    mockDataset.simulation.messages.forEach((message) => {
      expect(sessionIds.has(message.sessionId)).toBe(true);
      expect(message.timestamp).toBeTruthy();
    });
    mockDataset.simulation.events.forEach((event) => {
      expect(sessionIds.has(event.sessionId)).toBe(true);
      expect(event.eventType).toBeTruthy();
    });
  });
});
