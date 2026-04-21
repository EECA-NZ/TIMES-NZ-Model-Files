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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleSync, { once: true });
  } else {
    scheduleSync();
  }

  window.addEventListener("resize", scheduleSync);

  const observer = new MutationObserver(scheduleSync);
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  if (document.fonts?.ready) {
    document.fonts.ready.then(scheduleSync);
  }
})();
