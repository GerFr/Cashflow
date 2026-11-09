/**
 * Cashflow UI - entry point
 */
(function () {
  async function checkConnection() {
    const badge = document.getElementById("connection");
    try {
      const health = await CashflowAPI.fetchHealth();
      badge.textContent = `Service ${health.version} · ${health.connectors} formats`;
      badge.className = "badge badge-success";
    } catch (error) {
      badge.textContent = "Service unreachable";
      badge.className = "badge badge-error";
    }
  }

  CashflowTabs.init();
  CashflowImport.init();
  checkConnection();
})();
