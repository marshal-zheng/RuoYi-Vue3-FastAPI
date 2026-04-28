import 'fake-indexeddb/auto';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { DemoOfflineDb, replaceDemoOfflineDb } from '@/demo/db';
import { createDemoOfflineHandlers } from '@/demo/handlers';
import {
  AuthRepository,
  ProjectRepository,
  ProjectVersionRepository,
  ScenarioRepository,
  SimulationRepository,
  TopologyRepository,
} from '@/demo/repositories';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import {
  candidateScenarioRegistry,
  getDemoScenarioPackage,
  validateDemoScenarioPackage,
} from '@/demo/scenarios';
import { DemoAuthService, DemoProjectService, DemoSimulationService } from '@/demo/services';
import { mockServer, resetMockServerHandlers } from '../../../../../tests/mocks/server';

const candidateScenarioId = process.env.VITE_DEMO_SCENARIO_ID?.trim();
const shouldRunCandidateRuntimeTest =
  process.env.VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS === 'true' && Boolean(candidateScenarioId);
const candidateIt = shouldRunCandidateRuntimeTest ? it : it.skip;

const logger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

function createRuntimeConfig(scenarioId: string): RuntimeConfig {
  return {
    mode: 'demo-offline',
    mockMode: 'pure',
    apiPrefix: '/api',
    scenarioId,
    allowCandidateScenarios: true,
    debug: true,
    source: 'runtime-mode',
  };
}

async function createAuthHeaders(db: DemoOfflineDb): Promise<HeadersInit> {
  const authService = new DemoAuthService(new AuthRepository(db));
  const login = await authService.login({
    username: 'admin',
    password: 'admin123',
  });

  return {
    Authorization: `Bearer ${login.token}`,
    'Content-Type': 'application/json',
  };
}

describe('generated candidate runtime validation', () => {
  afterEach(async () => {
    replaceDemoOfflineDb(undefined);
    resetMockServerHandlers();
  });

  candidateIt('loads the selected candidate through registry, IndexedDB, services, and handlers', async () => {
    const scenarioId = candidateScenarioId!;
    const candidatePackage = candidateScenarioRegistry[scenarioId];

    expect(candidatePackage).toBeDefined();
    expect(getDemoScenarioPackage(scenarioId, { allowCandidateScenarios: true })).toStrictEqual(
      validateDemoScenarioPackage(candidatePackage)
    );

    const db = new DemoOfflineDb(`candidate-runtime-${scenarioId}-${crypto.randomUUID()}`);
    replaceDemoOfflineDb(db);

    try {
      await new ScenarioRepository(db).ensureScenario(candidatePackage);

      const firstProject = candidatePackage.project.projects[0];
      const firstSession = candidatePackage.simulation.sessions[0];

      expect(firstProject).toBeDefined();
      expect(firstSession).toBeDefined();
      await expect(db.projects.count()).resolves.toBeGreaterThan(0);
      await expect(db.simulationSessions.count()).resolves.toBeGreaterThan(0);

      const projectService = new DemoProjectService(
        new ProjectRepository(db),
        new ProjectVersionRepository(db),
        new TopologyRepository(db)
      );
      const simulationService = new DemoSimulationService(
        new ProjectRepository(db),
        new ProjectVersionRepository(db),
        new SimulationRepository(db)
      );

      await expect(projectService.getProject(firstProject.projectId)).resolves.toMatchObject({
        projectId: firstProject.projectId,
        projectName: firstProject.projectName,
      });
      await expect(simulationService.getStatus(firstSession.sessionId)).resolves.toMatchObject({
        sessionId: firstSession.sessionId,
      });

      const runtimeConfig = createRuntimeConfig(scenarioId);
      const headers = await createAuthHeaders(db);
      mockServer.use(...createDemoOfflineHandlers({ config: runtimeConfig, logger }));

      const projectResponse = await fetch(
        `/api/project/list?projectName=${encodeURIComponent(firstProject.projectName)}`,
        { headers }
      );
      const projectPayload = await projectResponse.json();

      expect(projectResponse.status).toBe(200);
      expect(projectPayload.data).toMatchObject({
        total: expect.any(Number),
        items: expect.arrayContaining([
          expect.objectContaining({
            projectId: firstProject.projectId,
          }),
        ]),
      });

      const statusResponse = await fetch(
        `/api/simulation/sessions/${firstSession.sessionId}/status`,
        { headers }
      );
      const statusPayload = await statusResponse.json();

      expect(statusResponse.status).toBe(200);
      expect(statusPayload.data).toMatchObject({
        sessionId: firstSession.sessionId,
      });
    } finally {
      await db.delete();
    }
  });
});
