# pollen-data

A daily job that turns the Atmo France national pollen index into small static
JSON files for the Pollen iOS app, published on GitHub Pages.

- Source: **Atmo France / AASQA** national pollen index, per commune, today to
  D+2, under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
- Commune centres: [geo.api.gouv.fr](https://geo.api.gouv.fr/) (Licence Ouverte / Etalab 2.0).
- The published files under `v1/` are a derivative database and are themselves
  available under ODbL 1.0, with the attribution "Source : Atmo France / AASQA".
- The job's code is under the MIT licence in [LICENSE](LICENSE).

The file format is `v1/fr/manifest.json` plus `v1/fr/tiles/<lat>_<lon>.json`,
one file per whole degree of latitude and longitude.
