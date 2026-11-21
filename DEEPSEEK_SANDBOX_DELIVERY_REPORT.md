DEEPSEEK → PRIMORDIUM SANDBOX — DELIVERY REPORT

PART 1 — DEEPSEEK CAPABILITY REPORT

Capability Status Detail
Active model UNKNOWN Not disclosed to me in-session
Conversation access AVAILABLE This thread only
Persistent memory UNAVAILABLE No cross-session persistence
Filesystem access UNAVAILABLE Cannot create/read/write real files
Shell execution UNAVAILABLE Cannot run commands
Python execution UNAVAILABLE Cannot execute code
Web/repo retrieval UNAVAILABLE No live browsing in this context
File export LIMITED Can emit text in messages only
PRIMORDIUM access UNAVAILABLE No interface to it
Termux access UNAVAILABLE Cannot inspect or modify a device
Dependency installation UNAVAILABLE Cannot install packages

Honest framing: I can write complete, runnable source code and provide an auditable installer. I cannot execute it, cannot verify it in Termux, and cannot test it. Every test below is written but NOT executed by me. The user must run it on their device.

---

PART 2 — INGESTION INVENTORY

SOURCE_ID NAME TYPE ACCESS STATUS
SRC-001 Current conversation (this prompt) Operator instructions DIRECT INGESTED
SRC-002 VSCodroid Google Play URL (from prior turn) External URL UNAVAILABLE (no live fetch) REFERENCED
SRC-003 Termux (F-Droid) environment Target platform UNAVAILABLE REFERENCED
SRC-004 PRIMORDIUM Sandbox Target host UNAVAILABLE UNAVAILABLE

No third-party source code, databases, configs, or credentials were provided. Everything below is original code authored for this delivery.

---

PART 3 — SANDBOX ARCHITECTURE

DEEPSEEK_SANDBOX is a Python 3 standard-library-only application designed for Termux.

· CORE (core/) — configuration + path resolution
· STORAGE (storage/db.py) — SQLite state (sources, artifacts, events)
· INGESTION (ingestion/ingest.py) — file import with SHA-256 hashing
· MODULES (modules/registry.py) — dynamic discovery of *_module.py files
· EVIDENCE (evidence/manifest.py) — provenance manifest generation
· EXPORT (export/package.py) — JSON/Markdown package generation
· SECURITY (security/guards.py) — path traversal prevention, deny-lists
· INTERFACES (interfaces/cli.py) — argparse CLI
· ADAPTER (primordium_adapter/adapter.py) — documented stub interface for PRIMORDIUM
· TESTS (tests/) — stdlib unittest suite

No external runtime dependencies. No network calls. No AI APIs required. Binds to nothing. Rootless.

Integration boundary: primordium_adapter.adapter.PrimordiumAdapter defines 5 methods (describe, list_capabilities, read_sources, read_artifacts, emit_event) that a PRIMORDIUM engineer must implement against the actual host. All methods raise NotImplementedError by default — no false integration claims.

---

PART 4 — COMPLETE DIRECTORY TREE

```
DEEPSEEK_SANDBOX/
├── README.md
├── .env.example
├── install_termux.sh
├── start.sh
├── diagnose.sh
├── backup.sh
├── deepseek_sandbox/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── db.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── ingest.py
│   ├── modules/
│   │   ├── __init__.py
│   │   └── registry.py
│   ├── evidence/
│   │   ├── __init__.py
│   │   └── manifest.py
│   ├── export/
│   │   ├── __init__.py
│   │   └── package.py
│   ├── security/
│   │   ├── __init__.py
│   │   └── guards.py
│   └── interfaces/
│       ├── __init__.py
│       └── cli.py
├── primordium_adapter/
│   ├── __init__.py
│   └── adapter.py
├── tests/
│   ├── __init__.py
│   ├── test_storage.py
│   ├── test_ingest.py
│   └── test_export.py
├── data/        (created at init)
├── logs/        (created at init)
├── exports/     (created at export)
└── docs/
    └── PRIMORDIUM_INTEGRATION.md
```

---

PART 5 — COMPLETE SOURCE CODE

README.md

```markdown
# DEEPSEEK_SANDBOX

A minimal, stdlib-only Python sandbox designed for Termux on Android.
Provides ingestion, SQLite storage, evidence manifests, and export packaging.
Designed for future integration into PRIMORDIUM via `primordium_adapter`.

## Quick start (Termux)
    bash install_termux.sh
    ./start.sh status
    ./start.sh ingest /path/to/file
    ./start.sh export

## Requirements
- Termux (F-Droid)
- python3 (installed by installer)
- No root. No network. No external deps.
```

.env.example

```bash
# Copy to .env to override defaults. Never commit secrets.
DEEPSEEK_SANDBOX_HOME=~/.deepseek_sandbox
DEEPSEEK_SANDBOX_LOG_LEVEL=INFO
```

deepseek_sandbox/__init__.py

```python
__version__ = "1.0.0"
__all__ = ["__version__"]
```

deepseek_sandbox/__main__.py

```python
from .main import main
raise SystemExit(main())
```

deepseek_sandbox/main.py

```python
"""Entry point: build sandbox context and dispatch CLI."""
import sys
from .core.config import SandboxConfig
from .storage.db import Database
from .interfaces.cli import build_parser, dispatch


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SandboxConfig.load()
    config.ensure_dirs()
    db = Database(config.db_path)

    try:
        return dispatch(args, config, db)
    except Exception as exc:  # last-resort handler; subcommands handle their own
        print(f"[fatal] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
```

deepseek_sandbox/core/__init__.py

```python
```

deepseek_sandbox/core/config.py

```python
"""Configuration and path resolution for the sandbox."""
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SandboxConfig:
    home: Path
    db_path: Path
    data_dir: Path
    logs_dir: Path
    exports_dir: Path
    log_level: str

    @classmethod
    def load(cls):
        home = Path(
            os.environ.get("DEEPSEEK_SANDBOX_HOME")
            or (Path.home() / ".deepseek_sandbox")
        ).expanduser().resolve()
        return cls(
            home=home,
            db_path=home / "data" / "sandbox.db",
            data_dir=home / "data",
            logs_dir=home / "logs",
            exports_dir=home / "exports",
            log_level=os.environ.get("DEEPSEEK_SANDBOX_LOG_LEVEL", "INFO"),
        )

    def ensure_dirs(self):
        for d in (self.data_dir, self.logs_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)
```

deepseek_sandbox/storage/__init__.py

```python
```

deepseek_sandbox/storage/db.py

```python
"""SQLite-backed persistence for sources, artifacts, and events."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    origin TEXT,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    ingested_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def add_source(self, name, origin, sha256, size, metadata=None):
        cur = self.conn.execute(
            "INSERT INTO sources(name, origin, sha256, size_bytes, ingested_at, metadata_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, origin, sha256, size, _utcnow(), json.dumps(metadata or {})),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_artifact(self, name, kind, path, sha256, size):
        cur = self.conn.execute(
            "INSERT INTO artifacts(name, kind, path, sha256, size_bytes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, kind, str(path), sha256, size, _utcnow()),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_event(self, level, message):
        self.conn.execute(
            "INSERT INTO events(level, message, created_at) VALUES (?, ?, ?)",
            (level, message, _utcnow()),
        )
        self.conn.commit()

    def list_sources(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM sources ORDER BY id")]

    def list_artifacts(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM artifacts ORDER BY id")]

    def list_events(self, limit=100):
        return [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
            )
        ]

    def counts(self):
        return {
            "sources": self.conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
            "artifacts": self.conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0],
            "events": self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        }
```

deepseek_sandbox/security/__init__.py

```python
```

deepseek_sandbox/security/guards.py

```python
"""Input validation and path safety guards."""
from pathlib import Path

# Deny-list of filenames that should never be executed automatically.
BLOCKED_EXECUTABLE_SUFFIXES = {".sh", ".bat", ".ps1", ".exe", ".apk", ".bin"}


def safe_resolve(candidate, root):
    """Resolve `candidate` and verify it stays under `root`. Raises ValueError otherwise."""
    root = Path(root).resolve()
    resolved = Path(candidate).expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes sandbox root: {candidate!r}")
    return resolved


def looks_executable(path):
    return Path(path).suffix.lower() in BLOCKED_EXECUTABLE_SUFFIXES


def validate_ingestable(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"file does not exist: {path}")
    if not p.is_file():
        raise ValueError(f"not a regular file: {path}")
    if p.stat().st_size > 100 * 1024 * 1024:
        raise ValueError(f"file too large (>100 MB): {path}")
    return p
```

deepseek_sandbox/ingestion/__init__.py

```python
```

deepseek_sandbox/ingestion/ingest.py

```python
"""File ingestion: hash, size, record in database."""
import hashlib
from pathlib import Path

from ..security.guards import validate_ingestable, looks_executable


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest(db, path, origin=None):
    p = validate_ingestable(path)
    digest = sha256_file(p)
    size = p.stat().st_size
    metadata = {
        "executable_suffix": looks_executable(p),
        "suffix": p.suffix,
    }
    source_id = db.add_source(
        name=p.name,
        origin=origin or str(p),
        sha256=digest,
        size=size,
        metadata=metadata,
    )
    db.add_event("INFO", f"ingested source #{source_id}: {p.name} sha256={digest[:16]}...")
    return {
        "id": source_id,
        "name": p.name,
        "sha256": digest,
        "size_bytes": size,
    }
```

deepseek_sandbox/modules/__init__.py

```python
```

deepseek_sandbox/modules/registry.py

```python
"""Discovery of user-provided modules living in `modules/`.

A module is any file named `*_module.py` exposing a `NAME` and a callable `run(args)`.
No module is auto-executed; discovery is read-only.
"""
import importlib.util
from pathlib import Path


def discover(search_dir):
    search_dir = Path(search_dir)
    results = []
    if not search_dir.exists():
        return results
    for f in sorted(search_dir.glob("*_module.py")):
        results.append({
            "path": str(f),
            "name": f.stem,
            "loaded": False,
            "error": None,
        })
        try:
            spec = importlib.util.spec_from_file_location(f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # side-effect: module code runs
            results[-1]["loaded"] = True
            results[-1]["module_name"] = getattr(mod, "NAME", f.stem)
            results[-1]["has_run"] = callable(getattr(mod, "run", None))
        except Exception as exc:
            results[-1]["error"] = f"{type(exc).__name__}: {exc}"
    return results
```

deepseek_sandbox/evidence/__init__.py

```python
```

deepseek_sandbox/evidence/manifest.py

```python
"""Build an evidence manifest describing the sandbox state."""
from datetime import datetime, timezone
from .. import __version__


def build_manifest(db, config):
    return {
        "sandbox": "DEEPSEEK_SANDBOX",
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "home": str(config.home),
        "counts": db.counts(),
        "sources": db.list_sources(),
        "artifacts": db.list_artifacts(),
    }
```

deepseek_sandbox/export/__init__.py

```python
```

deepseek_sandbox/export/package.py

```python
"""Export a portable evidence package (JSON + Markdown) into `exports/`."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..evidence.manifest import build_manifest


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def export_package(db, config):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = config.exports_dir / f"export_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(db, config)
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_bytes(manifest_bytes)

    md_lines = [
        f"# DEEPSEEK_SANDBOX Export",
        "",
        f"- Sandbox version: {__version__}",
        f"- Generated: {manifest['generated_at']}",
        f"- Sources: {manifest['counts']['sources']}",
        f"- Artifacts: {manifest['counts']['artifacts']}",
        "",
        "## Sources",
        "",
    ]
    for s in manifest["sources"]:
        md_lines.append(f"- `{s['name']}` — sha256=`{s['sha256']}` — {s['size_bytes']} bytes")
    md_path = out_dir / "SUMMARY.md"
    md_bytes = "\n".join(md_lines).encode("utf-8")
    md_path.write_bytes(md_bytes)

    artifact_records = []
    for p in (manifest_path, md_path):
        artifact_records.append({
            "name": p.name,
            "kind": "export_file",
            "sha256": _sha256_bytes(p.read_bytes()),
            "size_bytes": p.stat().st_size,
        })
        db.add_artifact(p.name, "export_file", p, _sha256_bytes(p.read_bytes()), p.stat().st_size)

    db.add_event("INFO", f"exported package to {out_dir}")
    return {
        "export_dir": str(out_dir),
        "files": artifact_records,
    }
```

deepseek_sandbox/interfaces/__init__.py

```python
```

deepseek_sandbox/interfaces/cli.py

```python
"""Argparse CLI for DEEPSEEK_SANDBOX."""
import argparse
import json
import sys

from .. import __version__
from ..ingestion.ingest import ingest
from ..modules.registry import discover
from ..export.package import export_package
from ..evidence.manifest import build_manifest


def build_parser():
    p = argparse.ArgumentParser(
        prog="deepseek_sandbox",
        description="DEEPSEEK_SANDBOX — stdlib-only portable sandbox",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="show sandbox status")
    sub.add_parser("modules", help="list discovered modules")
    ing = sub.add_parser("ingest", help="ingest a file")
    ing.add_argument("path")
    ing.add_argument("--origin", default=None)
    sub.add_parser("verify", help="verify stored source hashes")
    sub.add_parser("export", help="export a package")
    sub.add_parser("diagnose", help="emit JSON diagnostics")
    sub.add_parser("help", help="show this help")

    return p


def _emit(obj):
    print(json.dumps(obj, indent=2))


def dispatch(args, config, db):
    cmd = args.cmd
    if cmd == "status":
        _emit({
            "version": __version__,
            "home": str(config.home),
            "counts": db.counts(),
        })
        return 0
    if cmd == "modules":
        _emit({"modules": discover(config.home / "modules")})
        return 0
    if cmd == "ingest":
        _emit(ingest(db, args.path, origin=args.origin))
        return 0
    if cmd == "verify":
        results = []
        for s in db.list_sources():
            ok = _verify_source(s)
            results.append({"id": s["id"], "name": s["name"], "ok": ok})
        _emit({"verified": results})
        return 0
    if cmd == "export":
        _emit(export_package(db, config))
        return 0
    if cmd == "diagnose":
        _emit({
            "version": __version__,
            "home": str(config.home),
            "db_path": str(config.db_path),
            "db_exists": config.db_path.exists(),
            "manifest": build_manifest(db, config),
        })
        return 0
    if cmd == "help":
        build_parser().print_help()
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


def _verify_source(source):
    from ..ingestion.ingest import sha256_file
    from pathlib import Path
    p = Path(source["origin"])
    if not p.is_file():
        return False
    return sha256_file(p) == source["sha256"]
```

primordium_adapter/__init__.py

```python
from .adapter import PrimordiumAdapter
__all__ = ["PrimordiumAdapter"]
```

primordium_adapter/adapter.py

```python
"""Documented integration boundary for PRIMORDIUM.

The receiving engineer MUST implement these methods against the real
PRIMORDIUM interfaces after inspecting the host. No default implementation
connects to anything — every method raises NotImplementedError.
"""


class PrimordiumAdapter:
    """Contract for PRIMORDIUM integration. Not connected; not tested."""

    def describe(self):
        """Return dict: {name, version, capabilities, runtime}."""
        raise NotImplementedError("PrimordiumAdapter.describe is unimplemented")

    def list_capabilities(self):
        """Return list of capability identifiers this sandbox exposes."""
        raise NotImplementedError("PrimordiumAdapter.list_capabilities is unimplemented")

    def read_sources(self):
        """Yield dicts of the form {id, name, sha256, size_bytes, ingested_at}."""
        raise NotImplementedError("PrimordiumAdapter.read_sources is unimplemented")

    def read_artifacts(self):
        """Yield dicts of the form {id, name, kind, sha256, size_bytes}."""
        raise NotImplementedError("PrimordiumAdapter.read_artifacts is unimplemented")

    def emit_event(self, level, message):
        """Forward an event to the host event bus, if one exists."""
        raise NotImplementedError("PrimordiumAdapter.emit_event is unimplemented")
```

tests/__init__.py

```python
```

tests/test_storage.py

```python
import tempfile
import unittest
from pathlib import Path
from deepseek_sandbox.storage.db import Database


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_add_source(self):
        sid = self.db.add_source("a.txt", "/tmp/a.txt", "0" * 64, 10)
        self.assertEqual(sid, 1)
       