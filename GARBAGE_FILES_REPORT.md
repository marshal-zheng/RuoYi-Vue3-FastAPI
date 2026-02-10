# 垃圾文件和临时文件清理报告

生成时间：2026-02-10

## 🗑️ 需要删除的垃圾文件和临时文件

### 1. 测试覆盖率文件（应删除）

```
.coverage                          # 68KB - pytest 覆盖率数据库文件
tests/coverage/                    # 4.4MB - 覆盖率报告目录
tests/coverage/coverage.json
```

**说明**：测试覆盖率文件是运行测试后自动生成的，不应提交到版本控制。

**清理命令**：
```bash
rm -f .coverage
rm -rf tests/coverage/
```

### 2. 系统缓存文件（应删除）

```
.DS_Store                          # 27+ 个 macOS 系统文件
__pycache__/                       # 多个 Python 字节码缓存目录
*.pyc                             # Python 编译文件（当前已清理）
*.pyo                             # Python 优化编译文件
```

**清理命令**：
```bash
find . -name ".DS_Store" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### 3. 测试缓存目录（应删除）

```
ruoyi-fastapi-backend/.hypothesis/     # 212KB - hypothesis 测试数据
ruoyi-fastapi-backend/.pytest_cache/   # pytest 缓存
```

**清理命令**：
```bash
rm -rf ruoyi-fastapi-backend/.hypothesis/
rm -rf ruoyi-fastapi-backend/.pytest_cache/
```

### 4. 构建产物（应删除）

```
ruoyi-fastapi-frontend/dist/       # 11MB - 前端构建产物
```

**清理命令**：
```bash
rm -rf ruoyi-fastapi-frontend/dist/
```

### 5. 备份文件（应删除）

```
ruoyi-fastapi-frontend/.prettierrc.js.bak
```

**清理命令**：
```bash
find . -name "*.bak" -delete
```

### 6. 日志文件（可选删除）

```
logs/2026-01-28_error.log          # 0B - 空日志
logs/2026-01-30_error.log          # 1.7KB
```

**清理命令**：
```bash
rm -rf logs/
```

## 📄 业务无关的文件（建议处理）

### 1. 空报告文件（应删除）

```
docs/reports/P0_COMPLETION_REPORT.md   # 完全空文件
```

**清理命令**：
```bash
rm docs/reports/P0_COMPLETION_REPORT.md
```

### 2. 已完成的任务报告（可归档）

这些是已完成的 P0 任务报告，建议移到归档目录：

```
docs/reports/P0-001_EVAL_FIX_SUMMARY.md
docs/reports/P0_ALL_TASKS_COMPLETED.md
docs/reports/P0_SECURITY_FIXES_SUMMARY.md
```

**建议操作**：
```bash
# 创建归档目录
mkdir -p docs/archive/p0-tasks

# 移动报告
mv docs/reports/P0*.md docs/archive/p0-tasks/
```

### 3. 临时修复文档（可归档或删除）

```
ruoyi-fastapi-backend/MIGRATION_FIX.md   # 1.4KB - 登录错误修复说明
```

**说明**：这个文档描述了一个已经修复的问题（数据库迁移），建议移到 FAQ 或删除。

**建议操作**：
```bash
# 方案 1：移到 FAQ
mv ruoyi-fastapi-backend/MIGRATION_FIX.md FAQ/数据库迁移修复-登录create_time字段.md

# 方案 2：直接删除（如果问题已解决且不需要记录）
rm ruoyi-fastapi-backend/MIGRATION_FIX.md
```

### 4. Mock Service Worker（MSW）文件（确认是否使用）

```
ruoyi-fastapi-frontend/public/mockServiceWorker.js   # 8.9KB
```

**说明**：这是 MSW (Mock Service Worker) 的运行时文件，用于前端接口 Mock。

**需要确认**：
- 如果项目仍在使用 MSW 进行开发/测试，保留
- 如果已不再使用，可以删除

### 5. AI 工具配置目录（确认是否需要）

```
.agent/rules/global.md              # Agent 规则配置
.trae/rules/project_rules.md        # Trae 规则配置
```

**说明**：这些是 AI 辅助工具的配置文件。

**建议**：
- 如果团队使用这些工具，保留
- 如果不使用，可以删除

### 6. 空目录（应删除）

以下空目录没有任何文件，应该删除：

```
shared/                            # 项目根目录空目录
vf_admin/                         # 已在 .gitignore 但仍存在
ruoyi-fastapi-frontend/openapi/    # 空目录
ruoyi-fastapi-frontend/tests/e2e/  # 空的 E2E 测试目录
ruoyi-fastapi-frontend/tests/unit/mocks/
ruoyi-fastapi-frontend/tests/integration/mocks/
ruoyi-fastapi-frontend/src/mocks/runtime/
ruoyi-fastapi-frontend/src/mocks/generator/audit/
... (共 25+ 个空目录)
```

**清理命令**：
```bash
find . -type d -empty -not -path "./.git/*" -delete
```

## 🚀 一键清理脚本

### 完整清理（推荐）

```bash
#!/bin/bash
# 一键清理所有垃圾文件

echo "清理测试覆盖率文件..."
rm -f .coverage
rm -rf tests/coverage/

echo "清理系统缓存..."
find . -name ".DS_Store" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "清理测试缓存..."
rm -rf ruoyi-fastapi-backend/.hypothesis/
rm -rf ruoyi-fastapi-backend/.pytest_cache/

echo "清理构建产物..."
rm -rf ruoyi-fastapi-frontend/dist/

echo "清理备份文件..."
find . -name "*.bak" -delete
find . -name "*.old" -delete
find . -name "*.tmp" -delete

echo "清理空报告..."
rm -f docs/reports/P0_COMPLETION_REPORT.md

echo "清理日志文件..."
rm -rf logs/

echo "清理空目录..."
find . -type d -empty -not -path "./.git/*" -delete

echo "清理完成！"
```

### 保守清理（只删除明确的垃圾）

```bash
#!/bin/bash
# 保守清理 - 只删除明确无用的文件

echo "清理测试覆盖率文件..."
rm -f .coverage
rm -rf tests/coverage/

echo "清理系统缓存..."
find . -name ".DS_Store" -delete

echo "清理测试缓存..."
rm -rf ruoyi-fastapi-backend/.hypothesis/
rm -rf ruoyi-fastapi-backend/.pytest_cache/

echo "清理备份文件..."
find . -name "*.bak" -delete

echo "清理空报告..."
rm -f docs/reports/P0_COMPLETION_REPORT.md

echo "清理完成！"
```

## 📊 清理效果预估

| 类型 | 文件/目录数 | 大小 |
|------|------------|------|
| 测试覆盖率文件 | 2+ | ~4.5MB |
| 系统缓存 (.DS_Store) | 27+ | ~100KB |
| 测试缓存 (.hypothesis, .pytest_cache) | 2 | ~212KB |
| 构建产物 (dist/) | 1 | ~11MB |
| 备份文件 | 1+ | <1MB |
| 日志文件 | 2 | ~2KB |
| 空目录 | 25+ | 0B |
| **总计** | **60+** | **~16MB** |

## ⚠️ 注意事项

1. **执行前备份**：虽然删除的都是可重新生成的文件，但建议先提交当前更改
2. **确认 MSW**：检查项目是否仍在使用 Mock Service Worker
3. **AI 工具配置**：确认 `.agent/` 和 `.trae/` 是否团队需要
4. **日志文件**：根据需要决定是否保留历史日志

## 🔧 更新 .gitignore

建议在 `.gitignore` 中添加以下规则以防止这些文件再次被提交：

```gitignore
# 测试覆盖率
.coverage
tests/coverage/
htmlcov/
coverage.xml

# 日志
logs/
*.log

# 临时文件
*.bak
*.tmp
*.old
*~

# 空的运行时目录
shared/
vf_admin/

# AI 工具（如果不使用）
# .agent/
# .trae/
```

## ✅ 清理后检查清单

- [ ] 执行清理脚本
- [ ] 运行 `git status` 确认没有误删重要文件
- [ ] 更新 `.gitignore`
- [ ] 重新运行测试确保项目正常
- [ ] 重新构建前端确保构建正常
- [ ] 提交清理后的更改

## 📝 总结

本次排查发现的主要垃圾文件：

1. ✅ **测试覆盖率文件**：.coverage + tests/coverage/ (~4.5MB)
2. ✅ **系统缓存**：27+ 个 .DS_Store 文件
3. ✅ **测试缓存**：.hypothesis + .pytest_cache (~212KB)
4. ✅ **构建产物**：dist/ (~11MB)
5. ✅ **备份文件**：.prettierrc.js.bak
6. ✅ **空目录**：25+ 个空目录
7. ✅ **空报告**：P0_COMPLETION_REPORT.md
8. ⚠️ **日志文件**：logs/ (~2KB) - 可选
9. ⚠️ **临时文档**：MIGRATION_FIX.md - 建议归档
10. ⚠️ **P0 报告**：4 个已完成任务报告 - 建议归档

**建议优先级**：

1. **立即删除**：测试覆盖率、系统缓存、测试缓存、构建产物、备份文件、空目录、空报告
2. **归档处理**：P0 报告、MIGRATION_FIX.md
3. **确认后处理**：MSW 文件、AI 工具配置、日志文件
