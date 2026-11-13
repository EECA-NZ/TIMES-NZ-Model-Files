// Keep chart type toggle labels visually aligned by syncing button widths.
(function () {
  if (window.__chartToggleWidthSyncInitialized) {
    return;
  }
  window.__chartToggleWidthSyncInitialized = true;

  let scheduled = false;

  function syncChartToggleWidths() {
    scheduled = false;

    document.querySelectorAll(".chart-toggle-bar .shiny-options-group").forEach((group) => {
      const buttons = Array.from(group.querySelectorAll(".radio-inline > span"));
      if (buttons.length === 0) {
        return;
      }

      buttons.forEach((button) => {
        button.style.width = "auto";
      });

      const maxWidth = Math.max(
        ...buttons.map((button) => Math.ceil(button.getBoundingClientRect().width))
      );

      buttons.forEach((button) => {
        button.style.width = `${maxWidth}px`;
      });
    });
  }

  function scheduleSync() {
    if (scheduled) {
      return;
    }
    scheduled = true;
    window.requestAnimationFrame(syncChartToggleWidths);
  }

  function nodeTouchesToggleBar(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) {
      return false;
    }
    return (
      node.matches?.(".chart-toggle-bar, .chart-toggle-bar *") ||
      Boolean(node.querySelector?.(".chart-toggle-bar"))
    );
  }

  function mutationsAffectToggleBar(mutations) {
    return mutations.some((mutation) =>
      [...mutation.addedNodes, ...mutation.removedNodes].some(nodeTouchesToggleBar)
    );
  }

  function init() {
    scheduleSync();

    window.addEventListener("resize", scheduleSync);

    const observer = new MutationObserver((mutations) => {
      if (mutationsAffectToggleBar(mutations)) {
        scheduleSync();
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    if (document.fonts?.ready) {
      document.fonts.ready.then(scheduleSync);
    }
  }

  if (document.body) {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  }
})();
