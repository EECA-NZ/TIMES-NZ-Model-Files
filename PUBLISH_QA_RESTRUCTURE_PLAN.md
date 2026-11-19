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
  Payload preparation also copies the root `.python-version`.
- The public developer guide explains the workflow. EECA account setup and
  deployment targets are documented in the separately maintained internal
  runbook.
- The old Explorer, deployment files and duplicate app tests have been removed
  from INTERNAL-QA. Analysis retains its timeslice helper under `utilities/`.
  Archived legacy data and the old `.env` have also been removed locally;
  analysis code and outputs remain. The empty QA test step was removed from CI,
  and active local-app instructions now point to PUBLISH.
- Stale copied rsconnect deployment metadata has been removed from PUBLISH.
  PUBLISH pylint now runs in CI and pre-commit, covering the package and both
  app entry scripts. PUBLISH tests and the retained analysis helper imports
  passed after the old app was removed.

- The QA rename is complete: directory `QA-TIMES-NZ`, distribution
  `qa-times-nz`, and Python package `qa_times_nz`. Workspace configuration,
  lockfile, imports, hooks, ignore paths and active documentation use the new
  names; historical changelog entries retain the old name.
- Calibration checks, reference data, reports, analysis scripts and local outputs
  were preserved. Workspace sync, renamed imports, PUBLISH tests and
  QA/calibration pylint passed after the rename. The calibration and analysis
  methods themselves are unchanged.

See the [PUBLISH developer guide](PREPARE-TIMES-NZ/docs/source/developer_guide/publish_times_nz/index.md)
for the release format and commands. This plan now covers the remaining cleanup
rather than repeating those mechanics.

## Remaining steps for this PR

1. **Review dependencies left by the old app.**
   - Remove dependencies used only by the deleted Explorer where they are no
     longer needed; retain those used by calibration and analysis. Dependency
     declarations were preserved during the rename.

2. **Update integration and documentation.**
   - Include PUBLISH in the Black/isort hook paths, which still omit it;
     PUBLISH's pylint wiring is complete.

3. **Verify the cleanup.**
   - Run PUBLISH tests and the affected format and lint checks. No QA unit
     tests remain after removing the duplicated app tests; verify the retained
     package and helper imports without adding placeholder tests.
   - Check for stale active imports, workspace names and commands. Confirm the
     PUBLISH Explorer still starts with a selected release after the old app is
     removed. Deployment commands and smoke checks remain in the internal runbook.

## Deferred calibration and analysis work

Both calibration checks and analysis scripts are retained as a starting point
for a future method. They need some rewriting and integration, but this cleanup
PR does not discard them or require every check and report to run on new
releases. This supersedes the original plan to remove calibration tooling.

Legacy Parquets and raw scenario CSVs have already been removed locally after
archiving. Checks and reports that depend on them require restoring archived
inputs or migrating their loaders; retain the calibration reference data still
in the module.

- Define how calibration and analysis fit into the future QA workflow, then
  rewrite and integrate the retained code as needed.
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
- External release storage, new reports, chart redesign, and calibration and
  analysis redesign remain separate work.
