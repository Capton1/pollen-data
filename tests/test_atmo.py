import _path  # noqa: F401
import json
import unittest
from urllib.parse import parse_qs, urlparse

from pollen_job.atmo import fetch_atmo


def page(n):
    return json.dumps(
        {"features": [{"properties": {"code_zone": "%05d" % i}} for i in range(n)]}
    ).encode()


class FetchAtmoTests(unittest.TestCase):
    def test_fetch_atmo_pages_until_short_page(self):
        sizes = {0: 10000, 10000: 10000, 20000: 3}
        starts = []

        def fetch(url):
            start = int(parse_qs(urlparse(url).query)["startIndex"][0])
            starts.append(start)
            return page(sizes[start])

        records = fetch_atmo(fetch)
        self.assertEqual(len(records), 20003)
        self.assertEqual(starts, [0, 10000, 20000])
        self.assertEqual(records[0], {"code_zone": "00000"})


if __name__ == "__main__":
    unittest.main()
