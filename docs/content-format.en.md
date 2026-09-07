# Content format

> [中文](content-format.md)

## Packaged skills

SkillHub follows the [WorkBuddy skill structure](https://open.workbuddy.cn/docs/skill#%E6%8A%80%E8%83%BD%E5%9F%BA%E7%A1%80%E7%BB%93%E6%9E%84):

```text
knowledge/skills/
└── {skill-name}/
    ├── SKILL.md
    ├── references/       # optional
    ├── scripts/          # optional
    └── templates/        # optional
```

### Category directories

Skills may also be grouped under free-form category directories (any depth, any name including Chinese). A skill package is any directory that directly contains `SKILL.md`; directories above it act purely as category groups:

```text
knowledge/skills/
├── {skill-name}/                    # flat package (as above)
└── {category}/.../{skill-name}/     # nested package with category path
    └── SKILL.md
```

- `name` and the MCP id always come from the leaf directory name and must remain ASCII (letters/digits/`.`/`_`/`/`/`-`, starting alphanumeric).
- Category directory names are indexed as tags in order (outermost first), so `search`/`list` tag filters work across category groups.
- A non-package directory containing markdown directly (or holding files but no child packages) is reported as malformed. Empty directories are allowed as placeholders.

`SKILL.md` is UTF-8 Markdown with YAML front matter.

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `name` | No | string | Defaults to directory name; must match it when present |
| `display_name` | No | string | Preferred display title |
| `display_name_en` | No | string | English display title |
| `description` | Yes | string | Capability, usage, and trigger phrases |
| `description_zh` | Yes | string | Short Chinese introduction |
| `description_en` | Yes | string | Short English introduction |
| `category` | No | string | Indexed as a tag |
| `version` | Yes | string | Skill version |
| `author` | Yes | string | Publisher or author |
| `allowed-tools` | No | string | Comma-separated tool allowlist |
| `disable-model-invocation` | No | boolean | `true` disables automatic model invocation |
| `user-invocable` | No | boolean | `false` hides direct user invocation |
| `tags` / `keywords` | No | string list | Optional SkillHub search extensions |

The Markdown body must not be empty. References such as `@references/api.md`, `@scripts/fetch.py`, and `@templates/report.md` are validated against the package.

`search_knowledge` returns a compact skill candidate. `get_knowledge(id)` returns only the main instructions and a subresource manifest. `get_knowledge(id, resource)` reads one listed resource, capped at 1 MB and required to be UTF-8 text.

## Other knowledge types

`prompt`, `workflow`, `template`, and `rule` remain single Markdown files anywhere outside `knowledge/skills/`. Their required fields are `id`, `type`, `title`, and `description`; optional `tags` and `keywords` must be string lists.

## Validation

Run `uv run skillhub validate` before committing. Invalid packages are excluded from the live index until fixed, while other valid knowledge remains available.
