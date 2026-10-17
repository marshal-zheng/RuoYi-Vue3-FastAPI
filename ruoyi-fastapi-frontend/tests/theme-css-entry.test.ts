import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
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

it('scans application templates without turning automation selectors into utilities', async () => {
  const from = path.resolve(process.cwd(), 'src/assets/styles/tailwind.css');
  const input = await readFile(from, 'utf8');
  const { css } = await postcss([tailwind()]).process(input, { from });

  expect(css).toContain('.gap-2');
  expect(css).toContain('.overflow-hidden');
  expect(css).toContain('.items-center');
  expect(css).not.toContain(':visible:is()');
  expect(css).not.toContain('themeId');
});

it('includes production templates while excluding colocated test files and directories', async () => {
  const fixtureRoot = await mkdtemp(path.join(tmpdir(), 'ruoyi-tailwind-sources-'));
  try {
    const fixtureStyles = path.join(fixtureRoot, 'src/assets/styles');
    const fixtureViews = path.join(fixtureRoot, 'src/views');
    const fixtureTests = path.join(fixtureRoot, 'src/__tests__');
    await Promise.all([
      mkdir(fixtureStyles, { recursive: true }),
      mkdir(fixtureViews, { recursive: true }),
      mkdir(fixtureTests, { recursive: true }),
    ]);
    await Promise.all([
      writeFile(path.join(fixtureRoot, 'index.html'), '<main class="z-[73401]"></main>'),
      writeFile(path.join(fixtureViews, 'Example.vue'), '<div class="z-[73402]"></div>'),
      writeFile(
        path.join(fixtureViews, 'Example.test.ts'),
        'const selector = `[data-case="${unitTestId}"]:visible z-[73403]`;'
      ),
      writeFile(path.join(fixtureViews, 'Example.spec.ts'), 'const selector = "z-[73404]";'),
      writeFile(path.join(fixtureTests, 'fixture.ts'), 'const selector = "z-[73405]";'),
    ]);
    const source = await readFile(
      path.resolve(process.cwd(), 'src/assets/styles/tailwind.css'),
      'utf8'
    );
    const tailwindEntry = createRequire(import.meta.url).resolve('tailwindcss/index.css');
    const declarations = source
      .split('\n')
      .filter((line) => line.startsWith('@import "tailwindcss"') || line.startsWith('@source '))
      .join('\n')
      .replace('"tailwindcss"', JSON.stringify(tailwindEntry));
    const { css } = await postcss([tailwind({ base: fixtureRoot })]).process(declarations, {
      from: path.join(fixtureStyles, 'tailwind.css'),
    });

    expect(css).toContain('.z-\\[73401\\]');
    expect(css).toContain('.z-\\[73402\\]');
    expect(css).not.toContain('.z-\\[73403\\]');
    expect(css).not.toContain('.z-\\[73404\\]');
    expect(css).not.toContain('.z-\\[73405\\]');
    expect(css).not.toContain('unitTestId');
  } finally {
    await rm(fixtureRoot, { recursive: true, force: true });
  }
});
