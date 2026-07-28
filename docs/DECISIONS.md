# DECISIONS

Architecture and interpretation decisions, with the reasoning that produced
them. Decisions that resolve a contradiction in the PDF cross-reference
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) and **must appear in the final `README.md`
academic report**, per the academic-freedom clause (PDF p. 5).

Format: what was decided, why, what it costs, and what would reverse it.

---

## D-1 — Source priority is fixed and mechanical

**Decision.** When sources conflict, resolve in this order:

1. Appendix F parameter tables (numeric values) — PDF pp. 151–159
2. Explicit mandatory rules (Appendix E, and rule boxes in the chapters)
3. Recommendations
4. Illustrative examples, diagrams and sample code — **never** a source of
   requirements

**Why.** PDF p. 4 states the founding principle: a rule is not binding unless
explicitly written as a rule, and all illustrations, examples, code excerpts and
scenarios are a mode of demonstration. PDF p. 5 states that Appendix F remains
the single binding source for quantitative values even under contradiction.

**Cost.** Some intuitively-appealing details in the book's figures are
discarded. Accepted deliberately.

---

## D-2 — `num_games` = 6, not 1

**Decision.** The shipped shared config carries `num_games: 6`. No config used
in a counting league match may carry any other value.

**Why.** Appendix F table 18 sets it to 6 with status FIXED; the Appendix B
example file ships 1. D-1 rule 1 applies. Resolves
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-1.

**Cost.** A demo run is six sub-games long rather than one. Mitigated by a local
`--sub-games N` development override that is refused when the match is flagged
as counting.

**Reversal condition.** The lecturer stating that 1 is intended for league play.

---

## D-3 — `technical_loss: 0` is carried but marked as non-Appendix-F

**Decision.** Ship `scoring.technical_loss: 0` in the shared config; the
validator treats it as NEGOTIABLE with default 0 rather than FIXED.

**Why.** It appears in the Appendix B config example, Ch. 3's scoring table and
E-48, but has no row in Appendix F table 17 — so the binding numeric source does
not bind it. Asserting FIXED status would be inventing a requirement. Resolves
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-3.

**Cost.** None practically; all sources agree on 0.

---

## D-4 — Commit hash covers the rich record, canonically serialised

**Decision.** `H_commit = SHA256(canonical_json(record))` where the record is
`{game_id, sub_game, step, role, state, move, hint, intent, nonce}`,
serialised with `sort_keys=True, separators=(",", ":")`, UTF-8. The schema is
agreed with the opponent before the match and its hash exchanged at handshake.

**Why.** Ch. 5 gives a four-field formula but states in the same passage that
the record actually sealed is richer (hint, intent classification, step, role)
and that canonical JSON serialisation is used so both peers hash byte-identical
input. Ch. 7's two-field sketch is self-declared as simplified. The richer record
also binds more: sealing the hint means a peer cannot swap the hint after
committing to it. Resolves [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-4.

**Cost.** The schema must be negotiated, since a mismatch makes every audit fail.
Accepted — this is inherent to a judge-free design and is why the config-hash
exchange exists.

---

## D-5 — Gmail `mode` defaults to `send`, not `draft`

**Decision.** Default `send`. The reporting module refuses `draft` when the
match is flagged as counting.

**Why.** The private TOML skeleton shows `mode = "draft"` and the reference repo
sends drafts, but E-32 requires automatic reporting via Gmail, E-51 requires
sending to the lecturer address, and Ch. 9 states each team must itself send the
report, with non-receipt costing that side its points. A draft never reaches the
lecturer. Resolves [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-7.

**Cost.** Testing must use a throwaway recipient rather than drafts. Acceptable.

---

## D-6 — Simultaneous moves under commit-reveal, not strict alternation

**Decision.** A full turn is one step by each peer, executed simultaneously:
both commit, both acknowledge, both reveal. `step` increments once per full
turn. Scent decay applies once per full turn.

**Why.** The PDF never specifies who moves first, but fixes that decay happens
after *both* have moved — so turns are paired. Commit-reveal exists precisely to
let two mutually distrustful parties act simultaneously without either reacting
to the other. Choosing simultaneity dissolves the unspecified question instead of
resolving it arbitrarily. Addresses [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-2.

**Cost.** Must be agreed with the opponent; a peer expecting alternation will
deadlock. Raised explicitly in negotiation.

---

## D-7 — Capture evaluated on post-move positions only

**Decision.** Capture is true when post-move positions coincide. A cell swap is
not a capture. Moving onto a just-vacated cell is not a capture. If capture and
the survival threshold complete in the same turn, capture wins.

**Why.** Ch. 3 defines capture as the cop *landing on* the thief's cell, which
reads as post-move coincidence. The alternatives are not supported by any text.
Addresses [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-9.

**Cost.** Materially affects outcomes, so it must be agreed explicitly rather
than assumed.

---

## D-8 — Step-0 uses SHA-256 commitment, not a signature, pending clarification

**Decision.** Implement the step-zero declaration as canonical JSON + SHA-256,
exchanged and locked at handshake. Do **not** invent a key-distribution scheme.

**Why.** Ch. 5 refers to signing "with a pre-supplied key" but the PDF never
says who supplies it, what algorithm, or how it is verified. Fabricating one
would be inventing a requirement. A SHA-256 commitment satisfies the stated goal
("cannot be forged after the fact") using machinery the project already
mandates. Addresses [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-12 — which remains
**ESCALATE**: ask the lecturer before the first counting match.

**Cost.** If a real key is supplied later, this changes — but only behind the
crypto module's interface, so the blast radius is one module.

---

## D-9 — Local truth enforced structurally, not by convention

**Decision.** The live-state object has **no attribute** for the opponent's
position — not `None`, not `Optional`. The GUI is constructed with handles to
the local-truth and belief modules only, never to the network layer's raw data.
The replay verifier is the only omniscient component and imports nothing from
the live path.

**Why.** E-8 and E-9 carry the heaviest sanctions in the document
(disqualification of the project for an illegal advantage). A convention that
"we just won't display it" is not testable; an absent attribute is — a leak
becomes an `AttributeError` in a unit test. Cheap to do, and it converts the
highest-consequence rule into a mechanically verified one.

**Cost.** Slightly more plumbing when the replay verifier needs both sides'
data. Contained: the verifier reads logs from disk after the match.

---

## D-10 — Configuration is the only entry point for numeric constants

**Decision.** No numeric value from Appendix F appears as a literal in game
logic. All are read from a typed config object. A validator rejects any config
that lowers a MINIMUM or alters a FIXED value, and runs at load time on both
peers.

**Why.** Appendix F §2 makes defining all values in the config mandatory, and
E-11/E-12 make identity and non-lowering mandatory. Centralising also makes the
byte-identity requirement achievable, and makes "did we use the right value"
a single test rather than a grep.

**Cost.** A config object must be threaded through the domain layer. Cheap and
conventional.

---

## D-11 — Tkinter for both GUI and replay viewer

**Decision.** Tkinter for the Live GUI and the replay viewer.

**Why.** Standard library, zero install, cross-platform, sufficient for a
heatmap grid, a turn banner and step controls — which is the entire mandated
scope. The PDF names Tkinter and PyQt as examples only. Matches the brief's "a
simple GUI technology with minimal setup" and the priority ordering that puts
visual polish last.

**Cost.** Not pretty. Explicitly acceptable given the stated priorities.

---

## D-12 — Pure verifier separated from the viewer

**Decision.** `replay/verifier.py` is a pure function over a log file returning
`Verified OK` / `TAMPERED` with the offending entry. `replay/viewer.py` is the
Tkinter shell around it.

**Why.** E-19 and E-20 are the most testable rules in the document, and a
headless pure function lets pytest assert both the clean case and deliberately
tampered logs without a display. Also lets the same verifier run inside the
mutual audit (E-36) at end of match, so there is one implementation of hash
checking rather than two that can drift.

**Cost.** None.

---

## D-13 — `template` is the default verbal provider

**Decision.** `[trash_talk] provider = "template"`. Zero tokens, no network, no
LLM dependency in the default path.

**Why.** Appendix F table 21 names `template` as the default and states the
entire series can be played at zero tokens in template or ollama mode, moving
the competition onto the movement algorithm. The brief forbids paid LLM APIs and
prefers deterministic templates over optional AI complexity. It also removes an
entire class of nondeterminism from the test suite.

**Cost.** Less colourful bluffing. The provider interface stays swappable, so
adding `ollama` later is a config change.

---

## D-14 — Heuristic brain (Bayes belief + Manhattan) is the MVP strategy; no RL

**Decision.** Ship the Bayesian belief map + Manhattan distance policy. No
reinforcement learning in the MVP.

**Why.** The PDF states plainly that the course did not teach RL, that a fully
strong agent can be built with heuristics alone, and that RL is one optional
tool among three equal-standing routes — with pure heuristics being the
reference implementation's own default. Strategy quality ranks sixth in the
stated priorities, below compliance, working system, verification and
simplicity.

**Cost.** Possibly weaker play against a tuned opponent. Revisit only after every
mandatory requirement is complete and verified.

---

## D-15 — JSONL for the live audit log, sealed JSON for the artefact

**Decision.** Append-only JSON Lines during the match; sealed into the canonical
`log_<game_id>_g<NN>.json` at end of sub-game.

**Why.** E-7 requires the watchdog to extract data in a controlled way after a
crash — a partially-written JSON array is unreadable, a partially-written JSONL
file is fully readable up to the last complete line. The mandated artefact
filename is `.json`, so the seal step converts. Also matches the brief's
"JSON Lines audit logs".

**Cost.** One conversion step. Trivial, and it is the natural place to compute
the end-of-sub-game summary anyway.

---

## D-16 — Two repositories are produced by splitting at submission time

**Decision.** Develop in one repository; produce the two mandated repositories
(cop, thief) at submission, each carrying its role's config tree, its own
`README.md` with the cross-link, and the shared source.

**Why.** E-49 requires two separate GitHub repositories with cross-linked
READMEs. E-1/E-2 require two separate *processes* and separate config
directories — which is a runtime property, satisfied regardless of repository
layout. Developing twice in parallel would duplicate every change and is the
likeliest source of the two sides drifting apart, which is itself a compliance
risk.

**Cost.** A deliberate split step before submission, which must not be
forgotten. Tracked as a mandatory task in [../TASKS.md](../TASKS.md).

**Note.** The user's brief says no GitHub repository is to be created yet. This
decision records the intended end state only.

---

## D-18 — Config paths reconcile Appendix B filenames with Chapter 2 separation

**Decision.** `config/police/game.json`, `config/police/game.toml`,
`config/thief/game.json`, `config/thief/game.toml`.

**Why.** Two PDF passages have to be satisfied at once. Appendix B names the
files `config/game.json` and `config/game.toml` with no role sub-directory
(PDF pp. 126, 130). Chapter 2 requires the two roles to run under **separate
configuration directories**, offering `/config/thief` vs `/config/police` as an
example (PDF p. 31, "for example"). The layout above keeps Appendix B's
filenames and Chapter 2's mandatory separation.

**Cost.** The path is not literally the PDF's. Documented here and in
[PARAMETERS.md](PARAMETERS.md) §2 so it is never mistaken for a quotation.

**Reversal condition.** An opponent or the lecturer expecting the flat
Appendix B path. Trivial to change — it is one constant in the loader.

*Added in the second-pass audit.*

---

## D-19 — The log record schema is defined, and the scent field is not stored

**Decision.** Define an explicit log record schema
([PROTOCOL.md](PROTOCOL.md) §11) carrying commitments, moves, hints, **LLM
discussion fields**, nonce and hash. Do **not** store the rendered scent field
or either peer's position history as data; the verifier recomputes both from the
move sequence plus the config.

**Why.** PDF p. 94 enumerates the mandatory log contents, and the LLM discussion
fields are easy to overlook — the log is not a move list. The first-pass
documentation defined the wire protocol but never the log format, even though
the log is what the replay verifier and the mutual audit actually consume; that
was a real gap.

Not storing the scent field is the more interesting half. A live peer writes
this file, so any global-truth field inside it would put global truth in the
live path — exactly what E-9 forbids. Recomputation from moves costs nothing and
keeps the boundary structural rather than procedural.

**Cost.** The verifier must implement the physics to replay. It has to anyway,
in order to check capture claims.

*Added in the second-pass audit.*

---

## D-20 — Administrative lead-time work starts early, in parallel

**Decision.** Google Cloud / OAuth account provisioning and opponent-team
coordination move out of their code phases and begin in parallel from Phase 0,
as `[P]` tasks.

**Why.** Both have latency that is not ours to control. OAuth consent-screen
configuration requires adding test users and can stall; finding opponent teams
willing to negotiate a shared config and play a counting match depends on other
people's schedules, and E-31 requires at least two such matches against
different groups. Leaving either until its code phase risks the plan being
blocked by something no amount of engineering fixes.

This does **not** mean writing reporting code early — Phase 9 still owns that,
per the PDF's own ordering. It means the *account* and the *relationships* exist
before the code needs them.

**Cost.** None; these are administrative tasks with no code dependency.

*Added in the second-pass audit.*

---

## D-17 — One test per mandatory rule, named by rule ID

**Decision.** Test functions carry the rule ID, e.g.
`test_e13_rejects_diagonal_move`. [ACCEPTANCE_TESTS.md](ACCEPTANCE_TESTS.md)
maps every rule to its test or deterministic manual procedure.

**Why.** The brief requires every mandatory behaviour to have a test or
deterministic verification procedure. Naming by rule ID makes coverage
auditable by grep, and makes the compliance argument in the README concrete
rather than assertive.

**Cost.** Some tests are trivial. Worth it — the audit trail is itself a
deliverable.
