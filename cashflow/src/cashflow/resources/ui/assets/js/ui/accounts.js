/**
 * Cashflow UI - accounts view
 * ---------------------------
 * Accounts with their latest known balance, the liquid flag (counts towards
 * liquid net worth) and the opening balance for accounts whose exports carry
 * no balance. Balances that disagree with an export are shown as a warning:
 * usually an export is missing for that period.
 */
const CashflowAccounts = (function () {
  function element(id) {
    return document.getElementById(id);
  }

  function showError(message) {
    const node = element("accounts-error");
    node.textContent = message;
    node.hidden = !message;
  }

  async function save(account, change) {
    showError("");
    try {
      await CashflowAPI.updateAccount(account.id, change);
      await refresh();
    } catch (error) {
      showError(`${account.name}: ${error.message}`);
    }
  }

  function nameCell(account) {
    const td = document.createElement("td");
    const name = document.createElement("div");
    name.textContent = account.name;
    const detail = document.createElement("div");
    detail.className = "muted small";
    detail.textContent = `${account.iban || account.external_id} · ${account.transactions} transactions`;
    td.append(name, detail);
    account.mismatches.forEach((m) => {
      const warning = document.createElement("div");
      warning.className = "message-warning small";
      warning.textContent =
        `Balance on ${CashflowFormat.date(m.date)} (${m.source}) differs by ` +
        `${CashflowFormat.money(m.difference, account.currency)} from the computed one; is an export missing?`;
      td.appendChild(warning);
    });
    return td;
  }

  function balanceCell(account) {
    const td = document.createElement("td");
    td.className = "num";
    if (account.balance) {
      td.textContent = CashflowFormat.money(account.balance.amount, account.currency);
      const when = document.createElement("div");
      when.className = "muted small";
      when.textContent = CashflowFormat.date(account.balance.date);
      td.appendChild(when);
    } else {
      td.textContent = "unknown";
      td.classList.add("muted");
    }
    return td;
  }

  function liquidCell(account) {
    const td = document.createElement("td");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = account.liquid;
    box.setAttribute("aria-label", `Count ${account.name} towards liquid net worth`);
    box.addEventListener("change", () => save(account, { liquid: box.checked }));
    td.appendChild(box);
    return td;
  }

  function openingCell(account) {
    const td = document.createElement("td");
    const form = document.createElement("form");
    form.className = "inline-form";
    const amount = document.createElement("input");
    amount.type = "text";
    amount.inputMode = "decimal";
    amount.placeholder = account.balance ? "optional" : "needed";
    amount.size = 9;
    amount.value = account.opening_balance ? account.opening_balance.amount : "";
    amount.setAttribute("aria-label", `Opening balance of ${account.name}`);
    const when = document.createElement("input");
    when.type = "date";
    when.value = account.opening_balance ? account.opening_balance.date : "";
    when.setAttribute("aria-label", "Opening balance date (default: day before the first transaction)");
    const button = document.createElement("button");
    button.type = "submit";
    button.className = "button button-small";
    button.textContent = "Set";
    form.append(amount, when, button);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      // "1.234,56" (German) or "1234.56": a comma marks the decimals, dots are then thousands separators.
      const raw = amount.value.trim().replace(/\s|€/g, "");
      const value = raw.includes(",") ? raw.replace(/\./g, "").replace(",", ".") : raw;
      const change = value ? { amount: value, date: when.value || null } : null;
      save(account, { opening_balance: change });
    });
    td.appendChild(form);
    return td;
  }

  function render(accounts) {
    const body = element("accounts-rows");
    body.replaceChildren();
    accounts.forEach((account) => {
      const row = document.createElement("tr");
      if (!account.liquid) row.className = "excluded";
      const type = document.createElement("td");
      type.textContent = CashflowFormat.kind(account.kind);
      row.append(nameCell(account), type, balanceCell(account), liquidCell(account), openingCell(account));
      body.appendChild(row);
    });
    element("accounts-table").hidden = !accounts.length;
    element("accounts-empty").hidden = accounts.length > 0;

    const liquid = accounts.filter((a) => a.liquid && a.balance);
    const total = liquid.reduce((sum, a) => sum + Math.round(Number(a.balance.amount) * 100), 0) / 100;
    const unknown = accounts.filter((a) => a.liquid && !a.balance).length;
    element("accounts-total").textContent = accounts.length
      ? `${CashflowFormat.money(total, "EUR")}${unknown ? ` (+ ${unknown} without balance)` : ""}`
      : "-";
  }

  async function refresh() {
    try {
      render(await CashflowAPI.fetchAccounts());
    } catch (error) {
      showError(`Could not load accounts: ${error.message}`);
    }
  }

  return { init: refresh, refresh };
})();
