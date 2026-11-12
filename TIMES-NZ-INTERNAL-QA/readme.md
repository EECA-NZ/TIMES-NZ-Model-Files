# TIMES-NZ-INTERNAL-QA


This module contains the internal QA app and analysis tools. `SOLVE-TIMES-NZ`
owns result post-processing; QA consumes labelled parquet bundles assembled from
selected completed solver runs.

## Solver result bundles

`SOLVE-TIMES-NZ` now writes labelled parquet outputs for every completed model
run. Build and solve a case with:

```bash
uv run --directory SOLVE-TIMES-NZ solve-times-nz solve steady
```

The run directory under `SOLVE-TIMES-NZ/build/solves/` contains the raw `.vd`,
`raw_results.parquet`, the labelled output parquets, and the PREP metadata used
for that run. QA bundles will combine selected run outputs for the app.

## Deploying the app 

A few adjustments are made to the shared uv workspace structure to enable the app to build on shinyapps.io:

1) `app.py` adds `src` to the system path. This enables Shinyapps.io to import the application package without the workspace's editable installation.
2) Shinyapps.io uses `requirements.txt` for its separate hosted environment. If runtime dependencies change, regenerate it from the root lockfile:
   ```bash
   uv export --locked --package times-nz-internal-qa --no-dev --no-emit-workspace --no-hashes -o TIMES-NZ-INTERNAL-QA/requirements.txt
   ```

In general, you can deploy the app locally by simply running the script `run_local.py`.

### Production Deployment

When deploying to the production app on shinyapps.io (the one that will be presented on the EECA website for public use), use the following terminal command:
```
uv run --directory TIMES-NZ-INTERNAL-QA rsconnect deploy shiny . .env \
  --entrypoint app \
  --app-id <PRODUCTION_APP_ID>
```
Before deployment, ensure you have created a `.env` file in the TIMES-NZ-INTERNAL-QA directory. This is so that the Pendo Analytics script can run on the production dashboard, allowing us to gather insights into how the dashboard is used. Note that the .env file must not be committed to Git. If the production deployment does not include a valid PENDO_API_KEY, Pendo analytics will not initialise.

Ensure that the `.env` contains the following line:
```
PENDO_API_KEY="<KEY>"
```
Replace `<KEY>` with the production Pendo API key. The production Pendo key is stored in the Data and Analytics 1Password vault. If you do not have access, contact the Data and Analytics or Data Products team.

### Development Deployments

Alternatively, you can deploy a new version-specific development build like so: 
```
uv run --directory TIMES-NZ-INTERNAL-QA rsconnect deploy shiny . \
  --entrypoint app \
  --title times-nz-internal-explorer-v<VERSION> \
  --new
```

If there is an existing development build that you wish to overwrite, the following command can be used. The <APP-ID> must be replaced the with the appropriate deployed development application id, which can be found on shinyapps.io or below.
```
uv run --directory TIMES-NZ-INTERNAL-QA rsconnect deploy shiny . \
  --entrypoint app \
  --app-id <APP-ID>
```

Some app-ids:
- `times-nz-internal-explorer`: 16527158 (This is our prerelease version for v300)
- `times-nz-internal-explorer-v301`: 16588202
- `times-nz-internal-explorer-v302`: 16596189
- `times-nz-internal-explorer-v303`: 16757346
- `times-nz-internal-explorer-v304`: 16904540
- `times-nz-internal-explorer-v305`: 17015159
- `times-nz-internal-explorer-v306`: 17262489
- `times-nz-internal-explorer-v307`: 17500112
- `times-nz-internal-explorer-v308-df-sensitivity`: 17584023


Production app-id:
 - `times-nz-v3`: 17242024
