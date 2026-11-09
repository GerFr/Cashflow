/**
 * Cashflow UI - import view
 * -------------------------
 * Drop or choose a bank export, send it to POST /api/parse and show what the
 * connector read. All values are written with textContent (never innerHTML),
 * because they come straight from the file.
 */
const CashflowImport = (function () {
  let selectedFile = null;

  function element(id) {
    return document.getElementById(id);
  }

  function showError(message) {
    const node = element("import-error");
    node.textContent = message;
    node.hidden = !message;
  }

  function selectFile(file) {
    selectedFile = file || null;
    const label = element("file-name");
    label.textContent = selectedFile ? selectedFile.name : "";
    label.hidden = !selectedFile;
    element("parse").disabled = !selectedFile;
    showError("");
  }

  function cell(row, text, className) {
    const td = document.createElement("td");
    td.textContent = text;
    if (className) td.className = className;
    row.appendChild(td);
  }

  function renderResult(result) {
    element("result-connector").textContent = `${result.connector.id} ${result.connector.version}`;
    element("result-accounts").textContent = result.accounts.join(", ") || "-";
    element("result-count").textContent = String(result.transactions.length);
    element("result-skipped").textContent = String(result.skipped_rows.length);
    const balance = result.balances[0];
    element("result-balance").textContent = balance
      ? `${CashflowFormat.money(balance.balance, "EUR")} on ${CashflowFormat.date(balance.date)}`
      : "-";

    const body = element("result-rows");
    body.replaceChildren();
    result.transactions.forEach((tx) => {
      const row = document.createElement("tr");
      if (tx.status === "pending") row.className = "pending";
      cell(row, CashflowFormat.date(tx.booking_date));
      cell(row, tx.counterparty_name || "-");
      cell(row, tx.remittance_information || tx.booking_text || "-");
      cell(row, tx.status);
      cell(row, CashflowFormat.money(tx.amount, tx.currency, tx.direction), `num ${tx.direction}`);
      body.appendChild(row);
    });
    element("import-result").hidden = false;
  }

  async function submit(event) {
    event.preventDefault();
    if (!selectedFile) return;
    const button = element("parse");
    button.disabled = true;
    showError("");
    try {
      renderResult(await CashflowAPI.parseFile(selectedFile, element("connector").value));
    } catch (error) {
      element("import-result").hidden = true;
      showError(error.message);
    } finally {
      button.disabled = false;
    }
  }

  async function loadConnectors() {
    const select = element("connector");
    try {
      const connectors = await CashflowAPI.fetchConnectors();
      connectors.forEach((connector) => {
        const option = document.createElement("option");
        option.value = connector.id;
        option.textContent = connector.name;
        select.appendChild(option);
      });
    } catch (error) {
      showError(`Could not load formats: ${error.message}`);
    }
  }

  function init() {
    const zone = element("drop-zone");
    element("file").addEventListener("change", (event) => selectFile(event.target.files[0]));
    ["dragenter", "dragover"].forEach((type) =>
      zone.addEventListener(type, (event) => {
        event.preventDefault();
        zone.classList.add("dragging");
      }),
    );
    ["dragleave", "drop"].forEach((type) =>
      zone.addEventListener(type, () => zone.classList.remove("dragging")),
    );
    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      selectFile(event.dataTransfer.files[0]);
    });
    element("import-form").addEventListener("submit", submit);
    loadConnectors();
  }

  return { init };
})();
