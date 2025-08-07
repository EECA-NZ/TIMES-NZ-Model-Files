from prepare_times_nz.utilities.logger_setup import blue_text, logger


def save_output(df, name, dir):
    """Save DataFrame output to the output location."""
    filename = f"{dir}/{name}"
    logger.info("Saving output:\n%s", blue_text(filename))
    df.to_csv(filename, index=False)


def save_checks(df, name, label, dir):
    """Save DataFrame checks to the checks location."""
    filename = f"{dir}/{name}"
    logger.info("Saving %s:\n%s", label, blue_text(filename))
    df.to_csv(filename, index=False)
