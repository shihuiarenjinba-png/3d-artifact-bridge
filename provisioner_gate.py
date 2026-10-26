"""Dry-run/live contract consistency gate between Factory and Provisioner.

This offline module never creates a GitHub repository or verifies GitHub ownership.
"""
import json
import re
from urllib.parse import urlsplit

LANES = {"APP": "AI-App-Factory", "GAME": "AI-Game-Factory", "GAME_3D": "3d-game-factory"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REPO = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$")
SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def _match(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def inspect(request, response):
    errors = []
    if not isinstance(request, dict) or not isinstance(response, dict):
        return {"status": "BLOCKED", "errors": ["objects required"]}
    if request.get("schema_version") != "1.0" or response.get("schema_version") != "1.0":
        errors.append("schema version mismatch")
    typ = request.get("product_type")
    if typ not in LANES or request.get("source_factory") != LANES.get(typ):
        errors.append("source factory mismatch")
    if not _match(ID, request.get("request_id")):
        errors.append("invalid request id")
    repo = str(request.get("repository_owner", "")) + "/" + str(request.get("repository_name", ""))
    if not _match(REPO, repo):
        errors.append("invalid repository")
    if type(request.get("dry_run")) is not bool:
        errors.append("explicit dry_run boolean required")
    if response.get("request_id") != request.get("request_id"):
        errors.append("response request id mismatch")
    if response.get("product_type") != typ:
        errors.append("response product type mismatch")
    status = response.get("status")
    if status not in ("CREATED", "EXISTING_VERIFIED", "DRY_RUN", "HOLD",
                      "CONFLICT", "FAILED", "RETRYABLE_FAILURE"):
        errors.append("unknown status")
    if request.get("dry_run") is True and status in ("CREATED", "EXISTING_VERIFIED"):
        errors.append("live creation claimed for dry_run request")
    if status in ("CREATED", "EXISTING_VERIFIED"):
        url = response.get("repository_url")
        expected = f"https://github.com/{repo}"
        if not isinstance(url, str) or url.rstrip("/") != expected:
            errors.append("repository URL mismatch")
        if not _match(SHA, response.get("head_sha")):
            errors.append("missing repository head SHA")
        if not isinstance(response.get("repository_id"), (str, int)) or not str(response["repository_id"]).isdigit():
            errors.append("invalid repository id")
    if errors:
        return {"status": "BLOCKED", "errors": errors, "live_verified": False}
    if status == "DRY_RUN":
        return {"status": "DRY_RUN_OK", "errors": [], "live_verified": False}
    if status in ("CREATED", "EXISTING_VERIFIED"):
        return {"status": "REPOSITORY_REVIEW_CANDIDATE", "errors": [], "live_verified": False,
                "next_stage": "VERIFY_GITHUB_REPO_AND_TEMPLATE"}
    return {"status": "HOLD", "errors": [f"provisioner response: {status}"],
            "live_verified": False}
