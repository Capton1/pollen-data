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
    """Return every feature's properties, paging until a short page.

    Raise ValueError when the server reports a total that differs from the count read.
    """
    records: list[dict] = []
    start = 0
    while True:
        url = f"{WFS_URL}&count={page_size}&startIndex={start}"
        page = json.loads(fetch(url))
        features = page["features"]
        records.extend(f["properties"] for f in features)
        if len(features) < page_size:
            total = page.get("numberMatched", page.get("totalFeatures"))
            if isinstance(total, int) and total != len(records):
                raise ValueError(f"read {len(records)} records, server reports {total}")
            return records
        start += page_size
