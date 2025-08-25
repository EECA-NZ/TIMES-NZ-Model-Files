import pandas as pd
from prepare_times_nz.utilities.logger_setup import logger

RUN_TESTS = True


def check_missing_times_codes(df: pd.DataFrame, varname: str) -> None:
    """Warn if any values lacked a TIMES code during a merge."""
    varname_times = f"{varname}_TIMES"
    missing = df[df[varname_times].isna()][[varname, varname_times]].drop_duplicates()

    if missing.empty:
        logger.info("Full %s code coverage found", varname)
        return

    logger.warning(
        "Warning: the following %d '%s' items have no TIMES code equivalent",
        len(missing),
        varname,
    )
    for _, row in missing.iterrows():
        logger.warning("        %s", row[varname])
    logger.warning(
        "This will lead to issues: please check the input concordance file and "
        "ensure you have full '%s' coverage",
        varname,
    )


def add_times_codes(
    df: pd.DataFrame, code_mapping: pd.DataFrame, varname: str, run_tests=RUN_TESTS
) -> pd.DataFrame:
    """Left‑join *code_mapping* onto *df* and (optionally) run coverage tests."""
    df = pd.merge(df, code_mapping, on=varname, how="left")
    if run_tests:
        check_missing_times_codes(df, varname)
    return df
