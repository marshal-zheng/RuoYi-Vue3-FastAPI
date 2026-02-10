---
name: brainstorming
description: "Explore user intent, requirements and design before implementation. Use before any creative work - creating features, building components, adding functionality, or modifying behavior."
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

## Phase 2: Explore Approaches

- Propose **2-3 approaches** with clear trade-offs
- Lead with your recommendation and explain why
- Include: complexity estimate, risk level, implementation effort
- Let the user pick before moving forward

## Phase 3: Hand Off to Spec Generation

Once alignment is clear, ask user:

> "探索完成，是否开始生成规格文档？"

If yes → use `writing-specs` skill to start三阶段 spec 生成流程 (requirements → design → tasks)。

## Key Principles

- **One question at a time** - don't overwhelm
- **YAGNI ruthlessly** - strip unnecessary features from all designs
- **Explore alternatives** - always 2-3 approaches before settling
- **Use Chinese** - all dialogue must be in Chinese
