/**
 * Cashflow UI - formatting helpers
 * --------------------------------
 * Amounts arrive as absolute decimal strings plus a direction; they are only
 * turned into numbers for display, never for calculations.
 */
const CashflowFormat = (function () {
  const dateFormat = new Intl.DateTimeFormat(CashflowConfig.LOCALE, { dateStyle: "medium" });

  function money(amount, currency, direction) {
    const value = Number(amount) * (direction === "debit" ? -1 : 1);
    return new Intl.NumberFormat(CashflowConfig.LOCALE, {
      style: "currency",
      currency: currency || "EUR",
      signDisplay: direction ? "always" : "auto",
    }).format(value);
  }

  function date(isoDate) {
    if (!isoDate) return "-";
    return dateFormat.format(new Date(`${isoDate}T00:00:00`));
  }

  return { money, date };
})();
