"""Falsifier for the kecksburg-ufo-incide-ab793e permalink collision cure.

Before the cure, two truncated permalinks were each claimed by two level-3
``*_index.md`` documents, shadowing one index per family. The cure keeps
the live winner at each shared route and gives each shadowed index a
unique ``-<index title>`` suffixed permalink.
"""
import io
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
PERMALINK = re.compile(r"^permalink:\s*[\"']?([^\s\"'#]+)[\"']?\s*$", re.M)


def page_permalinks():
    out = {}
    for p in PAGES.glob("*.md"):
        m = FRONT_MATTER.match(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        pm = PERMALINK.search(m.group(1))
        if pm:
            out[p.name] = pm.group(1)
    return out


SHARED_SLUGS = {
    "/kecksburg-ufo-incide-ab793e-acorn/",
    "/kecksburg-ufo-incide-ab793e-great/",
}

EXPECTED_CURED = {
    "/kecksburg-ufo-incide-ab793e-acorn-acorn-monument/",
    "/kecksburg-ufo-incide-ab793e-great-fireball-timeline/",
}


class TestPermalinkUniqueness(unittest.TestCase):
    def test_all_permalinks_unique(self):
        pls = page_permalinks()
        counts = Counter(pls.values())
        dups = {k: v for k, v in counts.items() if v > 1}
        owners = {k: sorted(n for n, v in pls.items() if v == k) for k in dups}
        self.assertEqual({}, owners)

    def test_shared_family_slugs_claimed_by_one_document(self):
        pls = page_permalinks()
        for slug in SHARED_SLUGS:
            owners = sorted(n for n, v in pls.items() if v == slug)
            self.assertEqual(1, len(owners), f"{slug} claimed by {owners}")

    def test_expected_cured_index_routes_exist(self):
        pls = set(page_permalinks().values())
        self.assertEqual(set(), EXPECTED_CURED - pls)

    def test_manifest_canonical_urls_for_cured_indexes(self):
        manifest = json.loads(io.open(ROOT / "phoenix-manifest.json", encoding="utf-8").read())
        cured = {
            "kecksburg-ufo-incide-ab793e-acorn-monument-origi-93d1e8:index": "/kecksburg-ufo-incide-ab793e-acorn-acorn-monument/",
            "kecksburg-ufo-incide-ab793e-great-lakes-fireball-100930:index": "/kecksburg-ufo-incide-ab793e-great-fireball-timeline/",
        }
        bad = []
        for page in manifest.get("pages", []):
            lid = page.get("logical_id")
            if lid in cured:
                route = "/" + (page.get("canonical_url") or "").split("/", 3)[-1].split("/", 1)[-1]
                if route != cured[lid]:
                    bad.append((lid, route, cured[lid]))
        self.assertEqual([], bad)

    def test_index_bodies_link_only_existing_routes(self):
        existing = set(page_permalinks().values())
        dangling = []
        for p in PAGES.glob("*_index.md"):
            for m in re.finditer(r"\{\{\s*'(/[^']*?)'\s*\|\s*relative_url", p.read_text(encoding="utf-8", errors="replace")):
                if m.group(1) not in existing:
                    dangling.append((p.name, m.group(1)))
        self.assertEqual([], dangling)


if __name__ == "__main__":
    unittest.main()
