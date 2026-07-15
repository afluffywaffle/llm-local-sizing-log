# Log schema

One append-only JSONL file. **One JSON object per session that did real work.** Never
rewrite past lines. Two special line types (`_schema`, `_calibration`) may appear anywhere
and are ignored by the aggregator except where noted.

## Session line — fields

| Field | Values | Meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | Session date. Don't guess the clock — read it from the OS. |
| `time` | `HH:MM` 24h local | Start time. Time-of-day + weekday can correlate with task size/interaction style. |
| `weekday` | `Mon`..`Sun` | |
| `project` | short name / `research` / `general` | |
| `domain` | `coding` \| `prose` \| `research` \| `general` (extend freely) | **Primary slicing axis.** A local model handles prose/recipes far more cheaply than coding — size per domain. |
| `task` | one line | What was done. *(Privacy-sensitive — keep generic.)* |
| `category` | coding: `mechanical`\|`feature`\|`debug`\|`architecture`; else `research`\|`general` | |
| `tier_needed` | `haiku`\|`sonnet`\|`opus` (or your hosted tiers) | Lowest hosted tier that could do it solo — honest floor. |
| `context` | `light`\|`medium`\|`heavy` | **Reasoning DEPTH only** (cross-file / interpretive difficulty). NOT prompt size. |
| `ctx_len` | `<4k`\|`4-16k`\|`16-64k`\|`64k+` | Working-set LENGTH of the delegatable chunk. Feeds the *quality* floor (small models degrade on long prompts) and RAM (KV cache) — independent of `context`. |
| `delegatable` | `none`\|`some`\|`most`\|`all` | How much of THIS session a cloud model could hand to a local executor while keeping only review/planning. |
| `min_model` | `7B`\|`14B`\|`32B`\|`70B`\|`>70B`\|`none` | **Scenario A — DELEGATED:** smallest local class that could execute the *delegatable chunk* well while cloud orchestrates + does the hard reasoning. |
| `min_model_solo` | same set (`none` = not doable locally at any size) | **Scenario B — ALL-LOCAL:** whole session on a local model, no cloud help. Watch the GAP vs `min_model`: big gap ⇒ value is in cloud orchestration, a small cheap box suffices. |
| `blocker` | short text / empty | If `delegatable < most` or `min_model >= 70B`: the one limiting thing (reasoning depth, context window, tool-loop reliability, niche-API knowledge, or `ctx_len` degradation). |
| `interaction` | `interactive`\|`mixed`\|`batch` | Tight wait-on-each-reply loop (latency-sensitive) vs fire-and-walk-away (tolerates a slow big box). |
| `interrupts` | integer | Times the user redirected mid-work. Proxy for loop tightness. *(Keep it an int.)* |
| `latency_note` | text / empty | Explicit impatience/patience signals. Don't fabricate seconds. |
| `verified` | `null` or object (below) | **The calibration oracle.** Fill on the ~8–12 sessions where you actually ran the chunk through a real small model. |
| `ttft_note` | text / empty | Prompt-prefill / time-to-first-token behavior when a real local run happens. Prefill is COMPUTE-bound (Macs weak, NVIDIA strong); decode is BANDWIDTH-bound. Long prompts make prefill a first-class axis. Log real numbers only. |

### `verified` object

```json
{"model": "14B", "outcome": "pass|minor-fix|failed", "note": "what needed correction"}
```

An **actual run** of the delegatable chunk through a real small local/cloud model (latency
irrelevant — this is a *capability* oracle). `outcome` = did its output need correction.
This is the field that separates "48GB is enough" from "you need 128GB" from "stays hosted."

## `_calibration` line

Append (never edit) when a batch of `verified` rows reveals your estimator's bias:

```json
{"_calibration": "direction-of-bias correction to APPLY to future min_model estimates, per domain", "date": "YYYY-MM-DD"}
```

`analyze.py --calibrate` generates the evidence for this line. **It is specific to your
orchestrating model** — do not import someone else's.

## Interpretation (why the fields split the way they do)

- **Split by `domain` first**, then look at the `min_model` / `min_model_solo`
  distribution within each. Mostly `7-14B` ⇒ a small cheap box; mostly `32B` ⇒ ~48GB
  unified; frequent `70B+` ⇒ ~128GB; `none` ⇒ stays hosted.
- **Depth vs length are different machines.** `context=heavy` (deep thinking) wants a
  *smarter* model; high `ctx_len` (long prompt) wants *more RAM* + raises the quality floor
  (small models hallucinate on long prompts) and stresses **prefill** (a Mac's weak axis).
  Patience rescues slow-but-correct; it never rescues a small model that hallucinates on a
  long prompt.
- **`interaction` picks the silicon shape.** Many interactive/high-interrupt sessions ⇒ you
  need high tokens/sec ⇒ favor a fast box + smaller models. Mostly batch ⇒ a slow roomy box
  is fine.
- **RAM floor > naive weight size.** Load-time transients + KV cache push the real
  requirement above the resident-weights estimate. Size the box for the peak, not the
  weights (see `CALIBRATION.md` for a measured example).
