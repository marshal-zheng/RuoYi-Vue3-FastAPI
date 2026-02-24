#!/usr/bin/env node
'use strict';

/**
 * Install / Update AI Workspace Skills
 * Usage: node scripts/install-skills.js [OPTIONS]
 * Options:
 *   --frontend   Include frontend-conventions skill
 *   --backend    Include backend-conventions skill
 *   --repo URL   Override default skills repository
 */

const { execSync } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');

const DEFAULT_REPO = 'git@git.tiduyun.com:fe-infra/td-skills.git';

const REQUIRED_SKILLS = [
  'brainstorming',
  'skill-loader',
  'update-codemaps',
  'writing-plans',
  'writing-skills',
  'writing-specs',
];

// --- Parse args ---
const args = process.argv.slice(2);
let repo = DEFAULT_REPO;
const optionalSkills = [];

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--frontend':
      optionalSkills.push('frontend-conventions');
      break;
    case '--backend':
      optionalSkills.push('backend-conventions');
      break;
    case '--repo':
      repo = args[++i] || DEFAULT_REPO;
      break;
    default:
      if (args[i].startsWith('--repo=')) {
        repo = args[i].split('=')[1];
      }
  }
}

const allSkills = [...REQUIRED_SKILLS, ...optionalSkills];

// --- Check prerequisites ---
try {
  execSync('npx --version', { stdio: 'ignore' });
} catch {
  console.error('❌ 需要 Node.js >= 18（npx 未找到）');
  console.error('   请先安装 Node.js: https://nodejs.org/');
  process.exit(1);
}

console.log(`📦 安装/更新 Skills（仓库: ${repo}）`);
console.log('');

// --- Show install plan ---
for (const skill of allSkills) {
  const skillPath = path.join('.cursor', 'skills', skill, 'SKILL.md');
  const label = existsSync(skillPath) ? '🔄 更新' : '📥 安装';
  console.log(`  ${label}: ${skill}`);
}
console.log('');

// --- Install/update all skills in one batch ---
const skillList = allSkills.join(' ');
const cmd = `npx @tdio/skills add ${repo} --skill ${skillList} -y`;

try {
  execSync(cmd, { stdio: 'inherit' });
} catch (err) {
  console.error('❌ Skills 安装失败，请检查网络和仓库权限');
  process.exit(1);
}

console.log('');
console.log('✅ Skills 安装/更新完成');
