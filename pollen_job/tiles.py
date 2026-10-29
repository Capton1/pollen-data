"""Group the Atmo index into one-degree tiles following data contract v1."""
import math
from datetime import date, datetime, timedelta, timezone

VERSION = 1
MAX_UNMATCHED_SHARE = 0.01
SPECIES = {
    "alder": "code_aul",
    "birch": "code_boul",
    "olive": "code_oliv",
    "grasses": "code_gram",
    "mugwort": "code_arm",
    "ragweed": "code_ambr",
}
DAYS = 3


def expected_dates(issued: str) -> list[str]:
    """The `DAYS` consecutive dates starting at the issue date."""
    start = date.fromisoformat(issued)
    return [(start + timedelta(days=n)).isoformat() for n in range(DAYS)]


def tile_key(lat: float, lon: float) -> str:
    return f"{math.floor(lat)}_{math.floor(lon)}"


def _level(value) -> int | None:
    """Atmo reports 0 for unavailable; the contract uses null."""
    level = int(value)
    return level if 1 <= level <= 6 else None


def _day(record: dict) -> dict:
    return {
        "date": record["date_ech"],
        "level": _level(record["code_qual"]),
        "species": {name: _level(record[field]) for name, field in SPECIES.items()},
    }


def build_tiles(
    records: list[dict], centres: dict[str, tuple[str, float, float]]
) -> tuple[dict, dict[str, dict]]:
    """Return (manifest, tiles by key); raise ValueError if too many codes lack a centre."""
    by_code: dict[str, list[dict]] = {}
    for record in records:
        by_code.setdefault(record["code_zone"], []).append(record)

    unmatched = sorted(code for code in by_code if code not in centres)
    if len(unmatched) > MAX_UNMATCHED_SHARE * len(by_code):
        raise ValueError(
            f"{len(unmatched)} of {len(by_code)} Atmo codes have no commune centre "
            f"(first: {unmatched[:5]})"
        )

    issued = min(r["date_ech"] for r in records)
    wanted = expected_dates(issued)
    points_by_tile: dict[str, list[dict]] = {}
    for code in sorted(by_code):
        if code not in centres:
            continue
        name, lat, lon = centres[code]
        days = sorted(
            (r for r in by_code[code] if r["date_ech"] in wanted),
            key=lambda r: r["date_ech"],
        )
        point = {
            "code": code,
            "name": name,
            "lat": round(lat, 3),
            "lon": round(lon, 3),
            "days": [_day(r) for r in days],
        }
        points_by_tile.setdefault(tile_key(lat, lon), []).append(point)

    tiles = {
        key: {"version": VERSION, "issued": issued, "points": points}
        for key, points in sorted(points_by_tile.items())
    }
    manifest = {
        "version": VERSION,
        "issued": issued,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Atmo France / AASQA",
        "licence": "ODbL-1.0",
        "points": sum(len(p) for p in points_by_tile.values()),
        "tiles": list(tiles),
    }
    return manifest, tiles
