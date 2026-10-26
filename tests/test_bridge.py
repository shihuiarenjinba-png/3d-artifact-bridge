import unittest
from copy import deepcopy
from bridge import inspect


def sample(kind="GAME_3D"):
    return {
        "schema_version": "1.0", "request_id": "case-001",
        "product_type": kind,
        "source_factory": {"APP": "AI-App-Factory", "GAME": "AI-Game-Factory", "GAME_3D": "3d-game-factory"}[kind],
        "repository_full_name": "shihuiarenjinba-png/example-project",
        "source_sha": "a" * 40,
        "artifact": {"uri": "https://example.org/store/game.msix", "sha256": "b" * 64,
                     "bytes": 2048, "package_kind": "MSIX"},
        "qa": {"build": "PASS", "automated": "PASS", "human": "PASS",
               "licensing": "PASS", "approval_reference": "review-001"},
    }


class BridgeTest(unittest.TestCase):
    def test_all_lanes_are_only_review_candidates(self):
        for kind in ("APP", "GAME", "GAME_3D"):
            with self.subTest(kind=kind):
                x = inspect(sample(kind))
                self.assertEqual(x["status"], "REVIEW_CANDIDATE")
                self.assertFalse(x["evidence_verified"])
                self.assertFalse(x["store_submission_authorized"])

    def test_cross_lane_cannot_be_mixed(self):
        x = sample()
        x["source_factory"] = "AI-App-Factory"
        self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_invalid_checksum_blocks(self):
        x = sample()
        x["artifact"]["sha256"] = "invalid"
        self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_http_and_credentials_block(self):
        for uri in ("http://example.com/pkg", "https://u:p@example.org/pkg"):
            x = sample()
            x["artifact"]["uri"] = uri
            self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_human_hold_prevents_review_candidate(self):
        x = sample()
        x["qa"]["human"] = "HOLD"
        self.assertEqual(inspect(x)["status"], "HOLD")

    def test_human_pass_requires_approval_reference(self):
        x = sample()
        x["qa"].pop("approval_reference")
        self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_bool_byte_count_fails(self):
        x = sample()
        x["artifact"]["bytes"] = True
        self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_missing_source_sha_fails(self):
        x = sample()
        x.pop("source_sha")
        self.assertEqual(inspect(x)["status"], "BLOCKED")

    def test_deterministic_fingerprint(self):
        a = sample()
        b = deepcopy(a)
        self.assertEqual(inspect(a)["fingerprint"], inspect(b)["fingerprint"])

    def test_invalid_package_fails(self):
        x = sample("APP")
        x["artifact"]["package_kind"] = "WIN64_TEST"
        self.assertEqual(inspect(x)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
