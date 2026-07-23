"""Helpers for updating charts through the Datawrapper API."""

import os
from io import BytesIO
from pathlib import Path

import datawrapper as dw
import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageChops, ImageColor
from times_nz_internal_qa.utilities.filepaths import ANALYSIS_RESULTS

DATAWRAPPER_DATA = ANALYSIS_RESULTS / "data_for_charts/datawrapper"


def something_happened_here():
    """Create and update the example Datawrapper bar chart."""
    # Load DATAWRAPPER_ACCESS_TOKEN and other local settings from .env.
    load_dotenv()

    # Set up your data
    data = pd.DataFrame(
        {
            "Language": ["me", "a mate", "aother guy", "a fella", "a folk"],
            "Percentage": [49.3, 62.3, 38.5, 30.5, 27.1],
        }
    )

    chart = dw.BarChart(
        title="API-generated charts",
        intro="Based on some random numbers in a script",
        data=data,
        value_label_format=dw.NumberFormat.ONE_DECIMAL,
        chart_id="34hus",
    )

    chart.update()


def modify_chart(chart_id):
    """Apply the example title and byline changes to a chart."""

    chart = dw.BarChart.get(chart_id)

    chart.title = "testtest"
    # chart.intro = "This does not overwrite any part of the chart"
    # chart.chart_type = :
    # chart.data = data
    # chart.value_label_format = dw.NumberFormat.ONE_DECIMAL

    chart.byline = ""

    chart.update()


def flatten_folders(folders):
    """Return a flat list containing all folders and their descendants."""
    result = []

    for folder in folders:
        result.append(folder)
        result.extend(flatten_folders(folder.get("folders", [])))

    return result


def get_charts_in_folder(folder_id):
    """Return the IDs and names of charts directly inside a Datawrapper folder."""
    client = dw.Datawrapper(access_token=os.environ["DATAWRAPPER_ACCESS_TOKEN"])
    data = client.get_folders()

    all_folders = [
        folder
        for user_or_team in data["list"]
        for folder in flatten_folders(user_or_team["folders"])
    ]

    folder = next(
        (folder for folder in all_folders if str(folder["id"]) == str(folder_id)),
        None,
    )

    if folder is None:
        raise ValueError(f"Datawrapper folder {folder_id!r} was not found")

    return [
        {"id": chart["id"], "name": chart["title"]}
        for chart in folder.get("charts", [])
    ]


def identify_folders():
    """
    Fetch and print the names and IDs of all Datawrapper folders accessible
    using the configured access token, including nested folders.
    """

    # we find that we need to re-access the token explicitly
    # when calling dw.Datawrapper
    # just to avoid weird environment load timings
    client = dw.Datawrapper(access_token=os.environ["DATAWRAPPER_ACCESS_TOKEN"])

    data = client.get_folders()

    all_folders = [
        folder
        for user_or_team in data["list"]
        for folder in flatten_folders(user_or_team["folders"])
    ]

    folder_details = [
        {
            "id": folder["id"],
            "name": folder["name"],
        }
        for folder in all_folders
    ]

    for f in folder_details:

        print(f"Found Datawrapper folder '{f["name"]}' ({f["id"]})")


def refresh_report_chart_list(add_figure_numbers=True):
    """
    Return the report-folder chart names, IDs, and figure numbers.
    Optionally adds a figure number variable if this can be extracted from
    the name

    Saves this from the existing datawrapper folder into a metadata table
    """

    # use identify_folders optionally to return a list of folders and their IDs
    # identify_folders()
    charts = get_charts_in_folder(423789)  # report charts folder ID

    df = pd.DataFrame(charts, columns=["name", "id"])

    if add_figure_numbers:

        figure_numbers = df["name"].str.extract(
            r"(?i)(?:^|\b)fig(?:ure)?[\s_.-]*(\d+)", expand=False
        )
        df["figure_number"] = pd.to_numeric(figure_numbers).astype("Int64")
        df = df.sort_values("figure_number")

    # save
    DATAWRAPPER_DATA.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATAWRAPPER_DATA / "metadata_raw.csv", index=False)


def get_chart_metadata():
    """Load the chart metadata table."""

    df = pd.read_csv(DATAWRAPPER_DATA / "metadata.csv")

    return df


def publish_svg(chart_name, chart_id):
    """
    For a given chart ID, publishes the chart
    """

    chart = dw.BaseChart.get(chart_id)
    chart.publish()

    output_dir = DATAWRAPPER_DATA / "svg"
    output_dir.mkdir(parents=True, exist_ok=True)

    out = chart.export_svg(full_vector=True)

    Path(output_dir / f"{chart_name}.svg").write_bytes(out)


def publish_png(chart_name, chart_id):
    """
    For a given chart ID, publishes the chart
    """

    chart = dw.BaseChart.get(chart_id)
    chart.publish()

    output_dir = DATAWRAPPER_DATA / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)

    out = chart.export_pdf(full_vector=True)

    Path(output_dir / f"{chart_name}.pdf").write_bytes(out)


def publish_all_svgs():
    """Publish and export every chart listed in the metadata table."""
    load_dotenv()
    metadata = pd.read_csv(DATAWRAPPER_DATA / "metadata.csv")

    required_columns = {"name", "id"}
    missing_columns = required_columns.difference(metadata.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Chart metadata is missing required columns: {missing}")

    for row_number, row in metadata.iterrows():
        if pd.isna(row["name"]) or pd.isna(row["id"]):
            raise ValueError(
                f"Chart metadata row {row_number + 2} has a missing name or id"
            )

        publish_svg(chart_name=str(row["name"]), chart_id=str(row["id"]))


def publish_all_pngs():
    """Publish and export every chart listed in the metadata table."""
    load_dotenv()
    metadata = pd.read_csv(DATAWRAPPER_DATA / "metadata.csv")

    required_columns = {"name", "id"}
    missing_columns = required_columns.difference(metadata.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Chart metadata is missing required columns: {missing}")

    for row_number, row in metadata.iterrows():
        if pd.isna(row["name"]) or pd.isna(row["id"]):
            raise ValueError(
                f"Chart metadata row {row_number + 2} has a missing name or id"
            )

        publish_png(chart_name=str(row["name"]), chart_id=str(row["id"]))


def append_data(chart_id, columns, unit):
    """Append the same unit suffix to multiple chart columns."""
    load_dotenv()
    client = dw.Datawrapper(access_token=os.environ["DATAWRAPPER_ACCESS_TOKEN"])

    column_formats = {column: {"number-append": f" {unit}"} for column in columns}

    return client.update_metadata(
        chart_id,
        metadata={
            "data": {
                "column-format": column_formats,
            }
        },
    )


def _png_image(contents):
    """Load PNG bytes into an independent RGB Pillow image."""
    with Image.open(BytesIO(contents)) as image:
        return image.convert("RGB")


def _detect_area_plot_top(image, background):
    """Find the first dense, non-background row in an area-chart template."""
    background_rgb = ImageColor.getrgb(background)
    background_image = Image.new("RGB", image.size, background_rgb)
    difference = ImageChops.difference(image, background_image).convert("L")
    mask = difference.point(lambda value: 255 if value > 10 else 0)

    # Titles and legends contain relatively few coloured pixels per row. An
    # area plot has several consecutive rows covering a substantial width.
    minimum_run = image.width // 5
    longest_runs = []
    for y in range(image.height):
        longest = 0
        current = 0
        for value in mask.crop((0, y, image.width, y + 1)).tobytes():
            if value:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        longest_runs.append(longest)

    for y in range(image.height - 2):
        if all(run > minimum_run for run in longest_runs[y : y + 3]):
            # The sloping upper boundary of an area can become wide gradually.
            # Move up slightly so its first anti-aliased pixels are erased too.
            return max(0, y - 20)
    return None


def export_facets(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    chart_id_or_name,
    chart_type="Area",
    chart_width=800,
    panel_gap=0,
    plot_top=None,
    footer_height=0,
    background="white",
):
    """Export and combine the Steady and Shift charts for one facet.

    ``chart_id_or_name`` can be the ID of either component chart or the shared
    ``chart_name`` value in metadata.csv. The Steady chart supplies the shared
    title, legend, and other full-chart layout. Datawrapper also renders a
    scenario heading above each component chart before they are combined.

    ``footer_height`` is measured in pixels in the exported PNG. Leave it at
    zero when the template has no footer; otherwise set it to preserve that
    many pixels at the bottom of the template.

    For area charts, the top of the old plot is detected automatically.
    ``plot_top`` can override that exported-pixel coordinate if needed.

    Returns the path of the combined PNG.
    """
    # This function coordinates API updates, image exports, and composition.
    # Keeping those stages together makes its restoration guarantees explicit.
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    if chart_type not in {"Area", "Line"}:
        raise ValueError("Chart type for facet must be 'Line' or 'Area'")
    if chart_width < 2:
        raise ValueError("chart_width must be at least 2")
    if panel_gap < 0 or panel_gap >= chart_width:
        raise ValueError("panel_gap must be between 0 and chart_width")
    if plot_top is not None and plot_top < 0:
        raise ValueError("plot_top cannot be negative")
    if footer_height < 0:
        raise ValueError("footer_height cannot be negative")

    load_dotenv()
    all_metadata = get_chart_metadata()
    identifier = str(chart_id_or_name)

    matching_id = all_metadata[all_metadata["id"].astype(str) == identifier]
    if not matching_id.empty:
        facet_name = matching_id["chart_name"].iloc[0]
    else:
        facet_name = chart_id_or_name

    metadata = all_metadata[all_metadata["chart_name"] == facet_name].copy()
    if metadata.empty:
        raise ValueError(f"No facet metadata found for {chart_id_or_name!r}")

    scenario_rows = {}
    for scenario in ("Steady", "Shift"):
        rows = metadata[metadata["Scenario"] == scenario]
        if len(rows) != 1:
            raise ValueError(
                f"Expected one {scenario} chart for {facet_name!r}, found {len(rows)}"
            )
        scenario_rows[scenario] = rows.iloc[0]

    output_dir = DATAWRAPPER_DATA / "png"
    pieces_dir = output_dir / "facet_pieces"
    output_dir.mkdir(parents=True, exist_ok=True)
    pieces_dir.mkdir(parents=True, exist_ok=True)

    chart_class = dw.AreaChart if chart_type == "Area" else dw.LineChart
    template_row = scenario_rows["Steady"]
    template_chart = chart_class.get(str(template_row["id"]))
    original_title = template_chart.title
    output_name = str(template_row["name"]).replace(" (Steady)", "")

    # Temporarily give the full chart its facet title, export the layout, then
    # put the Datawrapper chart back exactly as it was.
    try:
        template_chart.title = output_name
        template_chart.update().publish()
        template = _png_image(template_chart.export_png(width=chart_width))
    finally:
        template_chart.title = original_title
        template_chart.update().publish()

    template_path = pieces_dir / f"{output_name} (Template).png"
    template.save(template_path)

    left_width = (chart_width - panel_gap) // 2
    panel_widths = (left_width, chart_width - panel_gap - left_width)
    panels = []

    for scenario, panel_width in zip(("Steady", "Shift"), panel_widths):
        row = scenario_rows[scenario]
        chart = chart_class.get(str(row["id"]))
        original_fields = {
            field: getattr(chart, field)
            for field in (
                "title",
                "intro",
                "byline",
                "source_name",
                "source_url",
                "notes",
            )
        }
        original_color_key = getattr(chart, "show_color_key", None)

        try:
            chart.title = scenario
            for field in original_fields:
                if field != "title":
                    setattr(chart, field, "")
            if original_color_key is not None:
                chart.show_color_key = False
            chart.update().publish()
            panel = _png_image(chart.export_png(width=panel_width, plain=False))
        finally:
            for field, value in original_fields.items():
                setattr(chart, field, value)
            if original_color_key is not None:
                chart.show_color_key = original_color_key
            chart.update().publish()

        panel.save(pieces_dir / f"{row['name']}.png")
        panels.append(panel)

    if panels[0].height != panels[1].height:
        raise ValueError(
            "Facet panels have different heights: "
            f"{panels[0].height} and {panels[1].height} pixels"
        )

    panel_height = panels[0].height
    if plot_top is None and chart_type == "Area":
        plot_top = _detect_area_plot_top(template, background)
    if plot_top is None:
        plot_top = template.height - footer_height - panel_height

    if panels[0].width + panels[1].width > template.width:
        raise ValueError("The component panels are wider than the template")

    # Build a fresh canvas from the retained template header and optional
    # footer. This removes the old template plot completely, regardless of the
    # height added by the Datawrapper-rendered scenario headings.
    combined = Image.new(
        "RGB",
        (template.width, plot_top + panel_height + footer_height),
        background,
    )
    combined.paste(template.crop((0, 0, template.width, plot_top)), (0, 0))
    combined.paste(panels[0], (0, plot_top))
    combined.paste(panels[1], (combined.width - panels[1].width, plot_top))
    if footer_height:
        footer = template.crop(
            (
                0,
                template.height - footer_height,
                template.width,
                template.height,
            )
        )
        combined.paste(footer, (0, plot_top + panel_height))

    output_path = output_dir / f"{output_name}.png"
    combined.save(output_path)
    return output_path


#     chart = dw.BaseChart.get(id)
#     chart.publish()
#
#     output_dir = DATAWRAPPER_DATA / "pdf"
#     output_dir.mkdir(parents=True, exist_ok=True)
#
#     out = chart.export_pdf(full_vector=True)
#
#     Path(output_dir / f"{name}.pdf").write_bytes(out)


def get_columns(df):
    """Return chart value columns, excluding period and unit metadata."""

    all_cols = df.columns

    group_cols = [col for col in all_cols if col not in ["Period", "Unit"]]

    return group_cols


def get_unit(df):
    """Return the sole unit used by a chart data table."""

    unit_list = df["Unit"].unique()

    if len(unit_list) == 1:
        return unit_list[0]

    return ValueError(
        "Multiple units detected! All dw tables should have only one unit."
    )


def append_all_units():
    """Append each chart data table's unit to its Datawrapper columns."""

    # get all charts

    all_metadata = pd.read_csv(DATAWRAPPER_DATA / "metadata.csv")

    chart_ids = all_metadata["id"].unique()

    for chart_id in chart_ids:
        # get the data
        metadata = all_metadata[all_metadata["id"] == chart_id].copy()
        if len(metadata) != 1:
            raise ValueError(
                f"Expected one metadata row for chart {chart_id}, found {len(metadata)}"
            )
        df_filename = str(metadata["source_data"].iloc[0])
        df = pd.read_csv(DATAWRAPPER_DATA / df_filename)

        unit = get_unit(df)
        group_cols = get_columns(df)

        append_data(chart_id, group_cols, unit)


def _prepare_chart_data_updates(metadata):  # pylint: disable=too-many-locals
    """Validate metadata and load all chart data before any API updates."""
    required_columns = {"id", "source_data"}
    missing_columns = required_columns.difference(metadata.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Chart metadata is missing required columns: {missing}")

    required_values = metadata[["id", "source_data"]]
    missing_values = required_values.isna() | required_values.apply(
        lambda column: column.astype(str).str.strip().eq("")
    )
    if missing_values.any(axis=None):
        rows = ", ".join(
            str(row_number)
            for row_number, is_missing in enumerate(missing_values.any(axis=1), start=2)
            if is_missing
        )
        raise ValueError(
            f"Chart metadata has a missing id or source_data on row(s): {rows}"
        )

    chart_ids = metadata["id"].astype(str).str.strip()
    duplicated_ids = chart_ids[chart_ids.duplicated(keep=False)].unique()
    if len(duplicated_ids):
        duplicates = ", ".join(sorted(duplicated_ids))
        raise ValueError(f"Chart metadata contains duplicate chart IDs: {duplicates}")

    data_directory = DATAWRAPPER_DATA.resolve()
    updates = []
    for row_number, (_, row) in enumerate(metadata.iterrows(), start=2):
        chart_id = str(row["id"]).strip()
        source_data = str(row["source_data"]).strip()
        source_path = (DATAWRAPPER_DATA / source_data).resolve()

        if not source_path.is_relative_to(data_directory):
            raise ValueError(
                f"Chart metadata row {row_number} points outside the data directory: "
                f"{source_data}"
            )
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Chart data for {chart_id} was not found: {source_path}"
            )

        data = pd.read_csv(source_path)
        if data.empty:
            raise ValueError(f"Chart data for {chart_id} is empty: {source_path}")
        updates.append((chart_id, source_path, data))

    return updates


def update_all_chart_data():
    """Upload each source CSV to the chart ID aligned in metadata.csv."""
    load_dotenv()
    updates = _prepare_chart_data_updates(get_chart_metadata())
    client = dw.Datawrapper(access_token=os.environ["DATAWRAPPER_ACCESS_TOKEN"])

    for chart_id, source_path, data in updates:
        print(f"Updating Datawrapper chart {chart_id} from {source_path.name}")
        client.add_data(chart_id=chart_id, data=data)

    return [chart_id for chart_id, _, _ in updates]


def get_all_ids():
    """
    Returns all the IDs in metadata
    """

    all_metadata = pd.read_csv(DATAWRAPPER_DATA / "metadata.csv")

    for i in all_metadata:
        print(i)


#     return all_metadata["id"].unique()


def main():
    """Update chart data and export the configured example facet."""
    load_dotenv()
    update_all_chart_data()
    export_facets("Total demand by fuel")
    # publish_all_pngs()


if __name__ == "__main__":
    main()
