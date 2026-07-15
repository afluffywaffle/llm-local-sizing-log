# llm-local-sizing-log

A **platform-agnostic format and method** for deciding what local-LLM hardware (if any)
to buy, using evidence from your *real* agent sessions instead of benchmarks and vibes.

You keep an append-only JSONL log — one line per working session — recording how much
*machine* each task actually demanded. Periodically you run the delegatable chunk through
a real small model as a **capability oracle** and record whether its output needed
correction. Over time that turns your orchestrating model's *guesses* about smaller models
into a *measured direction-of-bias* you can correct for.

This repo ships the **method**, not one person's data. It includes a Claude Code reference
implementation, but the format and analyzer are drop-in for any agent harness.

## The idea in one paragraph

An LLM's estimate of "a 14B model could have done this chunk" is a *prediction with no
error term* — produced by the same model that did the work, never a counterfactual run.
Left uncorrected, your log is a well-organized record of one model's opinions about its own
routing. The fix is cheap: a handful of **verified** oracle runs (~8–12, spread across
domains) is enough to learn the *direction* your estimator skews, after which you keep
estimating cheaply and apply the correction.

## What's here

| File | What it is | Platform-specific? |
|---|---|---|
| `SCHEMA.md` | Field definitions for a log line | No — neutral |
| `template.jsonl` | Schema line + synthetic example rows | No — neutral |
| `analyze.py` | Aggregate by domain; `--calibrate` computes your estimator's bias | No — neutral |
| `BOOTSTRAP.md` | Meta-prompt: your agent writes *its own* logger for *your* harness | Generator |
| `WORKFLOW.md` | Example: tie the log append to a wrap-up ritual (handoff/commit) so it never gets skipped | Pattern |
| `CALIBRATION.md` | Protocol to derive *your* estimator's bias correction | Generator |
| `privacy_scan.py` | Flag likely PII / secrets before you push | No — neutral |
| `claude-code/` | Reference logging instruction for Claude Code | Yes — example |

## Adopter flow (stand up your own — nothing here depends on the author's data)

1. **Bootstrap the logger.** Paste `BOOTSTRAP.md` into your own agent → it emits the
   persistent per-session instruction in *your* harness's form (system prompt / hook /
   `CLAUDE.md` / wrapper). See `claude-code/` for a worked example, and `WORKFLOW.md` for the
   key reliability trick: tie the append to a wrap-up ritual you already do (handoff / commit)
   so it never gets skipped.
2. **Let rows accrue.** Each real working session appends one line.
3. **Run oracles.** Periodically send a session's delegatable chunk to a real small model
   (Ollama / OpenRouter / local) and fill the `verified` field with the outcome.
4. **Calibrate.** After ~8–12 verified rows, `python analyze.py --calibrate` prints *your*
   estimator's direction-of-bias per domain. Append it as a `_calibration` line.
5. **Decide.** `python analyze.py` shows the per-domain `min_model` distribution; buy the
   cheapest box whose RAM covers what the data (bias-corrected) actually demands.

## Example findings (illustration only — not data shipped in this repo)

Aggregated, anonymized output from the author's own log (~24 sessions, 8 verified oracle
runs), to show the *shape* of what the method produces. These are **one person's numbers for
one buying decision on one orchestrating model** — an example, not a benchmark. No task text
or personal data is included, here or anywhere in this repo.

| Domain | Delegated `min_model` (est.) | Oracle verdict | Read |
|---|---|---|---|
| **coding** | ~30–32B | 30B coder **passed** a graded test oracle (matched the hosted mid-tier) | **Feasible** — delegates well to a local ~30B; estimate ~accurate |
| **prose** | logged ~32B | 32B *and* 70B **failed** (intrinsic fabrication) | **Not feasible** at any local size; estimate was optimistic |

The domain split is the whole point: a *verifiable* domain (coding) delegated cheaply and the
estimate held up; a *grounded-generation* domain (prose) was over-estimated because
fabrication doesn't show in a self-graded look. **Your domains and your numbers will differ —
run the protocol for your own estimator.**

## Scope / honesty

This is a **method, not a leaderboard.** A filled-in log is n=1 *you*, for one buying
decision. The calibration direction is specific to **your orchestrating model** — the
author's Claude-Opus correction (prose-optimistic, coding-accurate; see `CALIBRATION.md`)
is a *worked example*, not a number to copy onto a different model. Re-run the protocol for
your own estimator.

## Privacy

`task` notes and oracle `note` fields tend to accumulate project details. **Run
`python privacy_scan.py your_log.jsonl` before pushing anything**, and never commit your
real log to a public repo — commit the *format* and (optionally) an aggregated,
anonymized findings table. `.gitignore` here excludes `*.local.jsonl` by default.
