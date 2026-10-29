import _path  # noqa: F401
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pollen_job import publish as publish_module
from pollen_job.publish import publish


def point(code, dates=("2026-10-25", "2026-10-26", "2026-10-27")):
    return {
        "code": code,
        "name": "x",
        "lat": 46.1,
        "lon": 2.1,
        "days": [{"date": d, "level": 1, "species": {}} for d in dates],
    }


def make(n, issued="2026-10-25", **kwargs):
    points = [point("%05d" % i, **kwargs) for i in range(n)]
    tile = {"version": 1, "issued": issued, "points": points}
    manifest = {"version": 1, "issued": issued, "points": n, "tiles": ["46_2"]}
    return manifest, {"46_2": tile}


class PublishTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name) / "site"

    def test_publish_writes_layout(self):
        manifest, tiles = make(3)
        publish(manifest, tiles, self.out, None, min_points=3)
        base = self.out / "v1" / "fr"
        self.assertEqual(json.loads((base / "manifest.json").read_text()), manifest)
        self.assertEqual(
            json.loads((base / "tiles" / "46_2.json").read_text()), tiles["46_2"]
        )
        self.assertFalse(self.out.with_suffix(".tmp").exists())

    def test_publish_refuses_too_few_points(self):
        manifest, tiles = make(29999)
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, None)
        self.assertFalse(self.out.exists())

    def test_publish_accepts_exactly_min_points(self):
        manifest, tiles = make(30000)
        publish(manifest, tiles, self.out, None)
        self.assertTrue((self.out / "v1" / "fr" / "manifest.json").exists())

    def test_publish_refuses_older_issue_than_previous(self):
        manifest, tiles = make(3, issued="2026-10-24")
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, {"issued": "2026-10-25"}, min_points=3)
        self.assertFalse(self.out.exists())

    def test_publish_accepts_same_issue_as_previous(self):
        manifest, tiles = make(3)
        publish(manifest, tiles, self.out, {"issued": "2026-10-25"}, min_points=3)
        self.assertTrue(self.out.exists())

    def test_publish_requires_three_days_per_point(self):
        manifest, tiles = make(3, dates=("2026-10-25", "2026-10-26"))
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, None, min_points=3)
        self.assertFalse(self.out.exists())

    def test_publish_refuses_duplicate_dates(self):
        manifest, tiles = make(3, dates=("2026-10-25", "2026-10-25", "2026-10-26"))
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, None, min_points=3)
        self.assertFalse(self.out.exists())

    def test_publish_refuses_dates_not_starting_at_issue(self):
        manifest, tiles = make(3, dates=("2026-10-26", "2026-10-27", "2026-10-28"))
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, None, min_points=3)
        self.assertFalse(self.out.exists())

    def test_publish_refuses_gap_in_dates(self):
        manifest, tiles = make(3, dates=("2026-10-25", "2026-10-26", "2026-10-28"))
        with self.assertRaises(ValueError):
            publish(manifest, tiles, self.out, None, min_points=3)

    def test_publish_writes_atomically(self):
        manifest, tiles = make(3)
        publish(manifest, tiles, self.out, None, min_points=3)
        (self.out / "stale.txt").write_text("old")
        seen = []
        real_rename = Path.rename

        def spy(path, target):
            seen.append(sorted(p.name for p in path.rglob("*")))
            return real_rename(path, target)

        with mock.patch.object(Path, "rename", spy):
            publish(manifest, tiles, self.out, None, min_points=3)
        self.assertIn("manifest.json", seen[-1] if seen else [])
        self.assertTrue(any("46_2.json" in s for s in seen))
        self.assertFalse((self.out / "stale.txt").exists())
        self.assertFalse(self.out.with_suffix(".tmp").exists())

    def test_failed_write_leaves_out_untouched(self):
        manifest, tiles = make(3)
        publish(manifest, tiles, self.out, None, min_points=3)
        before = (self.out / "v1" / "fr" / "manifest.json").read_text()
        with mock.patch.object(publish_module, "_write_json", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                publish(manifest, tiles, self.out, None, min_points=3)
        self.assertEqual((self.out / "v1" / "fr" / "manifest.json").read_text(), before)
        self.assertFalse(self.out.with_suffix(".tmp").exists())


if __name__ == "__main__":
    unittest.main()
