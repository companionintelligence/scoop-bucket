#!/usr/bin/env python3
"""Check the Scoop manifests in this bucket against their GitHub release assets.

For each root-level *.json manifest this checks that:

- the file parses as JSON and has a "version";
- each concrete download URL (the top-level "url", or "architecture".<arch>."url") that points
  at a GitHub release asset exists, and its SHA-256 equals the manifest "hash". GitHub's asset
  digest is used when present; otherwise the download is hashed;
- the manifest version appears in that URL, so a version bump cannot keep an old installer.

URLs on other hosts are reported as SKIP. Set GITHUB_TOKEN to avoid anonymous rate limits.
Exit status is 1 if any check fails. Standard library only.
"""
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_ASSET = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$")
USER_AGENT = "scoop-bucket-manifest-check"


def open_url(url, api=False):
    headers = {"User-Agent": USER_AGENT}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300)


def release_assets(owner, repo, tag, cache):
    key = (owner, repo, tag)
    if key not in cache:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{urllib.parse.quote(tag)}"
        with open_url(url, api=True) as resp:
            cache[key] = {asset["name"]: asset for asset in json.load(resp)["assets"]}
    return cache[key]


def sha256_of_download(url):
    digest = hashlib.sha256()
    with open_url(url) as resp:
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_blocks(manifest):
    """Yield (url, expected_hash) for every concrete download in the manifest."""
    blocks = [manifest] if "url" in manifest else []
    blocks += list((manifest.get("architecture") or {}).values())
    for block in blocks:
        urls = block["url"] if isinstance(block["url"], list) else [block["url"]]
        hashes = block.get("hash")
        hashes = hashes if isinstance(hashes, list) else [hashes] * len(urls)
        for url, expected in zip(urls, hashes):
            yield url, expected


def check_download(version, url, expected, cache):
    if not expected:
        return "FAIL", "no hash in the manifest"
    clean = url.split("#", 1)[0]
    match = RELEASE_ASSET.match(clean)
    if not match:
        return "SKIP", f"not a GitHub release asset: {clean}"
    owner, repo, tag, asset_name = match.groups()
    asset_name = urllib.parse.unquote(asset_name)
    if version not in tag and version not in asset_name:
        return "FAIL", f"version {version} does not appear in {clean}"
    asset = release_assets(owner, repo, tag, cache).get(asset_name)
    if asset is None:
        return "FAIL", f"asset {asset_name} is not in release {tag} of {owner}/{repo}"
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        actual, source = digest.split(":", 1)[1], "GitHub digest"
    else:
        actual, source = sha256_of_download(clean), "downloaded"
    if actual.lower() != expected.lower():
        return "FAIL", f"hash {expected} != {actual} ({source}) for {asset_name}"
    return "OK", f"{asset_name} matches ({source})"


def main():
    failures = 0
    cache = {}
    for path in sorted(ROOT.glob("*.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            print(f"FAIL {path.name}: invalid JSON: {err}")
            failures += 1
            continue
        version = manifest.get("version")
        if not isinstance(version, str) or not version:
            print(f"FAIL {path.name}: no version")
            failures += 1
            continue
        for url, expected in download_blocks(manifest):
            status, detail = check_download(version, url, expected, cache)
            failures += status == "FAIL"
            print(f"{status} {path.name} {version}: {detail}")
    print(f"{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
