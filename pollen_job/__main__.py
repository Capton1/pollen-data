"""Download the Atmo index and write manifest.json and tiles/ under --out."""
import argparse
import json
import urllib.request
from pathlib import Path

from .atmo import fetch_atmo
from .communes import fetch_centres
from .tiles import build_tiles

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
TIMEOUT_SECONDS = 60


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    out = parser.parse_args().out

    manifest, tiles = build_tiles(fetch_atmo(fetch), fetch_centres(fetch))

    (out / "tiles").mkdir(parents=True, exist_ok=True)
    for key, tile in tiles.items():
        write_json(out / "tiles" / f"{key}.json", tile)
    write_json(out / "manifest.json", manifest)
    print(
        f"{manifest['points']} points, {len(tiles)} tiles, issued {manifest['issued']}"
    )


if __name__ == "__main__":
    main()
