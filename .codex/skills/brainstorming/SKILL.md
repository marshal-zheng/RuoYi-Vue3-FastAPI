---
name: brainstorming
description: "Use when the user wants to brainstorm, compare approaches, explore architecture or tech choices, or refine unclear requirements before implementation."
---

# Brainstorming Ideas Into Designs

Turn ideas into validated designs through collaborative dialogue. Understand first, explore options, then hand off to spec generation.

**Announce at start:** "正在使用 brainstorming skill 来探索这个想法。"

## Phase 1: Understand the Idea

- Check current project state first (files, docs, recent commits)
- Ask **one question per message** - never batch multiple questions
- Prefer **multiple choice** (use AskQuestion tool when available), open-ended when needed
- Focus on: purpose, constraints, scope, success criteria
- Apply YAGNI ruthlessly - challenge any feature that isn't essential
- If user提出多个需求, force convergence with:
  - **"你提了多个需求，当前这轮最关键的是哪个？"**
  - Keep only the top priority in current scope; defer the rest to later iterations

## Phase 2: Explore Approaches

- Propose **2-3 approaches** with clear trade-offs
- Lead with your recommendation and explain why
- Include: complexity estimate, risk level, implementation effort
- Let the user pick before moving forward

## Phase 3: Hand Off to Spec Generation

Once alignment is clear, ask user:

> "探索完成，是否开始生成规格文档？"

If yes → use `writing-specs` skill to start三阶段 spec 生成流程 (requirements → design → tasks)。

## When NOT to Use

- 用户需求、验收标准、范围都已明确，且只要求直接执行（实现/重构/补测试）
- 任务本质是机械执行（例如按既定清单修改字段、搬运配置、格式化代码）
- 用户不是要探索方案，而是要你立刻落地一个已确定方案

## Key Principles

- **One question at a time** - don't overwhelm
- **YAGNI ruthlessly** - strip unnecessary features from all designs
- **Explore alternatives** - always 2-3 approaches before settling
- **Use Chinese** - all dialogue must be in Chinese

## Correct vs Wrong Dialogue

**Correct (收敛范围后再讨论方案):**

- 用户: "我想升级权限系统，还要加审计、导出、性能优化。"
- 助手: "你提了多个需求，当前这轮最关键的是哪个？我建议先锁定 1 个核心目标。"

**Wrong (跳过理解直接给方案):**

- 用户: "我想升级权限系统，还要加审计、导出、性能优化。"
- 助手: "我给你一个完整三个月路线图，先做 RBAC 再做审计链路再做报表中心。"

## Common Mistakes

- **问题轰炸**: 一次抛多个问题导致用户难以回答
  - Fix: 每条消息只问一个关键问题，优先选择题
- **跳过理解直接给方案**: 在目标和约束不清时直接设计实现
  - Fix: 先确认目标、范围、成功标准，再提 2-3 个方案
- **不挑战范围**: 用户提什么都收，导致范围失控
  - Fix: 用固定问句收敛优先级，只保留本轮最关键目标
