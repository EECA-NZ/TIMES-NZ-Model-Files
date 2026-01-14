

function setExpanded(wrapper, expanded) {
  const btn = wrapper.querySelector(".table-expand-btn");

  wrapper.classList.toggle("fullscreen", expanded);

  if (btn) {
    btn.textContent = expanded ? "⤡ Close" : "⤢ Expand table";
    btn.setAttribute("aria-expanded", expanded ? "true" : "false");
  }

  document.documentElement.classList.toggle("table-no-scroll", expanded);
  document.body.classList.toggle("table-no-scroll", expanded);
}




document.addEventListener("DOMContentLoaded", () => {
    
    document.querySelectorAll(".expandable-table").forEach((wrapper) => {
    
    // Avoid double-init
    if (wrapper.dataset.expandInit === "1") return;
    wrapper.dataset.expandInit = "1";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "table-expand-btn";
    btn.textContent = "Expand table";
    btn.setAttribute("aria-expanded", "false");

    btn.addEventListener("click", () => {
      setExpanded(wrapper, !wrapper.classList.contains("fullscreen"));
    });

    // Put button above the table
    wrapper.prepend(btn);
  });
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document
      .querySelectorAll(".expandable-table")
      .forEach(w => setExpanded(w, false));
  }
});

