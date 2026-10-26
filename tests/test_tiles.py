import _path  # noqa: F401
import json
import unittest
from pathlib import Path

from pollen_job.communes import fetch_centres
from pollen_job.tiles import build_tiles, tile_key

FIX = Path(__file__).parent / "fixtures"


def load():
    records = [f["properties"] for f in json.loads((FIX / "atmo_page.json").read_text())["features"]]
    raw = (FIX / "communes.json").read_bytes()
    centres = fetch_centres(lambda url: raw)
    return records, centres


class TileTests(unittest.TestCase):
    def test_build_tiles_groups_by_floor_and_orders_days(self):
        records, centres = load()
        _, tiles = build_tiles(records, centres)
        self.assertEqual(sorted(tiles), ["44_1", "44_3", "46_2"])
        self.assertEqual(tiles["46_2"]["version"], 1)
        point = tiles["46_2"]["points"][0]
        self.assertEqual(
            (point["code"], point["name"], point["lat"], point["lon"]),
            ("03064", "Château-sur-Allier", 46.768, 2.974),
        )
        self.assertEqual(
            [d["date"] for d in point["days"]], ["2026-10-25", "2026-10-26", "2026-10-27"]
        )
        self.assertEqual(
            point["days"][0]["species"],
            {"alder": 1, "birch": 1, "olive": 1, "grasses": 1, "mugwort": 1, "ragweed": 1},
        )
        other = tiles["44_1"]["points"][0]
        self.assertEqual([d["level"] for d in other["days"]], [3, 4, 5])

    def test_zero_level_becomes_null(self):
        records, centres = load()
        _, tiles = build_tiles(records, centres)
        zero_day = tiles["46_2"]["points"][0]["days"][2]
        self.assertIsNone(zero_day["level"])
        self.assertTrue(all(v is None for v in zero_day["species"].values()))
        birch_zero = tiles["44_1"]["points"][0]["days"][0]
        self.assertEqual(birch_zero["level"], 3)
        self.assertIsNone(birch_zero["species"]["birch"])

    def test_days_are_the_issue_date_and_the_two_after(self):
        records, centres = load()
        extra = {**records[0], "date_ech": "2026-10-28"}
        _, tiles = build_tiles(records + [extra], centres)
        point = tiles["46_2"]["points"][0]
        self.assertEqual(
            [d["date"] for d in point["days"]], ["2026-10-25", "2026-10-26", "2026-10-27"]
        )

    def test_point_missing_an_issue_date_keeps_fewer_days(self):
        records, centres = load()
        records = [r for r in records if (r["code_zone"], r["date_ech"]) != ("03064", "2026-10-26")]
        _, tiles = build_tiles(records, centres)
        point = tiles["46_2"]["points"][0]
        self.assertEqual([d["date"] for d in point["days"]], ["2026-10-25", "2026-10-27"])

    def test_negative_longitude_key(self):
        self.assertEqual(tile_key(47.2, -1.55), "47_-2")
        self.assertEqual(tile_key(46.768, 2.974), "46_2")

    def test_unmatched_codes_fail_above_one_percent(self):
        records, centres = load()
        del centres["48001"]
        with self.assertRaises(ValueError) as ctx:
            build_tiles(records, centres)
        self.assertIn("1", str(ctx.exception))

    def test_unmatched_codes_tolerated_below_one_percent(self):
        records, centres = load()
        many = {"%05d" % i: ("c", 46.5, 2.5) for i in range(100, 300)}
        many_records = [{**records[0], "code_zone": code} for code in many]
        lost = {**records[0], "code_zone": "99999"}
        manifest, _ = build_tiles(records + many_records + [lost], {**centres, **many})
        self.assertEqual(manifest["points"], 203)

    def test_manifest_counts_points_and_lists_tiles(self):
        records, centres = load()
        manifest, _ = build_tiles(records, centres)
        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["issued"], "2026-10-25")
        self.assertEqual(manifest["source"], "Atmo France / AASQA")
        self.assertEqual(manifest["licence"], "ODbL-1.0")
        self.assertEqual(manifest["points"], 3)
        self.assertEqual(manifest["tiles"], ["44_1", "44_3", "46_2"])
        self.assertRegex(manifest["generated_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


if __name__ == "__main__":
    unittest.main()
