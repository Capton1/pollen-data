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

## App pages

`pages/` holds the app's privacy policy and support pages, in English and French.
Each publish copies them next to the data, at
<https://capton1.github.io/pollen-data/privacy/> and
<https://capton1.github.io/pollen-data/support/>. The app's About screen and its
App Store Connect record link to both, so a change to what the app sends or
stores changes the privacy policy in the same release.

## Schedule and hosting

- `publish.yml` runs daily at 11:30 and 13:30 UTC. Atmo publishes the new
  index around 11:00 UTC; the second run catches a late publication and
  accepts an unchanged issue date.
- `keepalive.yml` runs monthly and calls `gh workflow enable publish.yml`
  (`permissions: actions: write`). GitHub disables scheduled workflows on a
  public repository after 60 days without activity; this keeps the schedule alive.
- Scheduled workflows run only on the default branch, so `main` must be the
  default branch.
- The `github-pages` environment must allow deployments from `main`
  (Settings, Environments, Deployment branches).
- Only the `deploy` job holds `pages: write` and `id-token: write`.
- A run is refused when any point's days are not exactly the issue date and the
  two days after it.
