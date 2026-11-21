import unittest
from datetime import datetime, timedelta, timezone

from primordium_adapter import (
    AdapterEvent,
    ArtifactRecord,
    Capability,
    EventLevel,
    ReferenceAdapter,
    RequestContext,
    SourceRecord,
)
from primordium_adapter.errors import AuthorizationError, InvalidRequest


class AdapterBoundaryTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.source = SourceRecord("src-1", "notes.txt", "a" * 64, 12, now, "local_file")
        self.adapter = ReferenceAdapter(sources=[self.source])
        self.ctx = RequestContext(
            request_id="req-1",
            audit_id="audit-1",
            caller="test",
            deadline=now + timedelta(minutes=1),
            approved_capabilities=frozenset(Capability),
        )

    def test_describe_is_read_only_and_versioned(self):
        info = self.adapter.describe()
        self.assertEqual(info.protocol_version, "1.0")
        self.assertTrue(info.read_only)

    def test_pagination_and_cursor_tamper_detection(self):
        page = self.adapter.read_sources(self.ctx, limit=1)
        self.assertEqual(page.items, (self.source,))
        self.assertIsNone(page.next_cursor)
        with self.assertRaises(InvalidRequest):
            self.adapter.read_sources(self.ctx, cursor="tampered", limit=1)

    def test_capability_is_required(self):
        denied = RequestContext("req-2", "audit-2", "test", self.ctx.deadline, frozenset())
        with self.assertRaises(AuthorizationError):
            self.adapter.read_sources(denied)

    def test_integrity_does_not_claim_unavailable_verification(self):
        result = self.adapter.verify_source(self.ctx, "src-1")
        self.assertIsNone(result.current_sha256)
        self.assertIsNone(result.verified)
        self.assertEqual(result.status, "unavailable")

    def test_events_require_matching_correlation(self):
        event = AdapterEvent("evt-1", "audit-1", "req-1", EventLevel.INFO, "test", self.ctx.deadline)
        self.assertEqual(self.adapter.emit_event(self.ctx, event), "evt-1")
        mismatch = AdapterEvent("evt-2", "other", "req-1", EventLevel.INFO, "test", self.ctx.deadline)
        with self.assertRaises(InvalidRequest):
            self.adapter.emit_event(self.ctx, mismatch)


if __name__ == "__main__":
    unittest.main()
