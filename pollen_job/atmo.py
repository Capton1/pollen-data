"""Download the Atmo France pollen index from the national WFS layer."""
import json
from collections.abc import Callable

WFS_URL = (
    "https://data.atmo-france.org/geoserver/ind_pol/ows?service=WFS&version=2.0.0"
    "&request=GetFeature&typeNames=ind_pol:ind_national_pol"
    "&outputFormat=application/json"
    "&propertyName=code_zone,lib_zone,date_ech,code_qual,code_aul,code_boul,"
    "code_oliv,code_gram,code_arm,code_ambr"
    "&sortBy=gml_id"
)


def fetch_atmo(fetch: Callable[[str], bytes], page_size: int = 10000) -> list[dict]:
    """Return every feature's properties, paging until a short page."""
    records: list[dict] = []
    start = 0
    while True:
        url = f"{WFS_URL}&count={page_size}&startIndex={start}"
        features = json.loads(fetch(url))["features"]
        records.extend(f["properties"] for f in features)
        if len(features) < page_size:
            return records
        start += page_size
