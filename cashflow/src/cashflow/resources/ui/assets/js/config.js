/**
 * Cashflow UI - configuration
 * ---------------------------
 * The page is served by the Cashflow service itself (/app/), so the API is
 * same-origin and every request uses a relative URL: no CORS, no proxy.
 */
const CashflowConfig = (function () {
  const API_BASE = "/api";

  return {
    HEALTH_ENDPOINT: `${API_BASE}/health`,
    CONNECTORS_ENDPOINT: `${API_BASE}/connectors`,
    PARSE_ENDPOINT: `${API_BASE}/parse`,
    DEFAULT_VIEW: "import",
    LOCALE: "de-DE",
  };
})();
