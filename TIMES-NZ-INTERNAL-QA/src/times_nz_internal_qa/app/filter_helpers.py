"""
A list of functional helpers and factories for the app
"""

from shiny import render, ui
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
        result.append({"chart_id": chart_id, "id": fid, "label": label, **f})
    return result


_dynamic_outputs = []


# pylint:disable = too-many-positional-arguments, too-many-arguments
# could break out the factory from the register method
def register_filter_from_factory(fspec, df, filters, inputs, outputs, session):
    """
    Register a dynamic Shiny UI output for a selectize filter, created from a
    filter specification and a data source.

    This helper builds a `ui.input_selectize(...)` using the unique values from
    the specified column, wraps it with `@render.ui`, assigns it to a concrete
    output id using `@outputs(id=...)`, and stores the resulting callable to
    prevent garbage collection. It supports optional module namespacing via
    `session.ns`. The corresponding UI placeholder should be created with
    `ui.output_ui(ns("filter_<chart_id>_<id>_ui"))`.
    """

    ns = session.ns  # no-op if not modular

    # factory needs namespace (ns) to build the input id correctly
    def make_filter_ui_factory(fspec, data_src, ns, filters, inputs):
        def _df():
            return data_src() if callable(data_src) else data_src

        def _ui():
            base = _df()
            filtered = apply_filters(
                base, filters, inputs, exclude_id=fspec["id"], ns=ns
            )

            col = fspec["col"]
            choices = sorted(filtered[col].astype(str).dropna().unique())

            iid = ns(f"filter_{fspec['chart_id']}_{fspec['id']}_selected")
            # ensure we just output a clean empty list if no selection available
            # on exception or shiny's silent exception current is still an empty list
            try:
                current = getattr(inputs, iid)()
            except SilentException:
                current = []

            selected = [v for v in current if v in choices]
            # generate the selectize function
            return ui.input_selectize(
                iid,
                fspec.get("label", col),
                choices,
                selected=selected,
                multiple=True,
            )

        return _ui

    # factory
    f_ui = make_filter_ui_factory(fspec, df, ns, filters, inputs)
    # inner decorator
    wrapped = render.ui(f_ui)
    # outer decorator
    registered = outputs(id=ns(f"filter_{fspec['chart_id']}_{fspec['id']}_ui"))(wrapped)
    # keep alive
    _dynamic_outputs.append(registered)
    return registered


def filter_output_id(f):
    """output function name for ui.output_ui(...)"""
    return f"filter_{f["chart_id"]}_{f["id"]}_ui"


def filter_input_id(f):
    """input_selectize id that holds selections"""
    return f"filter_{f["chart_id"]}_{f["id"]}_selected"


def apply_filters(df, filters, inputs, exclude_id=None, ns=lambda x: x):
    """
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
    for f in filters:
        # we optionally might want to skip a filter input for generation reasons
        if f["id"] == exclude_id:
            continue
        # ensure namespace matching
        iid = ns(filter_input_id(f))
        # ensure sel is None if something goes wrong so we always return the data
        try:
            sel = getattr(inputs, iid)()
        except SilentException:
            sel = None
        # if any filter is found, we filter the data on it
        if sel:
            df = df[df[f["col"]].astype(str).isin(sel)]
    return df


def filter_output_ui_list(filters, ns=lambda x: x):
    """Build output_ui placeholders for all filters."""
    return [ui.output_ui(ns(filter_output_id(f))) for f in filters]


def filter_output_ui_rows(filters, per_row=6, ns=lambda x: x):
    """Chunk placeholders into rows. Not always needed."""
    items = filter_output_ui_list(filters, ns)
    return [ui.row(*items[i : i + per_row]) for i in range(0, len(items), per_row)]
