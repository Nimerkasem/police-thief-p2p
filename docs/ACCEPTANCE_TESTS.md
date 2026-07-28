# ACCEPTANCE TESTS

Every mandatory requirement mapped to an executable test or a deterministic
verification procedure. Rule IDs are Appendix E's own numbering
(see [REQUIREMENTS.md](REQUIREMENTS.md)).

**Verification classes.**

| Class | Meaning |
|---|---|
| `AUTO` | pytest test. Must pass in CI-equivalent local run. |
| `MANUAL` | Deterministic procedure a human executes and records. Used where the check is inherently observational (a screenshot, a public URL, a Moodle form). Every `MANUAL` entry states the exact steps and the exact pass condition — no judgement calls. |
| `PROCESS` | An administrative obligation verified by a checklist item before submission. |

**Naming convention** (D-17): test functions carry the rule ID, e.g.
`test_e13_rejects_diagonal_move`, so coverage is greppable.

Tests do not exist yet — this document is the specification the test suite is
written against, and the source for `tests/` in Phase 0 onward.

---

## 1. Network architecture and decentralisation

| Rule | Requirement | Class | Verification |
|---|---|---|---|
| E-1 | Cop and thief in two entirely separate processes | `AUTO` + `MANUAL` | **AUTO:** `test_e1_peers_have_no_shared_module_state` — import both role runtimes in one interpreter, instantiate both, mutate one's state, assert the other is unchanged; assert no module-level mutable singletons via a registry scan. **MANUAL:** launch both peers per README; `Get-Process python` shows two distinct PIDs; both play a full sub-game. |
| E-2 | No shared memory or variables between sides | `AUTO` | `test_e2_no_cross_role_imports` — walk `src/police_thief`, assert no module imports another role's runtime and no module holds live game state at module scope. `test_e2_state_objects_are_independent` — deep-compare two role states after divergent mutation. |
| E-3 | Orchestrator is the single entry point | `AUTO` | `test_e3_subsystems_reachable_only_via_orchestrator` — assert the five sub-systems (MCP connector, decision, log, deadline, watchdog) hold no references to each other; assert each is constructed by the orchestrator. |
| E-4 | Game states managed by a proper state machine | `AUTO` | `test_e4_legal_turn_cycle_completes` — drive the full cycle `WAITING_FOR_OPPONENT → COMPUTING_MOVE → COMMITTING → AWAITING_REVEAL → VERIFYING → WAITING_FOR_OPPONENT` and assert each transition is accepted. |
| E-5 | Reject every illegal state transition | `AUTO` | `test_e5_rejects_illegal_transition` — for every (state, target) pair **not** in the transition table, assert it raises and **assert the phase is unchanged after the rejection**. |
| E-6 | Deadline tracking prevents freeze | `AUTO` | `test_e6_request_deadline_expires` — mock a peer that never responds; assert the call aborts at `response_timeout_sec`, retries `max_retries` times with `retry_backoff_sec` spacing, then transitions to `TECHNICAL_LOSS`. Use a fake clock, not `sleep`. |
| E-7 | Watchdog monitors crashes, extracts data | `AUTO` | `test_e7_watchdog_detects_stall` — advance a fake clock past `watchdog_timeout_sec` with no heartbeat; assert controlled shutdown fired and state was persisted. `test_e7_partial_jsonl_is_readable` — truncate a JSONL log mid-line; assert all complete lines still parse. |
| E-8 | Live GUI displays local truth only | `AUTO` | `test_e8_gui_has_no_opponent_truth_handle` — assert the GUI object graph reaches only local-truth and belief modules; assert no path from GUI to the network layer's decoded opponent state. |
| E-9 | Never display the full objective board state | `AUTO` | `test_e9_live_state_has_no_opponent_position` — assert `LocalState` has **no attribute** for the opponent's position (D-9); assert `getattr` raises. `test_e9_render_model_excludes_truth` — snapshot the GUI's render model; assert opponent's true cell appears nowhere. |
| E-10 | Tunnelling tool exposes server publicly | `MANUAL` | Start peer; start tunnel (`ngrok http <port>`); from a **different machine or network**, call the `hello` tool against the public URL and receive `ok:true`. Pass condition: successful handshake from off-host. Record the URL and timestamp in the match declaration. |

---

## 2. Spatial mechanics and board constraints

| Rule | Requirement | Class | Verification |
|---|---|---|---|
| E-11 | Config identical byte-for-byte on both sides | `AUTO` | `test_e11_config_hash_matches` — canonical-hash the same file loaded twice, assert equal. `test_e11_refuses_play_on_mismatch` — handshake with a peer whose `config_sha256` differs by one byte; assert `ERR_CONFIG_MISMATCH` and that **no sub-game starts**. |
| E-12 | Raise minimums only by agreement; never lower | `AUTO` | `test_e12_rejects_lowered_minimum` — parametrised over every MINIMUM parameter; load a config with the value one below the table and assert the validator rejects it. `test_e12_accepts_raised_minimum` — assert a raised value loads. `test_e12_rejects_altered_fixed` — parametrised over every FIXED parameter; assert any change is rejected. |
| E-13 | Move only orthogonally | `AUTO` | `test_e13_accepts_orthogonal_and_stay` — assert all of `move_set` are legal from an interior cell. |
| E-14 | No diagonal moves | `AUTO` | `test_e14_rejects_diagonal_move` — submit a diagonal in `reveal`; assert `ERR_ILLEGAL_MOVE` and that the board state is unchanged. |
| E-15 | Declare every barrier placement openly | `AUTO` | `test_e15_barrier_appears_in_reveal_and_log` — place a barrier; assert the reveal payload carries the exact cell and the log records it. `test_e15_rejects_undeclared_barrier` — assert a board diff showing an undeclared barrier is rejected at audit. |
| E-16 | Never lie about barrier location | `AUTO` | `test_e16_barrier_cell_is_sealed_in_commit` — assert the barrier cell is inside the committed record, so a later inconsistency breaks the hash at audit. |
| E-46 | Barrier on the thief's cell counts as capture | `AUTO` | `test_e46_barrier_on_thief_is_capture` — cop forgoes movement and places on the thief's cell; assert terminal state is capture with `capture_cop` / `capture_thief`. |
| E-47 | Thief with no legal move is captured | `AUTO` | `test_e47_enclosed_thief_is_captured` — construct a board where all four neighbours are barriers/edges; assert capture. Include the board-corner case where edges alone enclose. |
| E-48 | Score every end scenario per the tables | `AUTO` | `test_e48_scoring_matrix` — parametrised over capture / survival / technical loss; assert exact scores from config, never literals. |
| — | Barrier quota respected | `AUTO` | `test_barrier_quota_enforced` — attempt placement number `max_barriers + 1`; assert rejection. |
| — | Barrier is irreversible and blocks both | `AUTO` | `test_barrier_permanent_and_blocks_both` — assert neither role may enter a blocked cell, for the remainder of the sub-game. |
| — | Barrier only within one step, only when forgoing movement | `AUTO` | `test_barrier_placement_constraints` — assert placement two cells away is rejected, and placement combined with a move is rejected. |

---

## 3. Cryptography and log integrity

| Rule | Requirement | Class | Verification |
|---|---|---|---|
| E-17 | Commit-reveal over SHA-256 | `AUTO` | `test_e17_commit_then_reveal_verifies` — full round trip; assert the recomputed canonical hash equals the declared commitment. `test_e17_uses_sha256` — assert digest length 64 hex and matches `hashlib.sha256` of the canonical payload. |
| E-18 | Nonce secret until end of match | `AUTO` | `test_e18_reveal_payload_omits_nonce` — assert the `reveal` schema **rejects** a nonce field and that no nonce appears in any wire payload before `final_reveal`. `test_e18_nonce_is_cryptographic` — assert generation uses `secrets`, not `random`, and is ≥128 bits. |
| E-19 | Technical loss on any audit hash mismatch | `AUTO` | `test_e19_tampered_log_is_rejected` — take a valid log, flip one character of one move; assert audit returns mismatch, the offending entry is identified, and the outcome is technical loss with score 0 for the forger. Parametrise the tamper across move, hint, intent, state and step. |
| E-20 | Replay viewer application exists | `AUTO` + `MANUAL` | **AUTO:** `test_e20_verifier_verified_ok_on_clean_log`, `test_e20_verifier_tampered_on_dirty_log`. **MANUAL:** launch `python -m police_thief replay --log matches/<id>/log_<id>_g01.json`; step forward and backward; observe green `Verified OK`. Pass condition: screenshot captured for the README (also a submission requirement). |
| E-21 | Declare truth only on capture | `AUTO` | `test_e21_thief_must_answer_capture_truthfully` — assert the thief's response is sealed in its commitment, so a false denial breaks the hash at audit. |
| E-22 | Never falsely declare a capture | `AUTO` | `test_e22_false_capture_claim_detected` — cop claims capture while positions differ in the log; assert audit flags it and the outcome is immediate disqualification. |
| E-23 | Cryptographically lock the scent model pre-match | `AUTO` | `test_e23_scent_model_hash_exchanged` — assert `hello` carries `scent_model_sha256` covering formula **and** the numeric example. `test_e23_refuses_on_model_mismatch` — differing ρ ⇒ refuse to play. `test_e23_worked_example` — assert τ=0.9 decays to 0.81 after one turn at ρ=0.10. |
| E-24 | Cryptographic hardware declaration pre-match | `AUTO` | `test_e24_step_zero_precedes_step_one` — assert no `commit` is accepted before both `declare` messages. `test_e24_declaration_sealed` — assert the declaration hash is stable and recorded. |
| E-53 | Step-0 records the commit hash played | `AUTO` | `test_e53_declaration_carries_commit_hash` — assert `github_commit` is present, non-empty, and hex; assert it also lands in `[declaration_file]` and `[result_file]`. |
| — | Canonical serialisation is byte-identical | `AUTO` | `test_canonical_json_is_key_order_independent` — build the same record with keys in different insertion orders; assert identical bytes and identical hash. |

---

## 4. Scent physics

| Requirement | Class | Verification |
|---|---|---|
| Emission window `pheromone_grid_size` with centre `pheromone_center_intensity`, radial falloff | `AUTO` | `test_scent_emission_field_shape` — assert window side equals config, centre equals config, and intensity is non-increasing with Chebyshev/radial distance from centre. |
| Decay rule `τ(t+1) = max(0, (1−ρ)·τ(t) + Δτ)` | `AUTO` | `test_scent_decay_formula` — assert exact arithmetic against hand-computed values; assert the clamp holds (never negative). |
| Decay applied once per **full** turn, after both moves | `AUTO` | `test_scent_decays_once_per_full_turn` — run one full turn; assert exactly one decay pass was applied, not two. |
| Each peer reads only the **opponent's** field | `AUTO` | `test_peer_reads_only_opponent_scent` — assert the observation object exposes the opponent's field and that the peer's own emitted field is not part of its observation input. |
| Scent cannot be forged | `AUTO` | `test_scent_emitted_only_at_own_position` — assert the API offers no way to deposit scent at a non-occupied cell. |

---

## 5. Strategy, language and network protection

| Rule | Requirement | Class | Verification |
|---|---|---|---|
| E-25 (**RECOMMENDED**) | LLM does not decide the move | `AUTO` | `test_e25_move_decided_without_llm` — run a full sub-game with a verbal provider that raises on any call requiring a move; assert the game completes. `test_e25_llm_interface_surface` — assert the verbal module exposes only *produce hint* and *classify hint*. |
| E-26 | Free natural language only | `AUTO` | `test_e26_hint_is_natural_language` — assert generated hints contain no coordinate encodings and are within `hint_max_words`. |
| E-27 | No direct numeric position protocols | `AUTO` | `test_e27_rejects_numeric_position_hint` — parametrised over `"3,4"`, `"(3,4)"`, `"[3,4]"`, `"row=3 col=4"`, `"B4"`; assert `ERR_ILLEGAL_HINT`. `test_e27_wire_schema_has_no_position_field` — assert no protocol message carries the sender's own position. |
| E-28 | Token-bucket rate limiter for Gmail | `AUTO` | `test_e28_token_bucket_rule` — assert `tokens ← min(C, tokens + r·Δt)` and `allow ⟺ tokens ≥ 1` against a fake clock; assert a burst beyond capacity is blocked and recovers after quiet time. |
| E-29 | DOS detector | `AUTO` | `test_e29_dos_detector_locks_pipe` — simulate a send loop; assert the gatekeeper locks and **all** subsequent sends are refused until reset. |
| E-30 | Send-only Gmail permission | `AUTO` | `test_e30_scope_is_send_only` — assert the scope constant is exactly `https://www.googleapis.com/auth/gmail.send` and that no read/modify scope appears anywhere in the source. |
| — | Gatekeeper order: quota → bucket → DOS | `AUTO` | `test_gatekeeper_fail_fast_order` — assert a quota failure short-circuits before the bucket is consulted. |
| — | 429 triggers backoff, not immediate retry | `AUTO` | `test_429_backs_off` — mock a 429; assert the sender waits and does not immediately resend. |

---

## 6. League, reporting and administration

| Rule | Requirement | Class | Verification |
|---|---|---|---|
| E-31 | Minimum matches vs different groups | `PROCESS` | Before submission: `matches/` contains ≥ `min_games_to_pass` completed counting matches against **distinct** `group_id` values. `AUTO`: `test_e31_counting_matches_distinct_opponents` over the artefact directory. |
| E-32 | Automatic result reporting via Gmail | `AUTO` + `MANUAL` | **AUTO:** `test_e32_report_send_invoked_on_completion` — assert match completion triggers exactly one send. **MANUAL:** run a match end-to-end against a test recipient; confirm the message arrives with the JSON attached. |
| E-33 | Report is standard JSON | `AUTO` | `test_e33_result_file_is_valid_json` — assert it parses, validates against the result schema, and contains all mandatory fields (both teams' GitHub links, per-sub-game commit hash, token totals). |
| E-34 | Never free text; JSON attachment only | `AUTO` | `test_e34_report_sent_as_attachment` — assert the MIME message has a JSON attachment and that the body carries no report payload. |
| E-35 | Agree result; each team sends separately | `AUTO` | `test_e35_result_agreement_required_before_send` — assert send is refused until `result_agreement` returns `agreed:true`. `test_e35_contradictory_result_blocks_send` — differing totals ⇒ refuse and log. |
| E-36 | Mutual log audit every match | `AUTO` | `test_e36_audit_runs_before_result_agreement` — assert ordering; assert a failed audit prevents result agreement. |
| E-37 | Declare counted-match count at match start | `AUTO` | `test_e37_hello_carries_games_played` — assert present, integer, and matches the count derivable from `matches/`. |
| E-38 | Never declare falsely | `AUTO` | `test_e38_declared_count_derives_from_artefacts` — assert the value is computed from the artefact store, not hand-set, so it cannot silently diverge. |
| E-39 | Never push secrets | `AUTO` + `PROCESS` | `test_e39_no_secrets_tracked` — assert `git ls-files` matches none of the secret patterns. **PROCESS:** before tagging, run `git log -p | grep` for the patterns across full history. |
| E-40 | Secrets in `.gitignore` | `AUTO` | `test_e40_gitignore_covers_secrets` — assert `.gitignore` matches `credentials.json`, `token.json`, `.env` (via `git check-ignore`, not string search). |
| E-41 | Documented Git tag for submission | `PROCESS` | `git tag -a v1.0-submission -m "…"` then `git push origin v1.0-submission`; verify with `git show v1.0-submission`. Pass condition: annotated tag exists on the remote. |
| E-42 | Comprehensive academic report in repo | `PROCESS` | `README.md` contains all six mandatory components (Ch. 9, PDF p. 97). Checklist in §7 below. |
| E-43 | Moodle form: fill, do not alter fields | `MANUAL` | Download the Word template from Moodle, fill only the data fields, save as PDF, verify no field moved or renamed by diffing against a blank render. |
| E-44 | Each member submits separately in Moodle | `PROCESS` | One Moodle submission per group member, confirmed by each. |
| E-45 | Unique 8-char group code, no spaces | `AUTO` | `test_e45_group_id_format` — assert `len == 8` and `not any(c.isspace())`. |
| E-49 | Two repos, cross-linked, 2 links Moodle, 4 links JSON | `AUTO` + `PROCESS` | `test_e49_result_json_has_four_links` — assert both teams' cop and thief URLs are present. **PROCESS:** verify each repo's README links the other. |
| E-50 | Each repo has README, /config, PRD, PLAN, TODO | `AUTO` | `test_e50_required_repo_files_exist` — assert `README.md`, `PLAN.md`, `TODO.md`, `config/`, `docs/prd/` with ≥1 PRD each. |
| E-51 | Send reports to `[agent_reporting_address]` | `AUTO` | `test_e51_recipient_is_lecturer_address` — assert the configured recipient equals `rmisegal+uoh26finalgame@gmail.com`. |
| E-52 | One counting match per opponent | `AUTO` | `test_e52_one_counting_match_per_opponent` — assert no two counting matches share an opponent `group_id`; assert warm-up matches are flagged and excluded. |
| E-54 | Report total tokens consumed | `AUTO` | `test_e54_tokens_reported` — assert `tokens_used` present per sub-game and in the series total; assert it is 0 in `template` mode rather than absent. |
| E-55 | Self-grade for code quality only | `PROCESS` | Moodle self-grade field reflects code quality; explicitly not derived from match results. |
| — | Config file per match, distinct name, committed | `AUTO` | `test_config_filename_pattern` — assert `config_<game_id>_g<NN>.json` and uniqueness across `matches/`. |
| — | Tie rule | `AUTO` | `test_tie_awards_tie_score_to_both` — equal cumulative totals across all sub-games ⇒ both receive `tie_score`. |

---

## 7. Submission-artefact checklist

`PROCESS`. Mirrors Appendix C table 6 (PDF p. 136) and Ch. 11 (PDF pp. 113–114).
Every line must be *observed*, not intended.

- [ ] Two GitHub repositories (cop, thief), public **or** shared with
      `rmisegal@gmail.com`
- [ ] Cross-link present in **both** READMEs
- [ ] Annotated tag `v1.0-submission` created **and pushed** in both repos
- [ ] `README.md` in **both** repos contains all six mandatory components:
  - [ ] 1. Chosen Dec-POMDP model — state space, observations, uncertainty
  - [ ] 2. FastMCP orchestration dilemmas — turns, network failures, Gatekeeper
        and Orchestrator roles
  - [ ] 3. Strategies implemented — heuristics / belief map / (optional
        Q-Learning)
  - [ ] 4. Learning curves — **only if** RL was used
  - [ ] 5. Screenshots — Live GUI belief map **and** Replay showing
        `Verified OK`
  - [ ] 6. Link to the companion repository
- [ ] **Also in the README:** the documented contradiction choices from
      [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — where identified, what chosen,
      why (PDF p. 5)
- [ ] `PLAN.md`, `TODO.md`, `docs/prd/*` present in both repos
- [ ] Each match's `config_<game_id>_g<NN>.json` committed
- [ ] ≥ 2 counting matches against **different** groups
- [ ] End-of-match email sent by **both** sides for every counting match
- [ ] No secrets anywhere in git history; `.gitignore` verified
- [ ] Moodle: PDF form filled without altering fields; one submission per member;
      8-character group code; self-grade for code quality only

---

## 8. End-to-end verification scenario

`MANUAL`, run before tagging. Exercises the whole compliance surface in one
pass.

1. Start two peers on separate machines, each behind its own tunnel.
2. Handshake: config hashes match; scent-model hashes match; game counts
   declared.
3. Step zero: both hardware declarations exchanged, each carrying its commit
   hash.
4. Play all `num_games` sub-games to completion. Observe in each peer's GUI:
   belief heatmap updating, turn banner alternating green/grey. Confirm **no**
   window shows the opponent's true position.
5. Force one failure deliberately: kill one peer mid-turn. Confirm the survivor
   hits its deadline, retries, and lands in `TECHNICAL_LOSS` cleanly with a
   readable log rather than hanging.
6. Restart and complete a clean match.
7. Final reveal + mutual audit ⇒ `Verified OK` on both sides.
8. Load each log in the replay viewer ⇒ green `Verified OK`. **Screenshot.**
9. Screenshot the belief map in the Live GUI. **Screenshot.**
10. Tamper with a saved log copy; reload in the viewer ⇒ red `TAMPERED`.
    Confirms the detector actually fires.
11. Result agreement ⇒ both sides email their own `result_<game_id>.json`.
    Confirm both arrive with the JSON attached.
12. Commit all four artefacts under `matches/<game_id>/`.
