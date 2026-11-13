# PUBLISH-TIMES-NZ

Creates and serves named TIMES-NZ release artefacts. Release bundles are local
data and belong in the ignored `releases/` directory. Every Parquet below a
release directory is part of that release, including raw solver results.

```bash
uv run publish-times-nz build <release-name> <postprocessed-directory>...
uv run publish-times-nz import-legacy <release-name> <legacy-result-directory>
```
