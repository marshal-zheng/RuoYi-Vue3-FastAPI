#!/usr/bin/env node
'use strict';

/**
 * Init AI Workspace — directory scaffold + command installation + skill install
 * Usage: node scripts/init.js [OPTIONS]
 * Options:
 *   --frontend   Include frontend-conventions skill
 *   --backend    Include backend-conventions skill
 *   --learned    Create docs/learned/
 *   --faq        Create FAQ/
 */

const { execSync } = require('child_process');
const { existsSync, mkdirSync, copyFileSync } = require('fs');
const path = require('path');

const SCRIPT_DIR = __dirname;
const ASSETS_DIR = path.join(SCRIPT_DIR, '..', 'assets', 'commands');

// --- Parse args ---
const args = process.argv.slice(2);
const flags = { frontend: false, backend: false, learned: false, faq: false };

for (const arg of args) {
  switch (arg) {
    case '--frontend': flags.frontend = true; break;
    case '--backend':  flags.backend = true; break;
    case '--learned':  flags.learned = true; break;
    case '--faq':      flags.faq = true; break;
    default:
      console.error(`Unknown option: ${arg}`);
      process.exit(1);
  }
}

console.log('=== 初始化 AI 工作区 ===');
console.log('');

// --- 1. Install/update skills via @tdio/skills CLI ---
const skillOpts = [];
if (flags.frontend) skillOpts.push('--frontend');
if (flags.backend) skillOpts.push('--backend');

const installScript = path.join(SCRIPT_DIR, 'install-skills.js');
execSync(`node "${installScript}" ${skillOpts.join(' ')}`, { stdio: 'inherit' });

// --- 2. Commands (copy from assets, skip existing) ---
console.log('');
console.log('📋 安装 Commands...');

const commandsDir = path.join('.cursor', 'commands');
mkdirSync(commandsDir, { recursive: true });

const COMMANDS = ['faq.md', 'learn.md', 'task-alignment-review.md', 'update-codemaps.md'];

for (const cmd of COMMANDS) {
  const src = path.join(ASSETS_DIR, cmd);
  const dst = path.join(commandsDir, cmd);

  if (!existsSync(src)) {
    console.log(`  ⚠️  ${cmd} 模板不存在于 assets/，跳过`);
  } else if (existsSync(dst)) {
    console.log(`  ⏭️  ${dst} (已存在，跳过)`);
  } else {
    copyFileSync(src, dst);
    console.log(`  ✅ ${dst}`);
  }
}

// --- 3. Required docs directories ---
console.log('');
console.log('📂 创建 docs 目录...');

const requiredDirs = [
  path.join('docs', 'codemaps'),
  path.join('docs', 'plans'),
  path.join('docs', 'specs'),
];

for (const dir of requiredDirs) {
  mkdirSync(dir, { recursive: true });
  console.log(`  ✅ ${dir}/`);
}

// --- 4. Optional directories ---
if (flags.learned) {
  const dir = path.join('docs', 'learned');
  mkdirSync(dir, { recursive: true });
  console.log(`  ✅ ${dir}/`);
}
if (flags.faq) {
  mkdirSync('FAQ', { recursive: true });
  console.log('  ✅ FAQ/');
}

// --- Summary ---
console.log('');
console.log('=== 初始化完成 ===');
console.log('');
console.log('💡 AGENTS.md 将由 Agent 根据你的项目信息单独生成');
