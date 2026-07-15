# Example workflow — tie logging to your session handoff

The hardest part of this method isn't the schema, it's *remembering to log*. A log line is
only useful if it lands on **every** real session, and a "log at session end" instruction is
easy for both you and the model to skip.

The fix: **hook the log append onto a wrap-up ritual you already perform** — a handoff, a
session summary, a "commit + close out" step. Whenever that ritual runs, the log line is
part of it. You never decide to log; logging is a side effect of ending the session properly.

## The pattern

```
end of a real session
        │
        ▼
  run your handoff / wrap-up step   ──►  (a) write the handoff for the next session
  (something you already do)             (b) append ONE sizing-log line  ← added here
        │
        ▼
   next session starts from the handoff
```

Because the handoff already forces you to *summarize what the session did*, you have exactly
the context the log line needs — domain, how much was delegatable, how deep/long the work
was, whether you were in a tight loop. Logging piggybacks on judgment you're already making.

## How to wire it (pick what your harness supports)

- **Handoff skill / command.** If your wrap-up is a slash-command or skill, add one final
  step to its instructions: *"After writing the handoff, append one schema-conformant line to
  the sizing log (read the clock from the OS; leave `verified` null unless an oracle actually
  ran)."* This is what the author does — the handoff routine ends by logging.
- **Stop / session-end hook.** If your harness has a session-end hook, call a tiny script
  that prompts for (or infers) the fields and appends the line.
- **Git post-commit.** If "done" means a commit, a `post-commit` hook can append a line (best
  for coding domains where every session ends in a commit).
- **Manual checklist.** Lowest-tech: add "append sizing line" as the last item of whatever
  close-out checklist you keep.

## Worked example — handoff-tied logging (the author's setup)

The author runs a per-thread **handoff** at the end of each session so the next session
resumes cleanly. The handoff routine's final step appends one sizing-log line. Result: ~24
sessions logged with zero standalone "remember to log" effort — the data accrued as a
byproduct of good session hygiene, and the 8 oracle-verified rows were added opportunistically
on top.

Genericized handoff-final-step instruction:

> After writing the handoff summary for the next session, append ONE line to the sizing log
> (`~/llm_local_sizing_log.jsonl`): run `date "+%Y-%m-%d %H:%M %A"` for the timestamp, set
> `domain` and `interaction`, size `min_model` / `min_model_solo` blind to any target
> machine, keep `task` generic, leave `verified` null unless a real small-model run happened
> this session. One line, append-only, never rewrite past lines. Skip trivial sessions.

## Why this beats a standalone "log at session end" rule

A bare "log at the end" instruction competes with the natural urge to just *stop* when the
work is done. Bolting it to a ritual you won't skip anyway (you want the handoff; you want the
commit) removes the decision. Completeness of the dataset is what makes the per-domain
distribution trustworthy — a log that only captures the sessions you *remembered* is biased
toward memorable (big) sessions and oversizes the hardware.
