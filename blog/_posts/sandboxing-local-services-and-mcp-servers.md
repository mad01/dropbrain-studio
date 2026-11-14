---
title: "A local MCP server runs as you"
date: 2026-11-11
slug: sandboxing-local-services-and-mcp-servers
description: "Claude Code's sandbox covers shell commands only, so a local MCP server or web service runs with your full access. How I confine mine with Anthropic's sandbox runtime, one access manifest per process, and a small tool that renders and checks the policy."
tags: claude-code, mcp, sandboxing, security, macos, developer-tools
ai_context: "Blog post on sandboxing local MCP servers and local web services on macOS with Anthropic's open source sandbox runtime (srt, npm @anthropic-ai/sandbox-runtime, a beta research preview at version 0.0.81). Describes the setup in github.com/mad01/thismoon: one access manifest per process (spec.access in service-info.yaml or a standalone access.yaml) as the source of truth, the srtspec tool that renders manifests to srt settings JSON, checks them for drift in CI, launches processes (srtspec run, installed as srt-run) and explains the effective policy, a machine-local layer that may only widen access, a watcher that turns kernel sandbox denials into notifications, and a three-outcome triage routine. Includes a worked example with real command output: a denied file read, a denied network call, widening the manifest, and verifying. States the limits: srt is a 0.0.x preview, some processes stay unsandboxed, denial reporting is lossy."
---

# A local MCP server runs as you

I run about a dozen small processes beside my coding agent. Some are Model Context Protocol (MCP) servers the agent spawns. The rest are local web services on loopback ports. Every one of them starts as me. It can read `~/.ssh`, my cloud credentials and every repo on the disk, and it can open a connection to any host.

I had assumed the agent's sandbox covered this. It doesn't. The Claude Code docs say it in one line: ["The sandbox covers shell commands only. Claude's file tools, MCP servers, and hooks run outside it."](https://code.claude.com/docs/en/sandboxing.md) So the sandbox stops a bad `curl` in a shell command, and does nothing about the MCP server that pulled in a poisoned dependency last week.

Most of my servers are my own code, but their dependencies aren't. One wraps a Python engine from PyPI, and another is a third-party binary. That is the risk I wanted to contain: a compromised package reads a secret and sends it somewhere.

## The piece that already exists

Anthropic published the sandbox Claude Code uses for its shell as a separate tool, the [sandbox runtime](https://github.com/anthropics/sandbox-runtime) (srt). Its README says it can sandbox "agents, local MCP servers, bash commands and arbitrary processes". On macOS it generates a seatbelt profile from a short JSON settings file and runs your command under it. Network traffic goes through a local proxy that lets through only the hosts you list. The [engineering post](https://www.anthropic.com/engineering/claude-code-sandboxing) explains why you need both halves. Without network isolation a compromised process can send your SSH keys out, and without filesystem isolation it can escape the sandbox and reach the network anyway.

The host filter is why I switched. I used to write seatbelt profiles by hand, and seatbelt can't filter by hostname. "HTTPS to GitHub" came out as "port 443 to anywhere", which is no protection against a leak.

Now the part I should be honest about. Its README calls srt a "Beta Research Preview" and says the configuration format may change. I pin version 0.0.81. I build a security boundary on a 0.0.x tool, and I treat it that way. The version is pinned exactly, and a bump means running every sandboxed process again and reading what it gets denied.

## What I built on top

srt gives you one command and one JSON file. With a dozen processes on two machines, I needed more around it.

1. One access manifest per process. A short YAML block beside the code says what the process may reach. It is the source of truth.
2. Settings rendered from the manifest. A small Go tool, [srtspec](https://github.com/mad01/thismoon/tree/main/tools/srtspec), turns the manifest into the JSON srt reads. Nobody edits the JSON. Continuous integration (CI) renders every manifest again and fails on any difference.
3. One launcher. Every sandboxed process starts through `srt-run`, a shim over `srtspec run`. There is one launch path to reason about.
4. A machine-local layer that may only widen. One machine sometimes needs one more path or host. That goes in a file on that machine, and the launcher refuses the file if it does anything but add.
5. A watcher. It reads the kernel's sandbox denials from the system log and turns them into a notification and a ledger line with the process's label.

Here is a real manifest, for my local event log service. It listens on a port, reads its own binary, and writes its own data directory.

```yaml
spec:
  access:
    sandbox: srt
    workdir: ~/.local/share/events
    listen: 7430
    reads: [~/code/bin, workdir]
    writes: [workdir, temp]
```

Every render starts from the same floor. Reads of the whole home directory are denied, writes go to temp only, and no host is allowed. A manifest carves back what its process needs. I can review those five lines in seconds. The six lists of JSON they render to take longer, and they don't say why an entry is there.

## One process, start to finish

You need srt (`npm install -g @anthropic-ai/sandbox-runtime`) and srtspec (`go install github.com/mad01/thismoon/tools/srtspec/cmd/srtspec@latest`). srtspec is my tool, not Anthropic's. Without it, write the JSON by hand and run `srt --settings <file> -- <command>`. The idea is the same.

Start with a manifest that allows almost nothing. Save it as `access.yaml`.

```yaml
sandbox: srt
label: demo
reads: [~/code/bin]
writes: [temp]
```

Render it into the directory the launcher reads from.

```bash
srtspec render access.yaml -o ~/.config/srt/demo.json
```

Now launch something through it. I use `head` and `curl` here so the output is short. Your server's binary goes in the same place.

```bash
$ srtspec run ~/.config/srt/demo.json -- head -1 ~/code/src/github.com/mad01/thismoon/README.md
srt-run: demo runtime bun
head: /Users/me/code/src/github.com/mad01/thismoon/README.md: Operation not permitted

$ srtspec run ~/.config/srt/demo.json -- curl -sS -o /dev/null -w '%{http_code}\n' https://example.com
srt-run: demo runtime bun
curl: (56) CONNECT tunnel failed, response 403
```

Both fail closed. The kernel refuses the file read, and srt's proxy refuses the request. On my machine the watcher wrote this to its ledger:

```
2026-11-11 10:11:02  ALERT  demo · head(42359) · file-read-data · /Users/me/code/src/github.com/mad01/thismoon/README.md
```

That line is the whole point of the label. The launcher starts the command as `env SRT_RUN=demo ...`, srt tags each deny rule with the command, and the watcher decodes the label back out. Without my watcher you can see the raw line yourself:

```bash
/usr/bin/log stream --predicate 'eventMessage CONTAINS "deny(1)"'
```

Say the process really needs that file and that host. Widen the manifest by exactly those two things.

```yaml
sandbox: srt
label: demo
egress: [example.com]
reads:
  - ~/code/bin
  - ~/code/src/github.com/mad01/thismoon/README.md
writes: [temp]
```

Before rendering, `srtspec check access.yaml ~/.config/srt/demo.json` exits 1 with a diff and the line `drifted from access.yaml; run srtspec render`. CI catches a manifest change without its render the same way. Render again, and the same two commands print the first line of the file and `200`. A request to `example.org` still gets the 403.

Then ask what a launch gets. I added a local layer file and one host from the environment to show where each entry comes from.

```
$ SRT_RUN_ALLOW_DOMAINS=api.example.net srtspec explain demo
srt policy for demo
  base   ~/.config/srt/demo.json
  local  ~/.config/srt/demo.local.json
  env    SRT_RUN_ALLOW_DOMAINS=api.example.net

filesystem.allowRead    ~/code/bin                                      base
filesystem.allowRead    ~/code/src/github.com/mad01/thismoon/README.md  base
filesystem.allowRead    ~/notes                                         local
filesystem.allowWrite   /private/tmp                                    base
filesystem.allowWrite   /private/var/folders                            base
filesystem.denyRead     ~                                               base
filesystem.denyWrite    (empty)                                         base
network.allowedDomains  example.com                                     base
network.allowedDomains  api.example.net                                 env
network.deniedDomains   (empty)                                         base
```

The local layer can't take a deny away. I put `"allowRead": ["~"]` in it, and the answer was `srt-run refuses to launch demo` with the reason `would lift the ~ deny`. The renderer has the same kind of guard. An `egress` of `*` fails with `a bare * allows every host; name the hosts`, and a misspelled field is an error. A typo can't quietly drop a rule.

## Wiring an MCP server

An MCP registration can't express the whole launch, so each server gets a small wrapper script. The end of the one I use for the GitHub MCP server, trimmed:

```bash
token="$(gh auth token --hostname "$host")"

cd /
exec /usr/bin/env -i "${env_allow[@]}" \
  "$HOME/code/bin/srt-run" "$settings" "$server" "${args[@]}"
```

Each line is there for a reason.

- The token is resolved outside the sandbox, so the server never needs the keychain.
- `env -i` rebuilds the environment from an allow-list. The sandbox doesn't filter environment variables, so this is where shell secrets stay out.
- `cd /` is there because the client spawns the server from the session's directory. If that directory is read-denied, the process fails before `main` runs.

The MCP registration then points at the wrapper and not at the binary.

## When something is denied

A denial has three possible meanings, and I decide which one before touching anything.

Real breakage: the tool fails and the path is one it needs. I add the narrowest allow to the manifest, render, and restart the process.

Expected noise: the tool works and the denial is a library probing. My `curl` run above also tried to read three preference files under `~/Library` that it didn't need. Those get a line in the watcher's ignore list, with a comment saying why.

A sign of compromise: a read of `~/.ssh`, or a network attempt from a process with no allowed hosts, most of all right after a version bump. I don't allow it and I don't silence it. I diff the dependencies against the previous pins.

The rule under all three: never allow or silence a denial I can't explain.

## What stays outside

Seven services and two MCP servers in the public repo launch this way, and my private config repo wires a few more. Not everything is in.

- My code search service pulls repos over SSH. The proxy can't carry that, and SSH needs the keys the sandbox exists to keep out. Its manifest says `sandbox: none` and why.
- The code search and task-state MCP servers are my own code and run unsandboxed. That is trust, not containment.
- The text-to-speech engine needs graphics access that srt has no setting for. It keeps a hand-written seatbelt profile.
- Claude Code's own shell sandbox is off on my machines. It broke too much of my tooling.

And these are the limits I live with:

- Denial reporting is lossy. macOS reports a denial once and throttles a binary that keeps violating, so the ledger is a signal and not an audit trail. Enforcement doesn't depend on the report.
- A process that may read source can read a token someone left in a YAML file. The nested denies cover `.env` and key files only. I accept that because the hosts are pinned.
- Go binaries need a weaker network setting to verify TLS certificates. The srt README warns that it opens a possible leak path.
- Each sandboxed process costs one extra srt process beside it, about 48 MB under bun in my measurement.

## What I would do differently

I would write the manifest first. I started with hand-written settings files, and review only became easy once the YAML existed.

I would put the launcher in one binary from the start. For a short while the widen-only rules lived twice, as jq in a shell launcher and as Go in the tool that explains the policy. Two copies of a security rule is one too many, so the launcher became a shim over the Go code.

One wart is still there. A host that differs per machine comes from the wrapper at launch, so the egress policy lives in two places: the manifest and the wrapper. A wrapper change is a policy change and has to be reviewed like one.

The tool, the manifests and the full walkthrough are in [thismoon](https://github.com/mad01/thismoon), under `tools/srtspec` and [`docs/SANDBOXING.md`](https://github.com/mad01/thismoon/blob/main/docs/SANDBOXING.md). The decision records beside it say why each piece is there.
