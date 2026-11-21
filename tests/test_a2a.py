import unittest

from primordium_adapter.a2a import (
    CardSchemaError,
    LegacyCardError,
    NegotiationError,
    ProtocolVersionError,
    build_handshake_envelope,
    build_send_message,
    detect_legacy_card,
    negotiate,
)


def card():
    return {
        "name": "QuantumForge",
        "description": "Test agent",
        "supportedInterfaces": [
            {"url": "https://example.test/a2a", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}
        ],
        "version": "1.0.0",
        "capabilities": {"streaming": True},
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [{"id": "feasibility-verdict", "name": "Verdict", "description": "Assess", "tags": ["quantum", "feasibility"]}],
    }


class A2ATests(unittest.TestCase):
    def test_negotiates_compatible_interface_and_skill(self):
        result = negotiate(card(), {"feasibility"})
        self.assertEqual(result["matched_skills"], ["feasibility-verdict"])
        self.assertEqual(result["protocol_binding"], "JSONRPC")

    def test_skips_unsupported_interface(self):
        value = card()
        value["supportedInterfaces"].insert(0, {"url": "https://old", "protocolBinding": "JSONRPC", "protocolVersion": "0.3"})
        self.assertEqual(negotiate(value, {"quantum"})["endpoint"], "https://example.test/a2a")

    def test_rejects_legacy_card_with_migration_message(self):
        with self.assertRaises(LegacyCardError):
            detect_legacy_card({"url": "https://old", "security": {}})

    def test_rejects_no_matching_protocol(self):
        value = card()
        value["supportedInterfaces"][0]["protocolVersion"] = "0.3"
        with self.assertRaises(ProtocolVersionError):
            negotiate(value, {"quantum"})

    def test_rejects_streaming_when_not_advertised(self):
        value = card()
        value["capabilities"]["streaming"] = False
        with self.assertRaises(NegotiationError):
            negotiate(value, {"quantum"}, streaming=True)

    def test_reports_schema_defects(self):
        with self.assertRaises(CardSchemaError):
            negotiate({"name": "bad"}, {"quantum"})

    def test_builds_json_rpc_message(self):
        envelope = build_handshake_envelope("urn:agent:test", ["quantum"])
        request = build_send_message(envelope, message_id="msg-1")
        self.assertEqual(request["method"], "SendMessage")
        self.assertEqual(request["params"]["message"]["messageId"], "msg-1")


if __name__ == "__main__":
    unittest.main()
