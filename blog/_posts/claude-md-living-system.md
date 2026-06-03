---
title: "My CLAUDE.md is a living system, not a config file"
date: 2026-06-03
slug: claude-md-living-system
description: "CLAUDE.md drifts: rules get ignored, go stale, or were never right. Instead of editing it by feel, I run a self-eval skill after each session that grades my rules and proposes the diff."
tags: claude-code, ai, developer-tools, workflow
ai_context: "Blog post on treating Claude Code's CLAUDE.md as a living system maintained by a post-session self-evaluation skill. The skill reads the finished session, sorts each rule into buckets (fired-and-helped, ignored, wrong, missing, redundant), and proposes concrete edits. Includes an annotated skeleton of the skill.md and the prune-to-tool pattern."
---

# My CLAUDE.md is a living system, not a config file

My global `CLAUDE.md` had crept past two hundred lines before I admitted I had no idea which rules still mattered. Some of them I added after a bad session months ago. Some I copied from a thread because they sounded sensible. A few I'm fairly sure the model has never once obeyed.

That's the trap with a file like this. Every rule feels free when you add it, so you keep adding. The file only grows. And a long list of instructions isn't a stronger prompt; it's a noisier one. Rules compete for the model's attention, and the more you pile on, the more each individual rule gets diluted.

So I stopped treating `CLAUDE.md` as a config file I write once and forget. I treat it as a system that has to keep earning its size.

## How rules earn their place

A rule is not free. It costs tokens in every single session, and it competes with every other rule for priority. So the default state of any rule should be deleted. It only survives if I can point to a session where it changed the model's behavior for the better.

That flips the usual maintenance question. Instead of "what should I add after this annoying thing happened," the question becomes "which of the rules I already have actually did anything." Most editing energy goes into cutting and sharpening, not appending.

The problem is that I can't answer that question from memory. I don't remember, three weeks later, whether the "always use conventional commits" line did the work or whether the model would have done it anyway. I need evidence from real sessions, and I need something other than my own optimism to read it.

## The self-eval pass

So I built a skill that runs at the end of a substantial session. It reads back what actually happened and grades my rules against it. The output isn't a vague "here's how it went." It sorts each relevant rule into one of five buckets:

- **Fired and helped.** The rule was relevant, the model followed it, and the outcome was better for it. Keep. Maybe tighten the wording.
- **Ignored.** The rule was relevant and the model didn't follow it. This is the interesting one. Usually it means the rule is buried, too vague to act on, or quietly contradicted by another rule somewhere above it.
- **Wrong.** The rule fired, the model obeyed, and I had to correct the result anyway. The rule itself is bad advice.
- **Missing.** I corrected the model on something no rule covers. That correction is a candidate for a new rule, but only if it's likely to recur.
- **Redundant.** The behavior is already handled better somewhere else, so the prose in `CLAUDE.md` is dead weight.

The split between "ignored" and "wrong" is the part I care about most. For a long time I lumped them together as "the model didn't do what I wanted," and the fix was always to make the rule louder. ALL CAPS, more bolding, an extra "ALWAYS." That helps an ignored rule a little. It does nothing for a wrong rule except make the model fail more confidently.

## The skill.md

The skill is short. The frontmatter says when it runs and what it's allowed to touch:

```yaml
---
name: claude-md-eval
description: After a substantial session, audit CLAUDE.md against what actually
  happened. Sort each relevant rule into fired/ignored/wrong/missing/redundant
  and propose concrete edits. Use at end of session or when invoked.
allowed-tools: [Read, Grep, Glob, AskUserQuestion]
---
```

Note what's missing from `allowed-tools`: there's no `Edit` and no `Write`. The skill can read my config and read the session, but it cannot rewrite the file on its own. That constraint is the whole point, and I'll come back to it.

The body is a handful of steps, each doing one thing:

1. **Read the rules.** Load the active `CLAUDE.md`, both the global one and any repo-level file, so the audit knows what it's grading against.
2. **Read the session for signal.** This is where the discipline lives. The skill looks for three kinds of signal only: a behavioral diff (the model did X, a rule said Y), an explicit correction from me, or an outright failure. The guardrail is that every finding has to cite a specific moment in the session. No "this rule seems weak." If it can't point to the turn where the rule mattered, it isn't a finding.
3. **Bucket each rule.** Walk the relevant rules and drop each into one of the five buckets above.
4. **Propose a diff, don't apply it.** For every finding the skill writes a concrete edit: sharpen this line, move it above the rule that contradicts it, delete it, add this new one. Then it stops and asks. The minimal-change rule applies here, so it only proposes edits a signal justifies. It doesn't get to "tidy up while it's in there."

That fourth step is why the frontmatter withholds write access. An eval that grades my config and then silently rewrites it is an eval I'll stop trusting the first time it deletes something I wanted. I want the verdict and the proposed patch in front of me, and I want to be the one who applies it. The skill's job is to find evidence and draft the change. The decision stays mine.

The output reads like a short review:

```text
RULE: "use conventional commits"          → fired + helped
  Model wrote `feat:` / `fix:` prefixes unprompted across 3 commits. Keep as-is.

RULE: "never add a co-author line"         → ignored
  Model appended a co-author trailer on the first commit; I removed it by hand.
  Rule is on line 180, well below the commit section. Proposed: move it into
  the commit rules near the top and bold the NEVER.

RULE: 28-line block on how to use my CLI   → redundant
  Model never consulted it; it called the tool directly via its description.
  Proposed: delete the block.
```

Three findings, three different actions. None of them is "make the rule louder."

## The first run graded itself wrong

The first time I ran the eval, it flagged one of my rules as ignored, and the evidence looked damning: a safe command the rule should have covered, denied hundreds of times across the logs. The proposed fix was to move the rule into config. Reasonable. Also wrong.

Two things the first pass skipped. It didn't separate my interactive sessions from the background agents I spawn for long jobs, and it didn't check what my config already allowed. Once I split those apart the picture inverted. My interactive sessions had almost no denials. The command was already allowlisted. And every one of those hundreds of denials came from background agents running in a stricter permission context that never loaded the allowlist. The rule wasn't ignored. It was working fine, and the noise was piling up somewhere the rule couldn't reach.

That's the failure mode of any self-assessment. Evidence that isn't segmented, and a current state it never bothered to read. An eval that skips both doesn't find problems, it manufactures them. It's also the second reason the skill proposes instead of applies: if it had write access, it would have "fixed" a rule that was never broken.

## Pruning: when a rule becomes a tool

That last finding points at the most satisfying kind of cut. A lot of what accumulates in a `CLAUDE.md` is documentation of a command-line tool: when to reach for it, what flags it takes, how to read its output. Paragraphs of prose teaching the model about a thing.

The moment you expose that same tool as a typed tool the model can call directly, with a clear description of when to use it, the prose is obsolete. The description string carries the trigger now, right there in the tool list where the model reads it at planning time. It doesn't have to remember a paragraph buried halfway down a config file.

When the eval flags one of those blocks as redundant, the win isn't a tweak. It's deleting twenty or thirty lines outright and watching the behavior stay exactly the same, because the knowledge moved somewhere the model actually looks. That's the difference between a rule the model has to recall and a tool the model is handed.

## What I took away

The quality of a `CLAUDE.md` isn't set by how carefully you write it. It's set by how willing you are to cut from it, and that willingness only holds if something keeps showing you which rules are dead. Left alone, the file grows in one direction. Graded against real sessions, it can shrink and get sharper at the same time. The eval doesn't make my config longer. Most of the time it makes it shorter, and that's the point.
