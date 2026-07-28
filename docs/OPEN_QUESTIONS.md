# OPEN QUESTIONS — contradictions and ambiguities in the specification

PDF p. 5 grants **academic freedom on contradiction**: where the book
contradicts itself, we may choose one reading and proceed, *provided the choice
is stated explicitly in the report* — where the contradiction was identified,
what was chosen, and why. A reasoned, documented choice is not held against the
team.

This file is that record. Everything here must reach the final `README.md`
academic report.

Two things this freedom does **not** cover:

- **Appendix F remains the single binding source for numeric values** even in
  the presence of contradiction (PDF p. 5).
- Where two readings materially change compliance, the question is escalated
  rather than silently resolved.

Status key: **RESOLVED** (settled by source priority; recorded in
[DECISIONS.md](DECISIONS.md)) · **NEGOTIATE** (must be agreed with the opponent
team before a match) · **ESCALATE** (needs the lecturer, or a decision the user
must make).

---

## Q-1 — `num_games`: Appendix F says 6 FIXED, the example config ships 1

**Status: RESOLVED** → see [DECISIONS.md](DECISIONS.md) D-2.

- Appendix F table 18 row 1 (PDF p. 154): `[num_sub_games]` = **6**, status
  **FIXED** ("deviation disqualifies the team").
- Appendix B example `config/game.json` (PDF p. 129): `"num_games": 1`.
- Appendix B narrative (PDF p. 130): *"the `num_games` field is sent by default
  with the value 1 (a single example sub-game); the full league series requires
  `[num_sub_games]` sub-games."*

A parameter cannot simultaneously be FIXED at 6 and default to 1. The narrative
suggests the intent is that 1 is a demo convenience and 6 is the league value,
but Appendix F's FIXED status admits no such split.

**Resolution:** Source priority rule 1 — Appendix F overrides every numerical
example elsewhere. **We ship 6.** A local demo may override it, but no config
used in a counting league match may carry anything but 6.

**Residual risk:** if an opponent team ships the Appendix B example verbatim,
the config-hash exchange will fail and neither side will be able to play until
the discrepancy is discussed. Raise it in negotiation proactively.

---

## Q-2 — Turn order is never specified

**Status: NEGOTIATE.**

The PDF never states whether the cop or the thief moves first. What it fixes
(Ch. 4, PDF p. 43) is that decay is applied *at the end of each full turn — after
both the cop and the thief have completed their move*, so turns are paired.
Chapter 8's state machine is symmetric and role-agnostic.

**Our design** ([PROTOCOL.md](PROTOCOL.md) §5): simultaneous moves under
commit-reveal — both peers commit before either reveals — which dissolves the
question rather than answering it, and is what the commit-reveal machinery is
for. Must be confirmed with the opponent, since a peer expecting strict
alternation will deadlock against a peer expecting simultaneity.

---

## Q-3 — `technical_loss` has no row in Appendix F

**Status: RESOLVED** → see [DECISIONS.md](DECISIONS.md) D-3.

`scoring.technical_loss: 0` appears in the Appendix B example config
(PDF p. 129); the value 0/0 appears in Chapter 3's scoring table (PDF p. 38) and
in rule E-48 (PDF p. 149, "technical loss 0/0"). But Appendix F table 17
(PDF p. 154) tabulates only five scoring parameters and **does not include
`technical_loss`**.

So the single binding source for numeric values does not bind this one.

**Resolution:** carry `technical_loss: 0` in the shared config, sourced from
Ch. 3 table 2 and E-48, and flag in the report that it is not an Appendix F
parameter and therefore has no MINIMUM/FIXED/NEGOTIABLE status. Treated as
NEGOTIABLE-with-default-0 in the validator. Low risk: both sources agree on 0,
and 0 for both sides is the whole point of the rule.

---

## Q-4 — What exactly goes into the commit hash

**Status: RESOLVED** → see [DECISIONS.md](DECISIONS.md) D-4. **Also NEGOTIATE.**

Three different accounts appear in the PDF:

1. Ch. 5 formula (PDF p. 50): `H = SHA256(State ‖ Move ‖ Intent ‖ Nonce)` — four
   fields.
2. Ch. 5 narrative, same page and PDF p. 51: concatenation is done by canonical
   JSON serialisation with sorted keys and fixed separators, and *"the record
   actually sealed is richer than the four fields here, and also includes the
   verbal hint, the intent classification, the step number and the role"* — the
   sample code comment adds `sub_game`.
3. Ch. 7 replay sketch (PDF p. 74): `SHA256(f"{nonce}|{move}")` — two fields —
   annotated by the PDF itself as *"the sketch simplifies the input for
   illustration; in practice the signature covers the full step components"*.

Account 3 is self-declared illustrative. Accounts 1 and 2 differ, with 2 being
the explicit description of practice.

**Resolution:** implement the richer record with canonical JSON serialisation
(the schema in [PROTOCOL.md](PROTOCOL.md) §6.1). This satisfies E-17 (SHA-256
commit-reveal) and E-18 regardless of field set, and honours the explicit
"byte-identical input" requirement.

**Must be negotiated:** both peers must hash the *same* schema or every audit
fails. The sealed-record schema is therefore included in the pre-match
agreement and its hash exchanged at handshake.

---

## Q-5 — Three different timeout values, unclear which governs a turn

**Status: NEGOTIATE.**

| Value | Source | Scope stated |
|---|---|---|
| `response_timeout_sec = 30` | Appendix F table 19 row 6 (PDF p. 155), NEGOTIABLE | "timeout for each network request" |
| `watchdog_timeout_sec = 60` | Appendix F table 19 row 7 (PDF p. 155), NEGOTIABLE | "freeze time until Watchdog intervention" |
| `turn_timeout_seconds = 180` | Private TOML skeleton (PDF p. 131) | not stated |
| `timeout_sec = 180` | Ch. 8 watchdog sample code (PDF p. 83) | sample default |

The Appendix F pair is coherent (a request deadline shorter than the process
freeze threshold). The 180s values sit in a private file and in sample code, and
their relationship to the Appendix F pair is never explained. A private value
also cannot weaken a signed condition (PDF p. 132).

**Our reading:** `response_timeout_sec` governs each MCP request;
`watchdog_timeout_sec` governs the process-freeze detector;
`turn_timeout_seconds` is a private, softer budget for the peer's own
end-to-end turn processing (including LLM thinking, itself capped by
`step_deadline_seconds = 30`). Only the first two are on the wire and agreed.
Confirm with the opponent that neither side expects a 180s response deadline.

---

## Q-6 — Grid size: 7×7 or 10×10?

**Status: RESOLVED**, non-issue, recorded to prevent re-litigation.

`[grid_size]` = 7, status **MINIMUM** (Appendix F table 13, PDF p. 152).
Chapter 3 (PDF pp. 34–35) uses 7×7 as the default throughout and contrasts it
with earlier 5×5 versions. But the book's abstract (PDF p. 1) says 10×10, and
Chapter 6's belief-map text and figure 8 (PDF pp. 63–64) show a 10×10 grid
labelled `[grid_size]`.

Not a contradiction in binding terms: MINIMUM 7 means 7 is the floor and 10 is a
legal agreed value. The figures are `EXAMPLE`. **We default to 7** and read the
value from config.

---

## Q-7 — Gmail `mode = "draft"` versus the obligation to send

**Status: RESOLVED** → see [DECISIONS.md](DECISIONS.md) D-5. **Also ESCALATE
(low priority).**

The private TOML skeleton (PDF p. 131) has `[email] mode = "draft"`, and
Appendix D says the reference repo sends *"a JSON report sent as a Gmail
draft"* (PDF p. 139). But E-32 requires reporting results **automatically via
the Gmail interface**, E-51 requires sending the reports **to** the lecturer
address, and Ch. 9 (PDF p. 94) states each team must itself **send** the report,
with non-receipt costing that side its points.

A draft is not received by the lecturer.

**Resolution:** `mode` defaults to `send` for any counting league match. `draft`
is retained as a development/testing convenience only, and the reporting module
refuses to run in `draft` mode when the match is flagged as counting.

**Escalate if convenient:** worth a one-line confirmation from the lecturer that
drafts are not accepted, but the rule text is clear enough to act on.

---

## Q-8 — "MINIMUM" semantics for rate-limiter parameters

**Status: NEGOTIATE / ESCALATE (low priority).**

Appendix F p. 155 defines MINIMUM as: negotiable *only in the direction that
makes the game harder (usually increasing the value)*, never an easement below
the tabulated value.

For most parameters that is unambiguous — a larger grid or more required
survival steps is harder. For table 19 rows 1–5 the mapping inverts:
`requests_per_minute = 30` MINIMUM would mean 30 is the *floor*, so raising it
to 60 is "allowed" — but a higher permitted request rate is a **looser** safety
limit, not a harder one, and the whole purpose of E-28/E-29 is to avoid a 429
account block.

**Our reading:** treat 30/2/5/3/100 as the **configured defaults**, and treat
the *protective* direction as the safe one: never send faster than
`requests_per_minute`, never fewer than `retry_backoff_sec` seconds between
retries, never fewer than `max_retries` attempts, never a queue shallower than
`queue_depth`. In practice these are per-peer protective settings that the
opponent does not rely on, so negotiation pressure here is minimal.

---

## Q-9 — Capture resolution under simultaneous movement

**Status: NEGOTIATE.**

Given simultaneous moves (Q-2), edge cases the PDF does not address:

- The cop moves onto the cell the thief just vacated — capture, or miss?
- The cop and thief swap cells (pass through each other) — capture, or miss?
- Both conditions for capture and for reaching `survival_threshold` complete on
  the same turn — which wins?

Chapter 3 defines capture as *"the cop lands on the thief's cell"* (PDF p. 38),
which reads naturally as *post-move positions coincide*.

**Our reading:** evaluate capture on **post-move positions only**. A swap is not
a capture; landing on a vacated cell is not a capture. If capture and survival
threshold coincide, capture takes precedence (the cop's claim is evaluated
before the step counter reaches the threshold). Must be agreed explicitly, since
it materially changes outcomes.

---

## Q-10 — Axis orientation: text says down, figure shows up

**Status: RESOLVED**, low severity.

Chapter 3 (PDF p. 34) states the default origin is the top-left corner *"(the
vertical axis grows downward)"*. Figure 3 (PDF p. 36) draws the 7×7 arena with
row 0 at the **bottom** and row 6 at the top. Additionally, Chapter 6's
Manhattan worked example (PDF p. 64) places the cop at (2,2), and calls (3,2)
"north" — which with a downward-growing vertical axis would be *south*.

**Resolution:** diagrams and worked examples are `EXAMPLE` and non-binding
(PDF p. 4). Follow the Chapter 3 **text**: origin top-left, vertical axis grows
downward, cells addressed `(row, col)`. `N` decreases row. Since
`axis_origin_corner` and `axis_start_index` are NEGOTIABLE but must be
**identical** on both sides, this is settled explicitly in the shared config, so
the ambiguity has no runtime consequence once agreed.

Note also that Ch. 3 uses `(row, col)` while the belief-map figure (PDF p. 64)
labels axes `x (column)` and `y (row)`. We use `(row, col)` throughout, per the
Chapter 3 text.

---

## Q-11 — Is a Live GUI mandatory in its own right?

**Status: RESOLVED**, treated as mandatory.

Appendix E has no rule "you must build a live GUI". E-8 and E-9 constrain *what
the live interface may display*, presupposing one exists. E-20 makes only the
**replay viewer** explicitly mandatory.

However: Chapter 9's mandatory README contents (PDF p. 97) list screenshots from
the Live GUI as *"an absolute obligation"*; Appendix C's submission checklist
(PDF p. 136) requires "screenshots of the belief map (GUI)" as *attached*; and
Chapter 11's final checklist (PDF p. 113) requires the Live GUI and Replay App
to display the game in real time and in replay.

**Resolution:** a Live GUI is mandatory in effect, via the submission
requirements. Build it. Its scope is nonetheless minimal: belief heatmap + turn
banner is exactly what the PDF describes.

---

## Q-12 — Step-0 signing key

**Status: ESCALATE.**

Ch. 5 (PDF p. 56) says the step-zero specification *"is packed into a JSON
string and cryptographically signed using **a pre-supplied key**, so it cannot be
forged after the fact."*

The PDF never says who supplies this key, where it comes from, what algorithm it
uses, or how the counterpart verifies it. No Appendix F parameter and no
Appendix A instruction covers it.

**Cannot be resolved from the document.** Options: (a) the lecturer distributes
a key out of band; (b) each team generates a keypair and exchanges public keys
at handshake; (c) "signed" loosely means SHA-256 hashed and committed, in line
with the rest of the project's mechanisms.

**Interim position:** implement (c) — canonical JSON + SHA-256, exchanged and
locked at handshake — since it satisfies "cannot be forged after the fact"
against the log, uses machinery the project already mandates, and requires no
external secret. **Do not fabricate a key or key-distribution scheme.** Ask the
lecturer before the first counting match; if a key is in fact supplied, swapping
the hash for a signature is a contained change behind the crypto module's
interface.

---

## Q-13 — Does the lecturer's address need the config file per match, by email or by repo?

**Status: RESOLVED**, both.

Appendix F §2 (PDF p. 156) requires: each match's config file **attached to the
GitHub repository**, and for each match **an email to the lecturer containing
the commit number** used. Ch. 9 requires the four JSON artefacts, of which
`[config_file]` is one, and `[result_file]` is the one emailed.

**Resolution:** commit all four artefacts per match under `matches/<game_id>/`,
and email `[result_file]` (which carries the commit hash per sub-game, E-53) to
`[agent_reporting_address]`. This satisfies both obligations without inventing a
separate email.

---

## Q-14 — `min_games_to_pass` = 2 matches, but E-31 says "matches against different groups"

**Status: RESOLVED**, non-issue, recorded for clarity.

E-31 (PDF p. 147) and Ch. 9 (PDF p. 86) require correct operation of at least
`[min_games_to_pass]` **against different groups**; Appendix C's checklist
(PDF p. 136) says "at least two matches against different groups: 2 and above".
Appendix F sets `min_games_to_pass = 2` FIXED, and `max_games_per_team = 10`
FIXED.

Combined with E-52 (only one counting match per opponent), this means: **at
least 2 distinct opponents, at most 10 distinct opponents.** No contradiction.
