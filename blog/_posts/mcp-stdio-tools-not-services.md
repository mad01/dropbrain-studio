---
title: "MCP stdio is just a subprocess"
date: 2026-04-10
slug: mcp-stdio-tools-not-services
description: "Exposing a local code-search CLI to Claude Code as native tools via MCP's stdio transport. No daemon, no port, just a subprocess the client spawns per call."
tags: mcp, claude-code, developer-tools, cli, go
ai_context: "Blog post about adding an MCP stdio subcommand to a Go CLI (ks) to expose local code-search functionality as native Claude Code tools. Explains that MCP stdio is subprocess IPC, not a running service, and shows the implementation shape."
---

# MCP stdio is just a subprocess

I've been using `ks`, the little session manager I wrote for kitty and Claude Code, as my local code search. It indexes all my checked-out repos with zoekt, runs a background gRPC daemon that keeps shards in memory, and exposes a `ks search` / `ks count` / `ks read` / `ks repo` surface. When I want to know where something lives, I ask Claude, Claude runs `ks search ...`, done.

Except it wasn't really done. Every `ks` call triggered a permission prompt. The first search of each session blocked on a full 42-repo index. And Claude didn't always reach for the CLI on its own. I had to nudge it, because the knowledge that `ks` existed lived in a paragraph of my global `CLAUDE.md` that got buried under everything else.

I wanted Claude to know about `ks` the same way it knows about `Read` and `Grep`. Tools in the tool list, with descriptions, no prose.

## What I considered

Four options. A Bash allowlist makes the prompts go away, but Claude still has to build the shell string and parse text output. A skill loads on-demand when the task description matches, which is better, but you still write bash commands inside the skill and the trigger depends on the skill router matching correctly. A slash command is user-invoked, which is the opposite of what I wanted. Or I could build an MCP server.

I reflexively ruled out MCP because "server" sounded like something I'd have to keep alive. I have enough background processes already. I didn't want another `launchctl` plist to maintain.

That was the wrong mental model.

## What stdio MCP actually is

For the stdio transport, "server" is the wrong word. The MCP client (Claude Code, in this case) spawns your binary as a subprocess when it needs the tools. It pipes JSON-RPC 2.0 messages over stdin and stdout. Your process answers each request by writing a JSON response line. When the client closes stdin, your process exits.

No port, no socket, no service to run. The lifecycle is the same as any `Bash()` call Claude already makes: short-lived subprocess, stdin in, stdout out, exit. The only real difference is that the wire protocol is structured JSON instead of shell string construction, and the tool metadata (names, descriptions, JSON schemas) lives in code instead of in a CLAUDE.md paragraph.

Once I understood that, MCP stopped feeling like infrastructure. It's a packaging format for a CLI.

## What it looks like when the tools are native

When `ks_repo_lookup` and `ks_search` are registered MCP tools, Claude sees them in its tool list at plan time, with their descriptions attached. The description string is the prompt for when to use the tool. You write it once, carefully, and Claude discovers it naturally while working.

Here's what I ended up with for the repo lookup tool:

> Resolve a git repo name to its local checkout path. Use when the user mentions a repo by name and you need its absolute path before cd-ing, reading, or grepping inside it. Matching is case-insensitive regex against the org/repo name. Returns an empty matches array if the repo is not checked out locally; in that case, tell the user the repo is not present locally and do not guess a path.

Claude reads that at plan time. If the task looks like "find where the tboi repo is checked out", the tool fires. If the task looks like something unrelated, it doesn't. The second-person phrasing ("use when...") does almost all the work. No CLAUDE.md section required. I ended up removing about 45 lines of `ks` documentation from my global CLAUDE.md after wiring this up, because the tool descriptions now carry that weight.

## How the subcommand is built

`ks mcp` is one new cobra subcommand. Inside, it imports `github.com/modelcontextprotocol/go-sdk/mcp`, calls `mcp.NewServer`, registers five tools with `mcp.AddTool`, and runs a `StdioTransport`. Each tool handler is a thin adapter over the same internal Go packages that back the existing CLI commands. There's no reimplementation of zoekt search, repo discovery, or file reading. The existing gRPC search daemon keeps running exactly as before; the new MCP subprocess connects to it as a client, so zoekt index shards stay mmap'd across MCP calls.

The whole thing is about 400 lines of Go, most of it tool input/output structs with `jsonschema` struct tags that the SDK uses to infer the schemas automatically.

Registration with Claude Code is a one-liner:

```bash
claude mcp add --scope user ks -- ks mcp
```

That writes a user-scoped MCP entry. The next time I open Claude Code, the five `ks_*` tools show up in the tool list alongside `Read`, `Grep`, and `Bash`.

## Before and after

Before, if I asked Claude "find where the tboi repo is checked out", it would recall the `ks repo --json | jq` recipe from my CLAUDE.md, build the bash command, ask for permission, run it, and parse the output.

After, it calls `ks_repo_lookup({name: "tboi"})` and hands me the path.

For search: "how many iOS projects do I have locally" becomes `ks_search({query: "file:\\.pbxproj$"})` and I get 15 results back in structured form.

The difference isn't raw speed. Both flows take a few hundred milliseconds. The difference is that the second one happens without me having told Claude about `ks`. The tool is in the registry, the description explains the trigger, and Claude finds it the same way it finds any built-in.

## What I took away

If you have a local CLI you want an agent to use on its own, the interesting question is how to expose it as typed tools with clear descriptions, not how to document it in prose so the model remembers it exists. For stdio MCP, that's one cobra subcommand and one line in `~/.claude.json`. No running service to maintain, and no nudging Claude toward tools it should already be reaching for.

## Reference

- [`ks` source on GitHub](https://github.com/mad01/kitty-session) — the `ks mcp` subcommand lives under `internal/mcpserver/`.
