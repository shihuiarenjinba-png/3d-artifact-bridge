import unittest
from provisioner_gate import inspect


def pair():
    request = {
        "schema_version": "1.0", "request_id": "req-1",
        "product_type": "GAME_3D", "source_factory": "3d-game-factory",
        "repository_owner": "shihuiarenjinba-png", "repository_name": "example-game",
        "dry_run": True,
    }
    response = {"schema_version": "1.0", "request_id": "req-1",
                "product_type": "GAME_3D", "status": "DRY_RUN"}
    return request, response


class ProvisionerGateTest(unittest.TestCase):
    def test_dry_run_ok(self):
        self.assertEqual(inspect(*pair())["status"], "DRY_RUN_OK")

    def test_live_response_to_dry_run_is_blocked(self):
        a, b = pair()
        b["status"] = "CREATED"
        self.assertEqual(inspect(a, b)["status"], "BLOCKED")

    def test_cross_lane_is_blocked(self):
        a, b = pair()
        a["source_factory"] = "AI-Game-Factory"
        self.assertEqual(inspect(a, b)["status"], "BLOCKED")

    def test_invalid_repository_url_is_blocked(self):
        a, b = pair()
        a["dry_run"] = False
        b.update(status="CREATED", repository_url="https://github.com/other/repo",
                 repository_id=10, head_sha="a" * 40)
        self.assertEqual(inspect(a, b)["status"], "BLOCKED")

    def test_live_candidate_remains_unverified(self):
        a, b = pair()
        a["dry_run"] = False
        b.update(status="CREATED", repository_url="https://github.com/shihuiarenjinba-png/example-game",
                 repository_id=10, head_sha="a" * 40)
        x = inspect(a, b)
        self.assertEqual(x["status"], "REPOSITORY_REVIEW_CANDIDATE")
        self.assertFalse(x["live_verified"])

    def test_error_status_holds(self):
        a, b = pair()
        b["status"] = "HOLD"
        self.assertEqual(inspect(a, b)["status"], "HOLD")

    def test_unknown_status_blocks(self):
        a, b = pair()
        b["status"] = "PUBLISHED"
        self.assertEqual(inspect(a, b)["status"], "BLOCKED")

    def test_request_mismatch_blocks(self):
        a, b = pair()
        b["request_id"] = "another"
        self.assertEqual(inspect(a, b)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
