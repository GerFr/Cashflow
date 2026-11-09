/**
 * Cashflow UI - tabs
 * ------------------
 * One <section id="view-..."> per tab. The active view is kept in the URL
 * hash (#import, #bubbles, ...) so a reload stays on the same view.
 */
const CashflowTabs = (function () {
  function views() {
    return Array.from(document.querySelectorAll(".tab")).map((tab) => tab.dataset.view);
  }

  function show(view) {
    const target = views().includes(view) ? view : CashflowConfig.DEFAULT_VIEW;
    document.querySelectorAll(".tab").forEach((tab) => {
      const active = tab.dataset.view === target;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    document.querySelectorAll(".view").forEach((section) => {
      section.hidden = section.id !== `view-${target}`;
    });
    if (window.location.hash !== `#${target}`) {
      history.replaceState(null, "", `#${target}`);
    }
  }

  function init() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => show(tab.dataset.view));
    });
    window.addEventListener("hashchange", () => show(window.location.hash.slice(1)));
    show(window.location.hash.slice(1));
  }

  return { init, show };
})();
