(function () {
  const READY_CLASS = "custom-plotly-hover-ready";
  const BOUND_ATTR = "data-custom-hover-bound";
  const TOOLTIP_ID = "custom-plotly-hover";

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
    tooltip.hidden = true;
    tooltip.innerHTML = "";
    activePlot = null;
  }

  function bindPlot(plot) {
    if (!plot || plot.getAttribute(BOUND_ATTR) === "true") {
      return;
    }
    plot.setAttribute(BOUND_ATTR, "true");

    plot.addEventListener("mousemove", (event) => {
      latestPointer = event;
      if (activePlot === plot) {
        positionTooltip(event);
      }
    });

    plot.addEventListener("mouseleave", hideTooltip);

    plot.on("plotly_hover", (eventData) => {
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
    });

    plot.on("plotly_unhover", hideTooltip);
    plot.on("plotly_relayout", hideTooltip);
    plot.on("plotly_doubleclick", hideTooltip);
  }

  function scan() {
    document.querySelectorAll(".js-plotly-plot").forEach(bindPlot);
  }

  function init() {
    tooltip = ensureTooltip();
    document.body.classList.add(READY_CLASS);
    tooltip.hidden = true;
    scan();

    const observer = new MutationObserver(() => {
      scan();
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
