"""Validate a computed forecast and publish it into a fresh output directory."""
import json
import shutil
from datetime import date, timedelta
from pathlib import Path

MIN_POINTS = 30000
DAYS = 3
LAYOUT = Path("v1") / "fr"
# The app's privacy policy and support pages, published at the site root.
PAGES = Path(__file__).resolve().parent.parent / "pages"


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _validate(
    manifest: dict, tiles: dict[str, dict], previous: dict | None, min_points: int
) -> None:
    points = [p for tile in tiles.values() for p in tile["points"]]
    if len(points) < min_points:
        raise ValueError(f"{len(points)} points, expected at least {min_points}")
    if previous and manifest["issued"] < previous["issued"]:
        raise ValueError(
            f"issued {manifest['issued']} is older than published {previous['issued']}"
        )
    start = date.fromisoformat(manifest["issued"])
    wanted = [(start + timedelta(days=n)).isoformat() for n in range(DAYS)]
    for point in points:
        dates = [day["date"] for day in point["days"]]
        if len(dates) != DAYS:
            raise ValueError(f"point {point['code']} has {len(dates)} days, expected {DAYS}")
        if len(set(dates)) != DAYS:
            raise ValueError(f"point {point['code']} repeats a date: {dates}")
        if dates != wanted:
            raise ValueError(f"point {point['code']} dates {dates}, expected {wanted}")


def publish(
    manifest: dict,
    tiles: dict[str, dict],
    out: Path,
    previous: dict | None,
    min_points: int = MIN_POINTS,
) -> None:
    """Write the site under `out`, replacing it whole; raise before touching `out` on bad data."""
    _validate(manifest, tiles, previous, min_points)

    staging = out.with_suffix(".tmp")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        shutil.copytree(PAGES, staging)
        base = staging / LAYOUT
        (base / "tiles").mkdir(parents=True)
        for key, tile in tiles.items():
            _write_json(base / "tiles" / f"{key}.json", tile)
        _write_json(base / "manifest.json", manifest)
        if out.exists():
            shutil.rmtree(out)
        staging.rename(out)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
