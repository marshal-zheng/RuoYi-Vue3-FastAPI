#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkSource, UI_SCOPE } from './ui-standards-core.mjs';

const options = { strict: false, format: 'summary', checkRawInput: true };
for (const arg of process.argv.slice(2)) {
  if (arg === '--strict') options.strict = true;
  else if (arg.startsWith('--format=')) options.format = arg.slice(9);
  else if (arg === '--skip-input') options.checkRawInput = false;
  else if (arg === '--help') {
    process.stdout.write(
      'Usage: node scripts/check-ui-standards.mjs [--strict] [--format=summary|json|markdown]\n--skip-input is an implementation-stage diagnostic; CI always enables input checks.\n'
    );
    process.exit(0);
  } else throw new Error(`Unknown argument: ${arg}`);
}
if (!['summary', 'json', 'markdown'].includes(options.format))
  throw new Error(`Unsupported format: ${options.format}`);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const files = [];
function collect(directory) {
  for (const entry of fs.readdirSync(path.resolve(root, directory), { withFileTypes: true })) {
    const file = `${directory}/${entry.name}`;
    if (file === 'src/views/project/simulation' || UI_SCOPE.excludedModules.includes(file))
      continue;
    if (entry.isDirectory()) collect(file);
    else if (
      entry.isFile() &&
      /\.(vue|[cm]?[jt]sx?|css|less|scss)$/.test(file) &&
      !/\.(?:test|spec)\.[cm]?[jt]sx?$/.test(file)
    )
      files.push(file);
  }
}
collect('src');
const violations = files
  .sort()
  .flatMap((filePath) =>
    checkSource(fs.readFileSync(path.resolve(root, filePath), 'utf8'), {
      filePath,
      checkRawInput: options.checkRawInput,
    })
  );
const report = {
  scope: UI_SCOPE,
  checkedFiles: files.length,
  checkRawInput: options.checkRawInput,
  violations,
  passed: violations.length === 0,
};
if (options.format === 'json') process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
else {
  const scope = `Scope: ${UI_SCOPE.include}; excludes only simulation modules (${UI_SCOPE.excludedModules.join(', ')}).`;
  if (options.format === 'markdown')
    process.stdout.write(
      `${scope}\n\nChecked ${files.length} files; ${violations.length} violations.\n\n| File | Line | Rule | Message |\n| --- | --- | --- | --- |\n${violations.map((v) => `| ${v.file} | ${v.line}:${v.column} | ${v.rule} | ${v.message.replaceAll('|', '\\|')} |`).join('\n')}\n`
    );
  else
    process.stdout.write(
      `${scope}\nUI standards: ${files.length} files, ${violations.length} violations${options.checkRawInput ? '' : ' (input migration pending)'}.\n${violations.map((v) => `${v.file}:${v.line}:${v.column} [${v.rule}] ${v.message}`).join('\n')}\n`
    );
}
if (violations.length) process.exitCode = 1;
