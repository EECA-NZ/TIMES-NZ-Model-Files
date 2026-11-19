# PUBLISH-TIMES-NZ

Creates and serves named TIMES-NZ release artefacts. Releases are local
data and belong in the ignored `releases/` directory. Every Parquet below a
release directory is part of that release, including raw solver results.

Manually maintained release definitions under `release_definitions/` list the cases and
scenario labels to include. `build-release` selects the latest completed,
postprocessed SOLVE run for each case at the workspace version and creates a
release under `releases/`. Its generated `release-manifest.json` records the selected
timestamped runs and scenario labels. Select the release and maintain region
display labels in `explorer_bundle.toml`. Restart the app after editing it.

```bash
uv run publish-times-nz build-release release_definitions/standard.toml
uv run publish-times-nz build <release-name> <postprocessed-directory>...
uv run publish-times-nz import-legacy <release-name> <legacy-result-directory>
```

For deployment payloads and deployment instructions, see the internal TIMES-NZ Explorer deployment runbook.
