# 进阶使用与维护参考

> [English](advanced.en.md)

> README 只保留"快速上手"，本文收纳其余内容：部署模式、逐客户端完整接入、Windows 开机自启、Trae 主动检索、FAQ、维护者开发命令。技能/文档格式规范见 [content-format.md](content-format.md)，架构见 [architecture.md](architecture.md)。

## 部署模式速查

| 场景 | 做法 |
| --- | --- |
| 一个人自己电脑用 | 本机 HTTP 常驻 + Windows 开机自启（下节），客户端填 `http://127.0.0.1:8765/mcp` |
| 局域网/团队共用 | 服务器跑 `--host 0.0.0.0` 并放行端口；客户端填 `http://<内网IP>:8765/mcp` |
| 公网共享 | 任意机器常驻 + 前面套**带鉴权的反向代理**（Nginx/Caddy）。⚠️ MVP 无内置鉴权 |
| 客户端自己拉起 | 用 stdio 配置（见下节），由各客户端按需启动引擎 |

## 客户端接入（完整）

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

`.cursor/mcp.json`（项目）或 `~/.cursor/mcp.json`（全局），JSON 同 Claude Code。

### Trae

- HTTP 模式：**设置 → MCP → 添加 HTTP**，填 `http://127.0.0.1:8765/mcp`（最简单）
- stdio / 项目级：项目根 `.trae/mcp.json`，JSON 同 Claude Code（注意把 `--repo` 指向你的知识库）

各客户端现成模板见 [examples/mcp](../examples/mcp)。

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

## 知识库与技能格式

- 技能是目录 `{skill-name}/SKILL.md`，可带 `references/` `scripts/` `templates/` 子资源；分类目录可中文、可多层，目录名自动成为可检索 tag
- 必填 frontmatter：`description`、`description_zh`、`description_en`、`version`、`author`；`name` 可选，写则必须等于叶子目录名且全库唯一（ASCII）
- ⚠️ frontmatter 值里出现英文冒号 `: ` 时必须加引号，否则 YAML 报错、该技能不生效
- 完整规范见 [content-format.md](content-format.md)

## FAQ

**Q：Agent 说没有相关技能 / 只看到内置技能，搜不到我的库？**
A：先确认 MCP 面板里 `skillhub` 已连接且能看到 4 个工具（没有 → 重新粘贴配置并重启）；再确认服务启动时 `--repo` 指向了你的知识库且 `validate` 通过。内置技能 ≠ SkillHub，SkillHub 内容必须主动检索才可见（Trae 用路由技能解决"主动"问题）。

**Q：validate 报错 / 某些技能没被索引？**
A：常见三类：必填字段（`description`/`description_zh`/`description_en`/`version`/`author`）缺失，或值含英文冒号未加引号；`name` 与叶子目录名不一致或重复；正文 `@references|scripts|templates/...` 引用了不存在的文件。逐个修好后再 validate。

**Q：我改了知识库，服务要重启吗？**
A：不用。文件监听会自动重建索引；`git pull` 更新文件同样会被感知。

**Q：端口被占用 / 起不来？**
A：`Get-NetTCPConnection -LocalPort 8765 -State Listen` 查占用；换端口用 bat 第二个参数或 `--port`。

**Q：想换/加一个知识库？**
A：改 `--repo`（或环境变量 `SKILLHUB_REPO` / `SKILLHUB_KNOWLEDGE_DIR` / `SKILLHUB_TRANSPORT` / `SKILLHUB_HOST` / `SKILLHUB_PORT`），重启服务即可。

## 开发与验证（维护者）

```bash
uv run pytest
uv run skillhub validate
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "release"
```

测试覆盖：WorkBuddy 技能包、资源引用校验、重复 ID、中英文搜索、子资源加载、分页、读取时刷新、文件系统监听、真实 MCP 协议调用。

## MVP 边界

当前版本不含：编辑 API、鉴权、持久化索引、Embedding/向量检索、Web 界面。合理的下一步：鉴权 HTTP 部署 → Web 编辑界面 → 词法/向量混合索引。架构见 [architecture.md](architecture.md)。
