# PROTOCOL

The minimum FastMCP tool interface and wire contract between two peers.

Design constraints from [REQUIREMENTS.md](REQUIREMENTS.md): symmetric peers, no
central referee, commit-reveal over SHA-256 with the nonce hidden until end of
match, natural-language hints only (**never numeric position protocols**, E-27),
explicit and schema-validated messages.

**Status of this document.** The PDF does not specify a wire protocol. It
specifies the *obligations* the protocol must satisfy (E-17, E-18, E-26, E-27,
E-11, E-6, E-4/E-5) and shows a minimal FastMCP server as an example (PDF p. 28,
`receive_move`). Everything below is our design meeting those obligations. It is
negotiable with the opponent, and **must** be agreed with them before a match,
because both sides must speak it. Where the PDF fixes something, it is cited.

---

## 1. Symmetry

Both peers expose **the same** tool set and call **the same** tools on each
other. There is no client-only or server-only side (Ch. 2, PDF pp. 25–26).

```python
mcp = FastMCP("police_thief_peer")

@mcp.tool
def hello(...) -> dict: ...
@mcp.tool
def declare(...) -> dict: ...
@mcp.tool
def commit(...) -> dict: ...
@mcp.tool
def acknowledge(...) -> dict: ...
@mcp.tool
def reveal(...) -> dict: ...
@mcp.tool
def capture_claim(...) -> dict: ...
@mcp.tool
def final_reveal(...) -> dict: ...
@mcp.tool
def result_agreement(...) -> dict: ...
```

Eight tools. That is the whole surface.

---

## 2. Common envelope

Every request and every response carries the same envelope fields. Anything
outside the schema is rejected.

```jsonc
{
  "protocol_version": "1.0",     // string, must match exactly on both sides
  "game_id":   "…",              // string, identifies the match (all sub-games)
  "sub_game":  1,                // int, 1..num_games
  "step":      7,                // int, 0-based; 0 reserved for step-zero
  "role":      "police",         // "police" | "thief" — the SENDER's role
  "group_id":  "abcd1234",       // 8 chars, no spaces (E-45)
  "ts":        "2026-07-28T09:14:22Z"  // RFC 3339 UTC, sender's clock
}
```

Standard response envelope:

```jsonc
{
  "ok":     true,
  "error":  null,        // when ok=false: one of the error codes in §9
  "detail": null         // human-readable; never load-bearing
}
```

**Validation is mandatory on ingress.** Unknown fields, wrong types, or a
`protocol_version` mismatch are rejected with `ERR_SCHEMA`. A peer never acts on
an unvalidated message.

---

## 3. Config-hash exchange (E-11)

Before any play, both peers must prove they loaded a byte-identical shared
config. This is the mechanism that replaces the referee's authority over the
rules.

**Canonical hash definition.** The hash is taken over the shared config file's
canonical JSON serialisation — `sort_keys=True`, `separators=(",", ":")`,
UTF-8 — so that formatting differences between the two teams' files cannot
produce a false mismatch, and no semantic difference can produce a false match.

```
config_sha256 = SHA256( canonical_json(config/game.json) )
```

### `hello` — handshake and config agreement

Request:

```jsonc
{
  "…envelope…",
  "peer_name":      "My-Team-cop",
  "config_sha256":  "3f9a…",       // 64 lowercase hex
  "schema_version": "1.2",
  "scent_model_sha256": "b71c…",   // E-23: hash of the agreed emission/decay
                                   // formula TOGETHER WITH its numeric example
  "games_played_counted": 3        // E-37: counted matches played so far
}
```

Response:

```jsonc
{
  "…response envelope…",
  "peer_name":      "Their-Team-thief",
  "config_sha256":  "3f9a…",
  "scent_model_sha256": "b71c…",
  "games_played_counted": 1,
  "agreed": true
}
```

**Rules.**

- If `config_sha256` differs → **refuse to play**. Return `ERR_CONFIG_MISMATCH`
  and terminate. Not a technical loss; the match simply never starts (E-11:
  "refuse to play on any mismatch").
- If `scent_model_sha256` differs → refuse to play (E-23; a deviation in the
  decay formula voids the match).
- `games_played_counted` is the E-37 declaration. It is recorded in the log and
  in `[declaration_file]`. A false declaration disqualifies (E-38); it is
  cross-checked by the lecturer against the reports both teams send.
- `hello` is idempotent and may be retried safely.

**What is hashed for the scent model.** E-23 requires exchanging the *full*
emission and decay model **including a concrete numeric example**. We hash the
canonical JSON of:

```jsonc
{
  "formula": "tau_next = max(0, (1 - rho) * tau + delta_tau)",
  "rho": 0.10,
  "center_intensity": 0.9,
  "window": 5,
  "falloff": "radial",
  "example": { "tau": 0.9, "after_one_decay_turn": 0.81 }
}
```

---

## 4. Step zero — `declare` (E-24, E-53)

Sent once per sub-game, before step 1, by both peers.

```jsonc
{
  "…envelope…",              // step = 0
  "code_version":   "1.0.0",
  "github_commit":  "a1b2c3d…",     // E-53: the commit actually played
  "github_repos":   { "cop": "https://…", "thief": "https://…" },
  "group_name":     "My-Team",
  "members":        ["id-1001", "id-1002"],
  "hardware": {
    "os":        "Windows 11 Pro 10.0.22621",
    "cpu_cores": 8,
    "cpu_ghz":   2.4,
    "ram_gb":    16,
    "gpu":       null,
    "vram_gb":   0
  },
  "llm": { "provider": "template", "model": null },
  "token_budget": 200000,
  "signature": "…"                  // signed per Ch. 5, PDF p. 56
}
```

Response echoes the peer's own declaration with the same shape.

Both declarations are written to `[declaration_file]`
(`declaration_<game_id>.json`) and are immutable for the match. Code **may**
change between matches, but every match must carry the commit hash actually
played (E-53), and an email with that commit number goes to the lecturer
(Appendix F §2).

---

## 5. Turn ordering

**Unspecified by the PDF.** The book never states whether the cop or the thief
moves first. What it *does* fix (Ch. 4, PDF p. 43) is that scent decay happens
**at the end of each full turn — after both the cop and the thief have completed
their move**. Turns are therefore *paired*, not interleaved. See
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-2.

Our design, to be confirmed in negotiation:

- A **full turn** = one step by each peer, executed **simultaneously** under
  commit-reveal. Both peers commit before either reveals, so neither can react
  to the other's move within the same turn. This is exactly what commit-reveal
  is for, and it removes the first-mover question entirely rather than resolving
  it by fiat.
- `step` counts full turns and increments only after both reveals are verified.
- Scent emission for both peers, then a single global decay pass, are applied at
  the end of the full turn — once, not twice.
- Terminal conditions are evaluated after both moves are applied.

**Simultaneity and capture.** If both peers' moves would resolve to a capture
condition in the same turn, capture is evaluated after both moves land. The
resolution rule (does the cop moving onto the thief's vacated cell count?) is a
physics question the two teams must agree in negotiation. Recorded as
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) Q-9.

---

## 6. Commit-reveal ordering (E-17, E-18)

The four phases are mandatory **and ordered** (Ch. 5, PDF pp. 50–51).

```
        COP                                    THIEF
         │                                       │
  1      ├──────────  commit(H_commit)  ────────►│
         │◄─────────  commit(H_commit)  ─────────┤
         │                                       │
  2      ├──────────  acknowledge()    ─────────►│
         │◄─────────  acknowledge()    ──────────┤
         │                                       │
  3      ├──────────  reveal(move,hint) ────────►│      nonce STILL HIDDEN
         │◄─────────  reveal(move,hint) ─────────┤
         │                                       │
         │           …repeat for all steps…      │
         │                                       │
  4      ├────────  final_reveal(nonces) ───────►│      end of match only
         │◄───────  final_reveal(nonces) ────────┤
```

### 6.1 The sealed record

The PDF's formula is `H = SHA256(State ‖ Move ‖ Intent ‖ Nonce)` (PDF p. 50) but
states in the same breath that the record actually sealed is **richer** and also
includes the hint, the intent classification, the step number and the role, and
that concatenation is done by **canonical JSON serialisation with sorted keys
and fixed separators** so both peers hash byte-identical input.

We therefore lock this schema and hash its canonical serialisation:

```jsonc
{
  "game_id":  "…",
  "sub_game": 1,
  "step":     7,
  "role":     "police",
  "state":    "…",        // SHA-256 of the canonical pre-move local state
  "move":     "N",        // one of move_set, or a barrier action (§6.4)
  "hint":     "…",        // the exact verbal hint text that will be revealed
  "intent":   "truth",    // "truth" | "lie"
  "nonce":    "…"         // 32 hex chars, secrets.token_hex(16)
}
```

```
H_commit = SHA256( json.dumps(record, sort_keys=True,
                              separators=(",", ":")).encode("utf-8") ).hexdigest()
```

**This schema must be agreed with the opponent before the match** and its hash
included in the config-hash exchange, since both sides must recompute it
identically at audit. See [DECISIONS.md](DECISIONS.md) D-4.

`state` is a hash rather than the raw state so the commitment binds the move to a
specific game position (preventing replay of an old commitment in a new context,
per PDF p. 51) without leaking the position itself.

### 6.2 `commit`

```jsonc
// request
{ "…envelope…", "h_commit": "9c1f…" }        // 64 lowercase hex, nothing else
// response
{ "…response envelope…" }
```

Sends **only** the signature — never its content (PDF p. 50).

### 6.3 `acknowledge`

```jsonc
// request
{ "…envelope…", "acking_h_commit": "9c1f…" }
// response
{ "…response envelope…", "locked": true }
```

Confirms receipt and that the peer is *locked* on the commitment. Prevents the
sender retreating, and ensures reveal happens only once **both** sides have
fixed their moves (PDF p. 51).

### 6.4 `reveal`

```jsonc
// request
{
  "…envelope…",
  "move":   "N",                  // or {"action":"barrier","cell":[r,c]}
  "hint":   "Slipping past the bright lights near the square",
  "intent": "truth"               // "truth" | "lie"
}
// response
{ "…response envelope…", "accepted": true }
```

**The nonce is NOT sent here** (E-18, PDF p. 51). Revealing it early enables
premature reverse-engineering of signatures and exposes the commitment to a
dictionary attack over the small move space.

**Receiver obligations on `reveal`:**

1. Validate the move against the agreed physics: orthogonal or STAY only
   (E-13/E-14), within bounds, not into a barrier. An illegal move is rejected
   with `ERR_ILLEGAL_MOVE` — *the opposing agent enforces the physics*
   (PDF p. 38).
2. Validate the hint is natural language within `hint_max_words`, and contains
   no numeric position protocol (E-26, E-27). See §8.
3. If the move is a barrier placement, it must be openly declared here with its
   exact cell (E-15, E-16), and must be within one step of the cop's cell on a
   turn where the cop forgoes movement, with the quota `max_barriers` not
   exceeded.
4. Log the revealed values. They cannot be verified against `h_commit` yet — the
   nonce is still hidden — so verification is deferred to the final audit. This
   is inherent to the scheme, not a gap.

### 6.5 `capture_claim` (E-21, E-22)

Issued by the cop when it believes it has captured; the thief is under a
**cryptographic obligation to answer truthfully** (PDF p. 38).

```jsonc
// request  (cop → thief)
{ "…envelope…", "claimed_cell": [3, 4], "reason": "landed" }
   // reason: "landed" | "barrier_on_thief" | "no_legal_move"
// response (thief)
{ "…response envelope…", "confirmed": true, "thief_cell": [3, 4] }
```

Three capture conditions, all mandatory: the cop lands on the thief's cell
(Ch. 3 scoring table); the cop places a barrier on the cell where the thief
stands (E-46); the thief has no legal move at all (E-47).

A false claim by the cop, or a false denial by the thief, is exposed at audit and
carries immediate disqualification with no right of appeal (E-22).

### 6.6 `final_reveal` (end of match)

```jsonc
// request
{
  "…envelope…",
  "records": [
    { "sub_game":1, "step":1, "nonce":"…", "move":"N",
      "hint":"…", "intent":"truth", "state":"…", "h_commit":"…" },
    …
  ]
}
// response
{ "…response envelope…", "audit": "OK" }   // "OK" | "MISMATCH"
```

Only now are all nonces disclosed (E-18). Each side then performs the **mutual
audit** (E-36): for every record, recompute the canonical hash and compare
against the `h_commit` received live. Any mismatch → `MISMATCH` → technical loss
for the forging side, score 0 (E-19).

### 6.7 `result_agreement` (E-35)

```jsonc
// request
{
  "…envelope…",
  "audit_result": "OK",
  "per_sub_game": [ { "sub_game":1, "cop":20, "thief":5, "outcome":"capture" }, … ],
  "totals":       { "cop": 45, "thief": 30 },
  "tokens_used":  0,                 // E-54
  "result_sha256": "…"               // hash of the canonical result payload
}
// response
{ "…response envelope…", "agreed": true, "result_sha256": "…" }
```

Both sides must agree on the result **before** each independently emails its own
`[result_file]`. If one side fails to report, or the two reports contradict, the
match is disqualified and **both** teams score 0 (E-35).

---

## 7. Timeouts, duplicates and invalid sequences

### 7.1 Timeouts (E-6)

Every outgoing request carries a timestamp and an expiry deadline of
`response_timeout_sec` (Appendix F table 19 row 6). A request whose deadline
passed **is a failure, not an invitation to wait longer** (PDF p. 81).

| Situation | Behaviour |
|---|---|
| No response within `response_timeout_sec` | Retry up to `max_retries`, waiting `retry_backoff_sec` between attempts |
| Retries exhausted | Transition to `TECHNICAL_LOSS`, log it, close the turn cleanly, notify |
| Main loop emits no heartbeat for `watchdog_timeout_sec` | Watchdog performs controlled shutdown with state persistence (E-7) |

Technical loss zeroes **both** sides (Ch. 3 scoring table) — which is precisely
why neither side benefits from stalling.

### 7.2 Duplicates

The network may deliver a message twice, and a retry after a lost response is
indistinguishable from a duplicate. Every tool is therefore **idempotent**,
keyed on `(game_id, sub_game, step, role, tool)`:

| Case | Behaviour |
|---|---|
| Duplicate with **identical** payload | Return the previously computed response. Do not re-apply. Do not re-log as a new event; log a `duplicate_suppressed` note. |
| Duplicate with **different** payload for the same key | **Reject** with `ERR_DUPLICATE_CONFLICT`. This is an attempt to change a committed decision — exactly what commit-reveal exists to prevent. Log it as evidence for the audit. |

### 7.3 Invalid sequence (E-5)

The state machine rejects every transition not in its table, immediately, rather
than leaving the system in an undefined state (PDF p. 80).

| Case | Behaviour |
|---|---|
| Tool arrives in a phase where it is not legal (e.g. `reveal` before `acknowledge`) | Reject with `ERR_ILLEGAL_SEQUENCE`; state unchanged; logged |
| `step` skips ahead or goes backwards | Reject with `ERR_STEP_ORDER`; logged |
| `sub_game` inconsistent with local counter | Reject with `ERR_SUBGAME_ORDER` |
| `protocol_version` mismatch | Reject with `ERR_SCHEMA` at handshake; refuse to play |
| Repeated illegal-sequence attempts beyond a small threshold | Treat as a faulty or hostile peer; transition to `TECHNICAL_LOSS` |

A rejected transition never mutates state. That is what makes E-4/E-5 testable:
a test asserts that after a rejected message the phase is byte-identical to
before.

---

## 8. Natural-language constraint (E-26, E-27)

Hints must be **free natural language**. Direct numeric position protocols are
forbidden — the prohibition exists to preserve the psychological character of
the game, and violating it disqualifies the game's character as defined in the
rule book.

Ingress validation on every `reveal`:

- Word count ≤ `hint_max_words`.
- Rejected if the text encodes a coordinate: bare digit pairs, `(r,c)` / `[r,c]`
  forms, `row=`/`col=` style key-value pairs, or grid references like `B4`.
- The `intent` flag is metadata, not part of the hint text; it is committed
  (so a peer cannot retroactively claim it "meant to lie") and revealed
  alongside the hint.

Note the flag is *self-declared truthfulness*, and a peer is free to declare
`lie` and send a false hint — deception through the verbal channel is the
intended game. What is forbidden is committing `truth` and then revealing a hint
the log shows to be false, or encoding positions numerically to bypass the
psychological layer.

Scent, by contrast, cannot lie: it is emitted by movement itself and cannot be
forged (Ch. 4).

---

## 9. Error codes

```
ERR_SCHEMA               malformed message or protocol_version mismatch
ERR_CONFIG_MISMATCH      config_sha256 or scent_model_sha256 differs → refuse to play
ERR_ILLEGAL_SEQUENCE     tool called in a phase where it is not legal
ERR_STEP_ORDER           step number out of order
ERR_SUBGAME_ORDER        sub_game number out of order
ERR_DUPLICATE_CONFLICT   same key, different payload
ERR_ILLEGAL_MOVE         diagonal, out of bounds, into a barrier, or quota exceeded
ERR_ILLEGAL_HINT         exceeds hint_max_words or encodes numeric positions
ERR_COMMIT_MISMATCH      audit: recomputed hash ≠ declared commitment
ERR_TIMEOUT              deadline expired
ERR_INTERNAL             local failure; caller should retry then declare technical loss
```

Errors are returned in the response envelope (`ok:false`), never raised across
the wire as transport faults, so both sides log the same thing.

---

## 10. Game-completion signalling

A sub-game ends when exactly one of these is true. All are evaluated locally by
both peers from the shared physics, and must agree — divergence is itself a
protocol failure.

| Outcome | Trigger | Cop | Thief |
|---|---|---|---|
| Capture | Cop lands on thief's cell, or barrier placed on thief's cell (E-46), or thief has no legal move (E-47) — confirmed via `capture_claim` | `capture_cop` | `capture_thief` |
| Survival | Thief survives `survival_threshold` valid steps without capture | `survival_cop` | `survival_thief` |
| Technical loss | Crash, deadline exhaustion, or cryptographic forgery | 0 | 0 |

Sequence at completion of a **sub-game**: both peers reach the same terminal
state → log sealed → `sub_game` increments → next sub-game begins, up to
`num_games`.

Sequence at completion of a **match** (all `num_games` sub-games):

1. `final_reveal` — all nonces disclosed by both sides (E-18).
2. Mutual audit (E-36) — each side re-hashes and compares. Mismatch → technical
   loss for the forger, score 0 (E-19).
3. Tie check: if the accumulated score across **all** sub-games is equal, each
   side receives `tie_score` (Ch. 9, PDF p. 87).
4. `result_agreement` — both sides agree on the result (E-35).
5. **Each side independently** emails its own `[result_file]` as a JSON
   **attachment** to `[agent_reporting_address]` through the Gatekeeper
   (E-32, E-33, E-34, E-51). Failure by one side to report costs *that side* its
   points even if it won on the board; contradictory reports disqualify the
   match for **both**.
6. The encounter against that opponent is **sealed** — no further counting match
   against them (E-52).
