import { readFile } from 'node:fs/promises';
import path from 'node:path';
import postcss from 'postcss';
import tailwind from '@tailwindcss/postcss';
import { expect, it } from 'vitest';

it('emits layout defaults with resets below utilities in the application CSS pipeline', async () => {
  const stylesRoot = path.resolve(process.cwd(), 'src/assets/styles');
  const outputs: string[] = [];
  // This is the same stylesheet order used by the application entry.
  for (const name of ['index.css', 'tailwind.css']) {
    const from = path.join(stylesRoot, name);
    const input = await readFile(from, 'utf8');
    const result = await postcss([tailwind()]).process(input, { from });
    outputs.push(result.css);
  }

  const css = postcss.parse(outputs.join('\n'));
  const layers: string[] = [];
  for (const node of css.nodes) {
    if (node.type !== 'atrule' || node.name !== 'layer') continue;
    for (const name of node.params.split(',').map((part) => part.trim())) {
      if (!layers.includes(name)) layers.push(name);
    }
  }
  expect(layers).toContain('base');
  expect(layers).toContain('utilities');
  expect(layers.indexOf('base')).toBeLessThan(layers.indexOf('utilities'));

  const defaults = new Map<string, string>();
  css.walkDecls((declaration) => {
    if (declaration.prop.startsWith('--')) {
      defaults.set(declaration.prop, declaration.value);
    }
  });
  expect(defaults.get('--spacing')).toBe('0.25rem');
  expect(defaults.get('--text-2xl')).toBe('1.5rem');
});
