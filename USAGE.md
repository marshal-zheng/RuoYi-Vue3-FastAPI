# @tdio/skills 使用文档

> **企业 AI 基础设施 — Agent Skills 统一管理工具**

## 概述

`@tdio/skills` 是基于 [Vercel Labs 官方 skills CLI](https://github.com/vercel-labs/skills) 的**二次扩展版本**，面向企业内部研发团队的 AI 工程化需求，在官方能力基础上增加了：

- **仓库管理（repos）**：注册、克隆企业内部 Git 仓库，统一 skills 来源
- **推送（push）**：将本地修改或新建的 skill 推送回远端仓库，团队协同共享
- **本地路径安装**：直接从本地目录安装 skills，适用于离线或内网环境

> **企业内部 Skills 仓库**：`git@git.tiduyun.com:fe-infra/td-skills.git`

---

## 安装

```bash
# 通过 npx 直接使用（推荐，能及时更新到最近版本特性）
npx @tdio/skills

# 全局安装 skills 命令
npm install -g @tdio/skills
```

![image-20260210115521443](./images/image-20260210115521443.png)要求：Node.js >= 18，已安装 Git。

---

## 一、仓库管理（repos）

管理企业内部 Git 仓库注册表，统一 skills 来源。

### 添加仓库

```bash
# 注册 TIDU 内部仓库（--clone 克隆到本地）
npx @tdio/skills repos add git@git.tiduyun.com:fe-infra/td-skills.git --clone
```

---

## 二、安装 Skills（add）

### 从企业仓库安装

```bash
# 注册 TIDU 内部仓库（--clone 克隆到本地，全局注册）
npx @tdio/skills repos add git@git.tiduyun.com:fe-infra/td-skills.git --clone

# 安装项目级 skills
npx @tdio/skills add td-skills/typescript-best-practices

# 安装全局 skills
npx @tdio/skills add td-skills/typescript-best-practices -g
```

输出示例：
![image-20260210115434249](./images/image-20260210115434249.png)

---

## 三、推送 Skills（push）

将本地修改的 skill 推送回远端中心仓库，实现团队共享。

```bash
# 交互式选择要推送的 skill
npx @tdio/skills push

# 推送指定 skill
npx @tdio/skills push git-commit
```

---

## 四、最佳实践 skills

```
fe-infra/td-skills/           # git@git.tiduyun.com:fe-infra/td-skills.git
├── skills/
│   ├── code-review/
│   │   └── SKILL.md          # 代码审查规范
│   ├── commit-convention/
│   │   └── SKILL.md          # 提交规范
│   ├── api-design/
│   │   └── SKILL.md          # API 设计规范
│   ├── security-checklist/
│   │   └── SKILL.md          # 安全检查清单
│   ├── testing-standards/
│   │   └── SKILL.md          # 测试规范
│   ├── vue2-typescript-standards/
│   │   └── SKILL.md          # Vue 2 TypeScript 编码规范
│   └── internal-framework/
│       └── SKILL.md          # 内部框架使用指南
└── README.md
```

### 项目级安装

```bash
cd my-project && \
	npx @tdio/skills add git@git.tiduyun.com:fe-infra/td-skills.git --skill api-design testing-standards -y
```

### 团队协作流程

```
开发者修改 skill → skills push → 团队成员 skills check → skills update → 全员同步
```

---

## 五、与官方 skills CLI 的区别

| 特性 | 官方 skills | @tdio/skills |
|------|------------|--------------|
| 基础 add/remove/list | ✅ | ✅ |
| GitHub/GitLab 仓库安装 | ✅ | ✅ |
| 本地路径安装 | ✅ | ✅ |
| **仓库注册管理（repos）** | ❌ | ✅ |
| **仓库持久化缓存** | ❌ | ✅ |
| **Skill 推送（push）** | ❌ | ✅ |
| **新 Skill 推送到远端** | ❌ | ✅ |
| **远端冲突处理** | ❌ | ✅ |
| 更新检查 (check/update) | ✅ | ✅ |
| Skill 搜索 (find) | ✅ | ✅ |
| 多 Agent 支持 | ✅ | ✅ |

---

## 六、快速参考卡片

```bash
# === 首次设置 ===
npx @tdio/skills repos add git@git.tiduyun.com:fe-infra/td-skills.git --clone
npx @tdio/skills add git@git.tiduyun.com:fe-infra/td-skills.git --all -g

# === 日常使用 ===
npx @tdio/skills list                                                            # 查看已装
npx @tdio/skills find typescript                                                 # 搜索
npx @tdio/skills add git@git.tiduyun.com:fe-infra/td-skills.git --skill git-commit  # 装指定
npx @tdio/skills push my-skill                                                   # 推送修改
npx @tdio/skills check && skills update                                          # 检查更新

# === 项目初始化 ===
cd my-project
npx @tdio/skills add git@git.tiduyun.com:fe-infra/td-skills.git --skill api-design -y

# === 创建新 skill ===
npx @tdio/skills init my-new-skill
npx @tdio/skills push my-new-skill
```

---