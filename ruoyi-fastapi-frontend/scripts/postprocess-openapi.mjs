import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const templateDir = resolve(scriptDir, 'openapi-client');
const generatedDir = resolve(process.argv[2] ?? resolve(scriptDir, '../src/api/_generated'));
const manifest = JSON.parse(await readFile(resolve(templateDir, 'manifest.json'), 'utf8'));
const require = createRequire(import.meta.url);
const installedVersion = require('@hey-api/openapi-ts/package.json').version;
if (installedVersion !== manifest.generatorVersion) {
  throw new Error(`Review the SDK templates before using generator ${installedVersion}`);
}
const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const candidates = await Promise.all(
  manifest.files.map(async (entry) => {
    const target = resolve(generatedDir, entry.path);
    const current = await readFile(target);
    const template = await readFile(resolve(templateDir, entry.template));
    const hash = sha256(current);
    if (hash !== entry.upstreamSha256 && hash !== sha256(template)) {
      throw new Error(`Generated SDK structure changed: ${entry.path}; review its owner template`);
    }
    return { target, template };
  })
);
for (const { target, template } of candidates) await writeFile(target, template);
process.stdout.write(
  `Applied ${candidates.length} reviewed SDK templates for @hey-api/openapi-ts ${installedVersion}\n`
);
