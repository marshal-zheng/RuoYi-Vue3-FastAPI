import { createHash } from 'node:crypto';
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  cpSync,
  rmSync,
  symlinkSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { describe, expect, it } from 'vitest';

const frontend = process.cwd();
const repo = resolve(frontend, '..');
const generator = resolve(frontend, 'scripts/generate-ai-context.mjs');
const run = (path: string) =>
  spawnSync(process.execPath, [path, '--check'], { encoding: 'utf8', timeout: 10000 });
const targets = [
  'shared/ai-context/manifest.json',
  'ruoyi-fastapi-backend/resources/ai-context/manifest.json',
];

describe('manifest source and deployment drift gate', () => {
  it('regenerates from the static source and excludes all secret metadata', () => {
    expect(run(generator).status).toBe(0);
    const one = readFileSync(join(repo, targets[0]), 'utf8');
    expect(readFileSync(join(repo, targets[1]), 'utf8')).toBe(one);
    expect(one).not.toContain('password');
    expect(one).not.toContain('configValue');
    expect(
      readFileSync(resolve(frontend, 'src/ai-context/manifest-revision.ts'), 'utf8')
    ).toContain(createHash('sha256').update(one).digest('hex'));
  });
  it('fails when two old manifests still match each other after their definition changes', () => {
    const fixture = mkdtempSync(join(tmpdir(), 'aicontext-manifest-'));
    try {
      for (const path of [...targets, 'shared/ai-context/manifest.schema.json']) {
        mkdirSync(resolve(fixture, path, '..'), { recursive: true });
        cpSync(join(repo, path), join(fixture, path));
      }
      for (const path of [
        'scripts/generate-ai-context.mjs',
        'src/ai-context/definitions.ts',
        'src/ai-context/manifest-revision.ts',
      ]) {
        const destination = join(fixture, 'ruoyi-fastapi-frontend', path);
        mkdirSync(resolve(destination, '..'), { recursive: true });
        cpSync(join(frontend, path), destination);
      }
      symlinkSync(
        join(frontend, 'node_modules'),
        join(fixture, 'ruoyi-fastapi-frontend/node_modules'),
        'dir'
      );
      const script = join(fixture, 'ruoyi-fastapi-frontend/scripts/generate-ai-context.mjs');
      expect(run(script).status).toBe(0);
      const source = join(fixture, 'ruoyi-fastapi-frontend/src/ai-context/definitions.ts');
      const old = readFileSync(source, 'utf8');
      writeFileSync(source, old.replace("label: '岗位名称'", "label: '岗位名称更新'"));
      expect(readFileSync(join(fixture, targets[0]), 'utf8')).toBe(
        readFileSync(join(fixture, targets[1]), 'utf8')
      );
      const failed = run(script);
      expect(failed.status).not.toBe(0);
      expect(failed.stderr).toContain('AI manifest drift');
      writeFileSync(
        source,
        old.replace(
          "defaultContextIds: ['configName', 'configKey', 'configType']",
          "defaultContextIds: ['configValue']"
        )
      );
      const secretRef = run(script);
      expect(secretRef.status).not.toBe(0);
      expect(secretRef.stderr).toContain('Invalid AI context purpose reference');
    } finally {
      rmSync(fixture, { recursive: true, force: true });
    }
  });
});
