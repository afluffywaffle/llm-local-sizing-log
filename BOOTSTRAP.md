# BOOTSTRAP — generate your own logger

This repo does **not** ship a ready-made logging hook, because how a session gets logged is
specific to your agent harness. Instead, paste the meta-prompt below into your own agent
(Claude Code, a custom SDK agent, an IDE assistant, a shell wrapper — whatever you run).
It will emit the persistent per-session instruction *in the form your harness uses*.

See `claude-code/instruction.md` for a worked example of what the output looks like on one
platform.

---

## Meta-prompt (paste into your agent)

> I want you to self-log hardware-sizing data at the end of every session that did real
> work, so I can decide what local-LLM hardware to buy. Here is the log schema:
>
> `<paste the contents of SCHEMA.md here>`
>
> Do two things:
>
> 1. Tell me the mechanism in **my** harness that will make you append one schema-conformant
>    JSONL line at the end of each real working session without me asking each time — e.g. a
>    persistent system-prompt / project-instruction file, a Stop hook, a session-end script,
>    or a wrapper. Pick the one my harness actually supports and write the exact
>    configuration.
> 2. Write the standing instruction text itself: at session end, read the real clock from the
>    OS (never guess), size `min_model` and `min_model_solo` **independently and blind to any
>    hardware I hope to buy** (if the honest floor is 70B+, say so), keep `interrupts` an
>    integer, keep `task` generic (no secrets/PII), leave `verified` null unless I actually
>    ran the chunk through a real small model, and append exactly one line to
>    `~/llm_local_sizing_log.jsonl` (or a path I specify). Never rewrite past lines.
>
> Then confirm the mechanism is installed.

---

## Notes

- **Size blind to the target box.** The single biggest failure mode is anchoring `min_model`
  to the machine you hope to buy. Estimate on the task's own merits; the analyzer and the
  calibration step exist precisely to catch this bias, but don't feed it in.
- **`verified` stays null by default.** It's only filled on the ~8–12 sessions where you run
  a real oracle (see `CALIBRATION.md`). The estimate columns are cheap; the oracle is the
  expensive, decisive part — do a few, not all.
- **One line per session; append-only.** The whole dataset's integrity is that past lines are
  never edited. Corrections go in as *new* `_calibration` lines.
