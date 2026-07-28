# COMPLIANCE AUDIT

Second-pass audit of the documentation set against `police_thief_p2p.pdf`.

**Scope.** This audits whether each PDF requirement is *correctly captured and
assigned* in the documentation. It does **not** audit implementation — no
application code exists yet, so no requirement can be marked as implemented.
"COVERED" here means *documented, classified, parameterised where applicable,
and mapped to a verification*.

**Status key.**

| Status | Meaning |
|---|---|
| `COVERED` | Captured in the docs with correct classification, PDF page, sanction, and a mapped verification in `ACCEPTANCE_TESTS.md`. |
| `MISSING` | Present in the PDF, absent from the docs. **Zero entries — all gaps found in this pass were corrected before publishing.** |
| `AMBIGUOUS` | The PDF itself is unclear or self-contradictory. Logged in `OPEN_QUESTIONS.md`; a reading chosen and recorded in `DECISIONS.md` where possible. |
| `N/A` | Not applicable at this stage, or explicitly non-binding. |

**Audit date:** 2026-07-28. **Audited against:** book version 3.0.0.

---

## 1. Appendix E — all 55 mandatory rules (PDF pp. 142–150)

### Table 7 — Network architecture, decentralisation, local epistemology

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-1 two separate processes | `COVERED` | REQ §1, ARCH §5, CLAUDE §3 | AT §1 (AUTO + MANUAL) |
| E-2 no shared memory/variables | `COVERED` | REQ §1, ARCH §5, DEC D-9 | AT §1 (AUTO) |
| E-3 orchestrator = single entry point | `COVERED` | REQ §1, ARCH §3, §2 | AT §1 (AUTO) |
| E-4 proper state machine | `COVERED` | REQ §1, ARCH §2, PROTO §7.3 | AT §1 (AUTO) |
| E-5 reject illegal transitions | `COVERED` | REQ §1, PROTO §7.3 | AT §1 (AUTO) |
| E-6 deadline tracking | `COVERED` | REQ §1, PROTO §7.1, PARAM table 19 | AT §1 (AUTO, fake clock) |
| E-7 watchdog | `COVERED` | REQ §1, ARCH §4, DEC D-15 | AT §1 (AUTO) |
| E-8 live GUI shows local truth only | `COVERED` | REQ §1, ARCH §3.6, DEC D-9 | AT §1 (AUTO) |
| E-9 never show objective board state | `COVERED` | REQ §1, ARCH §3.1, DEC D-9 | AT §1 (AUTO, structural) |
| E-10 tunnelling tool | `COVERED` | REQ §1, TASKS Phase 8 | AT §1 (MANUAL, off-host) |

### Table 8 — Spatial mechanics, physics, board constraints

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-11 byte-identical config both sides | `COVERED` | REQ §2, PROTO §3, PARAM §2 | AT §2 (AUTO) |
| E-12 raise minimums only, never lower | `COVERED` | REQ §2, PARAM §1, DEC D-10 | AT §2 (AUTO, parametrised) |
| E-13 orthogonal only | `COVERED` | REQ §2, PARAM table 15 | AT §2 (AUTO) |
| E-14 no diagonals | `COVERED` | REQ §2 | AT §2 (AUTO) |
| E-15 declare every barrier openly | `COVERED` | REQ §2, PROTO §6.4 | AT §2 (AUTO) |
| E-16 never lie about barrier location | `COVERED` | REQ §2, PROTO §6.1 (sealed) | AT §2 (AUTO) |

### Table 9 — Cryptography, log integrity, zero-knowledge

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-17 commit-reveal over SHA-256 | `COVERED` | REQ §3, PROTO §6, DEC D-4 | AT §3 (AUTO) |
| E-18 nonce secret until end of match | `COVERED` | REQ §3, PROTO §6.4, §6.6 | AT §3 (AUTO) |
| E-19 technical loss on hash mismatch | `COVERED` | REQ §3, PROTO §6.6, ARCH §3.7 | AT §3 (AUTO, parametrised tamper) |
| E-20 replay viewer application | `COVERED` | REQ §3, ARCH §3.7, DEC D-12 | AT §3 (AUTO + MANUAL screenshot) |
| E-21 truthful capture declaration | `COVERED` | REQ §3, PROTO §6.5 | AT §3 (AUTO) |
| E-22 no false capture claim | `COVERED` | REQ §3, PROTO §6.5 | AT §3 (AUTO) |
| E-23 lock scent model pre-match | `COVERED` | REQ §3, §4, PROTO §3 | AT §3 (AUTO, incl. worked example) |
| E-24 cryptographic hardware declaration | `COVERED` | REQ §3, PROTO §4 | AT §3 (AUTO) |

### Table 10 — Strategy, language, public network

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-25 LLM must not decide the move | `COVERED` — correctly classified **RECOMMENDED** | REQ §5, ARCH §8, CLAUDE §3 | AT §5 (AUTO) |
| E-26 free natural language only | `COVERED` | REQ §5, PROTO §8 | AT §5 (AUTO) |
| E-27 no numeric position protocols | `COVERED` | REQ §5, PROTO §8 | AT §5 (AUTO, parametrised) |
| E-28 token-bucket rate limiter | `COVERED` | REQ §5, PARAM table 19 | AT §5 (AUTO, fake clock) |
| E-29 DOS detector | `COVERED` | REQ §5, ARCH §3.8 | AT §5 (AUTO) |
| E-30 send-only Gmail permission | `COVERED` | REQ §5, §8 | AT §5 (AUTO, source scan) |

### Table 11 — League fairness, administration, competition purity

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-31 minimum matches vs different groups | `COVERED` | REQ §6, PARAM table 18 | AT §6 (PROCESS + AUTO) |
| E-32 automatic Gmail reporting | `COVERED` | REQ §6, ARCH §3.8 | AT §6 (AUTO + MANUAL) |
| E-33 report as standard JSON | `COVERED` | REQ §6 | AT §6 (AUTO) |
| E-34 never free text; attachment only | `COVERED` | REQ §6 | AT §6 (AUTO) |
| E-35 agree result; each sends separately | `COVERED` | REQ §6, PROTO §6.7, §10 | AT §6 (AUTO) |
| E-36 mutual log audit every match | `COVERED` | REQ §6, ARCH §3.5, PROTO §6.6 | AT §6 (AUTO, ordering) |
| E-37 declare counted-match count | `COVERED` | REQ §6, PROTO §3 | AT §6 (AUTO) |
| E-38 no false game-count declaration | `COVERED` | REQ §6 | AT §6 (AUTO, derived not hand-set) |
| E-39 never push secrets | `COVERED` | REQ §6, §7.6, `.gitignore` | AT §6 (AUTO + full-history PROCESS) |
| E-40 secrets in `.gitignore` | `COVERED` | REQ §6, `.gitignore` shipped | AT §6 (AUTO, `git check-ignore`) |
| E-41 documented Git tag | `COVERED` | REQ §7.1 | AT §6 (PROCESS) |
| E-42 comprehensive academic report | `COVERED` | REQ §7.3, README | AT §7 (PROCESS checklist) |
| E-43 Moodle form, fields unchanged | `COVERED` | REQ §7.5 | AT §6 (MANUAL) |
| E-44 each member submits separately | `COVERED` | REQ §7.5 | AT §6 (PROCESS) |
| E-45 unique 8-char group code | `COVERED` | REQ §7.5, PARAM §15 | AT §6 (AUTO) |

### Table 12 — Additions found when cross-checking the book

| Rule | Status | Where documented | Verification |
|---|---|---|---|
| E-46 barrier on thief's cell = capture | `COVERED` | REQ §2 (rule box) | AT §2 (AUTO) |
| E-47 thief with no legal move = captured | `COVERED` | REQ §2 | AT §2 (AUTO, incl. corner case) |
| E-48 score every scenario per tables | `COVERED` | REQ §2, PARAM table 17 | AT §2 (AUTO, parametrised) |
| E-49 two repos, cross-link, 2+4 links | `COVERED` | REQ §7.1, DEC D-16 | AT §6 (AUTO + PROCESS) |
| E-50 README, /config, PRD, PLAN, TODO | `COVERED` | REQ §7.2, ARCH §9 | AT §6 (AUTO) |
| E-51 send to `[agent_reporting_address]` | `COVERED` | REQ §6, PARAM table 20 | AT §6 (AUTO) |
| E-52 one counting match per opponent | `COVERED` | REQ §6 | AT §6 (AUTO) |
| E-53 commit hash in step-zero | `COVERED` | REQ §3, PROTO §4 | AT §3 (AUTO) |
| E-54 report total tokens consumed | `COVERED` | REQ §6, PROTO §6.7 | AT §6 (AUTO) |
| E-55 self-grade for code quality only | `COVERED` | REQ §6, §7.5 | AT §6 (PROCESS) |

**Appendix E result: 55/55 COVERED. 0 MISSING.**

---

## 2. Appendix F — mandatory parameters (PDF pp. 151–159)

| Table | Parameters | Status | Notes |
|---|---|---|---|
| 13 Board, axes, start positions | 6 | `COVERED` | All six in PARAM §3 with status and JSON key |
| 14 Arena and verbal hints | 2 | `COVERED` | PARAM §4 |
| 15 Movement and barriers | 4 | `COVERED` | PARAM §5 |
| 16 Dynamic pheromones | 3 | `COVERED` | PARAM §6; all FIXED |
| 17 Scoring | 5 | `COVERED` | PARAM §7; `technical_loss` correctly noted as **not** in this table |
| 18 Network and league | 5 | `COVERED` | PARAM §8; `num_games` conflict flagged |
| 19 Network, rate limiter, gatekeeper | 7 | `COVERED` | PARAM §9 |
| 20 Files, repo, addresses | 7 | `COVERED` | PARAM §10; reference table, not negotiable |
| 21 LLM modes | 4 modes | `COVERED` | PARAM §11; private per-peer choice |
| 22 Strategy module selection | 2 keys | `COVERED` | PARAM §12; private per-peer choice |
| §1 Status definitions | 3 statuses | `COVERED` | PARAM §1 — the semantics of MINIMUM/FIXED/NEGOTIABLE |
| §2 Mandatory instructions | 6 obligations | `COVERED` | PARAM §13 |

**Total parameters: 32 tabulated values + 3 status definitions + 6 accompanying
obligations. All COVERED.**

**Critical semantic point verified.** The "example value" column in Appendix F is
**not** an `EXAMPLE` in the non-binding sense. PDF pp. 151 and 155 define those
values as the binding minimum / fixed value / default. PARAM §1 states this
explicitly and warns against the misreading. This is the single most consequential
thing to get right in the parameter extraction, and it is correct.

### Parameter-level findings

| Finding | Status | Resolution |
|---|---|---|
| `num_games` = 6 FIXED (App. F) vs 1 (App. B example config) | `AMBIGUOUS` | OQ Q-1 → DEC D-2: **6 prevails** |
| `technical_loss` absent from App. F table 17 | `AMBIGUOUS` | OQ Q-3 → DEC D-3: carried at 0, marked non-Appendix-F |
| `grid_size` 7 (App. F) vs 10×10 in abstract and figure 8 | `AMBIGUOUS`, low | OQ Q-6: MINIMUM 7 is the floor; figures are EXAMPLE |
| `turn_timeout_seconds` 180 (TOML) vs `response_timeout_sec` 30 / `watchdog_timeout_sec` 60 (App. F) | `AMBIGUOUS` | OQ Q-5: App. F pair governs the wire; 180 is a private budget |
| MINIMUM direction inverts for rate-limiter parameters | `AMBIGUOUS`, low | OQ Q-8: treat tabulated values as protective defaults |
| `[email] mode = "draft"` vs obligation to send | `AMBIGUOUS` | OQ Q-7 → DEC D-5: default `send`; `draft` refused for counting matches |

---

## 3. The seven recommended development priorities (Ch. 10, PDF pp. 99–106)

| Item | Status | Notes |
|---|---|---|
| Chapter 10 classified as **entirely a recommendation** | `COVERED` | REQ §9 states this explicitly, citing PDF p. 99. Important: treating it as mandatory would over-constrain the build. |
| Stage 1 Base Logic | `COVERED` | TASKS Phase 1 |
| Stage 2 Basic MCP Infrastructure | `COVERED` | TASKS Phase 2 |
| Stage 3 Blind Strategy | `COVERED` | TASKS Phase 3 |
| Stage 4 Language and Scent | `COVERED` | TASKS Phase 4 (LLM narrowed to template — documented deviation) |
| Stage 5 Cloud Exposure and Tunnelling | `COVERED` | TASKS Phase 8 (**reordered** — documented deviation with rationale) |
| Stage 6 Security and Cryptography | `COVERED` | TASKS Phase 5 (**reordered**) |
| Stage 7 Reporting and Visualisation Shell | `COVERED` | TASKS Phases 6, 7, 9 (split) |
| Seven PRD files, one per stage | `COVERED` | TASKS Phase 0; `docs/prd/`. Note E-50 makes PRD *existence* mandatory even though the seven-stage split is a recommendation. |
| Milestone checklist (7 binary criteria) | `COVERED` | REQ §9 reproduces all seven; each is a phase exit criterion in TASKS |
| "Do not skip ahead" | `COVERED` | REQ §9; TASKS phase-gating |
| Incremental delivery principle | `COVERED` | REQ §9; TASKS preamble |

**Deviations from the recommended order are permitted** (the chapter is a
recommendation) and are documented with rationale in TASKS Phase 5 and Phase 8:
cryptography before cloud exposure, because crypto is offline-testable and
carries the heaviest sanctions, and because the transport was already proven over
localhost in Phase 2 — which is the PDF's own stated reason for its ordering.

---

## 4. Live GUI restrictions

| Requirement | Status | Notes |
|---|---|---|
| Local truth only (E-8) | `COVERED` | ARCH §3.6, DEC D-9 |
| Never the full objective board state (E-9) | `COVERED` | Enforced structurally, not by convention |
| Belief heatmap, colour intensity = probability | `COVERED` | REQ §1 supporting detail; ARCH §3.6; TASKS Phase 7 |
| Turn banner green `YOUR TURN` / grey `LOCKED` | `COVERED` | ARCH §3.6; input ignored while locked |
| Banner is the visual form of the state machine; prevents a race condition | `COVERED` | ARCH §3.6 |
| Symmetry — both sides run their own GUI showing belief about the *opponent* | `COVERED` | ARCH §3.6, §5 |
| Is a Live GUI mandatory in its own right? | `AMBIGUOUS` → resolved | OQ Q-11: no Appendix E rule mandates building one, but the README contents (PDF p. 97, "absolute obligation"), the Appendix C checklist and the Ch. 11 checklist all require GUI screenshots. **Treated as mandatory in effect.** |
| Tkinter/PyQt as toolkit | `N/A` — `EXAMPLE` | REQ §12; DEC D-11 chooses Tkinter |

---

## 5. Replay verification

| Requirement | Status | Notes |
|---|---|---|
| Build a replay viewer (E-20) — mandatory submission requirement, not optional | `COVERED` | REQ §3; ARCH §3.7; TASKS Phase 6 |
| Load the final log file | `COVERED` | PROTO §10; PARAM table 20 (`log_<game_id>_g<NN>.json`) |
| Step forward and backward with controls | `COVERED` | ARCH §3.7; TASKS Phase 6 |
| Live cryptographic verification at each step | `COVERED` | ARCH §3.7 |
| Green `Verified OK` stamp | `COVERED` | AT §3, §8 |
| Red `TAMPERED` banner; match immediately disqualified, no appeal | `COVERED` | REQ §3; AT §8 step 10 explicitly tests the detector fires |
| The `verify_step` sketch is simplified (PDF's own annotation) | `COVERED` | REQ §3 records this; DEC D-4 uses the full record |
| Screenshot with `Verified OK` is a submission requirement | `COVERED` | REQ §7.3, §7.4; AT §7 |
| Verifier separated from viewer so it is headless-testable | `COVERED` | DEC D-12 |
| One hash-checking implementation shared with the mutual audit | `COVERED` | TASKS Phase 6; prevents drift between two copies |

---

## 6. Commit-reveal

| Requirement | Status | Notes |
|---|---|---|
| SHA-256 based (E-17) | `COVERED` | PROTO §6 |
| Four ordered phases: commit → acknowledge → reveal → final reveal/audit | `COVERED` | PROTO §6; REQ §3 |
| Commit transmits the signature **only**, never content | `COVERED` | PROTO §6.2 |
| Acknowledge locks; prevents retreat; reveal only after both fixed | `COVERED` | PROTO §6.3 |
| Reveal carries move + hint, **nonce still hidden** | `COVERED` | PROTO §6.4; schema *rejects* a nonce field |
| Final reveal of all nonces only at end of match (E-18) | `COVERED` | PROTO §6.6 |
| Nonce cryptographically generated, defeats dictionary attack | `COVERED` | REQ §3; AT §3 asserts `secrets` not `random` |
| Canonical JSON serialisation, sorted keys, fixed separators, byte-identical | `COVERED` | PROTO §6.1; DEC D-4; single shared helper (TASKS Phase 0) |
| Sealed record is richer than the four-field formula | `AMBIGUOUS` → resolved | OQ Q-4 → DEC D-4: implement the rich record; **must be negotiated** with the opponent |
| `State` binds the commitment to a specific position (prevents reuse) | `COVERED` | PROTO §6.1 (hashed, so it binds without leaking) |
| `Intent` flag committed so a peer cannot retroactively claim it meant to lie | `COVERED` | PROTO §6.1, §8 |
| Mutual audit reconstructs and compares (E-36) | `COVERED` | PROTO §6.6; ARCH §3.5 |
| Any mismatch ⇒ technical loss, score 0 (E-19) | `COVERED` | REQ §3; AT §3 |
| Zero-knowledge framing: certainty of commitment, zero knowledge of content | `COVERED` | REQ §3 |

---

## 7. FastMCP P2P symmetry

| Requirement | Status | Notes |
|---|---|---|
| Each agent is simultaneously server **and** client | `COVERED` | ARCH §3.4, §5; PROTO §1 |
| No strong side / weak side; peers fully equivalent | `COVERED` | PROTO §1 |
| MCP is the project requirement and must **not** be replaced | `COVERED` | REQ §12 (A2A/ACP are RECOMMENDED awareness only) |
| Tools exposed via `@mcp.tool` decorator | `COVERED` | PROTO §1 |
| No central referee, no game-state server | `COVERED` | ARCH §1; README |
| Physics enforced by the agents themselves, each in turn | `COVERED` | REQ §2; PROTO §6.4 (receiver enforces legality) |
| Responsibility split: server / client engine / LLM (Ch. 2 table 1) | `COVERED` | ARCH §3 |
| Tunnelling for NAT traversal (E-10); localhost only in early dev | `COVERED` | REQ §1; TASKS Phase 8 |
| Tunnel resilience is part of game resilience | `COVERED` | REQ §1 |
| Same program, two roles | `COVERED` | ARCH §5 with an explicit what-changes/what-doesn't table |
| Minimal, explicit, schema-validated messages | `COVERED` | PROTO §2; eight tools total |
| Turn ordering | `AMBIGUOUS` | OQ Q-2 → DEC D-6: simultaneous under commit-reveal; **must be negotiated** |
| Timeout / duplicate / invalid-sequence behaviour | `COVERED` | PROTO §7 — including that a rejected transition never mutates state |

---

## 8. Local-state restrictions

| Requirement | Status | Notes |
|---|---|---|
| Local truth definition (Ch. 7, PDF p. 70) | `COVERED` | ARCH §3.1 |
| No bird's-eye view | `COVERED` | E-9; DEC D-9 |
| Derives from Dec-POMDP: Ωᵢ is a partial subset of S | `COVERED` | REQ §1 |
| Each peer reads only the **opponent's** scent field, not its own | `COVERED` | ARCH §3.2; AT §4 |
| Scent cannot be forged; only the verbal hint can lie | `COVERED` | REQ §4; AT §4 asserts no API to deposit scent remotely |
| Barriers are legitimately shared knowledge (E-15 openly declared) | `COVERED` | ARCH §3.1 — important, else barrier state looks like a leak |
| Full global state reconstructible only post-match, by the verifier | `COVERED` | ARCH §1, §3.7 |
| Separate config directories per role | `COVERED` | ARCH §5, §7 |
| No shared module holding live state | `COVERED` | E-2; AT §1 (import-graph scan) |

---

## 9. League-game requirements

| Requirement | Status | Notes |
|---|---|---|
| Live academic league, not closed lab conditions | `COVERED` | REQ §6 |
| Play against **different** opponents (E-31) | `COVERED` | AT §6 |
| Diversity incentive `[diversity_reward]` for a new opponent | `COVERED` | REQ §6; PARAM table 18 |
| One counting match per opponent (E-52) | `COVERED` | AT §6 |
| Warm-up matches permitted and recommended, not counted | `COVERED` | REQ §6; TASKS Phase 10 |
| Encounter sealed once result agreed and reported | `COVERED` | REQ §6; PROTO §10 step 6 |
| Game-count declaration at match opening (E-37/E-38) | `COVERED` | PROTO §3 |
| `min_games_to_pass` = 2, `max_games_per_team` = 10 | `COVERED` | PARAM table 18; OQ Q-14 confirms no conflict |
| Match = `num_games` sub-games; terminology משחק vs משחקון | `COVERED` | PARAM §8 — distinguished explicitly, as the two are easily conflated |
| Tie rule: equal cumulative across **all** sub-games ⇒ `tie_score` each | `COVERED` | REQ §6; PROTO §10; AT §6 |
| Computational fairness; normalisation rewards efficiency | `COVERED` | REQ §3, §6 |
| Step-0 hardware declaration feeds fairness scoring | `COVERED` | PROTO §4 |
| Mutual log audit before agreeing result (E-36) | `COVERED` | PROTO §10 ordering |

---

## 10. Gmail reporting

| Requirement | Status | Notes |
|---|---|---|
| Automatic reporting at end of every legal match (E-32) | `COVERED` | ARCH §3.8; TASKS Phase 9 |
| **Each team sends its own** report; one side's silence costs that side its points (E-35) | `COVERED` | REQ §6 (rule box quoted in full) |
| Contradictory reports ⇒ match disqualified, 0 for **both** | `COVERED` | REQ §6 |
| Binding recipient `rmisegal+uoh26finalgame@gmail.com` (E-51) | `COVERED` | PARAM table 20; AT §6 |
| Standard JSON structure (E-33) | `COVERED` | REQ §6 |
| Sent as an **attachment**, never free text (E-34) | `COVERED` | AT §6 |
| Mandatory report fields: both teams' GitHub links, per-sub-game commit hash, total tokens | `COVERED` | REQ §6; PROTO §6.7 |
| Four JSON artefacts and their filename patterns | `COVERED` | REQ §6 table; PARAM table 20 |
| Gatekeeper: Quota Manager → Token Bucket → DOS Detector, fail fast | `COVERED` | REQ §5; ARCH §3.8; AT §5 asserts the order |
| Token-bucket rule `tokens ← min(C, tokens + r·Δt)` | `COVERED` | REQ §5; AT §5 |
| Three distinct meanings of "token" not to be confused | `COVERED` | REQ §5 — flagged explicitly |
| 429 ⇒ back off, do not immediately resend | `COVERED` | REQ §5; AT §5 |
| OAuth five setup steps | `COVERED` | REQ §8 |
| Scope `gmail.send` **only**; never read/modify (E-30) | `COVERED` | REQ §8; AT §5 scans the whole source |
| `credentials.json` + `token.json` secret, both in `.gitignore` | `COVERED` | REQ §8; `.gitignore` shipped in this commit |
| Least-privilege principle | `COVERED` | REQ §8 |
| Built **last**, after the core works | `COVERED` | TASKS Phase 9 |
| `draft` vs `send` | `AMBIGUOUS` → resolved | OQ Q-7 → DEC D-5 |

---

## 11. GitHub submission requirements

| Requirement | Status | Notes |
|---|---|---|
| Submission is a whole development artefact, not a source file | `COVERED` | REQ §7.1 |
| Repos accessible to lecturer: public **or** shared with `rmisegal@gmail.com` | `COVERED` | REQ §7.1; PARAM table 20 |
| **Two** separate repositories, cop and thief (E-49) | `COVERED` | REQ §7.1; DEC D-16 |
| Cross-link mandatory in both READMEs | `COVERED` | REQ §7.1; AT §7 |
| Two links in Moodle, four links in the JSON | `COVERED` | REQ §7.1; AT §6 |
| Development via branches | `COVERED` — `RECOMMENDED` | REQ §7.1 |
| Annotated Git tag `v1.0-submission`, pushed (E-41) | `COVERED` | REQ §7.1; AT §6 |
| Never push secrets, even to a private shared repo (E-39) | `COVERED` | REQ §7.6; AT §6 checks **full history**, not just HEAD |
| A leaked secret is compromised permanently; rotate | `COVERED` | REQ §7.6; `.gitignore` header comment |
| No GitHub repo to be created yet (user instruction) | `N/A` at this stage | CLAUDE §7; DEC D-16 records intended end state only |

---

## 12. Required files, screenshots, reports and repository structure

| Requirement | Status | Notes |
|---|---|---|
| Each repo: `README.md`, `/config`, PRD files, `PLAN`, `TODO` (E-50) | `COVERED` | REQ §7.2; ARCH §9; AT §6; TASKS Phase 0 |
| Markdown PRD folder attached; readable root README | `COVERED` | REQ §7.2 |
| README = academic report with six mandatory components | `COVERED` | REQ §7.3 (all six enumerated); AT §7 checklist |
| Screenshot: Live GUI belief map — "absolute obligation" | `COVERED` | REQ §7.3; AT §7, §8 |
| Screenshot: Replay showing `Verified OK` | `COVERED` | REQ §7.3; AT §7, §8 |
| Learning curves **only if** RL used | `COVERED` — conditional | REQ §7.3 |
| Why screenshots matter (proof of inference + integrity) | `COVERED` | REQ §7.3 |
| Appendix C submission checklist (9 items) | `COVERED` | REQ §7.4 reproduces all nine; AT §7 mirrors them |
| Ch. 11 final pre-submission checklist (8 items) | `COVERED` | REQ §9 milestones + AT §7, §8 |
| Moodle: PDF form unaltered (E-43) | `COVERED` | REQ §7.5 |
| Moodle: separate submission per member (E-44) | `COVERED` | REQ §7.5 |
| Moodle: 8-char group code (E-45) | `COVERED` | REQ §7.5; AT §6 |
| Self-grade for code quality only (E-55) | `COVERED` | REQ §7.5 |
| Per-match config file committed, distinct name (App. F §2) | `COVERED` | PARAM §13; AT §6; `matches/<game_id>/` in ARCH §9 |
| Per-match email with commit number (App. F §2) | `COVERED` | OQ Q-13 resolves how both obligations are met |
| Four success metrics (Ch. 11 table 4) | `COVERED` | REQ §10 |
| Assessed against the course-intro AI-software file | `COVERED` | REQ §7.2, §10 |

---

## 13. Items correctly marked NOT APPLICABLE or non-binding

Recording these matters as much as recording obligations — treating a
recommendation as mandatory wastes effort the priority ordering says should go
elsewhere.

| Item | Status | Basis |
|---|---|---|
| Reinforcement learning / Q-Learning | `N/A` — optional | PDF pp. 59, 61, 67, 115: course did not teach it; one tool among three |
| All of Chapter 10 (seven priorities) | `N/A` — recommendation | PDF p. 99, stated in the chapter's own opening |
| A2A and ACP protocols | `N/A` — recommended awareness | PDF p. 26; MCP must not be replaced |
| `AgentNet` reading | `N/A` — optional reading | PDF p. 60 |
| NotebookLM technique | `N/A` — tip | PDF p. 140 |
| Research/performance-analysis report | `N/A` — "highly recommended" | PDF p. 141; TASKS optional |
| Tkinter/PyQt specifically | `N/A` — EXAMPLE | PDF p. 70 |
| ngrok/Localtonet specifically | `N/A` — EXAMPLE tools | PDF p. 29 |
| State-machine state names | `N/A` — EXAMPLE sample code | PDF pp. 79–80 |
| `/config/thief` vs `/config/police` exact paths | `N/A` — EXAMPLE | PDF p. 31 |
| Example repo as a starting point | `N/A` — **explicitly forbidden** as a base | PDF p. 138 |
| Docker, databases, cloud infra | `N/A` | Never mentioned as requirements anywhere |
| Implementation status of all rules | `N/A` at this stage | No application code exists yet |

---

## 14. Cross-document consistency check

Final pass across REQUIREMENTS, PARAMETERS, ARCHITECTURE, PROTOCOL,
ACCEPTANCE_TESTS and TASKS.

| Check | Result |
|---|---|
| Every Appendix E rule ID appears in REQUIREMENTS **and** ACCEPTANCE_TESTS | ✅ 55/55 both |
| Every Appendix F parameter in PARAMETERS carries value + type + status + owning file | ✅ 32/32 |
| Every parameter referenced in ARCHITECTURE/PROTOCOL exists in PARAMETERS | ✅ no orphan references |
| No numeric literal from Appendix F appears as a hard-coded requirement in ARCHITECTURE or PROTOCOL | ✅ all by code-name or config key |
| Every component in ARCHITECTURE §9 has at least one TASKS phase | ✅ |
| Every TASKS phase has an exit criterion and named tests | ✅ 12 phases |
| Every PROTOCOL tool appears in TASKS Phase 2 or Phase 5 | ✅ 8/8 |
| Every OPEN_QUESTIONS entry is either RESOLVED with a DECISIONS entry, or flagged NEGOTIATE/ESCALATE | ✅ 14 entries: 8 resolved, 5 negotiate, 2 escalate (Q-7 and Q-12; Q-7 also resolved) |
| Every DECISIONS entry that resolves a contradiction cites its OPEN_QUESTIONS ID | ✅ D-2, D-3, D-4, D-5, D-6, D-7, D-8 |
| README documentation table matches the actual files in `docs/` | ✅ 8 documents |
| CLAUDE.md source priority matches DECISIONS D-1 | ✅ |
| CLAUDE.md repository map matches ARCHITECTURE §9 | ✅ |
| `.gitignore` covers every secret named in the PDF | ✅ `credentials.json`, `token.json`, `.env`, keys |
| `.gitignore` does **not** ignore match artefacts that must be committed | ✅ explicit comment; only `scratch/`, `tmp/`, `*.log` ignored |
| Mandatory vs optional consistently marked in TASKS | ✅ `[M]` / `[O]` / `[P]` |
| Deviations from the PDF's recommended order are documented with rationale | ✅ TASKS Phase 4, 5, 8 |
| Contradiction choices are routed to the final README | ✅ AT §7, TASKS Phase 11, README closing note |

---

## 15. Audit conclusion

**No MISSING items.** All 55 Appendix E rules, all 32 Appendix F parameters, the
three status definitions, the six Appendix F §2 obligations, and every chapter
obligation cross-checked in this pass are documented, classified, and mapped to a
verification.

**Six AMBIGUOUS items** arise from genuine contradictions or silences in the PDF.
None was resolved silently: each is logged in `OPEN_QUESTIONS.md` with the
competing sources quoted, and each is either resolved by source priority in
`DECISIONS.md` or flagged for negotiation with the opponent team.

**One item requires escalation before the first counting match:**
`OPEN_QUESTIONS.md` Q-12 — the PDF refers to signing the step-zero declaration
"with a pre-supplied key" but never says who supplies it, what algorithm, or how
it is verified. An interim SHA-256 commitment is implemented (D-8); **no key
distribution scheme has been invented**, per the instruction not to fabricate
unresolved parameters.

**Five items must be agreed with each opponent team before a counting match:**
the sealed-record schema (Q-4), the turn model (Q-2), capture resolution under
simultaneity (Q-9), the shared config values including `num_games` (Q-1), and
the scent model with its numeric example (E-23). These are properties of a
judge-free protocol: both sides must compute identically, so both sides must
agree first.
