---
title: "Your code-search MCP shouldn't leave your laptop"
date: 2026-04-16
slug: csl-local-mcp-for-code-search
description: "code-search-local (csl) is a zoekt-backed local code search CLI with a built-in MCP stdio server. No cloud, no auth, no vendor. Just a binary and your filesystem."
tags: mcp, claude-code, code-search, privacy, zoekt, go, developer-tools
ai_context: "Blog post introducing code-search-local (csl), an open-source Go tool that indexes local git repositories with zoekt and exposes them to Claude Code as an MCP stdio server. Available at github.com/mad01/code-search-local. Argues that code-search MCP tools should run locally rather than as remote SaaS, for reasons of privacy, latency, offline availability, and avoiding lock-in."
---

# Your code-search MCP shouldn't leave your laptop

The pattern is so familiar by now it's almost automatic. Someone builds a useful thing. The useful thing becomes an MCP server. The MCP server lives on their infrastructure. You sign up, you authenticate, you send your data over the wire so that a model on someone else's laptop can reason about it.

For a lot of things, that's fine. Some tools genuinely need network effects or shared state. A calendar MCP has to talk to a calendar API. A ticketing MCP has to talk to Jira.

But code search? My code search doesn't need to phone home. The repos I work on are already on my laptop. A zoekt index is already a solved problem. The only reason to ship my code off-site to get it back as search results is that nobody has bothered to build a local-first alternative.

So I built one. It's called [`csl`](https://github.com/mad01/code-search-local), short for code-search-local, and it does exactly what the name says.

## The problem with remote code-search MCP

Most of the code-search MCP integrations I've looked at assume a remote indexer. You point them at a repo hosting provider, they crawl it, they expose search tools that query their backend.

That's a reasonable design when the code lives somewhere public. It falls apart for everything else. Private code means jumping through approval hoops to let a third party index your work, or not using the tool at all. Offline on a plane, the tools stop working. The vendor changes pricing or gets acquired, and you lose access to your own search. Searching across repos from three different hosts means three different integrations.

The remote model works when network access is free. Code search pays for that convenience in ways I don't want to keep paying.

## What local gets you

The obvious one is privacy. If the index lives on my laptop and the MCP server reads from it, no code I haven't explicitly published ever leaves the machine. Nothing to audit, no terms of service. The data just doesn't move.

The less obvious one is latency. A local zoekt query over 45 repos takes milliseconds once the shards are warm. Round-tripping that through a SaaS is two orders of magnitude slower, and you pay the cost on every call. When Claude does ten searches to trace a function, the difference between a warm local daemon and a cloud service is the difference between instant and waiting.

Then there's the airplane problem. I write a lot of code on planes and in hotel rooms with flaky wifi, and a tool that only works when the network is up is a tool I can't count on.

And the lock-in problem. If I install `csl` today and the author abandons it tomorrow, I still have the binary and the index. Worst case I stop getting updates. Nothing to close, nothing to export.

## How it works

The architecture is deliberately boring.

```
┌──────────────┐  spawn         ┌───────────┐  unix socket   ┌──────────────┐
│ Claude Code  │ ─────────────▶ │  csl mcp  │ ─────────────▶ │  csl daemon  │
│  (client)    │ ◀──JSON-RPC─── │  (stdio)  │ ◀──gRPC─────── │   (zoekt)    │
└──────────────┘                └───────────┘                └──────────────┘
```

Claude Code spawns `csl mcp` as a subprocess when it needs the tools. The subprocess talks JSON-RPC over stdin/stdout, same as any MCP stdio server. When Claude's done, stdin closes and the subprocess exits.

The subprocess itself is just an adapter. It forwards every search call to a long-running gRPC daemon over a unix socket at `~/.config/csl/search-daemon.sock`. The daemon keeps zoekt shards mmap'd in memory, so the hundredth call costs the same as the second. The daemon starts itself on demand and shuts down after idle timeout. There's no systemd unit, no plist, no service manager. You never have to think about it.

If the daemon is unreachable, the subprocess falls back to in-process search. It's slower because it reopens the shards, but it works. You can literally `rm ~/.config/csl/*` and the tools keep functioning, just less efficiently, until the next invocation rebuilds what it needs.

## What the tools look like

`csl` registers eight tools with Claude Code. The pattern is: search, count, read, validate for code content, plus lookup, info, pull, reindex for repo management.

- `csl_search` runs a zoekt query across all indexed repos. Returns file paths by default, matching lines with context if you ask.
- `csl_count` returns how many matches a query has, optionally grouped by repo or language. Cheap way to answer "does this codebase even contain X".
- `csl_read` reads a file from a named repo by relative path, with optional line range slicing.
- `csl_query_validate` parses a zoekt query and tells you what it means. Useful before running an expensive search.
- `csl_repo_lookup` resolves a repo name to its local checkout path. Case-insensitive regex.
- `csl_repo_info` reports git health and index state for a repo and returns a suggested action (ready, commit_or_stash, pull_recommended, needs_reindex).
- `csl_repo_pull` does a fast-forward git pull with safety checks for dirty working trees.
- `csl_repo_reindex` rebuilds the zoekt index for a single repo after significant changes.

A typical Claude session might call `csl_repo_lookup` to find where a repo lives, `csl_repo_info` to check git health before making changes, `csl_search` to locate a function, `csl_read` to pull the relevant lines. Four tool calls, all local, total latency measured in milliseconds.

## Install

```bash
go install github.com/mad01/code-search-local/cmd/csl@latest
mkdir -p ~/.config/csl
cat > ~/.config/csl/config.yaml <<EOF
dirs:
  - ~/code/src/github.com/yourorg
  - ~/workspace
EOF
claude mcp add --scope user csl -- csl mcp
```

That's the whole setup. `csl doctor` will show you the index state and whether the daemon is reachable. `csl search "func main"` warms things up.

## Why I split it out from ks

The search tooling used to live inside [`ks`](https://github.com/mad01/kitty-session), the kitty session manager I wrote about [last month](/blog/kitty-session-manager-for-claude-code/). That made sense when I was the only user and the two concerns happened to share a repo. It stopped making sense the moment I realized the search half was useful to anyone with a terminal, not just kitty users.

So I pulled the MCP server, the daemon, the zoekt integration, and all the supporting code into its own project. `ks` is back to being a small kitty session manager. `csl` is a standalone local code-search tool that works anywhere Go runs. They don't depend on each other. The repo discovery code lives in both, duplicated on purpose, because coupling them would defeat the split.

The general lesson: when two things in the same repo aren't really about the same topic, separate them. The awkwardness of maintaining two repos is almost always less than the awkwardness of explaining what the combined thing does.

## Try it

Source: [github.com/mad01/code-search-local](https://github.com/mad01/code-search-local). MIT licensed. It works today, with two honest caveats: zoekt is a lot of dependency to pull in for a search CLI, and first-run indexing of a big workspace takes a minute. After that, it stays out of your way.

If the pattern interests you but you don't care about the implementation, go read [MCP stdio is just a subprocess](/blog/mcp-stdio-tools-not-services/). That post covers why shipping this kind of tool as an MCP server is easier than it sounds.
