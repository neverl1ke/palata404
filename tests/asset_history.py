"""Resolve superseded art only for the immutable historical repair contracts.

Current assets are tested independently in test_female_faces. We keep the old
neck/retouch assertions against their original bytes instead of rewriting old
manifests to claim a different approved portrait is the same image.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def historical_asset(relative):
    relative = Path(relative)
    if relative.is_absolute(): relative = relative.relative_to(ROOT)
    manifest = ROOT/'review/female-faces-integration/integration-manifest.json'
    if manifest.exists():
        data = json.loads(manifest.read_text())
        changed = {e[k] for e in data['files'] for k in ['output','mask']}
        if str(relative) in changed and str(relative) in data['before_sha256']:
            old = manifest.parent/'before/assets'/relative
            assert hashlib.sha256(old.read_bytes()).hexdigest() == data['before_sha256'][str(relative)]
            return old
    return ROOT/relative


def approved_current_hash(relative, old_hash):
    """No broad exemption: only the explicit user-approved replacement list."""
    manifest = ROOT/'review/female-faces-integration/integration-manifest.json'
    if manifest.exists():
        data=json.loads(manifest.read_text())
        for e in data['files']:
            for key, field in [('output','sha256'),('mask','mask_sha256')]:
                if e[key]==relative:
                    assert data['before_sha256'][relative]==old_hash
                    return e[field]
    return old_hash
