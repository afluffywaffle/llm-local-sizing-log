# Claude Code reference implementation

A worked example of what `BOOTSTRAP.md` produces on **one** platform (Claude Code). Adapt
the mechanism for your own harness — the *content* of the instruction is portable; the
*delivery* (a persistent user/project instruction file) is Claude-Code-specific.

## Mechanism

Claude Code loads `~/.claude/CLAUDE.md` (global) and project `CLAUDE.md` files into every
session. Put the standing instruction there; the model appends a log line at session end.
(A `Stop` hook is an alternative if you'd rather script it deterministically.)

## Standing instruction text (paste into `~/.claude/CLAUDE.md`)

> ## Local-LLM hardware-sizing log
>
> At the **end of every session that did real work** — any project or general
> research/planning — append ONE JSON line to `~/llm_local_sizing_log.jsonl` (schema on the
> file's first line). Run `date "+%Y-%m-%d %H:%M %A"` for an accurate timestamp — never guess
> the clock. Always set `domain` (coding|prose|research|general — the primary slicing axis)
> and `interaction` (interactive|mixed|batch) + `interrupts` (integer).
>
> Size `min_model` (DELEGATED: cloud orchestrates + reasons, local executes the delegatable
> chunk) and `min_model_solo` (ALL-LOCAL: whole session on a local model) **independently and
> BLIND to any target machine** — if the honest floor is 70B+, log it. `context` = reasoning
> DEPTH only; prompt LENGTH is its own field `ctx_len`. Keep `task` generic (no secrets/PII).
> Leave `verified` null unless you actually ran the chunk through a real small model. One line
> only; never rewrite past lines. Skip trivial sessions.

## Notes specific to Claude Code

- Because `CLAUDE.md` is re-sent every turn, keep the instruction terse — link the full
  `SCHEMA.md` rather than inlining it.
- If you keep the log inside a project the assistant can read, it can also *analyze* it on
  request (`analyze.py`) and append `_calibration` lines itself.
- Sanitize before sharing: your real `~/llm_local_sizing_log.jsonl` will contain project
  names and task notes — run `privacy_scan.py` and never commit it to a public repo.
