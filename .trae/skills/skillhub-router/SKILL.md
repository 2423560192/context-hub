---
name: skillhub-router
description: 从 SkillHub 共享知识库渐进检索并加载可复用技能/提示词/工作流/模板，避免一次性全量注入上下文。当任务命中知识库已有能力（如 AI-Native PRD 编写、Python 异步问题排查、技能发布分类、发布检查、决策记录等），或用户提到"用 SkillHub/共享技能/知识库里的方法/按仓库技能来做"时触发。
---

# SkillHub 路由器

## 描述

本仓库是一个基于 Git 的共享知识中心（SkillHub），通过项目级 MCP（`skillhub` Server）对外提供 4 个工具：`search_knowledge`、`recommend_knowledge`、`get_knowledge`、`list_knowledge`。你的职责是**先检索、后按需加载**，而不是把知识库内容全部读入上下文。

## 使用场景

- 任务与仓库 `knowledge/` 下的既有技能、流程、模板相关（可先用 `recommend_knowledge` 判断）。
- 用户要求遵循仓库内的规范、模板或历史最佳实践。
- 需要判断"这个任务仓库里有没有现成方法"时。

## 指令

1. **先判断，再检索**：不确定任务是否命中知识库时，先调用 `recommend_knowledge(task=...)` 或 `search_knowledge(query=...)`，拿到 3~5 条紧凑候选即可，不要一次拉全量。
2. **只加载选中项**：从候选中选定最匹配的 `id` 后，再调用 `get_knowledge(id=...)` 获取正文与资源清单。
3. **子资源按需取**：技能正文引用到某个子资源（如 `references/xxx.md`、`templates/xxx.md`）且确实需要时，才用 `get_knowledge(id=..., resource="路径")` 加载单个资源。
4. **浏览用分页**：需要了解目录全貌时用 `list_knowledge` 分页浏览，禁止为"找内容"而批量 `get_knowledge`。
5. **遵循内容本身**：加载到技能/流程后，按其正文执行；正文说"只在需要时加载 references"就照做。
6. **只读**：SkillHub 是 Git 管理的知识源，修改走仓库提交，不要假想写回 MCP。

## 示例（可选）

用户："帮我写一份新功能的 PRD，用仓库里的规范" → `recommend_knowledge(task="编写 AI-Native PRD")` → 命中 `ai-native-prd` → `get_knowledge(id="ai-native-prd")` → 按正文与模板执行，需要时再取单个子资源。