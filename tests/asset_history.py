"""Resolve superseded art only for the immutable historical repair contracts.

Current assets are tested independently in test_female_faces. We keep the old
neck/retouch assertions against their original bytes instead of rewriting old
manifests to claim a different approved portrait is the same image.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def male_release_asset(relative):
    relative=Path(relative)
    if relative.is_absolute():relative=relative.relative_to(ROOT)
    old=ROOT/'review/male-heads-full-library/before-assets'/relative
    return old if old.is_file() else ROOT/relative


def female_independent_asset(relative):
    """Exact b00712b assets for the historical independent neck repair tests.

    The user's subsequent female-base replacement has its own current-resource
    tests. It must not rewrite the old repair's image or tone reference.
    """
    relative = Path(relative)
    if relative.is_absolute(): relative = relative.relative_to(ROOT)
    old = ROOT/'review/female-base-replacement/before-assets'/relative
    return old if old.is_file() else male_release_asset(relative)


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
    return female_independent_asset(relative)


def approved_current_hash(relative, old_hash):
    """No broad exemption: only the explicit user-approved replacement list."""
    if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==old_hash:
        return old_hash
    appearance=ROOT/'review/appearance-catalog-20261102/manifest.json'
    if appearance.exists():
        accepted=json.loads(appearance.read_text())
        if accepted['runtime_before_sha256'].get(relative)==old_hash:
            return accepted['runtime_after_sha256'][relative]
    male=ROOT/'review/male-heads-full-library/integration-manifest.json'
    if male.exists():
        data=json.loads(male.read_text())
        if relative=='base_male.png':
            assert hashlib.sha256(male_release_asset(relative).read_bytes()).hexdigest()==old_hash
            return data['base_sha256']
        for e in data['files']:
            for key,h in [('output','sha256'),('mask','mask_sha256')]:
                if e[key]==relative:
                    assert hashlib.sha256(male_release_asset(relative).read_bytes()).hexdigest()==old_hash
                    return e[h]
    replacement = ROOT/'review/female-base-replacement/replacement-manifest.json'
    if replacement.exists():
        for e in json.loads(replacement.read_text())['files']:
            if e['path'] == relative:
                # The original general-audit hash may predate the eight-face
                # release; its provenance remains in the original manifests.
                history = json.loads((ROOT/'review/female-faces-integration/integration-manifest.json').read_text())
                assert old_hash in {e['before_sha256'],history['before_sha256'].get(relative)}
                saved = replacement.parent/e['before']
                assert hashlib.sha256(saved.read_bytes()).hexdigest() == e['before_sha256']
                return e['sha256']
    manifest = ROOT/'review/female-faces-integration/integration-manifest.json'
    if manifest.exists():
        data=json.loads(manifest.read_text())
        for e in data['files']:
            for key, field in [('output','sha256'),('mask','mask_sha256')]:
                if e[key]==relative:
                    assert data['before_sha256'][relative]==old_hash
                    return e[field]
    return old_hash


def accepted_catalog_snapshot(items):
    """Apply only the enumerated approved retirements and three female head URLs."""
    path=ROOT/'review/appearance-catalog-20261102/manifest.json'
    if not path.exists():return items
    receipt=json.loads(path.read_text());retired=set(receipt['excluded_ids']);heads={h['id']:h for h in receipt['female_heads']}
    result=[]
    for item in items:
        if item['id'] in retired:continue
        item=json.loads(json.dumps(item))
        if item['id'] in heads:
            h=heads[item['id']];item['genderVariants']['female']=h['path']+'?v='+h['sha256'][:8]
        result.append(item)
    return result


def active_female_heads(heads):
    receipt=json.loads((ROOT/'review/appearance-catalog-20261102/manifest.json').read_text())
    corrected={h['id']:h for h in receipt['female_heads']};result=[]
    for head in heads:
        if head['id'] in receipt['excluded_ids']:continue
        head=dict(head)
        if head['id'] in corrected:
            h=corrected[head['id']];head['output']=h['path'];head['sha256']=h['sha256']
        result.append(head)
    return result
