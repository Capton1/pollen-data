"""Download the Atmo index and publish v1/fr/manifest.json and tiles/ under --out."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .atmo import fetch_atmo
from .communes import fetch_centres
from .publish import publish
from .tiles import build_tiles

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
TIMEOUT_SECONDS = 60
MANIFEST_URL = "https://capton1.github.io/pollen-data/v1/fr/manifest.json"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def fetch_previous(fetch_url=fetch) -> dict | None:
    """The live manifest, or None when none is published or it cannot be read."""
    try:
        return json.loads(fetch_url(MANIFEST_URL))
    except urllib.error.HTTPError as error:
        if error.code != 404:
            print(f"previous manifest unreadable: {error}", file=sys.stderr)
    except (OSError, ValueError) as error:
        print(f"previous manifest unreadable: {error}", file=sys.stderr)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    out = parser.parse_args().out

    records = fetch_atmo(fetch)
    centres = fetch_centres(fetch)
    unmatched = len({r["code_zone"] for r in records} - set(centres))
    print(f"{unmatched} unmatched communes", file=sys.stderr)

    manifest, tiles = build_tiles(records, centres)
    publish(manifest, tiles, out, fetch_previous())
    print(
        f"{manifest['points']} points, {len(tiles)} tiles, issued {manifest['issued']}"
    )


if __name__ == "__main__":
    main()
