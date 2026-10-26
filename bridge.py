"""Offline, fail-closed validation of three-factory handoff manifests.

Does not download artifacts, attest evidence, call GitHub, or submit to Store.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

LANES = {
    "APP": "AI-App-Factory",
    "GAME": "AI-Game-Factory",
    "GAME_3D": "3d-game-factory",
}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REPO = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$")
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PACKAGES = {
    "APP": {"MSIX"},
    "GAME": {"MSIX", "MSIXVC"},
    "GAME_3D": {"MSIX", "MSIXVC"},
}


def _secure_uri(uri):
    if not isinstance(uri, str):
        return False
    try:
        x = urlsplit(uri)
        return (
            x.scheme == "https" and bool(x.hostname)
            and not x.username and not x.password and not x.fragment
        )
    except ValueError:
        return False


def inspect(manifest):
    """Return a review-only result. Never equate a declared PASS with proof."""
    errors = []
    if not isinstance(manifest, dict):
        return {"status": "BLOCKED", "errors": ["manifest must be an object"], "next_stage": None}
    if manifest.get("schema_version") != "1.0":
        errors.append("unsupported schema_version")
    typ = manifest.get("product_type")
    if typ not in LANES:
        errors.append("unsupported product_type")
    elif manifest.get("source_factory") != LANES[typ]:
        errors.append("source_factory does not match product_type")
    if not isinstance(manifest.get("request_id"), str) or not ID.fullmatch(manifest["request_id"]):
        errors.append("invalid request_id")
    repo = manifest.get("repository_full_name")
    if not isinstance(repo, str) or not REPO.fullmatch(repo):
        errors.append("invalid repository_full_name")
    if not isinstance(manifest.get("source_sha"), str) or not HEX40.fullmatch(manifest["source_sha"]):
        errors.append("invalid source_sha")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("artifact object missing")
    else:
        if not _secure_uri(artifact.get("uri")):
            errors.append("artifact uri must be HTTPS without embedded credentials")
        if not isinstance(artifact.get("sha256"), str) or not HEX64.fullmatch(artifact["sha256"]):
            errors.append("artifact SHA-256 missing or malformed")
        if type(artifact.get("bytes")) is not int or artifact["bytes"] <= 0:
            errors.append("artifact bytes must be a positive integer")
        if typ in PACKAGES and artifact.get("package_kind") not in PACKAGES[typ]:
            errors.append("package_kind not valid for product_type")
    qa = manifest.get("qa")
    if not isinstance(qa, dict):
        errors.append("qa object missing")
    else:
        for key in ("build", "automated", "human", "licensing"):
            if qa.get(key) not in ("PASS", "FAIL", "HOLD"):
                errors.append(f"invalid qa.{key}")
        if qa.get("human") == "PASS" and (
            not isinstance(qa.get("approval_reference"), str)
            or not ID.fullmatch(qa["approval_reference"])
        ):
            errors.append("human approval_reference required")
    if errors:
        return {"status": "BLOCKED", "errors": errors, "next_stage": None}

    fingerprint = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    all_pass = all(qa[key] == "PASS" for key in ("build", "automated", "human", "licensing"))
    # Offline evidence is UNVERIFIED. Even a complete manifest cannot cause a Store action.
    status = "REVIEW_CANDIDATE" if all_pass else "HOLD"
    return {
        "status": status,
        "errors": [],
        "request_id": manifest["request_id"],
        "product_type": typ,
        "fingerprint": fingerprint,
        "evidence_verified": False,
        "store_submission_authorized": False,
        "next_stage": "WINDOWS_EVIDENCE_REVIEW" if all_pass else None,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        result = {"status": "BLOCKED", "errors": [f"unable to load JSON: {type(exc).__name__}"], "next_stage": None}
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "REVIEW_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
