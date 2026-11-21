# Archive import policy

The supplied `deepseek_data-2026-11-21.zip` is a private application export, not a source-code distribution. Its metadata describes 1,113 chat sessions and 16,107 messages. It contains account metadata, private conversations, personal identifiers, investigation material, and credential-like strings.

## What is integrated

Only privacy-safe engineering patterns were extracted:

- policy-first tool boundaries
- evidence and provenance tracking
- explicit capability declarations
- honest limitations and confidence labels
- typed handoff contracts
- A2A v1.0 card validation and negotiation
- safe Termux/stdlib-first design principles

The repository also contains the attached QuantumForge A2A document as a source reference, because it is an explicit technical design artifact rather than a raw private export.

## What is intentionally excluded

The raw ZIP, `user.json`, chat session bodies, personal identifiers, private case reports, API keys, bearer tokens, passwords, cookies, and unverified claims are not copied into this public repository. They must not be committed, placed in `.env` files, or embedded in source code. Any exposed credential should be revoked and rotated at its provider.

## Integration rule

A future import should produce sanitized, reviewable artifacts: source attribution, a short technical summary, executable tests, and an explicit security review. It should never publish the source export wholesale.
