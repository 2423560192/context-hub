---
id: rule.safe-changes
type: rule
title: Safe Repository Changes
description: Guardrails for making focused and recoverable changes in a shared repository.
tags:
  - safety
  - git
keywords:
  - dirty worktree
  - destructive commands
---
# Safe changes

Preserve unrelated user edits. Resolve exact targets before destructive operations, prefer recoverable actions, keep changes within the requested scope, and verify behavior in proportion to risk.

