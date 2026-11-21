# PRIMORDIUM

Policy-first, evidence-first agent platform scaffold.

PRIMORDIUM consolidates the PX-77 architecture into a modular, governed foundation for agent tooling. High-risk capabilities are denied by default, tool calls are policy-gated, and allowed activity is recorded in a cryptographically linked evidence ledger.

## Status

**Production readiness:** 61/100

Architecture direction is strong, while concrete adapters, hardening, observability, dependency locking, and test coverage remain in progress.

See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for the current architecture, risk assessment, and roadmap.

## Companion delivery report

The [DEEPSEEK_SANDBOX delivery report](DEEPSEEK_SANDBOX_DELIVERY_REPORT.md) documents a proposed standard-library-only Termux sandbox and its explicit `PrimordiumAdapter` integration boundary. The report is preserved as received; its code was not executed or represented as a completed integration.

## Safety principles

- Deny dangerous capabilities by default.
- Evaluate every tool call through policy before execution.
- Record allowed actions with auditable identifiers.
- Preserve cryptographic linkage in the evidence ledger.
- Prefer controlled browser access and accessibility-tree-first automation.
- Keep live individual OSINT targeting and unrestricted shell or JavaScript execution out of the default platform.

## Planned structure

```text
mcp/            thin stdio server and tool registry
core/           PolicyEngine and Orchestrator
evidence/       SHA3-512 EvidenceLedger
browser/        controlled asynchronous CDP client
osint/          provider interfaces
intelligence/   verification and reasoning components
security/       sandbox and capability-token components
tests/          policy, ledger, and adapter tests
```

## Roadmap

1. Fine-grained policy rules and human approval hooks
2. Evidence Ledger export and verification tools
3. Controlled CDP and Playwright accessibility adapter
4. Full pytest coverage, CI, sandboxing, and Docker packaging
