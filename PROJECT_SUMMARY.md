# PRIMORDIUM — Project Summary

**Production readiness score:** 61/100

## Executive Summary

All prior PX-77 concepts (MCP registration, CDP client with async queue, Truth Protocol direction, Playwright/BrowserOS hybrid strategy, DeepSeek-style routing, and Cherry automation concepts) have been consolidated into a new modular repository named **PRIMORDIUM**.

The architecture has shifted from a monolithic MCP script to a **policy-first, evidence-first agent platform scaffold**. High-risk capabilities—including arbitrary shell execution, unrestricted JavaScript evaluation, and live individual OSINT targeting—are denied by default.

## Architecture

- `mcp/` — thin stdio server and tool registry
- `core/` — PolicyEngine and Orchestrator
- `evidence/` — SHA3-512 EvidenceLedger with chain hashing
- `browser/` — CDPClient with dangerous methods blocked by default
- `osint/`, `intelligence/`, `security/` — expansion stubs

## Security and Governance

- Policy Engine evaluates every tool call before execution.
- Evidence Ledger records every allowed call with cryptographic linkage.
- Capability matrix and global deny list are enforced.
- Every decision generates an `audit_id`.
- The ledger creates an immutable chain using `previous_hash` and SHA3-512.
- Filesystem mutation is capability-gated; `FS_WRITE` is not enabled by default.
- Live individual OSINT is not implemented; provider interfaces only.
- Arbitrary CDP evaluation is explicitly blocked.

## Current Gaps

- Concrete tool adapters
- Full test coverage
- Observability
- Dependency locking
- A real sandbox such as gVisor or Podman
- OAuth/RBAC tokens
- A complete human-in-the-loop UI

## Prioritized Roadmap

1. **P0** — Expand PolicyEngine with finer-grained rules and a human-approval hook.
2. **P1** — Complete the Evidence Ledger, including export and verification tools.
3. **P2** — Add a Playwright accessibility adapter and controlled CDP support.
4. **P3** — Add a test harness and Docker packaging.

## Planned Modules

1. `security/sandbox.py` plus capability tokens
2. `intelligence/verifier.py` for claim extraction and confidence
3. `browser/playwright_adapter.py` using accessibility-tree-first access
4. A full pytest suite and CI

## Implementation Roadmap

- **Week 1:** Policy and Ledger maturity plus basic tests
- **Weeks 2–3:** Browser adapters and verification layer
- **Week 4+:** Sandbox, CI/CD, and documentation hardening

> The original source scaffold referenced in the project summary was not available in the environment used to initialize this repository. This repository currently contains the project summary and will serve as the canonical home for the implementation as source modules are added.
