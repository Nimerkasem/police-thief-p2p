# Partner handoff — Distributed Cops-and-Robbers over P2P

Written for a collaborator picking the project up cold. Read `CLAUDE.md` first,
then `docs/REQUIREMENTS.md` and `docs/PARAMETERS.md`, then this file.

---

## 1. Current status

The system is **complete and verified in-process, and blocked in two-process
play**. Every mandatory subsystem is implemented and tested; a full 35-turn game
runs, audits and replays correctly when both peers share one process. The same
game between two real OS processes stalls at turn 6. That single fault
(**Q-20**) is the whole of the remaining blocker and the reason for this handoff.

- **Latest stable code commit:** `e10477cb73c90d44cdcd7de04d4c158a959df842`
  — *fix(transport): per-channel worker-owned sessions; server stall still open*.
  The only commit after it is this document; no application code follows it.
- **Tag:** `pre-q20-handoff`, annotated, on the tip of `main` — so checking out
  the tag gives you the code *and* this file.
- **Tests:** 1468 passing.
- Nothing in the tree is half-finished. The stall is a runtime fault, not
  unfinished code.

## 2. Completed phases

| Phase | What it delivers | State |
|---|---|---|
| 0 | Configuration foundation, canonical JSON, `config_sha256`, Appendix F policy table (32 parameters, 14 FIXED / 9 MINIMUM / 9 NEGOTIABLE) | complete |
| 1 | Deterministic single-process game domain; `LocalState` with **no field** for the opponent's position | complete |
| 2 | Symmetric FastMCP transport, message schemas, peer state machine, orchestration | complete |
| 3 | SHA-256 commit-reveal, hash-chained JSONL audit log, full crypto turn | complete |
| 4 | Scent field (σ = 1.15), Bayesian belief map, deterministic cop/thief strategies, deterministic template hint layer with trust-weighted reading | complete |
| 6 | Independent two-log replay verification (10 tampering cases classified correctly) and offline Tk viewer | complete |
| 7 | Minimal live per-peer GUI showing local truth only | complete, limitation Q-19 |

Not started, deliberately: Phase 8 (public exposure), Phase 9 (Gmail
reporting), Phase 10 (league), Phase 11 (submission). **Do not start these.**
Q-20 comes first — a league match cannot be played over a transport that stalls.

## 3. The blocker — Q-20, two-process transport stall

Full write-up in `docs/OPEN_QUESTIONS.md` § Q-20. Summary:

A two-process game reaches turn 6 and stops. The peer that cannot proceed
reports `RuntimeError: Client failed to connect: All connection attempts
failed`. The opponent's **server** has stopped accepting new connections while
its own process is still alive and still trying to play.

### Exact dependency versions

| Package | Version |
|---|---|
| Python | 3.12.10 |
| fastmcp | **3.4.5** (pinned in `pyproject.toml`) |
| mcp | 1.28.1 |
| pytest | 9.1.1 |

The FastMCP API surface actually used is small and pinned deliberately:
`FastMCP(name=...)`, the `@mcp.tool` decorator,
`mcp.run_async(transport="http", host=, port=, path=, show_banner=False)`,
`Client(transport)` accepting a URL **or** a `FastMCP` instance, and
`client.call_tool(name, args) -> CallToolResult` with `.data` / `.is_error`,
raising `ToolError` on refusal.

### Transport approaches already tested — all failed

| # | Client topology | Fails at |
|---|---|---|
| 1 | A fresh `Client` per message | turn 1 |
| 2 | One shared persistent session, unguarded | turn 3–5 |
| 3 | One shared persistent session behind a lock | turn 5–8 |
| 4 | Two channels, sessions held as shared objects | turn 6 |
| 5 | **Two channels, each session owned end-to-end by its own worker task** (current, `src/police_thief/peer/channel.py`) | **turn 6, repeatably** |

Please do not re-attempt 1–4. They are measured, not guessed.

### Evidence that the failure is server-side

1. **Three unrelated client designs fail at the same turn (6).** If the fault
   were client concurrency, changing the concurrency model would move the wall.
   It does not move.
2. The error is a *connect* failure, not a request failure — the TCP connection
   is refused, so the client never gets far enough to misuse a session.
3. The refusing process is **alive**: it keeps logging, keeps its GUI
   responsive, and keeps trying to send its own messages.
4. **The identical turn sequence reaches 35 turns in-process**, where there is
   no HTTP server in the path at all. Protocol, crypto, belief and strategy
   layers are therefore exonerated.
5. Cancellation damage to a client session was reproduced in isolation and the
   channel recovers cleanly, so that is not it either.
6. **Q-19 is the same fault seen from another angle**: under `--gui` the server
   stops answering after roughly six turns. Two different pressures, one
   symptom, one component in common — the server.

A genuine client bug *was* found and fixed on the way (a FastMCP `Client` is
built on anyio cancel scopes that must be entered and exited by the same task;
the old code entered in the startup task and exited in a turn task, after which
every reconnect also raised and the channel died permanently). Fixing it did not
move the wall — which is itself part of the evidence above.

### Next experiment — and it is the only one being asked for

**FastMCP stateless HTTP with JSON responses.**

The working hypothesis is server-side session accumulation. FastMCP's default
streamable-HTTP transport gives each session a long-lived `GET /mcp` stream; a
peer that restarts a channel leaves the previous stream half-open, and a filling
session table or connection limit would produce exactly what is observed — a
live server that refuses new connections.

Stateless mode removes the long-lived stream entirely: every call becomes an
independent request/response with no server-side session to accumulate. If the
game then passes turn 6, the hypothesis is confirmed and the fix is a transport
configuration change rather than a redesign.

Two supporting measurements worth taking first, both cheap:

- Count active sessions on the server across a game and see whether the count
  climbs monotonically to a ceiling at turn 6.
- Run a one-way game (only one peer initiating) and see whether it survives
  longer than a bidirectional one. If it does, the accumulation is per-direction.

Start in `src/police_thief/peer/server.py` (the `run_async` call) and
`src/police_thief/peer/channel.py` (the `Client` construction).

## 4. Other unresolved questions you should know about

Full list in `docs/OPEN_QUESTIONS.md`. Two matter most:

### Q-12 — the step-zero signing key. **ESCALATE, do not close.**

The PDF (Ch. 5, p. 56) says the step-zero specification is "cryptographically
signed using a pre-supplied key" but never says who supplies the key, what
algorithm, or how the counterpart verifies it. No Appendix F parameter covers
it.

The interim position is canonical JSON + SHA-256 exchanged and locked at
handshake. **Do not invent a key or a key-distribution scheme.** This must be
asked of the lecturer before the first counting match. If a real key turns out
to exist, swapping the hash for a signature is contained behind the crypto
module's interface.

### Q-18 — a barrier landing on the cell the opponent already chose. **NEGOTIATE.**

Both peers choose from the same pre-turn board, so neither acts illegally, yet
the cop's barrier can land on the cell the thief already picked. Four readings
are all permitted by the specification. The harness applies
`BLOCKED_MOVE_BECOMES_STAY` **only so a demonstration terminates — it is not a
ruling.** Two peers applying different readings compute different boards from
identical action sequences, which surfaces as a failed audit that costs *both*
sides the match. This has to be agreed with each opponent team before play.

Also open and needing agreement with opponents: Q-2 (turn order), Q-5 (which
timeout governs a turn), Q-9 (capture under simultaneous movement), Q-17
(revealed actions make the belief map nearly redundant), Q-19 (GUI limitation).

## 5. Setup

```bash
git clone https://github.com/Nimerkasem/police-thief-p2p.git
```

```bash
cd police-thief-p2p
```

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

On macOS or Linux use `source .venv/bin/activate` instead.

```bash
python -m pip install -e ".[dev]"
```

### Running the tests

```bash
python -m pytest
```

Expect **1468 passed**. Anything less means the environment is wrong, not that
the code regressed — treat a failure here as a setup problem first.

### Reproducing the stall

```bash
python scripts/run_two_peers.py --game-id handoff-repro
```

Two independent peer processes launch and talk only to each other; the script
adjudicates nothing. It will fail at turn 6. That failure is the starting point,
not a surprise.

## 6. Branch to work on

```bash
git checkout -b partner/q20-stateless-http
```

Please work **only** on that branch and leave `main` alone. `main` is the last
state known to pass its whole suite, and it is what we fall back to if the
stateless experiment does not pan out.

## 7. Boundaries — please do not change these without verified evidence

The following are load-bearing for compliance, and a change made to work around
a transport symptom would disqualify the project rather than fix it:

- **commit-reveal semantics**
- **nonce timing** — the nonce stays secret until the end of the match (E-18)
- **replay semantics** — the verifier trusts neither peer's claims
- **message schemas**

"Verified evidence" means a failing test or a captured log that shows the
current behaviour is wrong — not that changing it makes the stall go away.

Two further standing rules from `CLAUDE.md`:

- The live peer must **never** access or display the opponent's true position
  (E-8, E-9). This is enforced structurally: `LocalState` has no attribute for
  it, so a leak surfaces as an `AttributeError`, never as a subtle bug.
- No Appendix F value may appear as a literal in game logic. The only module
  permitted those literals is `src/police_thief/config/policy.py`.

## 8. Files sent separately — not in this repository

- **`police_thief_p2p.pdf`** — the authoritative specification, and the single
  most important thing to have. It is the lecturer's copyrighted work ("all
  rights reserved", Dr. Yoram Segal, 2026), so it is **deliberately excluded
  from Git** and must be sent to you directly. Everything the project needs from
  it is extracted into `docs/` with page references, but the PDF governs where
  the docs and the PDF disagree.
  It is in Hebrew; raw `pypdf` extraction returns visually-reversed RTL text.
  `PDF page = book page + 16`.
- **`logs/`** — runtime audit logs from local runs. Excluded as generated
  output; regenerate them by running a game. Ask if you want a captured stall
  log rather than reproducing one.

## 9. Files that must never be shared, committed, or pushed

- `credentials.json`, `token.json` — Google OAuth material (E-39, E-40)
- `.env`, `.env.*`
- `*.pem`, `*.key`, anything under `secrets/`
- any API key, access token or refresh token, in any file or any commit message

All of these are in `.gitignore`, but the ignore file is a safety net, not the
rule. **A secret pushed once is compromised permanently** — it stays in the
history even after a later commit deletes it. If one is ever pushed, rotate the
credential in its provider console; do not try to erase it from the history.

Gmail integration has not been started, so no credential file should exist in
this project yet. If one appears, something is wrong.
