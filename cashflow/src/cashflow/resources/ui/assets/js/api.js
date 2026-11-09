/**
 * Cashflow UI - API client
 * ------------------------
 * All fetch() calls live here so the UI modules stay free of transport details.
 *
 *   GET   /api/health                 - service status
 *   GET   /api/connectors             - known export formats
 *   POST  /api/imports                - check a file (raw bytes + X-Filename) → preview
 *   POST  /api/imports/{id}/commit    - write a preview to the database
 *   GET   /api/accounts               - accounts with balances
 *   PATCH /api/accounts/{id}          - name, liquid flag, opening balance
 */
const CashflowAPI = (function () {
  async function readError(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await response.json().catch(() => null);
      if (body && body.detail) {
        if (Array.isArray(body.detail)) return body.detail.map((d) => d.msg).join("; ");
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

  /** Send the file's bytes; connectorId is optional (empty = detect). Nothing is stored yet. */
  function previewImport(file, connectorId) {
    const url = new URL(CashflowConfig.IMPORTS_ENDPOINT, window.location.origin);
    if (connectorId) url.searchParams.set("connector", connectorId);
    return request(url, {
      method: "POST",
      headers: { "X-Filename": encodeURIComponent(file.name) },
      body: file,
    });
  }

  function commitImport(previewId) {
    return request(`${CashflowConfig.IMPORTS_ENDPOINT}/${encodeURIComponent(previewId)}/commit`, { method: "POST" });
  }

  function fetchAccounts() {
    return request(CashflowConfig.ACCOUNTS_ENDPOINT);
  }

  function updateAccount(accountId, change) {
    return request(`${CashflowConfig.ACCOUNTS_ENDPOINT}/${encodeURIComponent(accountId)}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(change),
    });
  }

  return { fetchHealth, fetchConnectors, previewImport, commitImport, fetchAccounts, updateAccount };
})();
