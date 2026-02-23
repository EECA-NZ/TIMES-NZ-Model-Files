"""
A list of functional helpers and factories for the app
"""

import polars as pl
from shiny import reactive, render, ui
from shiny.types import SilentException


def create_filter_dict(chart_id, filters):
    """
    Ensures each filter dict includes:
      - chart_id (provided)
      - id (auto-generated from col if missing)
      - label (title-cased from col if missing)
    Expects: `filters` as list of dicts with at least "col".
    chart_id as string
    """
    result = []
    for f in filters:
        col = f["col"]
        fid = f.get("id", col.lower())
        label = f.get("label", col.replace("_", " ").title())
        multiple = f.get("multiple", True)
        result.append(
            {"chart_id": chart_id, "id": fid, "label": label, "multiple": multiple, **f}
        )
    return result


def filter_output_id(f):
    """output function name for ui.output_ui(...)
    Expects a filter spec dict to combine chart_id and id
    in a consistent way"""
    return f"filter_{f["chart_id"]}_{f["id"]}_ui"


def filter_input_id(f):
    """input_selectize id that holds selections
    Expects a filter spec dict to combine chart_id and id
    in a consistent way"""
    return f"filter_{f["chart_id"]}_{f["id"]}_selected"


# @lru_cache(maxsize=16)
def apply_filters(df: pl.LazyFrame, filters, inputs, ns=lambda x: x):
    """
    Apply filters to a Polars LazyFrame.

    Apply all found filters to the data.
    Robust to namespace matching.
    If there are no inputs, shiny fails silently, so we catch this and ensure
    data is returned even if there are no inputs or anything else goes wrong.

    NOTE: Includes optional "exclude_id" to remove an item from the list.
       See use of this in make_filter_ui_factory(),
       which derives filter choices based on filtered data.
       Removal is required for each ui item to avoid circular referencing
       while still assessing filter choices dynamically.
    """

    # build up filters as Polars expressions
    exprs = []

    for f in filters:
        # identify the input options
        iid = ns(filter_input_id(f))

        # pull the current selection for this filter
        try:
            sel = getattr(inputs, iid)()
        except SilentException:
            sel = None
        if sel:
            # add filter to list
            # ensure values are strings for comparison parity
            # we also need to apply the filter differently if it's multiple or not
            if f["multiple"]:
                exprs.append(pl.col(f["col"]).cast(pl.Utf8).is_in(sel))
            else:
                exprs.append(pl.col(f["col"]).cast(pl.Utf8) == sel)

    # if no filters found, return original df
    if not exprs:
        return df

    # combine filters together
    combined = exprs[0]
    for e in exprs[1:]:
        combined = combined & e
    # return filtered data
    return df.filter(combined)


# is it possible to remove some of these arguments?


# pylint:disable = too-many-arguments, too-many-positional-arguments, too-many-locals
def register_filter_from_factory(fspec, df, filters, inputs, outputs, session):
    """
    Creates a filter factory then uses that and the fspec inputs
    to register all filters in the server for a specific chart and it's associated fspec

    Generates input and output IDs etc

    Mounts the filters once, with the initial filter options

    Then adds an update feature to restrict the options based on current filter settings

    fspec: this filter's parameters from the dict
    df: filter options dataframe
    filters: all fspecs defined for this page, entered as dict
    inputs, outputs, session: server parameters
    """

    ns = session.ns  # no-op if not modular

    oid = ns(filter_output_id(fspec))
    iid = ns(filter_input_id(fspec))

    col = fspec["col"]
    allows_multiple = fspec["multiple"]

    @outputs(id=oid)
    @render.ui
    def _mount():
        base = df() if callable(df) else df
        choices = base.select(pl.col(col).cast(str)).to_series().to_list()

        choices = sorted(set(choices))

        if allows_multiple:
            ui_filter = ui.input_selectize(
                iid, fspec.get("label", col), choices, multiple=True
            )

        else:
            ui_filter = ui.input_select(
                iid,
                fspec.get("label", col),
                choices,
                selected=(
                    choices[1] if len(choices) > 1 else choices[0] if choices else None
                ),
            )

        return ui.div(
            ui_filter,
            class_="individual-filter",
        )

    # We set up listeners for if the other filters change
    # to adjust the options available according to the current selection
    # (We do not update the current filter if the user changes it)

    # first,  identify input triggers
    triggers = [
        # all live filter IDs in this chart's filter list
        getattr(inputs, ns(filter_input_id(s)))
        for s in filters
        # except the one we just changed
        if ns(filter_input_id(s)) != iid
    ]

    # define update method. Filters the options table for current inputs
    # (can we do this once?)
    def _update_body():
        base = df() if callable(df) else df
        # exclude this filter’s own value so we don’t depend on it
        opt_tbl = apply_filters(base, filters, inputs)

        # find new options for this filter spec column
        choices = opt_tbl.select(pl.col(col).cast(str)).to_series().to_list()
        choices = sorted(set("" if v is None else v for v in choices))

        # identify the current inputs (we need to keep these the same in selected)

        with reactive.isolate():
            try:
                current = list(getattr(inputs, iid)() or [])
            except SilentException:
                current = []
        current = ["" if v is None else str(v) for v in current]

        # keep only valid selections; do not clear unless invalid
        selected = [v for v in current if v in choices]

        if allows_multiple:
            ui.update_selectize(iid, choices=choices, selected=selected)

    if triggers:

        @reactive.effect
        @reactive.event(*triggers)
        def _update_self():
            _update_body()

    else:

        @reactive.effect
        def _update_self():
            _update_body()

    # robust to all filters clearing themselves
    # effectively, filters don't update when we add conditions
    # (which is desired behaviour)
    # but this forces updates when they're emptied to avoid users getting stuck
    @reactive.effect
    @reactive.event(getattr(inputs, iid))
    def _update_on_self_clear():
        val = getattr(inputs, iid)()
        is_empty = (
            val is None
            or val == ""
            or (isinstance(val, (list, tuple, set)) and len(val) == 0)
        )
        if is_empty:
            _update_body()

    return _mount, _update_self, _update_on_self_clear


def filter_output_ui_list(filters, ns=lambda x: x):
    """Build output_ui placeholders for all filters."""
    return [ui.output_ui(ns(filter_output_id(f))) for f in filters]


def filter_output_ui_rows(filters, per_row=6, ns=lambda x: x):
    """Chunk placeholders into rows. Not always needed."""
    items = filter_output_ui_list(filters, ns)
    return [ui.row(*items[i : i + per_row]) for i in range(0, len(items), per_row)]


def register_filter_clear_button(filter_dict: list[dict], inputs, session):
    """
    Defines server methods for clearing filters
    """
    ns = session.ns

    chart_id = filter_dict[0]["chart_id"]

    # IMPORTANT NOTE:
    # the serverside "chart-id" does not have a _chart suffix
    # but the UI side chart-id (as set in sections) DOES
    # so we add a _chart suffix here

    btn_id = f"{chart_id}_chart_clear_filters"

    def reset_input(iid: str):
        """
        We make this helper wrapper which is currently a bit extra
        We might need to use this to add more sophistication later
        Otherwise it could just go straught into _clear_all_filters
        """
        ui.update_selectize(iid, selected=[])

    @reactive.effect
    # @reactive.event(getattr(inputs, btn_id))
    @reactive.event(getattr(inputs, btn_id))
    def _clear_all_filters():
        for fs in filter_dict:
            # if fs carries chart_id, scope to this chart
            if fs.get("chart_id") not in (None, chart_id):
                continue
            # dw about it for single-select items:
            if fs.get("multiple") is False:
                continue
            iid = ns(filter_input_id(fs))
            reset_input(iid)


def register_all_filters_and_clear(filters, base_options, inputs, outputs, session):
    """
    A wrapper to register all filters and the clear button in the server
    Based on the filter dict and base options data
    """
    # register all filters
    # REGISTERING FS

    for fs in filters:

        register_filter_from_factory(
            fs, base_options, filters, inputs, outputs, session
        )
    # register clear button
    register_filter_clear_button(filters, inputs, session)
