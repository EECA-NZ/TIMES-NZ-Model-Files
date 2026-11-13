// Replace Plotly's native hover UI with a custom tooltip card.
(function () {
  const DEBUG = false;
  const READY_CLASS = "custom-plotly-hover-ready";
  const BOUND_CLASS = "custom-plotly-hover-bound";
  const TOOLTIP_ID = "custom-plotly-hover";
  const plotStates = new WeakMap();
  let scanScheduled = false;
  let bootstrapIntervalId = null;
  let warmupTimerIds = [];

  function debug(...args) {
    if (DEBUG) {
      console.log("[custom-plotly-hover]", ...args);
    }
  }

  function getPlotDebugId(plot) {
    if (!plot) {
      return "unknown-plot";
    }

    const widget = plot.closest(".shiny-ipywidget-output");
    return (
      plot.id ||
      widget?.id ||
      widget?.getAttribute("data-output-id") ||
      plot.getAttribute("data-testid") ||
      `plot-${document.querySelectorAll(".js-plotly-plot").length}`
    );
  }

  function ensureTooltip() {
    let tooltip = document.getElementById(TOOLTIP_ID);
    if (!tooltip) {
      tooltip = document.createElement("div");
      tooltip.id = TOOLTIP_ID;
      tooltip.className = "custom-plotly-hover";
      document.body.appendChild(tooltip);
    }
    tooltip.hidden = true;
    tooltip.style.display = "none";
    tooltip.style.visibility = "hidden";
    return tooltip;
  }

  let tooltip = null;
  let activePlot = null;
  let latestPointer = null;

  function getPlotState(plot) {
    let state = plotStates.get(plot);
    if (!state) {
      state = {
        bindAttempts: 0,
        domBound: false,
        plotlyHandlersBound: false,
        onMouseMove: null,
        onMouseLeave: null,
        onPlotlyHover: null,
        onPlotlyUnhover: null,
        onPlotlyRelayout: null,
        onPlotlyDoubleClick: null,
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
    if (!event || !tooltip || tooltip.style.display === "none") {
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
    tooltip.style.display = "none";
    tooltip.style.visibility = "hidden";
    tooltip.innerHTML = "";
    activePlot = null;
  }

  function showTooltip(plot, html, event) {
    if (!tooltip) {
      return;
    }

    activePlot = plot;
    tooltip.innerHTML = html;
    tooltip.hidden = false;
    tooltip.style.display = "block";
    tooltip.style.visibility = "visible";

    if (event?.clientX != null && event?.clientY != null) {
      positionTooltip(event);
      return;
    }

    const rect = plot.getBoundingClientRect();
    positionTooltip({
      clientX: rect.left + Math.min(rect.width * 0.5, 80),
      clientY: rect.top + Math.min(rect.height * 0.25, 80),
    });
  }

  function hideNativeHoverLayer(plot) {
    plot.querySelectorAll(".hoverlayer").forEach((layer) => {
      layer.style.setProperty("display", "none", "important");
    });
  }

  function unbindPlotlyHandlers(plot, state) {
    if (!state.plotlyHandlersBound || typeof plot.removeListener !== "function") {
      return;
    }

    plot.removeListener("plotly_hover", state.onPlotlyHover);
    plot.removeListener("plotly_unhover", state.onPlotlyUnhover);
    plot.removeListener("plotly_relayout", state.onPlotlyRelayout);
    plot.removeListener("plotly_doubleclick", state.onPlotlyDoubleClick);
    plot.classList.remove(BOUND_CLASS);
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
    if (state.plotlyHandlersBound) {
      hideNativeHoverLayer(plot);
      return;
    }

    if (typeof plot.on !== "function") {
      if (state.bindAttempts < 30) {
        state.bindAttempts += 1;
        debug("plot.on not ready yet", getPlotDebugId(plot), {
          bindAttempts: state.bindAttempts,
        });
        scheduleScan();
      } else if (state.bindAttempts === 30) {
        debug("giving up waiting for plot.on", getPlotDebugId(plot));
      }
      return;
    }

    debug("binding plotly hover handlers", getPlotDebugId(plot));
    state.bindAttempts = 0;
    hideNativeHoverLayer(plot);

    state.onPlotlyHover = (eventData) => {
      const point = eventData && eventData.points && eventData.points[0];
      const html = getTooltipHtml(point);
      if (!html) {
        debug("hover event received but no tooltip html", getPlotDebugId(plot), {
          hasPoint: Boolean(point),
          customdataType: typeof point?.customdata,
          fullCustomdataType: typeof point?.fullData?.customdata,
        });
        hideTooltip();
        return;
      }
      hideNativeHoverLayer(plot);
      debug("hover event received with tooltip html", getPlotDebugId(plot), {
        htmlLength: html.length,
      });
      showTooltip(plot, html, latestPointer || eventData.event);
    };

    state.onPlotlyUnhover = hideTooltip;
    state.onPlotlyRelayout = hideTooltip;
    state.onPlotlyDoubleClick = hideTooltip;

    plot.on("plotly_hover", state.onPlotlyHover);
    plot.on("plotly_unhover", state.onPlotlyUnhover);
    plot.on("plotly_relayout", state.onPlotlyRelayout);
    plot.on("plotly_doubleclick", state.onPlotlyDoubleClick);
    plot.classList.add(BOUND_CLASS);
    state.plotlyHandlersBound = true;
  }

  function bindPlot(plot) {
    if (!plot) {
      return;
    }
    const state = getPlotState(plot);
    debug("binding plot candidate", getPlotDebugId(plot), {
      domBound: state.domBound,
      plotlyHandlersBound: state.plotlyHandlersBound,
      hasPlotOn: typeof plot.on === "function",
    });
    bindDomHandlers(plot, state);
    bindPlotlyHandlers(plot, state);
  }

  function refreshPlots() {
    hideTooltip();
    const plots = document.querySelectorAll(".js-plotly-plot");
    debug("refreshing plots", { count: plots.length });
    plots.forEach(bindPlot);
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

  function stopBootstrapPolling() {
    if (bootstrapIntervalId !== null) {
      window.clearInterval(bootstrapIntervalId);
      bootstrapIntervalId = null;
    }
  }

  function startBootstrapPolling(reason) {
    stopBootstrapPolling();

    const startedAt = Date.now();
    const maxDurationMs = 10000;
    const intervalMs = 250;

    const tick = () => {
      const plots = Array.from(document.querySelectorAll(".js-plotly-plot"));
      const allBound =
        plots.length > 0 &&
        plots.every((plot) => getPlotState(plot).plotlyHandlersBound);

      debug("bootstrap poll", {
        reason,
        plotCount: plots.length,
        allBound,
      });
      scheduleScan();

      if (allBound || Date.now() - startedAt >= maxDurationMs) {
        debug("stopping bootstrap poll", {
          reason,
          plotCount: plots.length,
          allBound,
        });
        stopBootstrapPolling();
      }
    };

    tick();
    bootstrapIntervalId = window.setInterval(tick, intervalMs);
  }

  function restartWarmupScans(reason) {
    warmupTimerIds.forEach((id) => window.clearTimeout(id));
    warmupTimerIds = [];

    [0, 120, 350, 800].forEach((delay) => {
      const timerId = window.setTimeout(() => {
        debug("warmup rescan", { reason, delay });
        scheduleScan();
      }, delay);
      warmupTimerIds.push(timerId);
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
    return mutations.some((mutation) => {
      if (
        mutation.type === "attributes" &&
        mutation.target instanceof Element &&
        nodeContainsPlot(mutation.target)
      ) {
        return true;
      }

      return [...mutation.addedNodes, ...mutation.removedNodes].some(nodeContainsPlot);
    });
  }

  function init() {
    debug("initializing custom hover script");
    tooltip = ensureTooltip();
    document.body.classList.add(READY_CLASS);
    tooltip.hidden = true;
    restartWarmupScans("init");
    startBootstrapPolling("init");

    window.addEventListener("blur", hideTooltip);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        hideTooltip();
        return;
      }
      restartWarmupScans("visibilitychange");
      startBootstrapPolling("visibilitychange");
    });

    const observer = new MutationObserver((mutations) => {
      if (mutationsAffectPlots(mutations)) {
        debug("mutation affecting plot detected", { mutationCount: mutations.length });
        restartWarmupScans("mutation");
        startBootstrapPolling("mutation");
      }
    });

    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
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
