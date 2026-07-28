# Distributed Cops-and-Robbers over a Peer-to-Peer Network

Academic final project — *Orchestration of AI Agents*, Department of Computer
Science, University of Haifa, 2026.

Two autonomous, **symmetric** agents — a cop and a thief — race on a discrete
grid with **no central referee and no shared game-state server**. Neither agent
can see the other's true position. Each builds a probabilistic belief about its
opponent from two sources: a decaying scent trail that cannot be forged, and a
verbal hint that may well be a lie. Integrity between two mutually distrustful
peers is guaranteed not by trust but by mathematics — commit-reveal over
SHA-256, audited after the fact.

> **Status: documentation and analysis phase.** No application code exists yet.
> This repository currently contains the requirements extraction, parameter
> tables, architecture, protocol design, test map and phased plan. Implementation
> begins at Phase 0 of [TASKS.md](TASKS.md).

---

## Authoritative source

`police_thief_p2p.pdf` (book version 3.0.0, Dr. Yoram Segal) is the sole
specification. Everything in `docs/` is an extraction from it, with page
references throughout.

Two conventions worth knowing before reading the PDF yourself:

- **`PDF page = book page + 16`.** The printed page numbers in the footer and
  your PDF viewer's page counter differ by a constant 16. All references in this
  repository use the **viewer's** number.
- **The default is not binding.** PDF p. 4 states the founding principle: a rule
  is not binding unless it is explicitly written as a rule. Every illustration,
  diagram, code excerpt and scenario in the book is a mode of demonstration, not
  a requirement.

The single source of truth for every quantitative value is the **Mandatory
Parameter Table in Appendix F** (PDF pp. 151–159). Numeric values never appear
as hard numbers in the book's body text — only as code-names in square brackets
such as `[grid_size]`.

---

## Documentation

Read in this order.

| Document | What it holds |
|---|---|
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | All 55 Appendix E rules plus chapter obligations, organised by subsystem, classified MANDATORY / RECOMMENDED / EXAMPLE, with PDF pages and the stated sanction for each |
| [docs/PARAMETERS.md](docs/PARAMETERS.md) | Every Appendix F parameter — name, value, type, meaning, status, and which config file owns it |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Minimum architecture, layer separation, process model for one peer, how two identical peers take different roles |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | The eight-tool FastMCP interface, message schemas, config-hash exchange, turn ordering, commit-reveal sequencing, timeout/duplicate/invalid-sequence behaviour, completion signalling |
| [docs/ACCEPTANCE_TESTS.md](docs/ACCEPTANCE_TESTS.md) | Every mandatory rule mapped to an executable test or a deterministic manual procedure |
| [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | Contradictions and ambiguities found in the PDF, with status and resolution |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Decisions taken, with reasoning, cost and reversal conditions |
| [docs/COMPLIANCE_AUDIT.md](docs/COMPLIANCE_AUDIT.md) | Per-requirement COVERED / MISSING / AMBIGUOUS / NOT APPLICABLE status |
| [TASKS.md](TASKS.md) | Dependency-ordered phases; mandatory work separated from optional enhancements |
| [CLAUDE.md](CLAUDE.md) | Standing instructions for future development sessions |

---

## The shape of the system

```
        PEER A (cop)                                  PEER B (thief)
   ┌───────────────────┐                        ┌───────────────────┐
   │   Orchestrator    │                        │   Orchestrator    │
   │  (single gateway) │                        │  (single gateway) │
   ├───────────────────┤                        ├───────────────────┤
   │ state machine     │                        │ state machine     │
   │ strategy (Python) │                        │ strategy (Python) │
   │ local truth only  │                        │ local truth only  │
   │ belief map        │                        │ belief map        │
   │ JSONL audit log   │                        │ JSONL audit log   │
   ├───────────────────┤                        ├───────────────────┤
   │ FastMCP  server   │◄──── public internet ─►│ FastMCP  server   │
   │          client   │      (NAT traversal    │          client   │
   └─────────┬─────────┘       via tunnel)      └─────────┬─────────┘
             │                                            │
        Live GUI                                     Live GUI
     (belief heatmap,                             (belief heatmap,
      turn banner —                                turn banner —
      never the truth)                             never the truth)

                    ── after the match only ──
                     ┌────────────────────┐
                     │  Replay verifier   │   the only omniscient
                     │  Verified OK /     │   component; runs offline
                     │  TAMPERED          │   over the sealed logs
                     └────────────────────┘
```

Every peer is **simultaneously a server and a client**. There is no strong side
and no weak side. The same program runs both roles; the role changes only the
start cell, whether barrier placement is permitted, which side of the belief the
agent models, and how it scores.

---

## Design commitments

Five properties the implementation is built to guarantee structurally rather
than by convention:

**The live agent is blind.** The live-state object has no attribute for the
opponent's position — not `None`, not `Optional`. A leak surfaces as an
`AttributeError` in a unit test rather than as a subtle bug that survives to the
league. Only the replay verifier, running after the match over the sealed logs,
ever reconstructs the full global state.

**Moves are decided in Python, always.** The language model touches only the
verbal layer: composing a hint, and classifying an opponent's hint as truthful
or deceptive. It never validates a move, verifies a hash, or determines a
winner. The default verbal provider is a zero-token template, so the entire
series can be played with no model at all and the competition rests on the
movement algorithm.

**Numbers live in configuration.** No value from Appendix F appears as a literal
in game logic. A validator rejects any configuration that lowers a `MINIMUM`
value or alters a `FIXED` one, and both peers exchange a canonical hash of the
shared config before play — a mismatch means refusing to play, not playing
badly.

**Commitments bind.** Each step is sealed as a canonical JSON record hashed with
SHA-256 before anything is revealed; the nonce stays secret until the end of the
match. A single altered character anywhere in a log is caught at audit, and the
match is void.

**Everything mandatory is verifiable.** Each of the 55 rules maps to a pytest
test or a deterministic manual procedure, named by rule ID so coverage can be
checked by grep.

---

## Technology

Python 3.12 · FastMCP · asyncio · pytest · SHA-256 · JSON Lines audit logs ·
JSON (shared signed config) + TOML (private per-peer config) · Tkinter for the
live GUI and replay viewer · Gmail API with `gmail.send` scope only, added last.

Deliberately absent: Docker, databases, cloud infrastructure, web frameworks,
paid LLM APIs, and reinforcement learning. The specification is explicit that
the course did not teach RL and that a fully strong agent can be built from
heuristics alone; it is one optional tool among three equal-standing routes, and
out of scope until every mandatory requirement is complete and verified.

---

## Running it

Not yet applicable — no application code exists. Once Phase 2 lands:

```bash
python -m police_thief peer --role police
```

```bash
python -m police_thief peer --role thief
```

```bash
python -m police_thief replay --log matches/<game_id>/log_<game_id>_g01.json
```

The two peers **must** run as two entirely separate processes under separate
configuration directories. Sharing memory or variables between them breaks the
zero-trust model and disqualifies the solution even if the game works
technically.

---

## Note on this README

At submission time this file becomes the **academic report** and must carry six
mandatory components: the chosen Dec-POMDP model, the FastMCP orchestration
dilemmas, the strategies implemented, learning curves (only if RL was used),
screenshots of the live belief map and of the replay viewer showing
`Verified OK`, and a link to the companion repository. It must also document
every contradiction identified in the specification along with the reading
chosen and the reason — the specification grants that freedom explicitly,
provided the choice is stated.

The checklist lives in [docs/ACCEPTANCE_TESTS.md](docs/ACCEPTANCE_TESTS.md) §7;
the contradictions are already catalogued in
[docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md).
