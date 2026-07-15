# CALIBRATION — turn your estimator's guesses into a measured correction

Your `min_model` column is a *prediction with no error term*: the same model that did the
work also guessed what a smaller model could have done, and the delegated chunks are the ones
it *routed* as mechanical — so their low ceiling partly measures the router, not local-model
capability. This protocol adds the missing error term.

## The protocol

1. **Keep estimating cheaply.** Every session gets `min_model` / `min_model_solo` as usual.
2. **Run real oracles on a few sessions (~8–12 total, spread across domains).** Take that
   session's delegatable chunk, send it to a *real* small model (Ollama, a local runtime, or
   a cheap cloud host like OpenRouter — latency is irrelevant, this is a *capability* test),
   and record `verified: {model, outcome, note}` where `outcome ∈ pass | minor-fix | failed`.
3. **Make the oracle objective — pair it with a domain benchmark tool.** A self-graded
   "looks right" is weak evidence. Wherever the domain has an objective checker, run the
   oracle *through it*:
   - **Coding** → a graded test suite / fixture oracle (e.g. a vitest set with known-good
     answers). `outcome` = did it pass the tests.
   - **Prose / canon-grounded** → an author/rubric score, or a hallucination-trap task with a
     known correct answer (does it fabricate?).
   - **Research** → a citation-check / claim-verification pass.
   The benchmark tools are what make `verified` ground truth rather than another opinion.
   Build or reuse a small oracle per domain and point the delegated chunk at it.
4. **Derive the direction.** `python analyze.py your_log.jsonl --calibrate` crosses each
   verified outcome against the estimate it was logged with, per domain, and prints whether
   your estimator skews optimistic, accurate, or pessimistic.
5. **Record it.** Append a `_calibration` line (see `SCHEMA.md`). Then keep estimating
   cheaply and *apply the correction* when reading the distribution.

## What "enough" looks like

~8–12 verified runs spread across your domains is enough to read the **direction** of bias
(not a precise error bar). You don't verify every session — you verify enough to learn how to
discount the cheap estimates.

## Worked example (the author's Claude-Opus estimator — do NOT copy the numbers)

After 8 oracle runs across coding + prose, the author's log produced this `_calibration`:

> **Coding:** parameter estimates well-calibrated — a 30B coder matched the hosted mid-tier
> on a graded test oracle (12/12). Two refinements: **14B is the real floor** (below it the
> iterate-loop stops self-correcting), and the **RAM map understates the load-time peak** — a
> 30B model failed to *load* on an 18GB box (transient spiked past resident weights), so size
> for the peak ⇒ 30B-class needs ≥24–32GB real.
> **Prose:** estimates run **one-to-two tiers optimistic** — 32B and even 70B *failed* canon
> fidelity by fabricating; failure is intrinsic, not fixed by scale. Apply: log prose *prep*
> as `none`, prose *draft-from-clean-pack* as 24–32B assistive-only.
> **Confidence differs by domain:** trust coding estimates ~as-logged; discount prose by a
> tier.

The **shape** of that finding is the transferable lesson: *verifiable* domains (coding) tend
to calibrate well and delegate cheaply; *grounded-generation* domains (prose) tend to be
over-estimated because fabrication doesn't show up in a self-graded look. **The specific
tiers are that estimator's, on those tasks.** Re-run the protocol for yours — a different
orchestrating model will skew differently, and your domains may not be these.
