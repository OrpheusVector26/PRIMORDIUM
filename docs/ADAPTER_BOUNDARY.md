# PRIMORDIUM Adapter Boundary

The adapter is a narrow, read-mostly protocol between a sandbox and PRIMORDIUM. The reference implementation in `primordium_adapter/reference.py` is deliberately in-memory and does not access the filesystem, execute code, use a shell, or make network requests.

## Contract

- `describe()` returns versioned metadata and capabilities.
- `read_sources()` and `read_artifacts()` require an approved `RequestContext` capability and return bounded pages with signed opaque cursors.
- `verify_source()` distinguishes recorded metadata from current-content verification. The reference adapter reports `unavailable` rather than claiming integrity it cannot check.
- `emit_event()` accepts structured events and requires matching `request_id` and `audit_id` correlation.

## Authorization

Capability discovery is not authorization. The PRIMORDIUM orchestrator must create the `RequestContext` after policy evaluation. The adapter performs a second defensive check for capability approval and request deadline.

## Data handling

Records use opaque IDs and an `origin_class`; raw filesystem paths are intentionally not part of the public response model. Any future path disclosure requires a separate, explicitly governed diagnostic capability.

## Compatibility

The protocol version is currently `1.0`. Changes to method semantics or required fields require a protocol-version change and contract-test update. Stable adapter exceptions live in `primordium_adapter/errors.py`.

## Security boundary

Module discovery must not import untrusted `*_module.py` files merely to list them. If module metadata is needed, use static AST inspection. Any future module execution must be a separate capability with explicit policy approval and sandboxing; it is never implied by discovery.

## Running tests

```bash
python -m unittest discover -s tests -v
```
