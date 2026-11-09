/**
 * Cashflow UI - import view
 * -------------------------
 * Drop or choose a bank export → "Check file" sends it to POST /api/imports and
 * shows what the import would do (new, already imported, pending replaced) →
 * "Import" commits the preview. Values from the file are written with
 * textContent only (never innerHTML).
 */
const CashflowImport = (function () {
  const STATE_LABELS = {
    new: "new",
    duplicate: "already imported",
    replaces_pending: "replaces pending",
  };
  let selectedFile = null;
  let preview = null;

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
    element("check").disabled = !selectedFile;
    element("import-result").hidden = true;
    showError("");
  }

  function cell(row, text, className) {
    const td = document.createElement("td");
    td.textContent = text;
    if (className) td.className = className;
    row.appendChild(td);
  }

  function chip(list, text, tone) {
    const li = document.createElement("li");
    li.className = `chip chip-${tone}`;
    li.textContent = text;
    list.appendChild(li);
  }

  function writes(counts) {
    return counts.new + counts.replaces_pending + counts.removes_pending;
  }

  function renderPreview(result) {
    preview = result;
    element("result-connector").textContent = result.connector.name;
    element("result-accounts").textContent =
      [...new Set(result.transactions.map((tx) => tx.account_iban || tx.account_external_id))].join(", ") || "-";
    const balance = result.balances[0];
    element("result-balance").textContent = balance
      ? `${CashflowFormat.money(balance.balance, "EUR")} on ${CashflowFormat.date(balance.date)}`
      : "-";

    const counts = result.counts;
    const list = element("result-counts");
    list.replaceChildren();
    chip(list, `${counts.new} new`, counts.new ? "accent" : "neutral");
    chip(list, `${counts.duplicate} already imported`, "neutral");
    if (counts.replaces_pending) chip(list, `${counts.replaces_pending} pending → booked`, "accent");
    if (counts.removes_pending) chip(list, `${counts.removes_pending} outdated pending removed`, "warning");

    const notes = [];
    if (result.new_accounts.length) notes.push(`New account: ${result.new_accounts.join(", ")}.`);
    if (result.already_imported) notes.push("This exact file was imported before.");
    const notice = element("result-notice");
    notice.textContent = notes.join(" ");
    notice.hidden = !notes.length;

    const button = element("commit");
    button.textContent = writes(counts) ? `Import ${writes(counts)} changes` : "Save balances only";
    button.disabled = false;
    element("import-done").hidden = true;

    const body = element("result-rows");
    body.replaceChildren();
    result.transactions.forEach((tx) => {
      const row = document.createElement("tr");
      row.className = [tx.status === "pending" ? "pending" : "", tx.state === "duplicate" ? "duplicate" : ""].join(" ");
      cell(row, CashflowFormat.date(tx.booking_date));
      cell(row, tx.counterparty_name || "-");
      cell(row, tx.remittance_information || tx.booking_text || "-");
      cell(row, tx.status === "pending" ? `${STATE_LABELS[tx.state]} (pending)` : STATE_LABELS[tx.state]);
      cell(row, CashflowFormat.money(tx.amount, tx.currency, tx.direction), `num ${tx.direction}`);
      body.appendChild(row);
    });
    element("import-result").hidden = false;
  }

  async function check(event) {
    event.preventDefault();
    if (!selectedFile) return;
    const button = element("check");
    button.disabled = true;
    showError("");
    try {
      renderPreview(await CashflowAPI.previewImport(selectedFile, element("connector").value));
    } catch (error) {
      element("import-result").hidden = true;
      showError(error.message);
    } finally {
      button.disabled = false;
    }
  }

  async function commit() {
    if (!preview) return;
    const button = element("commit");
    button.disabled = true;
    showError("");
    try {
      const run = await CashflowAPI.commitImport(preview.id);
      preview = null;
      const done = element("import-done");
      done.textContent = `Imported: ${run.new} new, ${run.replaced_pending} pending booked, ${run.duplicate} already there.`;
      done.hidden = false;
      CashflowAccounts.refresh();
    } catch (error) {
      button.disabled = false;
      showError(error.message);
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
    element("import-form").addEventListener("submit", check);
    element("commit").addEventListener("click", commit);
    loadConnectors();
  }

  return { init };
})();
