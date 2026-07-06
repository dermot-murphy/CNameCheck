# Claude Code — standing instructions for CStyleCheck

## Branching strategy (Gitflow)

- This repo uses **Gitflow**. All feature/fix PRs target `develop`; hotfixes are the only exception that may target `main` directly.
- `develop` → `main` sync PRs are created only when explicitly requested by the repo owner; never create one automatically.
- After a release, `main` and `develop` are synced (docs, version bumps, etc. flow back to `develop`).
- Development branch naming convention: `claude/<topic>-<id>` (e.g. `claude/embedded-c-style-standards-pgqhdc`).

## Issue workflow

- Fix **all open GitHub issues except #191 and #194**.
- Never self-merge a PR — create the PR and wait for an external merge.

## Git / tagging

- Tag pushes (`git push origin <tag>`) return HTTP 403 from this environment's proxy. Tell the user to push tags manually from their local machine.

## Repository scope

- GitHub MCP tools are restricted to `dermot-murphy/CStyleCheck` only.

## Paths

- Remote working directory: `/home/user/CStyleCheck`
- User's local repo root: `U:\GitHub\CStyleCheck`
