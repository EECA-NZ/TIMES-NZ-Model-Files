// Keep Plotly charts sized to their rendered container width.
(function () {
  if (window.__plotlyChartResizeInitialized) {
    return;
  }
  window.__plotlyChartResizeInitialized = true;

  const plotStates = new WeakMap();
  let refreshScheduled = false;

  function getPlotState(plot) {
    let state = plotStates.get(plot);
    if (!state) {
      state = {
        resizeObserver: null,
        resizeQueued: false,
        lastWidth: null,
      };
      plotStates.set(plot, state);
    }
    return state;
  }

  function getPlotContainer(plot) {
    return plot.closest(".shiny-ipywidget-output") || plot.parentElement || plot;
  }

  function queueResize(plot, state) {
    if (
      !plot ||
      !state ||
      !plot.isConnected ||
      !window.Plotly?.Plots?.resize ||
      state.resizeQueued
    ) {
      return;
    }

    state.resizeQueued = true;
    window.requestAnimationFrame(() => {
      state.resizeQueued = false;
      if (!plot.isConnected) {
        return;
      }

      const container = getPlotContainer(plot);
      const width = Math.floor(container.clientWidth || 0);
      if (width <= 0 || width === state.lastWidth) {
        return;
      }

      state.lastWidth = width;
      window.Plotly.Plots.resize(plot);
    });
  }

  function bindResizeObserver(plot, state) {
    if (!plot || state.resizeObserver) {
      return;
    }

    const observer = new ResizeObserver(() => {
      queueResize(plot, state);
    });

    const container = getPlotContainer(plot);
    observer.observe(container);
    if (container.parentElement) {
      observer.observe(container.parentElement);
    }

    state.resizeObserver = observer;
  }

  function bindPlot(plot) {
    if (!plot) {
      return;
    }

    const state = getPlotState(plot);
    bindResizeObserver(plot, state);
    queueResize(plot, state);
  }

  function refreshPlots() {
    document.querySelectorAll(".js-plotly-plot").forEach(bindPlot);
  }

  function scheduleRefresh() {
    if (refreshScheduled) {
      return;
    }
    refreshScheduled = true;
    window.requestAnimationFrame(() => {
      refreshScheduled = false;
      refreshPlots();
    });
  }

  function resizeVisiblePlots() {
    document.querySelectorAll(".js-plotly-plot").forEach((plot) => {
      const state = getPlotState(plot);
      bindResizeObserver(plot, state);
      queueResize(plot, state);
    });
  }

  function nodeContainsPlot(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) {
      return false;
    }
    return (
      node.matches?.(".js-plotly-plot") ||
      Boolean(node.querySelector?.(".js-plotly-plot"))
    );
  }

  function mutationsAffectPlots(mutations) {
    return mutations.some((mutation) =>
      [...mutation.addedNodes, ...mutation.removedNodes].some(nodeContainsPlot)
    );
  }

  function init() {
    scheduleRefresh();

    window.addEventListener("resize", resizeVisiblePlots);
    window.addEventListener("focus", resizeVisiblePlots);

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        resizeVisiblePlots();
      }
    });

    const observer = new MutationObserver((mutations) => {
      if (mutationsAffectPlots(mutations)) {
        scheduleRefresh();
      }
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
