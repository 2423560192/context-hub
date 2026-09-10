# SkillHub — 详细技术文档

> 由 [readme-generate](https://github.com/agenvoy/skill-readme-generate) 生成 · 返回 [README.zh.md](README.zh.md) · English: [doc.md](doc.md)

本文覆盖安装、运行、客户端接入、CLI 与 MCP 参考、内容格式与维护。架构设计见 [architecture.zh.md](architecture.zh.md)。

## 概览

SkillHub 是一个**基于 Git 的 AI 技能知识引擎**。引擎代码（本仓库）与内容解耦：`--repo` 指向任何一个含 `knowledge/` 目录的仓库，引擎就为那里的内容建索引并通过 MCP 提供服务。Markdown 是唯一事实来源，索引由磁盘内容构建、可随时重建。

引擎自带可用的 `knowledge/` 分类骨架，零外部依赖即可起步；也可以直接克隆一份现成的知识库仓库，用 `--repo` 指向它。

## 环境要求与安装

- Python 3.11 及以上
- [uv](https://docs.astral.sh/uv/)（唯一工具依赖，可自动准备解释器）

```bash
git clone <你的引擎仓库地址> context-hub
cd context-hub
uv sync          # 安装依赖并创建虚拟环境
```

两个入口：

| 命令 | 用途 |
| --- | --- |
| `uv run skillhub ...` | 本地运维 CLI（validate / search / status / reindex） |
| `uv run skillhub-mcp ...` | MCP 服务（stdio 或 streamable-http） |

## 运行服务

### 共享 HTTP 模式（个人电脑推荐）

一个常驻服务、一个地址供所有客户端共用：

```bash
uv run skillhub-mcp --repo /path/to/your-knowledge \
    --transport streamable-http --host 127.0.0.1 --port 8765
```

客户端连接 `http://127.0.0.1:8765/mcp`。Windows 可直接用 `scripts\start-skillhub-mcp.bat <知识库路径> 8765`；登录自启（静默后台）见下文「Windows 开机自启动」。

### stdio 模式（由客户端拉起）

不传 `--transport`（默认 `stdio`），在客户端配置里让客户端自己启动服务，见「客户端接入」。

### 环境变量配置

| 变量 | 默认值 | 含义 |
| --- | --- | --- |
| `SKILLHUB_REPO` | 当前目录 | 含 `knowledge/` 的仓库根目录 |
| `SKILLHUB_KNOWLEDGE_DIR` | `knowledge` | 相对仓库根的知识目录 |
| `SKILLHUB_TRANSPORT` | `stdio` | `stdio` 或 `streamable-http` |
| `SKILLHUB_HOST` | `127.0.0.1` | HTTP 模式绑定地址 |
| `SKILLHUB_PORT` | `8765` | HTTP 模式绑定端口 |

## 客户端接入

统一约定：`command` 启动的是**引擎**（context-hub），`--repo` 指向**你的知识库**。Windows 路径用正斜杠，如 `D:/my-skills`。

HTTP 模式（所有客户端通用）：

```json
{ "mcpServers": { "skillhub": { "type": "http", "url": "http://127.0.0.1:8765/mcp" } } }
```

stdio 模式：

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

放置位置：

- **Claude Code**：项目 `.mcp.json`，或 `claude mcp add`
- **Codex**：`~/.codex/config.toml` 或项目 `.codex/config.toml`：

```toml
[mcp_servers.skillhub]
command = "uv"
args = ["--directory", "/path/to/context-hub", "run", "skillhub-mcp", "--repo", "/path/to/your-knowledge"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

- **Cursor**：`.cursor/mcp.json`（项目）或 `~/.cursor/mcp.json`（全局）
- **Trae**：HTTP 走「设置 → MCP → 添加 HTTP」；项目级 stdio 走根目录 `.trae/mcp.json`

现成模板见 [examples/mcp](../examples/mcp)。

## CLI 参考

所有子命令都支持 `--repo`（默认当前目录）与 `--knowledge-dir`（默认 `knowledge`）。

```bash
uv run skillhub --repo /path/to/knowledge validate
uv run skillhub --repo /path/to/knowledge search "发布" --tag 绘丹青 --limit 5
uv run skillhub --repo /path/to/knowledge status
uv run skillhub --repo /path/to/knowledge reindex
```

| 子命令 | 行为 |
| --- | --- |
| `validate` | 重建索引并输出 `{"valid", "documents", "issues"}`；有任意问题退出码 1；坏文件被排除出在线索引直至修复 |
| `search <query>` | 元数据与正文关键词检索。过滤：`--type {skill,prompt,workflow,template,rule}`（可重复）、`--tag <名称>`（可重复）、`--limit`（默认 5，限制 1–20） |
| `status` | 分类型文档数、校验问题、监听标志、索引时间、知识目录 Git 状态 |
| `reindex` | 强制全量重建并输出 `{"indexed", "invalid", "indexed_at"}` |

JSON 输出走 stdout，错误走 stderr、退出码 2。

## MCP 工具参考

| 工具 | 用途 | 返回完整正文 |
| --- | --- | --- |
| `search_knowledge(query, types?, tags?, limit?)` | 关键词检索 | 否，紧凑候选 |
| `recommend_knowledge(task, types?, tags?, limit?)` | 按任务描述推荐 | 否，紧凑候选 |
| `list_knowledge(type?, tags?, offset?, limit?)` | 分页浏览目录 | 否 |
| `get_knowledge(id, resource?)` | 取单篇完整正文；可再取技能单个子资源 | 是 |

推荐用法：

1. `search_knowledge` / `recommend_knowledge` 返回最多 `limit` 条摘要（`id`、`type`、`title`、`description`、`tags`、`path`，可选 `version`、`resources_count`）并带 `next_step` 提示。
2. 选中最匹配的 `id` 调 `get_knowledge(id)`——技能会返回 `SKILL.md` 正文、front matter（`metadata`）、关键词和**子资源清单**（`references/`、`scripts/`、`templates/` 的文件与大小/类型）。
3. 技能需要子资源时，用 `get_knowledge(id, resource="references/xxx.md")` 只取单个文件（路径可省略开头 `@`，反斜杠自动归一）。

安全限制：`search`/`list` 的 limit 有上限（20 / 100）；子资源上限 1 MB、必须为 UTF-8 文本；资源路径不能逃出技能包目录；未知 id 或资源会返回明确错误。

检索是确定性词法相关：按 `id > title > tags > keywords > description > content` 加权，另有短语加分；中文按整段+单字+双字切分。需要精确时可按类型与标签过滤。

## 技能与文档格式

- **技能包**是目录 `knowledge/skills/{skill-name}/SKILL.md`，可带 `references/`、`scripts/`、`templates/` 子目录；包上层的分类目录自由（支持中文、任意层级），目录名自动成为可检索标签。
- 技能必填 front matter：`description`、`description_zh`、`description_en`、`version`、`author`。`name` 可选，默认取目录名；写时必须等于目录名、全库唯一且为 ASCII（字母/数字/`.`/`_`/`/`/`-`，首字符字母数字）。可选字段：`display_name`、`category`、`allowed-tools`、`disable-model-invocation`、`user-invocable`、`tags`、`keywords`。
- **其它类型**（`prompt`、`workflow`、`template`、`rule`）是 `knowledge/skills/` 之外的单个 Markdown 文件，必填 `id`、`type`、`title`、`description`。
- 正文里的 `@references/api.md` 等引用会被校验，引用不存在的文件会导致该校验失败。
- ⚠️ front matter 值含英文冒号（`: `）时必须加引号，否则 YAML 解析失败、该文档被跳过。

提交前先跑 `uv run skillhub validate`。完整规范见 [../docs/content-format.md](../docs/content-format.md)（英文 [../docs/content-format.en.md](../docs/content-format.en.md)）。

## Trae：让 Agent 主动检索（路由技能）

内容只有主动检索才可见，所以 Trae 的 Agent 需要被强制"先搜索"。仓库自带的 `.trae/skills/skillhub-router/SKILL.md` 是一份"强制路由"技能：任何任务先 `recommend_knowledge` / `search_knowledge`，命中的知识优先于内置技能。

给 Trae 安装（二选一，之后重启 Trae）：

- **项目级**：把 `.trae/skills/skillhub-router/` 整目录复制到目标项目根目录
- **全局级**：复制到 Trae 全局技能目录（Windows CN：`%USERPROFILE%\.trae-cn\skills\...`）

若 Agent 仍不主动检索，把该技能内容做成 Trae 的「规则」（每会话全量注入）即可，行为等同。

## Windows 开机自启动

随登录静默启动共享 HTTP 服务，客户端无需 stdio 配置：

```powershell
# 1. 新建 scripts\start-skillhub.vbs（路径换成你的）
#    Set shell = CreateObject("WScript.Shell")
#    shell.Run """D:\context-hub\scripts\start-skillhub-mcp.bat"" D:\my-skills 8765", 0, False
# 2. 放入启动文件夹
$startup = [Environment]::GetFolderPath('Startup')
Copy-Item D:\context-hub\scripts\start-skillhub.vbs "$startup\SkillHub-MCP.vbs"
```

管理：

```powershell
Start-Process wscript.exe -ArgumentList '"D:\context-hub\scripts\start-skillhub.vbs"'
Get-NetTCPConnection -LocalPort 8765 -State Listen     # 看到 LISTENING 即成功
taskkill /PID <PID> /F                                  # 停服务（重启后自动再起）
```

### 崩溃自愈（看门狗，推荐）

开机自启只保证"登录时拉起一次"；若进程之后退出且无人接管，服务会一直断。仓库自带看门狗脚本，服务掉线后自动复活，且**全程无弹窗**：

- `scripts/watchdog-skillhub.ps1`：检查 8765 是否在监听，未监听则静默拉起服务（含 1 分钟防抖，避免并发重复启动）；
- `scripts/watchdog-skillhub.vbs`：用 wscript 静默调用上面的脚本，不弹控制台窗口。

注册为计划任务（每 2 分钟自检一次）：

```powershell
schtasks /Create /F /TN "SkillHub-Watchdog" `
  /TR "wscript.exe //B //Nologo D:\context-hub\scripts\watchdog-skillhub.vbs" `
  /SC MINUTE /MO 2
```

管理：

```powershell
schtasks /Query /TN "SkillHub-Watchdog" /FO LIST     # 查看状态与下次运行时间
schtasks /Run   /TN "SkillHub-Watchdog"              # 立即自检一次
schtasks /Delete /TN "SkillHub-Watchdog" /F          # 取消守护
```

> 务必用 wscript（或给 powershell 加 `-WindowStyle Hidden`）运行，否则计划任务每 2 分钟会闪一个控制台黑框。

替代方案：任务计划程序（登录触发）或 NSSM 注册 Windows 服务（无需登录、崩溃自动重启）。

## 部署模式

| 场景 | 做法 |
| --- | --- |
| 个人电脑 | 本机 HTTP 常驻 + Windows 开机自启，客户端填 `http://127.0.0.1:8765/mcp` |
| 局域网/团队 | `--host 0.0.0.0` 并放行端口，客户端填 `http://<内网IP>:8765/mcp` |
| 公网 | 常驻服务 + **带鉴权的反向代理**（Nginx/Caddy）。⚠️ MVP 无内置鉴权 |

## FAQ

**Q：Agent 说没有相关技能 / 只看到内置技能？**
A：先确认 MCP 面板里 `skillhub` 已连接且能看到 4 个工具；再确认启动时 `--repo` 指向了你的知识库且 `validate` 通过。SkillHub 内容必须主动检索才可见（Trae 装路由技能）。

**Q：validate 报错 / 有些技能没被索引？**
A：常见三类：必填字段缺失或值含英文冒号未加引号；`name` 与目录名不一致或重复；正文 `@references|scripts|templates/...` 引用不存在的文件。逐个修复后重新 validate。

**Q：改了知识库要重启吗？**
A：不用。监听会自动重建索引，`git pull` 更新同样会被感知（读取时指纹校验兜底）。

**Q：端口被占用 / 起不来？**
A：`Get-NetTCPConnection -LocalPort 8765 -State Listen` 查占用；换端口用 bat 第二个参数或 `--port`。

**Q：想换/加知识库？**
A：改 `--repo`（或上面的环境变量）后重启服务即可。

## 开发与验证

```bash
uv run pytest                                   # 测试套件
uv run skillhub validate                        # 校验本仓库自带骨架
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "release"
```

测试覆盖：WorkBuddy 技能包、资源引用校验、重复 ID、中英文检索、子资源加载、分页、读取时刷新、文件系统监听、真实 MCP 协议调用（见 `tests/`）。

## MVP 边界

当前版本不含：编辑 API、鉴权、持久化索引、Embedding/向量检索、Web 界面。合理下一步：鉴权 HTTP 部署 → Web 编辑界面 → 词法/向量混合索引。架构见 [architecture.zh.md](architecture.zh.md)。
