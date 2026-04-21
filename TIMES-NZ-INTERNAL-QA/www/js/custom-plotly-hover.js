(function () {
  const READY_CLASS = "custom-plotly-hover-ready";
  const TOOLTIP_ID = "custom-plotly-hover";
  const plotStates = new WeakMap();
  let scanScheduled = false;

  function ensureTooltip() {
    let tooltip = document.getElementById(TOOLTIP_ID);
    if (!tooltip) {
      tooltip = document.createElement("div");
      tooltip.id = TOOLTIP_ID;
      tooltip.className = "custom-plotly-hover";
      document.body.appendChild(tooltip);
    }
    return tooltip;
  }

  let tooltip = null;
  let activePlot = null;
  let latestPointer = null;

  function getPlotState(plot) {
    let state = plotStates.get(plot);
    if (!state) {
      state = {
        domBound: false,
        resizeObserver: null,
        plotlyHandlersBound: false,
        onMouseMove: null,
        onMouseLeave: null,
        onPlotlyHover: null,
        onPlotlyUnhover: null,
        onPlotlyRelayout: null,
        onPlotlyDoubleClick: null,
        onPlotlyAfterPlot: null,
      };
      plotStates.set(plot, state);
    }
    return state;
  }

  function resolveCustomdata(point) {
    if (!point) {
      return null;
    }

    if (point.customdata !== undefined && point.customdata !== null) {
      return point.customdata;
    }

    const pointNumber = point.pointNumber;
    const fullCustomdata = point.fullData && point.fullData.customdata;
    if (
      Number.isInteger(pointNumber) &&
      Array.isArray(fullCustomdata) &&
      pointNumber >= 0 &&
      pointNumber < fullCustomdata.length
    ) {
      return fullCustomdata[pointNumber];
    }

    return null;
  }

  function getTooltipHtml(point) {
    const customdata = resolveCustomdata(point);
    if (!customdata) {
      return "";
    }
    if (typeof customdata === "string") {
      return customdata;
    }
    if (Array.isArray(customdata) && typeof customdata[customdata.length - 1] === "string") {
      return customdata[customdata.length - 1];
    }
    return "";
  }

  function positionTooltip(event) {
    if (!event || tooltip.hidden) {
      return;
    }
    const offset = 18;
    const maxLeft = window.innerWidth - tooltip.offsetWidth - 12;
    const maxTop = window.innerHeight - tooltip.offsetHeight - 12;
    const nextLeft = Math.min(event.clientX + offset, Math.max(12, maxLeft));
    const nextTop = Math.min(event.clientY + offset, Math.max(12, maxTop));
    tooltip.style.left = `${nextLeft}px`;
    tooltip.style.top = `${nextTop}px`;
  }

  function hideTooltip() {
    if (!tooltip) {
      return;
    }
    tooltip.hidden = true;
    tooltip.innerHTML = "";
    activePlot = null;
  }

  function getPlotContainer(plot) {
    return plot.closest(".shiny-ipywidget-output") || plot.parentElement || plot;
  }

  function resizePlot(plot) {
    if (!plot || !plot.isConnected || !window.Plotly?.Plots?.resize) {
      return;
    }

    window.requestAnimationFrame(() => {
      if (!plot.isConnected) {
        return;
      }

      const container = getPlotContainer(plot);
      const width = Math.floor(container.clientWidth || 0);

      if (width > 0 && window.Plotly.relayout) {
        window.Plotly.relayout(plot, { width });
        return;
      }

      window.Plotly.Plots.resize(plot);
    });
  }

  function bindResize(plot, state) {
    if (!plot || state.resizeObserver) {
      return;
    }

    const observer = new ResizeObserver(() => {
      resizePlot(plot);
    });

    const container = getPlotContainer(plot);
    observer.observe(container);
    if (container.parentElement) {
      observer.observe(container.parentElement);
    }
    state.resizeObserver = observer;
  }

  function unbindPlotlyHandlers(plot, state) {
    if (!state.plotlyHandlersBound || typeof plot.removeListener !== "function") {
      return;
    }

    plot.removeListener("plotly_hover", state.onPlotlyHover);
    plot.removeListener("plotly_unhover", state.onPlotlyUnhover);
    plot.removeListener("plotly_relayout", state.onPlotlyRelayout);
    plot.removeListener("plotly_doubleclick", state.onPlotlyDoubleClick);
    plot.removeListener("plotly_afterplot", state.onPlotlyAfterPlot);
    state.plotlyHandlersBound = false;
  }

  function bindDomHandlers(plot, state) {
    if (state.domBound) {
      return;
    }

    state.onMouseMove = (event) => {
      latestPointer = event;
      if (activePlot === plot) {
        positionTooltip(event);
      }
    };

    state.onMouseLeave = () => {
      if (activePlot === plot) {
        hideTooltip();
      }
    };

    plot.addEventListener("mousemove", state.onMouseMove);
    plot.addEventListener("mouseleave", state.onMouseLeave);
    state.domBound = true;
  }

  function bindPlotlyHandlers(plot, state) {
    if (typeof plot.on !== "function") {
      return;
    }

    unbindPlotlyHandlers(plot, state);

    state.onPlotlyHover = (eventData) => {
      const point = eventData && eventData.points && eventData.points[0];
      const html = getTooltipHtml(point);
      if (!html) {
        hideTooltip();
        return;
      }
      activePlot = plot;
      tooltip.innerHTML = html;
      tooltip.hidden = false;
      positionTooltip(latestPointer || eventData.event);
    };

    state.onPlotlyUnhover = hideTooltip;
    state.onPlotlyRelayout = hideTooltip;
    state.onPlotlyDoubleClick = hideTooltip;
    state.onPlotlyAfterPlot = () => {
      resizePlot(plot);
    };

    plot.on("plotly_hover", state.onPlotlyHover);
    plot.on("plotly_unhover", state.onPlotlyUnhover);
    plot.on("plotly_relayout", state.onPlotlyRelayout);
    plot.on("plotly_doubleclick", state.onPlotlyDoubleClick);
    plot.on("plotly_afterplot", state.onPlotlyAfterPlot);
    state.plotlyHandlersBound = true;
  }

  function bindPlot(plot) {
    if (!plot) {
      return;
    }
    const state = getPlotState(plot);
    bindResize(plot, state);
    bindDomHandlers(plot, state);
    bindPlotlyHandlers(plot, state);
    resizePlot(plot);
  }

  function refreshPlots() {
    hideTooltip();
    document.querySelectorAll(".js-plotly-plot").forEach(bindPlot);
  }

  function scan() {
    scanScheduled = false;
    refreshPlots();
  }

  function scheduleScan() {
    if (scanScheduled) {
      return;
    }
    scanScheduled = true;
    window.requestAnimationFrame(scan);
  }

  function init() {
    tooltip = ensureTooltip();
    document.body.classList.add(READY_CLASS);
    tooltip.hidden = true;
    scheduleScan();

    window.addEventListener("resize", () => {
      scheduleScan();
    });

    window.addEventListener("blur", hideTooltip);
    window.addEventListener("focus", () => {
      scheduleScan();
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        hideTooltip();
        return;
      }
      scheduleScan();
    });

    const observer = new MutationObserver(() => {
      scheduleScan();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  if (document.body) {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  }
})();
