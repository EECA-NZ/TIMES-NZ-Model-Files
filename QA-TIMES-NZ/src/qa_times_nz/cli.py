"""Run the configured QA report and initialise a local developer configuration."""

import argparse

from qa_times_nz import report_inputs
from qa_times_nz.report import build_report
from qa_times_nz.report.build import comparisons_path


def init_dev_config():
    """Copy the validated main configuration, preserving any existing developer file."""
    report_inputs.load_config()
    root = report_inputs.REPOSITORY_ROOT / "QA-TIMES-NZ"
    contents = (root / "report_config.toml").read_bytes()
    path = root / "report_config_dev.toml"
    with path.open("xb") as target:
        target.write(contents)
    return path


def main():
    """Expose main/dev report selection without alternate result locations."""
    parser = argparse.ArgumentParser(prog="qa-times-nz")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser(
        "generate_qa", help="Write the HTML report and comparison CSV"
    )
    generate.add_argument(
        "--dev", action="store_true", help="Use report_config_dev.toml"
    )
    commands.add_parser(
        "init-dev-config", help="Create report_config_dev.toml from main"
    )
    arguments = parser.parse_args()
    try:
        if arguments.command == "init-dev-config":
            print(f"Developer configuration: {init_dev_config()}")
        else:
            path = build_report(dev=arguments.dev)
            print(f"Report: {path}")
            print(f"Comparisons: {comparisons_path(path)}")
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
