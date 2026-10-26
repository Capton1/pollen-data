"""Commune centres from geo.api.gouv.fr."""
import json
from collections.abc import Callable

COMMUNES_URL = "https://geo.api.gouv.fr/communes?fields=code,nom,centre&format=json"
URLS = (COMMUNES_URL, COMMUNES_URL + "&type=arrondissement-municipal")


def fetch_centres(fetch: Callable[[str], bytes]) -> dict[str, tuple[str, float, float]]:
    """Map INSEE code to (name, latitude, longitude), arrondissements included."""
    centres: dict[str, tuple[str, float, float]] = {}
    for url in URLS:
        for commune in json.loads(fetch(url)):
            centre = commune.get("centre")
            if not centre:
                continue
            lon, lat = centre["coordinates"]
            centres[commune["code"]] = (commune["nom"], lat, lon)
    return centres
