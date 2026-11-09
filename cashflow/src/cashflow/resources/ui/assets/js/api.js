/**
 * Cashflow UI - API client
 * ------------------------
 * All fetch() calls live here so the UI modules stay free of transport details.
 *
 *   GET  /api/health      - service status
 *   GET  /api/connectors  - known export formats
 *   POST /api/parse       - parse a bank export (raw bytes + X-Filename)
 */
const CashflowAPI = (function () {
  async function readError(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await response.json().catch(() => null);
      if (body && body.detail) {
        return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    }
    return response.statusText || `HTTP ${response.status}`;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: { accept: "application/json", ...(options.headers || {}) },
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    return response.json();
  }

  function fetchHealth() {
    return request(CashflowConfig.HEALTH_ENDPOINT);
  }

  function fetchConnectors() {
    return request(CashflowConfig.CONNECTORS_ENDPOINT);
  }

  /** Send the file's bytes; connectorId is optional (empty = detect). */
  function parseFile(file, connectorId) {
    const url = new URL(CashflowConfig.PARSE_ENDPOINT, window.location.origin);
    if (connectorId) url.searchParams.set("connector", connectorId);
    return request(url, {
      method: "POST",
      headers: { "X-Filename": encodeURIComponent(file.name) },
      body: file,
    });
  }

  return { fetchHealth, fetchConnectors, parseFile };
})();
