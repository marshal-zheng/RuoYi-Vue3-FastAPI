import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const frontendRoot = path.join(repoRoot, 'ruoyi-fastapi-frontend');

const API_ROOT = path.join(frontendRoot, 'src', 'api');
const REGISTRY_FILE = path.join(frontendRoot, 'src', 'utils', 'feedback', 'registry.ts');
const SOURCE_ROOT = path.join(frontendRoot, 'src');
const MODAL_FILE = path.join(frontendRoot, 'src', 'plugins', 'modal.js');
const CONTRACT_SCAN_DIRS = [
  path.join(frontendRoot, 'src', 'views', 'system'),
  path.join(frontendRoot, 'src', 'views', 'device'),
  path.join(frontendRoot, 'src', 'views', 'project'),
  path.join(frontendRoot, 'src', 'views', 'protocol'),
  path.join(frontendRoot, 'src', 'views', 'monitor'),
  path.join(frontendRoot, 'src', 'views', 'tool'),
  path.join(frontendRoot, 'src', 'components', 'business', 'Device'),
  path.join(frontendRoot, 'src', 'components', 'business', 'Protocol'),
  path.join(frontendRoot, 'src', 'components', 'business', 'Monitor'),
];
const DEMO_AND_MOCK_SCAN_DIRS = [
  path.join(frontendRoot, 'src', 'demo'),
  path.join(frontendRoot, 'src', 'mocks'),
];
const LOCAL_FEEDBACK_ALLOW_COMMENT = 'message-governance-allow-local';

const errors = [];

function walk(dir, matcher) {
  if (!fs.existsSync(dir)) return [];
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walk(fullPath, matcher));
      continue;
    }
    if (matcher(fullPath)) {
      results.push(fullPath);
    }
  }
  return results;
}

function read(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

function relative(filePath) {
  return path.relative(repoRoot, filePath);
}

function addError(filePath, message) {
  errors.push(`${relative(filePath)}: ${message}`);
}

function hasNearbyAllowComment(source, matchIndex) {
  const start = Math.max(0, matchIndex - 240);
  const snippet = source.slice(start, matchIndex);
  return snippet
    .split('\n')
    .slice(-3)
    .some((line) => line.includes(LOCAL_FEEDBACK_ALLOW_COMMENT));
}

function collectRequestBlock(source, startIndex) {
  let depth = 0;
  let inString = false;
  let stringChar = '';
  for (let i = startIndex; i < source.length; i += 1) {
    const char = source[i];
    const prev = source[i - 1];
    if (inString) {
      if (char === stringChar && prev !== '\\') {
        inString = false;
      }
      continue;
    }
    if (char === "'" || char === '"' || char === '`') {
      inString = true;
      stringChar = char;
      continue;
    }
    if (char === '(' || char === '{' || char === '[') depth += 1;
    if (char === ')' || char === '}' || char === ']') depth -= 1;
    if (depth === 0 && source.slice(i, i + 2) === ');') {
      return source.slice(startIndex, i + 2);
    }
  }
  return source.slice(startIndex);
}

function scanApiFiles() {
  const apiFiles = walk(
    API_ROOT,
    (filePath) => /\.(ts|js)$/.test(filePath) && !/\.test\./.test(filePath) && !/\/demo\//.test(filePath)
  );
  const autoKeys = new Set();

  for (const filePath of apiFiles) {
    const source = read(filePath);

    for (const match of source.matchAll(/return\s+request\(\{/g)) {
      const block = collectRequestBlock(source, match.index);
      if (!/method:\s*'(post|put|delete|patch)'/.test(block)) continue;
      if (!/feedback\s*:/.test(block)) {
        addError(filePath, 'mutation request({...}) 缺少 feedback 声明');
      }
      const keyMatch = block.match(/feedback\s*:\s*\{[\s\S]*?mode:\s*'auto'[\s\S]*?key:\s*'([^']+)'/);
      if (keyMatch) autoKeys.add(keyMatch[1]);
    }

    for (const match of source.matchAll(/return\s+request\.(post|put|delete|patch)\(/g)) {
      const block = collectRequestBlock(source, match.index);
      if (!/feedback\s*:/.test(block)) {
        addError(filePath, `mutation request.${match[1]}(...) 缺少 feedback 声明`);
      }
      const keyMatch = block.match(/feedback\s*:\s*\{[\s\S]*?mode:\s*'auto'[\s\S]*?key:\s*'([^']+)'/);
      if (keyMatch) autoKeys.add(keyMatch[1]);
    }
  }

  const registrySource = read(REGISTRY_FILE);
  for (const key of autoKeys) {
    const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (!new RegExp(`['"]${escaped}['"]\\s*:`).test(registrySource)) {
      addError(REGISTRY_FILE, `缺少 feedback registry key: ${key}`);
    }
  }
}

function scanLegacyModalApis() {
  const files = walk(
    SOURCE_ROOT,
    (filePath) => /\.(vue|ts|js)$/.test(filePath) && !/\.test\./.test(filePath) && !/\.spec\./.test(filePath)
  );

  const bannedPatterns = [
    {
      regex: /\$modal\.(msg|notify)(Error|Success|Warning)?\b/g,
      message: '禁止继续使用废弃的 $modal 消息/通知 API，请改用 request feedback 或 ElMessage/ElNotification',
    },
  ];

  for (const filePath of files) {
    const source = read(filePath);
    for (const { regex, message } of bannedPatterns) {
      regex.lastIndex = 0;
      if (regex.test(source)) {
        addError(filePath, message);
      }
    }
  }

  if (fs.existsSync(MODAL_FILE)) {
    const source = read(MODAL_FILE);
    const legacyExportPattern =
      /^\s*(msg|msgError|msgSuccess|msgWarning|notify|notifyError|notifySuccess|notifyWarning)\s*\(/gm;
    for (const match of source.matchAll(legacyExportPattern)) {
      addError(MODAL_FILE, `modal.js 不应重新暴露废弃消息 API: ${match[1]}`);
    }
  }
}

function scanContractConsumers() {
  const files = CONTRACT_SCAN_DIRS.flatMap((dir) =>
    walk(dir, (filePath) => /\.(vue|ts|js)$/.test(filePath) && !/backupindex\.vue$/.test(filePath))
  );

  const bannedPatterns = [
    { regex: /\$modal\.msgSuccess/g, message: '页面层不应直接声明服务端成功提示，请交由 wrapper feedback 处理' },
    { regex: /response\.rows|res\.rows/g, message: '页面层仍在消费旧 rows 列表字段' },
    { regex: /response\.msg|res\.msg/g, message: '页面层仍在消费旧 msg 成功消息字段' },
    { regex: /queryParams\.pageNum|v-model:page="queryParams\.pageNum"|:page\.sync="queryParams\.pageNum"/g, message: '页面层仍在使用旧 pageNum 分页字段' },
    { regex: /\bpageNum\s*:/g, message: '页面层仍在以旧 pageNum 作为请求或路由字段' },
    { regex: /route\.query\.pageNum/g, message: '页面层仍在读取旧 pageNum 路由字段' },
  ];

  for (const filePath of files) {
    const source = read(filePath);
    for (const { regex, message } of bannedPatterns) {
      regex.lastIndex = 0;
      if (regex.test(source)) {
        addError(filePath, message);
      }
    }
  }
}

function scanDirectUiFeedback() {
  const files = CONTRACT_SCAN_DIRS.flatMap((dir) =>
    walk(dir, (filePath) => /\.(vue|ts|js)$/.test(filePath) && !/backupindex\.vue$/.test(filePath))
  );

  const bannedPatterns = [
    {
      regex:
        /El(?:Message|Notification)\.success\(\s*(?:\{\s*message:\s*)?['"`](删除成功|修改成功|保存成功|新增成功|事件创建成功|事件更新成功|事件删除成功|事件已触发)['"`]/g,
      message: '页面层不应直接声明通用 CRUD 成功提示，请改用 wrapper feedback 或显式标注为本地反馈',
    },
    {
      regex: /El(?:Message|Notification)\.error\(\s*['"`]获取数据失败['"`]\s*\)/g,
      message: '页面层不应直接兜底服务端读取失败提示，请交由统一 problem feedback 处理',
    },
    {
      regex: /El(?:Message|Notification)\.error\([^)]*提交失败，请重试[^)]*\)/g,
      message: '页面层不应直接兜底服务端提交失败提示，请交由统一 problem feedback 处理',
    },
  ];

  for (const filePath of files) {
    const source = read(filePath);
    for (const { regex, message } of bannedPatterns) {
      for (const match of source.matchAll(regex)) {
        if (hasNearbyAllowComment(source, match.index ?? 0)) {
          continue;
        }
        addError(filePath, message);
      }
    }
  }
}

function scanDemoAndMocks() {
  const files = DEMO_AND_MOCK_SCAN_DIRS.flatMap((dir) =>
    walk(dir, (filePath) => /\.(ts|js)$/.test(filePath) && !/\.md$/.test(filePath))
  );

  const bannedPatterns = [
    { regex: /\bpageNum\b/g, message: 'demo/mock 代码仍在使用旧 pageNum 字段' },
    { regex: /[A-Za-z0-9_$]\.rows\b/g, message: 'demo/mock 代码仍在消费旧 rows 字段' },
    { regex: /readSearchParam\(request,\s*'pageNum'/g, message: 'demo handler 仍在兼容旧 pageNum 查询参数' },
    { regex: /searchParams\.get\('pageNum'\)/g, message: 'mock handler 仍在兼容旧 pageNum 查询参数' },
  ];

  for (const filePath of files) {
    const source = read(filePath);
    for (const { regex, message } of bannedPatterns) {
      regex.lastIndex = 0;
      if (regex.test(source)) {
        addError(filePath, message);
      }
    }
  }
}

scanApiFiles();
scanLegacyModalApis();
scanContractConsumers();
scanDirectUiFeedback();
scanDemoAndMocks();

if (errors.length > 0) {
  console.error('Frontend message governance check failed:');
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log('Frontend message governance check passed.');
