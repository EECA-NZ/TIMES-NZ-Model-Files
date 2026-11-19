# Publish and QA restructuring plan

## Work so far

- `PUBLISH-TIMES-NZ` owns the Explorer, release creation and deployment payload
  preparation. SOLVE still owns per-run postprocessing; PREPARE owns input
  preparation and reporting metadata.
- Manually maintained TOML files in `PUBLISH-TIMES-NZ/release_definitions/`
  define cases and scenario labels. `build-release` selects eligible completed
  runs and writes a named release with `release-manifest.json` recording its
  source runs. Explicit-run builds and legacy imports are also available.
- Legacy v308 and new-solver releases exist locally under the ignored
  `PUBLISH-TIMES-NZ/releases/` directory. The Explorer selects a release through
  `explorer_bundle.toml`; deployment packages the app with one selected release.
- The public developer guide explains the workflow. EECA account setup and
  deployment targets are documented in the separately maintained internal
  runbook.

See the [PUBLISH developer guide](PREPARE-TIMES-NZ/docs/source/developer_guide/publish_times_nz/index.md)
for the release format and commands. This plan now covers the remaining cleanup
rather than repeating those mechanics.

## Remaining steps for this PR

1. **Remove the old Explorer from `TIMES-NZ-INTERNAL-QA`.**
   - Delete the duplicated app modules, entry points, assets, web scripts and
     deployment-only files and utilities. Keep the working Explorer in PUBLISH.
   - Preserve the timeslice helper still used by analysis before deleting
     `app/`; move it into the retained QA utilities and update its callers.
   - Remove the duplicated app tests already covered in PUBLISH.
   - Remove `calibration_checks/`, including its calibration data and generated
     report, as agreed in the original scope. A replacement is separate work.
   - Preserve local result data and analysis inputs; deleting app code does not
     require deleting those files.

2. **Rename the remaining QA module.**
   - Directory: `TIMES-NZ-INTERNAL-QA` → `QA-TIMES-NZ`.
   - Distribution: `times-nz-internal-qa` → `qa-times-nz`.
   - Python package: `times_nz_internal_qa` → `qa_times_nz`.
   - Update retained imports, package metadata, root workspace members and
     sources, and `uv.lock`. Remove dependencies used only by the deleted app
     or calibration code where they are no longer needed.
   - Keep the existing analysis scripts with mechanical import/path updates;
     migrating their data access is deferred below.

3. **Update integration and documentation.**
   - Update CI, pre-commit hooks, ignore paths, module instructions and active
     documentation for the renamed module. Include PUBLISH in the formatter
     hook paths, which currently omit it.
   - Replace the obsolete INTERNAL-QA local-app command in the developer
     workflow overview with the PUBLISH command.
   - Check the PREP residential-analysis script's reference to the old QA data
     directory during the rename; migrating that analysis to releases can wait.
   - Keep historical changelog entries as history. Adjust the legacy-import
     example if its local source directory moves.

4. **Verify the cleanup.**
   - Sync the renamed workspace and confirm the QA package and retained helper
     imports resolve.
   - Run PUBLISH tests and any retained QA unit tests, plus the affected format
     and lint checks. If no QA tests remain after removing duplicate app tests,
     remove the obsolete CI test step rather than leave an empty pytest run.
   - Check for stale active imports, workspace names and commands. Confirm the
     PUBLISH Explorer still starts with a selected release after the old app is
     removed. Deployment commands and smoke checks remain in the internal runbook.

## Deferred analysis work

Analysis scripts are retained for later attention; making every report run on
new releases is not an acceptance criterion for this cleanup PR.

- Replace the common loader's `FINAL_DATA` path and default v308 scenario map
  with explicitly selected PUBLISH releases using `load_bundle`.
- Update sensitivity-report functions that read Parquets directly instead of
  using the common loader.
- Review demand-flex analysis's dependency on legacy raw scenario CSVs.
- Migrate the PREP residential analysis if it is still useful.

The intended direction remains that QA consumes releases and produces internal
analysis, while PUBLISH owns releases and the Explorer. QA can depend on the
public PUBLISH release reader; PUBLISH should remain independent of QA.

## Other follow-up work

- Restoring the full-results ZIP download control is out of scope.
- Keep `import-legacy` for now; retiring the migration tool can be considered
  separately once the completed legacy release is safely archived.
- External release storage, new reports, chart redesign and replacement
  calibration tooling remain separate work.
