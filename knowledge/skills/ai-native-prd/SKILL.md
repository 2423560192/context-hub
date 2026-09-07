---
name: ai-native-prd
display_name: AI-Native PRD 整理
display_name_en: AI-Native PRD Organizer
description: 把原始想法、聊天记录、会议纪要或松散需求整理成按模块拆分、可直接落地的 AI-Native PRD（模块目录 + Feature 文档），供后续 BDD/OpenAPI/TDD 使用。当用户说“先写 PRD、规范需求、按模块拆需求、整理原始想法、把口头需求变成结构化需求、把聊天记录整理成需求文档”时触发。
description_zh: 把原始想法与口头需求整理成模块化、可落地的 AI-Native PRD，包含量化 OKR、业务实体、行为动作链、场景矩阵与拦截铁网。
description_en: Turn raw ideas and loose requirements into modular, buildable AI-Native PRDs with quantified OKRs, entities, action chains, scenario matrices and guardrails.
category: software-development
version: 1.0.0
author: 阿柴
---

# AI-Native PRD 整理

把原始想法、聊天记录、会议纪要或松散需求整理成「按模块拆分」的 AI-Native PRD。PRD 是后续 BDD / OpenAPI / TDD 的上游事实来源，不是一篇大散文。

## 核心原则

先拆模块、再拆 Feature：**模块是目录，Feature 是 PRD 文档**。一个可独立交付的 Feature 单独一份 PRD；一个业务模块是一个目录（README.md + 多份 Feature PRD）。

## 何时触发

- 用户给出聊天记录、会议纪要、口述需求或粗糙 PRD，要求先写 PRD、规范或按模块拆分需求。
- 用户要把一个多功能的系统需求拆成可独立交付的 Feature。
- 新增参数、改流程、修漏洞之前，想先把需求与场景写稳。

## 执行顺序

1. 读原始需求，先识别模块边界，不要直接写单篇 PRD。
2. 输出模块清单，为每个模块确定中文目录名与职责一句话。
3. 扫描「顶层口径」：影响 ≥2 个模块或多数 Feature 的未定规则——如是否需要账号/登录、浏览是否公开、用户角色、产品范围口径、外部服务选型、合规要求等，产出《顶层待确认问题清单》。
4. **顶层口径关卡**：顶层未定问题数 ≥ 3，或它们影响后续 Feature 拆分时，先停下来向用户提问拍板。未拍板前只输出「模块规划 + 顶层待确认清单」，不落盘 README / Feature PRD；用户拍板或明确说「按默认假设先写」后再继续。
5. 为每个模块写 README（职责 / 量化 OKR / 核心实体 / Feature 列表 / 边界 / 依赖），模板见 @templates/module-readme.md
6. 为每个 Feature 单独写一份 PRD，模板见 @templates/feature-prd.md
7. 每份 Feature PRD 必须含：功能一句话、业务实体与属性、行为动作链、场景矩阵、拦截铁网、待确认问题、不做范围。
8. 场景矩阵必须覆盖至少 8 类场景：Happy Path、参数非法、鉴权失败、越权访问、状态非法、幂等/重复提交、并发冲突、外部依赖失败。
9. 拦截铁网每项必须给出明确处理策略：拒绝 / 排队 / 降级 / 重试 / 忽略。
10. 标清待确认问题，不脑补不确定规则；标清不做范围，防止 AI 顺手扩需求。
11. 不要直接写 BDD、OpenAPI 或代码——那是下游环节的事。

## 粒度规则（什么时候拆成独立 Feature）

满足任意一条就单独成一份 PRD：

- 有独立入口或独立接口
- 有独立 BDD 场景
- 有独立权限、参数校验或状态流转
- 有独立数据库写入或副作用
- 可以单独测试、单独上线、单独 Commit

典型拆分：CRUD 不建议塞进一份 PRD，因为 create / update / delete / list / detail 各有各的坑：

| 动作 | 隐藏风险 |
|---|---|
| 创建 | 创建者、成员角色、默认子资源等副作用 |
| 更新 | 字段校验、管理权限、部分更新 |
| 删除 | 软删除、级联影响、越权拦截、状态限制 |
| 查询列表 | 分页、筛选、排序、只返回有权限的数据 |
| 查询详情 | 资源可见性、成员权限、不存在/已删除状态 |

例外：低风险纯 CRUD（如后台字典表），四个动作共享同一套权限与实体时，可先合成一份 `xxxCRUD.md`，但场景矩阵仍要分开列 create/update/delete/list/detail；一旦某个动作变复杂，立即拆成独立 PRD。

## 落盘约定

1. 若用户项目已有文档约定目录（如 `docs/prd/`、`docs/NativePRD/`、`backend/docs/NativePRD/`），沿用该约定。
2. 用户明确指定输出路径时，按用户指定。
3. 都没有：建议 `<项目根>/docs/prd/`，在对话中询问确认后再写盘。

推荐目录结构：

```text
docs/prd/
  index.md            # 全局索引，列出所有模块与 Feature
  <模块名>/
    README.md         # 模块总览
    <功能名称>.md     # 单个 Feature 的 PRD
```

- 模块目录名与 Feature 文件名统一用中文，保持与项目文档一致。
- 一个模块可以有多个 Feature 文件；一个 Feature 不要跨多个模块写，确需跨模块要写清上游依赖与下游影响。
- 只生成一个模块也必须放进模块目录，不允许散落在 PRD 根目录。

如果当前环境无法写用户文件系统，则在对话中完整输出「文件规划 + 每份文档内容」，由用户自行落盘。

## 写作规范速查

| 要素 | 要求 |
|---|---|
| 量化 OKR | 模块 README 必须给可量化指标（响应时间 / 成功率 / 并发容量 / 鉴权拦截率等），禁止「尽量快」「尽可能高」类模糊词 |
| 实体与属性 | 字段名、类型、必填/nullable、长度/格式/枚举/默认值、关系与索引、中文备注 |
| 行为动作链 | 角色 → 触发 → 输入 → 校验 → 写入 → 副作用 → 响应 → 状态变化 |
| 场景矩阵 | ≥8 类场景的结构化表格（BDD 预埋，不写完整 Gherkin） |
| 拦截铁网 | 参数/鉴权/越权/状态/幂等/配额/并发/外部依赖 8 类拦截表 |
| 待确认 / 不做范围 | 模糊处就地标注，不做的不写不实现 |

详细规范与完整示例见 @references/writing-details.md，动笔前必须通读并照做。

## 结束输出

每次规范化完成后，必须输出文件清单（计划产出或已写入的路径）：

```text
docs/prd/index.md
docs/prd/<模块名>/README.md
docs/prd/<模块名>/<功能名称>.md
```
