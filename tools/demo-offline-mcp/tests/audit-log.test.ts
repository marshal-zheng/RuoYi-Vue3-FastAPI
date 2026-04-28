import fs from 'node:fs/promises';

import { describe, expect, it, vi } from 'vitest';

import { resolveAuditLogPath, withToolAudit } from '../src/audit-log.js';
import { createTempRepoFixture } from '../src/project-paths.js';
import { okEnvelope } from '../src/types.js';

describe('Tool audit log', () => {
  it('writes started and completed JSONL records under the candidate audit directory', async () => {
    const paths = await createTempRepoFixture();
    const stderrSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    try {
      const result = await withToolAudit(
        'demo_offline_test_tool',
        {
          repoRoot: paths.repoRoot,
          input: {
            scenarioId: 'audit-demo',
          },
        },
        async () =>
          okEnvelope('Audit demo completed.', {
            candidateId: 'audit-demo',
            paths: ['ruoyi-fastapi-frontend/src/demo/scenarios/generated/candidates/audit-demo.candidate.ts'],
          })
      );

      expect(result.ok).toBe(true);
      const logPath = await resolveAuditLogPath(paths);
      const records = (await fs.readFile(logPath, 'utf8'))
        .trim()
        .split('\n')
        .map((line) => JSON.parse(line));

      expect(records).toHaveLength(2);
      expect(records[0]).toMatchObject({
        tool: 'demo_offline_test_tool',
        phase: 'started',
        repoRoot: paths.repoRoot,
        runtime: {
          auditSchemaVersion: 2,
          pid: process.pid,
          nodeVersion: process.version,
        },
        input: {
          scenarioId: 'audit-demo',
        },
      });
      expect(records[0].runtime.processStartedAt).toEqual(expect.any(String));
      expect(records[0].runtime.loadedFiles.length).toBeGreaterThan(0);
      expect(records[0].runtime.loadedFiles[0]).toMatchObject({
        path: expect.stringContaining('audit-log'),
        sha256: expect.any(String),
      });
      expect(records[1]).toMatchObject({
        tool: 'demo_offline_test_tool',
        phase: 'succeeded',
        runtime: {
          pid: process.pid,
        },
        output: {
          ok: true,
          data: {
            candidateId: 'audit-demo',
          },
        },
      });
      expect(stderrSpy).toHaveBeenCalledWith(
        expect.stringContaining('audit=ruoyi-fastapi-frontend/src/demo/scenarios/generated/candidates/.audit/demo-offline-mcp.jsonl')
      );
    } finally {
      stderrSpy.mockRestore();
    }
  });

  it('records thrown tool failures before returning the error to the MCP handler', async () => {
    const paths = await createTempRepoFixture();
    const stderrSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    try {
      await expect(
        withToolAudit(
          'demo_offline_failing_tool',
          {
            repoRoot: paths.repoRoot,
            input: {
              candidateId: 'missing',
            },
          },
          async () => {
            throw new Error('candidate missing');
          }
        )
      ).rejects.toThrow('candidate missing');

      const logPath = await resolveAuditLogPath(paths);
      const records = (await fs.readFile(logPath, 'utf8'))
        .trim()
        .split('\n')
        .map((line) => JSON.parse(line));

      expect(records.map((record) => record.phase)).toEqual(['started', 'failed']);
      expect(records[1]).toMatchObject({
        tool: 'demo_offline_failing_tool',
        error: {
          code: 'unexpected_error',
          fixHint: 'Inspect the error details and retry after correcting the input or project state.',
        },
      });
    } finally {
      stderrSpy.mockRestore();
    }
  });
});
