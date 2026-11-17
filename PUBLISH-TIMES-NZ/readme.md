# PUBLISH-TIMES-NZ

Creates and serves named TIMES-NZ release artefacts. Release bundles are local
data and belong in the ignored `releases/` directory. Every Parquet below a
release directory is part of that release, including raw solver results.

Select the release and maintain scenario and region display labels in
`explorer_bundle.toml`. Restart the app after editing it.

```bash
uv run publish-times-nz build <release-name> <postprocessed-directory>...
uv run publish-times-nz import-legacy <release-name> <legacy-result-directory>
uv run publish-times-nz prepare-deployment-payload
```

Deploy `deployment_payload/`, not the module root. The command rebuilds it with
the release selected in `explorer_bundle.toml`, the local `.env` file, and requirements exported
from the locked workspace.

```bash
uv run publish-times-nz prepare-deployment-payload
uv run rsconnect deploy shiny deployment_payload --entrypoint app --app-id <APP-ID>
```

The payload contains the bundled `.env`, so Pendo continues to receive its API
key. Do not edit the generated directory by hand.
