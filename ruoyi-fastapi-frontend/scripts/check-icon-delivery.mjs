/* eslint-disable no-console -- CLI emits the build audit receipt. */
import { readFile } from 'node:fs/promises';
import path from 'node:path';

// Inspect emitted static closures, including lazy business pages. Dynamic
// designer imports are intentionally excluded until the feature is opened.
const buildRoot = path.resolve(process.argv[2] ?? 'dist');
const manifest = JSON.parse(await readFile(path.join(buildRoot, '.vite/manifest.json'), 'utf8'));
const names = new Set(
  JSON.parse(await readFile(new URL('../src/icons/element-names.json', import.meta.url), 'utf8'))
);
const catalog = 'src/views/tool/build/element-catalog.ts';
const picker = 'src/views/tool/build/IconsDialog.vue';
const sources = new Map();
for (const item of Object.values(manifest)) {
  if (item.file.endsWith('.js') && !sources.has(item.file)) {
    sources.set(item.file, await readFile(path.join(buildRoot, item.file), 'utf8'));
  }
}

function inspect(entries) {
  const visited = new Set();
  const files = new Set();
  function visit(key) {
    if (visited.has(key)) return;
    visited.add(key);
    const item = manifest[key];
    if (!item) throw new Error(`Missing manifest dependency: ${key}`);
    files.add(item.file);
    (item.imports ?? []).forEach(visit);
  }
  entries.forEach(visit);
  const code = [...files].map((file) => sources.get(file) ?? '').join('\n');
  const definitions = new Set(
    [...code.matchAll(/\bname\s*:\s*["'](\w+)["']/g)]
      .map((match) => match[1])
      .filter((name) => names.has(name))
  );
  return {
    wholeCatalog: visited.has(catalog) || definitions.size === names.size,
    iconDefinitions: definitions.size,
  };
}

const initial = inspect(Object.keys(manifest).filter((key) => manifest[key].isEntry));
const views = Object.keys(manifest).filter(
  (key) => key.startsWith('src/views/') && key.endsWith('.vue') && key !== picker
);
const violations = views.filter((key) => inspect([key]).wholeCatalog);
const report = {
  initial,
  auditedViews: views.length,
  deferredPicker: !!manifest[picker]?.isDynamicEntry && !!manifest[catalog]?.isDynamicEntry,
  violations,
};
console.log(JSON.stringify(report, null, 2));
if (initial.wholeCatalog || violations.length || !report.deferredPicker) process.exitCode = 1;
