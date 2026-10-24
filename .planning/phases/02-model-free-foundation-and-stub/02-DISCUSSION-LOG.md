# Phase 2: Model-Free Foundation and Stub - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-24
**Phase:** 02-model-free-foundation-and-stub
**Areas discussed:** Spike run policy (Stub gaps, Self-test UX and Sanitizer rules were offered; bokiko asked for a recommendation and accepted Claude's defaults for those three)

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Spike run policy | Isolation mode for S1, token budget, model id for the spikes | ✓ (on Claude's recommendation) |
| Stub gaps | Behaviour where the interface document and committed logs are silent | Claude's defaults |
| Self-test UX | Entry point, Python floor, `tests/harness/` layout | Claude's defaults |
| Sanitizer rules | Replacement tokens, deny sources, relation to gitleaks rules | Claude's defaults |

**User's choice:** "what do you think is better?" — Claude recommended discussing only the spike run policy because it needs facts only bokiko has; bokiko accepted.

---

## Spike run policy

### Login method on the spike machine

| Option | Description | Selected |
|--------|-------------|----------|
| Subscription login | claude.ai login; a scratch `CLAUDE_CONFIG_DIR` may hide the credentials | ✓ |
| API key | `ANTHROPIC_API_KEY`; strict isolation straightforward | |
| Both available | S1 probes both | |

### Isolation level the matrix claims

| Option | Description | Selected |
|--------|-------------|----------|
| Strict: scratch `CLAUDE_CONFIG_DIR` | User-level instructions, memory and skills provably absent | ✓ |
| Standard: `--setting-sources project,local` only | What the 2026-10-20 evidence used | |
| You decide after S1 | Let the spike result choose | |

### Token budget for both spikes

| Option | Description | Selected |
|--------|-------------|----------|
| Up to 5 USD total | 6 to 10 short headless calls, one retry each | ✓ |
| Up to 2 USD total | One call per probe, no retries | |
| Up to 15 USD total | Room for a longer stream-json fixture | |

### Model id for the spikes

| Option | Description | Selected |
|--------|-------------|----------|
| `claude-sonnet-5-5` | Cheapest capable model; stream shape identical across models | ✓ |
| `claude-opus-5-5` | Closer to a likely matrix baseline, higher cost | |
| Whatever Phase 3 pins | Defer to the matrix baseline | |

### Fallback if the scratch config dir loses the login

| Option | Description | Selected |
|--------|-------------|----------|
| Log in once into the scratch dir | bokiko runs `claude login` once with `CLAUDE_CONFIG_DIR` set to a persistent harness-owned dir outside the repo | ✓ |
| Fall back to standard isolation | Record the weaker claim in the flag table | |
| Stop and ask | S1 ends UNCONFIRMED, phase pauses | |

**User's choice:** the recommended option in every question.
**Notes:** none beyond the selections.

---

## Claude's Discretion

- Stub gaps: literal reading of `references/checkpoint-v1.md`, UNCONFIRMED marks for `handoff`,
  `note`, exit 5 and exit 6; labelled stub-internal switches for exits 5 and 6 only.
- Self-test UX: one bash 3.2 shim `tests/harness/selftest`, Python floor 3.9, flat modules.
- Sanitizer rules: angle-bracket tokens, runtime deny-list plus the local deny file, a Python
  regex leak gate cross-checked against the gitleaks identifier rules by a self-test.
- Internal module boundaries, test naming, spike ordering within the budget.

## Deferred Ideas

- Windows-style and `/root/` home-path coverage in the gitleaks rule (Phase 1 review leftover).
- Matrix-wide dry-run cost estimate (Phase 3 runner).
- Per-row structural comparison against committed evidence (Phase 4).
