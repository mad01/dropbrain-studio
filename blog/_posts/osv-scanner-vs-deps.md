---
title: "I tested osv-scanner against my own dependency scanner"
date: 2026-11-14
slug: osv-scanner-vs-deps
description: "I ran Google's osv-scanner over the same repos as deps, the small scanner I maintain. The findings overlapped on one package out of 25. Why that is, what each tool is for, and why I'm keeping mine."
tags: security, supply-chain, go, developer-tools, mcp
ai_context: "Blog post comparing Google's osv-scanner (v2.7.1, run with go run, scan source -r) against deps, a local dependency scanner in github.com/mad01/thismoon (services/deps) that checks pinned versions against OSV.dev on a daily loop and serves a local page. Reports timings (osv-scanner 14 to 16 s over 26 repos, deps check 32 to 36 s over 11 repos and 6 mise tools), coverage differences (deps reads the full Go module graph from go list -m all, 275 modules, where osv-scanner reads the 108 go.mod lines; osv-scanner resolves a requirements.txt transitively through deps.dev, 44 packages against 2 pins; osv-scanner honours .gitignore; deps reads GitHub Actions refs and mise-installed tool trees), and findings parity in repos both scanned: 1 flagged package in both, 18 only in deps (all in the module graph but not compiled in), 6 only in osv-scanner (all from deps.dev resolving one requirements.txt with no lockfile). Lists what only each tool has (osv-scanner: govulncheck call analysis, guided remediation, licence scanning, offline mode, SARIF, CycloneDX and SPDX output, container images, more ecosystems, ignore rules with expiry, an experimental MCP mode; deps: a repo registry with a daily loop, macOS banner, registry signals, Actions refs, vendored JavaScript, a web page and an MCP server). Decision: keep deps, register the missing repos, look at borrowing call analysis, and the conditions that would reverse the decision."
---

# I tested osv-scanner against my own dependency scanner

I maintain a small dependency scanner called [deps](https://github.com/mad01/thismoon/tree/main/services/deps). It runs on my Mac and reads the packages my repos pin. Each version gets checked against the Open Source Vulnerabilities (OSV) database at [osv.dev](https://osv.dev), and the result shows up on a local page at `deps.this`. That is about 6,900 lines of Go, and I am the one who has to keep them working.

Google ships [osv-scanner](https://github.com/google/osv-scanner) for the same database. It has a team behind it, a release about once a month, and a feature list much longer than mine. So I had to ask whether my tool still earns its place. I spent a morning finding out.

## The setup

I installed nothing. `go run` fetches and builds a pinned version:

```bash
go run github.com/google/osv-scanner/v2/cmd/osv-scanner@v2.7.1 \
  scan source -r --format json --output-file out.json <dirs>
```

v2.7.1 was the newest tag, published on 2026-11-09. Exit code 1 means it found something. I gave it 26 repo directories by name. deps scanned the 11 repos in its registry, plus the install trees of 6 command-line tools that [mise](https://mise.jdx.dev) put on the machine.

Pass the directories one by one. The help text says `--x-exclude` takes "just dirname for exact match". In a scratch test, `--x-exclude skipme` still scanned the directory named `skipme`, while `--x-exclude 'g:**/skipme'` skipped it.

| run | wall time |
|---|---|
| first `go run`, download and compile | 45.8 s |
| osv-scanner, 26 repos, Go call analysis on (the default) | 14 to 16 s |
| osv-scanner, 26 repos, `--no-call-analysis=go` | 10 to 20 s |
| `deps check`, 11 repos and 6 tools | 32 to 36 s |

This isn't like for like. deps runs `go list` in every module and asks three package registries about each version. The spread in the osv-scanner rows is the network. Both are fast enough for a job that runs once a day.

## What each one saw

| | deps | osv-scanner |
|---|---|---|
| packages checked | 623 | 461 |
| Go modules in thismoon | 275 | 108 |
| npm packages in two lockfiles | 49 and 39 | 49 and 39 |
| one `requirements.txt` | 2 | 44 |
| Swift `Package.resolved` files | 6 | 3 |
| GitHub Actions refs | 39 in 5 repos | none |
| tools installed by mise | 6 | none |
| repos with a `yarn.lock` or `pubspec.lock` | none | 2 |

The Go row is the big one. deps reads the full module graph from `go list -m all`. osv-scanner reads the lines in `go.mod`. Most of what follows comes from that difference.

## Why the findings barely overlap

In the 11 repos both tools scanned, they flagged 25 packages between them.

| flagged by | packages |
|---|---|
| both | 1 |
| deps only | 18 |
| osv-scanner only | 6 |

The shared one is `github.com/klauspost/compress@1.18.7`, advisory GO-2026-6865. It is a line in thismoon's `go.mod`, so both tools see it. deps marks it "not imported". osv-scanner reports `"called": false`. `go mod why -m` shows why: only a test inside a dependency needs it. The two tools get to the same answer by different routes. deps asks whether any package of the module is compiled in. osv-scanner runs govulncheck and asks whether the vulnerable function is called, which is the finer question.

The 18 that only deps found are all in the module graph and not in a `go.mod`. None is compiled in. One of my command-line tools carries a `golang.org/x/crypto` from 2021 with 46 advisories on it:

```
$ go mod why -m golang.org/x/crypto
# golang.org/x/crypto
(main module does not need module golang.org/x/crypto)
```

It is in the graph because some other module's `go.mod` names it. deps puts these under "Not compiled in", dims them and never sends a notification. osv-scanner leaves them out. If the question is what to fix, leaving them out is the better answer. I like seeing what the graph could pull in, but I can't count 18 dimmed rows as 18 catches.

The 6 that only osv-scanner found come from one `requirements.txt`. It has two exact pins and one unpinned package. deps reads the two pins and stops. osv-scanner resolves the file into 44 packages and flags six of them. As far as I can tell it asks [deps.dev](https://deps.dev) for the versions; its docs describe that lookup only for Maven. The resolved versions include setuptools 9.1.0, uploaded to PyPI in December 2014. I doubt a fresh install picks that. I can't prove it, because there is no lockfile, so neither tool knows what pip would install. osv-scanner made a guess; deps didn't look. The fix is on my side: write a lockfile.

Three things sit outside that table.

- osv-scanner flagged ten packages in repos deps never scanned, because I had never registered them. That is the real miss of the morning, and all it needs is a few lines in the registry.
- The one finding deps counts as live today is in the install tree of an npm tool that mise installed. No repo pins it, so a scan of repo directories can't find it.
- Three of my six `Package.resolved` files sit inside an `*.xcodeproj` that `.gitignore` covers, and osv-scanner honours `.gitignore`. `--no-ignore` finds them, along with every build directory. The package count went from 461 to 1,382.

## What each tool is for

osv-scanner answers a question you ask: is this tree vulnerable right now? It does a lot that deps can't.

- Call analysis for Go and Rust, down to the function.
- `osv-scanner fix`, which suggests the upgrades that remove a finding.
- Licence scanning, an offline mode, and container image scans.
- SARIF, CycloneDX, SPDX and HTML output for other tools to read.
- More ecosystems. It read the `yarn.lock` and the Dart `pubspec.lock` that deps has no parser for.
- Ignore rules that expire on a date. I tested that one, and it works.
- An `experimental-mcp` mode. It is a Model Context Protocol (MCP) server with three tools: `scan_vulnerable_dependencies`, `get_vulnerability_details` and `ignore_vulnerability`.

deps answers a question I forget to ask: did something I already pinned or installed go bad since yesterday?

- A registry of repos and a daily loop that catches up after the Mac sleeps.
- One macOS banner per scan, and events in my local event log.
- An acknowledgement tied to the exact version, so a finding comes back when the version changes.
- What the registries say: a version withdrawn, yanked, quarantined or deprecated on npm, PyPI or the Go proxy, often before an advisory exists.
- GitHub Actions refs, with a warning when a ref is a tag that can be moved.
- Browser libraries a script downloads, and the trees of tools mise installs.
- A web page and an MCP server that show the same scan.

Only the Go, npm, Python and Swift parsing overlaps, and that is the part of deps I maintain least.

## The decision

I'm keeping deps, with three changes.

1. The unregistered repos go into the registry. That closes the gap that mattered.
2. The `requirements.txt` gets a lockfile.
3. I'll look at running govulncheck per module, so "not imported" can become "not called".

I also asked what it would take to put osv-scanner under deps as the engine. A rough count, which I haven't checked line by line: about 1,500 of the 6,900 lines would go, about 700 would be rewritten, and the rest would stay. The module graph view would be lost. That saves less than a quarter of the code, and I would then follow someone else's JSON schema.

What would change my mind:

- A need for Rust, Dart or yarn support. I would call osv-scanner before I wrote those parsers.
- osv-scanner learning to read Actions refs and installed tool trees, and to watch the registries.
- A move to shared repos with continuous integration. There osv-scanner in the pipeline is the right tool, and a banner on one Mac isn't.

The morning was worth it for the registry gap alone. osv-scanner is the better scanner, and I'll keep running it by hand now and then as a second opinion. What I need every day is the watching, and that part is deps. The code is in [thismoon](https://github.com/mad01/thismoon).
