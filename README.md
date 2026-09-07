# SkillHub · AI 技能中心引擎

SkillHub 是一个**基于 Git 的 AI 技能/知识中心引擎**：把 Markdown 技能包管理在仓库里，通过 MCP 提供给 Claude Code、Codex、Trae、Cursor 等任意客户端 **先检索、再按需加载**，避免技能越来越多把上下文塞爆。

```text
search_knowledge / recommend_knowledge  →  紧凑候选（只回元数据）
get_knowledge                           →  一篇完整文档（按需取）
```

> 本仓库只含**引擎代码**，不含技能内容（`knowledge/` 只有目录骨架）。技能内容放在你自己的知识库仓库/文件夹里，引擎可以指向任意位置——见下方「知识库从哪来」。

## 它能做什么

- 一个 Git 仓库 = 一个技能库（Markdown 是唯一事实来源），索引可随时重建
- 文件改动自动刷新（监听 + 读取时校验），`git pull` 后无需重启
- 技能包遵循 WorkBuddy 结构，支持**多级/中文分类目录**（目录名自动成为可检索 tag）
- 中英文检索（英文 token + 中文单字/双字），可配类型/标签过滤
- 三种运行形态：本机共享 HTTP、各客户端 stdio 自启、服务器常驻共享

## 一、5 分钟上手

### 0. 准备

安装 [uv](https://docs.astral.sh/uv/)（唯一依赖）。

### 1. 拉取引擎并安装

```bash
git clone <你的引擎仓库地址> context-hub
cd context-hub
uv sync                # 首次执行，装依赖
```

### 2. 准备知识库（三选一）

引擎与内容是解耦的，`--repo` 指向哪个仓库，服务就提供哪里的内容：

```text
A. 已有符合规范的知识库（推荐）
   git clone <你的技能仓库> my-skills     # 或指向你现有的 knowledge 仓库

B. 用本仓库骨架自建
   本仓库 knowledge/skills/ 已预置分类目录（需求与文档/编码开发/可视化/效率工具/技能发布/项目/）
   把技能包目录 {skill-name}/SKILL.md 放进对应分类即可

C. 从零建
   mkdir -p my-skills/knowledge/skills/demo
   写一个 SKILL.md（格式见「技能格式」），有 1 个技能就能跑
```

校验内容合法（有错误会退出码 1，坏文件不进索引）：

```bash
uv run skillhub --repo /path/to/your-knowledge validate
# 期望: {"valid": true, "documents": N, "issues": []}
```

### 3. 启动服务

**推荐：本机共享 HTTP（一个常驻服务，所有客户端共用）：**

```bash
uv run skillhub-mcp --repo /path/to/your-knowledge \
    --transport streamable-http --host 127.0.0.1 --port 8765
```

Windows 也可用现成脚本：`scripts\start-skillhub-mcp.bat <知识库路径> 8765`。
想要开机自启（隐藏窗口、登录即跑）见「Windows 开机自启动」。

**或者：stdio（由客户端自己拉起），见「客户端接入」各客户端配置。**

### 4. 客户端接入

接入后所有 Agent 只需填一个地址：`http://127.0.0.1:8765/mcp`（HTTP 模式）：

```json
{ "mcpServers": { "skillhub": { "type": "http", "url": "http://127.0.0.1:8765/mcp" } } }
```

- Claude Code / Cursor：把上面 JSON 写进项目 `.mcp.json` / `.cursor/mcp.json`
- Trae：**设置 → MCP** 手动添加 HTTP 服务器填该地址；想要 Agent"主动去搜"，再装一个路由技能（见「Trae：让 Agent 主动检索」）
- 完整逐客户端说明与现成模板：见「客户端接入参考」与 [examples/mcp](examples/mcp)

### 5. 验证

```bash
# 方式一：命令行冒烟（需服务已在 8765 运行）
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "发布"
```

```text
# 方式二：直接问你的 Agent
你有哪些 MCP 工具？请调用 search_knowledge 搜一下“发布”，把命中的 id 告诉我。
```

能列出 `search_knowledge / get_knowledge / list_knowledge / recommend_knowledge` 并返回结果即成功。

## 技能格式与目录规范

- 每个技能是一个独立目录 `{skill-name}/SKILL.md`，可带 `references/` `scripts/` `templates/` 子资源
- 分类目录随意（可中文、可多层），技能包可以嵌套在任何层：`skills/{分类}/.../{skill-name}/SKILL.md`，分类目录名自动成为 tags
- 必填 frontmatter：`name`、`description`、`description_zh`、`description_en`、`version`、`author`；`name` 必须等于叶子目录名且全库唯一（ASCII）
- ⚠️ 值里出现英文冒号 `: ` 时必须加引号，否则 YAML 报错、该技能不生效

```markdown
---
name: code-review
description: 检查代码正确性与安全风险，当用户要求 code review 时触发。
description_zh: 代码安全审查与回归风险检查。
description_en: Review code for security and regressions.
version: 1.0.0
author: Your Name
category: software-development
---
正文写真正要注入 Agent 的指令；参考资料用 @references/xxx.md 按需加载。
```

完整规范（其余类型 prompt/workflow/template/rule、tags/keywords、子资源引用）见 [docs/content-format.md](docs/content-format.md)。

## MCP 工具用法

| 工具 | 用途 | 返回完整正文 |
| --- | --- | --- |
| `search_knowledge(query, types?, tags?, limit?)` | 关键词搜索（标题/标签/关键词/描述/正文加权） | 否 |
| `recommend_knowledge(task, types?, tags?, limit?)` | 按任务描述推荐候选 | 否 |
| `list_knowledge(type?, tags?, offset?, limit?)` | 分页浏览目录 | 否 |
| `get_knowledge(id, resource?)` | 取单个文档正文；技能包可再取单个子资源 | 是 |

推荐用法：先 `recommend_knowledge`/`search_knowledge` 拿 3~5 条候选 → 选中最匹配的 id → `get_knowledge(id)`；技能正文若引用子资源，需要时才取 `get_knowledge(id, resource="references/xxx.md")`。

## 部署模式速查

| 场景 | 做法 |
| --- | --- |
| 一个人自己电脑用 | 本机 HTTP 常驻 + Windows 开机自启（下节），客户端填 `http://127.0.0.1:8765/mcp` |
| 局域网/团队共用 | 服务器跑 `--host 0.0.0.0` 并放行端口；客户端填 `http://<内网IP>:8765/mcp` |
| 公网共享 | 任意机器常驻 + 前面套**带鉴权的反向代理**（Nginx/Caddy）。⚠️ MVP 无内置鉴权 |

## Windows 开机自启动（推荐，个人电脑）

随登录在后台静默启动共享 HTTP 服务，客户端不用配 stdio。

```powershell
# 1. 新建 scripts\start-skillhub.vbs（路径换成你的）
#    Set shell = CreateObject("WScript.Shell")
#    shell.Run """D:\context-hub\scripts\start-skillhub-mcp.bat"" D:\my-skills 8765", 0, False
# 2. 放入启动文件夹
$startup = [Environment]::GetFolderPath('Startup')
Copy-Item D:\context-hub\scripts\start-skillhub.vbs "$startup\SkillHub-MCP.vbs"
```

验证/管理：

```powershell
Start-Process wscript.exe -ArgumentList '"D:\context-hub\scripts\start-skillhub.vbs"'
Get-NetTCPConnection -LocalPort 8765 -State Listen     # 看到 LISTENING 即成功
taskkill /PID <PID> /F                                  # 停服务（重启后自动再起）
```

其他方式：任务计划程序（登录触发）、NSSM 注册 Windows 服务（无需登录、崩溃自动重启）。

## Trae：让 Agent 主动检索（路由技能）

SkillHub 内容在 MCP 里，Trae 的 Agent 只有**先检索**才会发现你的技能。仓库附带的 `.trae/skills/skillhub-router/SKILL.md` 是一份"强制路由"技能，约定：**任何任务先 recommend/search 知识库，命中就按技能执行，内置技能只是后备**。

```text
让 Trae 使用它（任选）：
A. 项目级：把 .trae/skills/skillhub-router/ 整个目录复制到目标项目根目录
B. 全局级：复制到 Trae 全局技能目录（Windows CN: %USERPROFILE%\.trae-cn\skills\...）
配置 MCP 后重启 Trae，让它重新扫描技能。
```

> 若 Agent 仍不主动检索，把该 SKILL.md 的内容做成 Trae 的「规则」（全量注入、每会话必读）即可，行为等同。

## 客户端接入参考

统一约定：`command` 启动的是**引擎**（context-hub），`--repo` 指向**你的知识库**。Windows 路径用正斜杠，如 `D:/my-skills`。

### Claude Code（项目 `.mcp.json` 或 `claude mcp add`）

```json
{
  "mcpServers": {
    "skillhub": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory", "/path/to/context-hub",
        "run", "skillhub-mcp",
        "--repo", "/path/to/your-knowledge"
      ]
    }
  }
}
```

> `--directory` 填引擎目录（context-hub），`--repo` 填你的知识库目录。JSON 不支持注释，复制时记得删掉说明文字。

### Codex（`~/.codex/config.toml` 或项目 `.codex/config.toml`）

```toml
[mcp_servers.skillhub]
command = "uv"
args = ["--directory", "/path/to/context-hub", "run", "skillhub-mcp", "--repo", "/path/to/your-knowledge"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

### Cursor

`.cursor/mcp.json`（项目）或 `~/.cursor/mcp.json`（全局），JSON 同上。

### Trae

- HTTP 模式：**设置 → MCP → 添加 HTTP**，填 `http://127.0.0.1:8765/mcp`（最简单）
- stdio / 项目级：项目根 `.trae/mcp.json`，JSON 同上（注意把 `--repo` 指向你的知识库）

各客户端现成模板见 [examples/mcp](examples/mcp)。

## CLI 自查命令

```bash
uv run skillhub --repo /path/to/knowledge validate   # 校验内容
uv run skillhub --repo /path/to/knowledge search "发布" --tag 绘丹青 --limit 5
uv run skillhub --repo /path/to/knowledge status      # 文档数/错误/索引时间/Git 状态
uv run skillhub --repo /path/to/knowledge reindex     # 强制重建
```

## 常见问题（FAQ）

**Q：Agent 说没有相关技能 / 只看到内置技能，搜不到我的库？**
A：先确认 MCP 面板里 `skillhub` 已连接且能看到 4 个工具（没有 → 重新粘贴配置并重启）；再确认服务启动时 `--repo` 指向了你的知识库且 `validate` 通过。内置技能 ≠ SkillHub，SkillHub 内容必须主动检索才可见（Trae 用路由技能解决"主动"问题）。

**Q：validate 报错 / 某些技能没被索引？**
A：常见三类：frontmatter 必填字段缺失或含英文冒号未加引号；`name` 与叶子目录名不一致或重复；正文 `@references|scripts|templates/...` 引用了不存在的文件。逐个修好后再 validate。

**Q：我改了知识库，服务要重启吗？**
A：不用。文件监听会自动重建索引；`git pull` 更新文件同样会被感知。

**Q：端口被占用 / 起不来？**
A：`Get-NetTCPConnection -LocalPort 8765 -State Listen` 查占用；换端口用 bat 第二个参数或 `--port`。

**Q：想换/加一个知识库？**
A：改 `--repo`（或环境变量 `SKILLHUB_REPO` / `SKILLHUB_KNOWLEDGE_DIR` / `SKILLHUB_TRANSPORT`），重启服务即可。

## 开发与验证（维护者）

```bash
uv run pytest
uv run skillhub validate
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "release"
```

测试覆盖：WorkBuddy 技能包、资源引用校验、重复 ID、中英文搜索、子资源加载、分页、读取时刷新、文件系统监听、真实 MCP 协议调用。

## MVP 边界

当前版本不含：编辑 API、鉴权、持久化索引、Embedding/向量检索、Web 界面。合理的下一步：鉴权 HTTP 部署 → Web 编辑界面 → 词法/向量混合索引。架构与文档见 [docs/architecture.md](docs/architecture.md)。
