---
title: "Let the small model do the reading"
date: 2026-11-01
slug: csl-ask-let-the-small-model-read
description: "csl_ask hands a file read to a cheap worker model and returns the answer, not the lines. Measured: the small model reads as well as the big ones at a hundredth of the price, and the agent only picks it up when the tools push."
tags: claude-code, mcp, code-search, evals, developer-tools, ai
ai_context: "Blog post on csl_ask, a bulk-reading tool in code-search-local (csl, part of github.com/mad01/thismoon). A search query selects files, a cheap worker model (Claude Haiku 5.5) reads them whole and returns only the answer. Reports an eval with Haiku 5.5, Opus 5.5 and Fable 5.1 as readers (every model finds the facts; Haiku is the cheapest and the tersest), four runs of an eval runner showing that a coding agent adopts the tool through tool-side signals (alwaysLoad, tool descriptions, a hook hint after a whole-file read) and not through CLAUDE.md prose, and a decision rule for when to use bulk reading, a direct read, or a subagent, including per-repo questions across a fleet of over a thousand repositories."
---

# Let the small model do the reading

Here is a thing my coding agent did last week. I asked which errors a function could return. The function lived in an 843-line file. The agent read the whole file into its context, about twelve thousand tokens, answered in one line, and never looked at those lines again.

That read wasn't free. The session model is the expensive one, and every token it reads feeds every token it thinks afterwards. Twelve thousand tokens for a one-line answer is a bad trade, and an agent makes that trade ten times a session.

The fix I landed on: the agent keeps the discovery and hands off the reading. Finding the right files is what a strong model is good at. Reading them isn't where its strength goes.

## What csl_ask does

[csl](https://github.com/mad01/thismoon/tree/main/services/csl) is my local code search, a zoekt index over every git checkout on the machine, exposed to Claude Code as a Model Context Protocol (MCP) server. I wrote about it [earlier this year](/blog/csl-local-mcp-for-code-search/). It now has a tool called `csl_ask`.

You give it a question and one or more search queries. The queries select up to a handful of files. A cheap worker model, Claude Haiku 5.5, reads those files whole and answers the question. What comes back into the session is the answer plus a footer with the corpus size and the list price of the call. The lines stay out.

The same tool has a per-repo mode. One question, a query that matches files in forty repositories, forty short answers back. That is the mode I care about most, since the fleet I work in has well over a thousand repositories and no session model can read across it.

## Does a small model read well enough?

That was my first worry, so I measured it before trusting it. The eval is eight questions over real files from my own tools, 666 to 2000 lines each. The grader is strict. Every expected fact must be present and no forbidden claim may appear. Every `path:line` reference must point at a line that holds what it names, and the answer must fit a size budget. Three reps per question, so 24 reads per model.

| reader | pass | facts found | wrong line references | list price for 24 reads |
|---|---|---|---|---|
| Haiku 5.5 | 79% | 0.99 | 2 of 185 | $0.055 |
| Opus 5.5 | 29% | 0.98 | 6 of 253 | $2.14 |
| Fable 5.1 | 50% | 0.98 | 1 of 213 | $5.33 |

Every model finds the facts. The pass rates differ because the big models write too much. Opus went over the size budget on 71 percent of its answers, Fable on 46 percent, Haiku on 8 percent. Fable had the most accurate line references of the three. Haiku was close behind it and a hundred times cheaper.

So the small model is a fine reader. For an extractive question, which is what most reads are, it loses nothing against the session model reading the same lines. It just answers shorter.

## Will the agent use it?

My second worry, and the more interesting one. A tool nobody calls is a tool that doesn't exist.

I have an eval runner that drives `claude -p` with my real hooks and MCP servers through six fixed tasks. Each run is scored on its outcome and on what it cost in turns and tokens. I ran it four times while rolling the tool out.

Runs A and B: the tool was listed in every session, and my global `CLAUDE.md` carried a rule saying to use it for large files. It was never called. The model read the 843-line file whole, both times. Prose did nothing.

Run C came after the tool-side round. The tool was marked as always loaded with a sharper description. The file-read tool named `csl_ask` in its "truncated" note, and a hook hint fired after any whole-file read. Now the model picked `csl_ask` first in both tasks that called for it, then checked the answer with two ranged reads of the spots it would cite. The worker calls cost three tenths of a cent and two tenths of a cent.

Run D raised the turn budget for the multi-file task and scored a mean of 0.97. Its large-file task finished in four turns against eleven without the tool. The multi-file task took seven against ten.

The pattern the model found on its own is the one I would have written: ask, then verify one claim with a ranged read. I didn't tell it to verify. It did that itself.

## When to reach for it

What I now have in my global rules, in one paragraph. Discovery is yours; reading is the worker's. Find the files with search and outline tools. A question over a file of 300 lines or more, or over two or more files, goes to `csl_ask` before any read. Verify a claim you will act on with one ranged read. Read lines yourself only for a small file or a region you are about to edit.

When reading it yourself is just as good:

- The file is under 300 lines. One read, nothing lost.
- You are about to edit the region. You need the exact lines anyway.
- The question needs judgment, not extraction. "Is this design sound" isn't a reading task.

When a subagent is the right tool: the discovery itself is the hard part. Following references across packages, searching with vocabulary you don't have yet. The worker reads a fixed corpus and can't search. An explorer agent can, and it can call `csl_ask` for its own reads.

When the fleet case applies: a question like "how does each service set its retry policy" is one per-repo ask over a query that selects those services. Never a read per repo in the session, never an agent per repo.

## What I'm not sure about yet

The answer is only as good as the query. A query that selects the wrong files gives a confident answer about the wrong files. The verify step covers this, and I wouldn't drop it.

My control arm leaked. The "without the tool" runs denied the MCP tool, and in run D the model found the command-line form and called that instead. It still took eleven turns, but the comparison isn't as clean as I wanted.

The cost columns in the eval runner are noisy. They rose on every task between runs C and D, including the two tasks the tool never touches. So they reflect prompt cache state and run-to-run variance more than anything I changed.

Per-repo asking runs four worker calls at a time. Forty repositories answer in under a minute. The whole fleet takes about twenty, so the query has to narrow first.

And these are one-rep runs on six tasks. Enough to see the pattern, not enough to put a decimal on it.

## Try it before you read

That is the rule in one line. A thin answer costs one cheap call, and the lines are still there to read after. The code and the run reports are in [thismoon](https://github.com/mad01/thismoon).
