# Connectors

Connectors translate the exports of banks, cards, payment services and brokers into Cashflow's canonical transaction record, which the core maps onto the [ontology](../ontology/). They are a central part of the project. Architecture: [ADR-0004](../docs/adr/0004-connector-architecture.md); requirements: [SPECIFICATION §6.2](../docs/SPECIFICATION.md#62-connectors--import-con).

```
connectors/
├── schema/connector.schema.json   JSON Schema of the declarative DSL (v0.1)
├── definitions/<id>.yaml          one declarative connector per export format
└── fixtures/<id>/<case>/          input.<ext> + expected.json (golden canonical output)
```

## Three tiers

| Tier | What | When |
|---|---|---|
| 1 | Native Rust parsers in `cf-connectors` | Open standards: ISO 20022 camt.052/053/054, MT940 |
| 2 | **Declarative YAML definitions** (this directory) | Tabular exports: CSV today, XLSX/JSON later |
| 3 | Sandboxed WebAssembly components | Anything else: multi-file ZIPs, PDFs, nested JSON |

Prefer tier 2. A definition is reviewable data that is safe to run.

## Status of definitions

| Id | Provider / format | Status | Fixtures |
|---|---|---|---|
| [`de.sparkasse.csv-camt-v2`](definitions/de.sparkasse.csv-camt-v2.yaml) | Sparkasse, "CSV-CAMT V2" | `draft` | [basic](fixtures/de.sparkasse.csv-camt-v2/basic/) |
| [`de.dkb.csv-2023`](definitions/de.dkb.csv-2023.yaml) | DKB, CSV layout since 2023 | `draft` | [basic](fixtures/de.dkb.csv-2023/basic/) |

The full first-wave target list is in [SPECIFICATION §6.2.3](../docs/SPECIFICATION.md#623-first-wave-connector-catalogue).

**Maturity levels**

* `draft`: written from documentation or memory; never checked against a real export.
* `community`: at least one user confirmed it against a real export (`verified_against` set).
* `verified`: `community` + fixtures derived from a real, anonymised export + checked within the last 12 months.

## The canonical record

Every tier emits records with these fields (absent values are omitted). Amounts are absolute decimal strings with at least two decimals; `direction` carries the sign.

| Field | Required | Ontology | Meaning |
|---|---|---|---|
| `id` | generated | IRI `urn:uuid:<id>` | UUIDv8 derived from `fingerprint` |
| `fingerprint` | generated | `cf:fingerprint` | SHA-256 over canonical fields + occurrence index |
| `row_number` | generated | `cf:rowNumber` | 1-based physical line of the record in the file |
| `account_iban` / `account_external_id` | one of them | `cf:account` → `cf:iban` / `cf:externalAccountId` | The user's own account |
| `booking_date` | ✔ | `cf:bookingDate` | ISO date |
| `value_date` | | `cf:valueDate` | ISO date |
| `transaction_datetime` | | `cf:transactionDateTime` | ISO date-time of the purchase |
| `direction` | generated | `cf:direction` | `debit` or `credit` |
| `amount` | ✔ | `cf:amount` | Absolute amount in account currency |
| `currency` | ✔ | `cf:currency` | ISO 4217 |
| `original_amount`, `original_currency`, `exchange_rate` | | `cf:originalAmount`, `cf:exchangeRate` | Foreign-currency details |
| `fee_amount` | | `cf:fee` | Provider fee |
| `status` | default `booked` | `cf:status` | `booked` or `pending` |
| `counterparty_name`, `counterparty_iban`, `counterparty_bic` | | `cf:counterpartyName/Iban/Bic` | Other party as delivered |
| `remittance_information` | | `cf:remittanceInformation` | Verwendungszweck |
| `booking_text` | | `cf:bookingText` | Buchungstext / transaction type |
| `creditor_id`, `mandate_reference`, `end_to_end_id` | | `cf:creditorId`, … | SEPA references |
| `merchant_category_code` | | `cf:merchantCategoryCode` | ISO 18245 MCC |
| `external_id`, `related_external_id` | | `cf:externalId`, `cf:relatedExternalId` | Provider transaction ids, for linking |
| `category_hint` | | category assignment `cf:BySource` | Provider category text |

Per file, the result also lists the `accounts` seen, `balances` read from the preamble, and `skipped_rows`.

## DSL reference (v0.1)

A complete, validated example: [`definitions/de.dkb.csv-2023.yaml`](definitions/de.dkb.csv-2023.yaml).

### Top level

| Key | Meaning |
|---|---|
| `dsl_version` | Always `"0.1"` for now. |
| `id` | `<country or intl>.<provider>.<format>`, equal to the file name. |
| `name`, `version`, `status`, `verified_against`, `maintainers`, `notes` | Metadata. Bump the **major** version whenever the output for the same input changes. |
| `institution` | `name`, `country` (ISO 3166-1), optional `bic`, `website`. |
| `account_kind` | `CheckingAccount`, `SavingsAccount`, `CreditCardAccount`, `PaymentServiceAccount`, `BrokerageCashAccount` or `CashWallet`. |
| `input` | File decoding: `type: csv`, `encoding`, `delimiter`, `quote`, `header`, `preamble`, `skip_empty_rows`. |
| `locale` | `decimal_separator`, `thousands_separator`, `date_formats` (tried in order; `%d %m %y %Y %H %M %S`). |
| `detect` | `required_columns` that must all appear in the header (used for automatic detection), optional `filename_patterns`. |
| `filters.exclude_if` | Conditions; matching rows are skipped and reported. |
| `fields` | Canonical field → value specification. |
| `direction` | `{mode: signed_amount}` (negative = debit) or `{mode: indicator_column, column, debit_values, credit_values}`. |

### Header and preamble

* `header.row: 1` — fixed header row (1-based, counted in CSV records), or
* `header.find_row_containing: [...]` — first row that contains all listed cells.
* `preamble.<name>: {row_matches, cell, regex?, type?, transform?}` — reads a value from the rows *before* the header: the first row whose first cell matches `row_matches`, cell index `cell` (0-based). Values are available to fields via `from_preamble`. The names `closing_balance` + `closing_balance_date` produce a balance observation.

### Value specifications

Exactly one source:

* `column: <header name>`
* `const: <string>`
* `from_preamble: <name>`

Then, in this order:

1. `transform`: `trim`, `collapse_whitespace`, `remove_spaces`, `upper`, `lower`, `strip_currency_symbol`;
2. empty values and `null_values` (e.g. SEPA's `NOTPROVIDED`) become absent;
3. `regex`: keep the first capture group (no match → absent);
4. `map`: translate raw values (unmapped values are an **error**, so new provider values are noticed);
5. `type`: `string` (default), `date`, `datetime`, `decimal`.

**Cases** pick the first matching alternative:

```yaml
counterparty_name:
  cases:
    - when: { column: Umsatztyp, equals: Ausgang }
      column: Zahlungsempfänger*in
    - column: Zahlungspflichtige*r      # no 'when' = default
```

**Conditions** (`when`, `filters.exclude_if`) test the raw cell of `column` with any combination of `equals`, `in`, `matches` (regex search), `empty`, `negative` (parses as a negative decimal); all given tests must hold.

### Identity

`fingerprint` = SHA-256 over account, booking date, value date, direction, amount, currency, counterparty IBAN, normalised counterparty name, normalised remittance information, end-to-end id, external id and an occurrence index (counts identical rows within the file). `id` = UUIDv8 (RFC 9562, SHA-256 name-based) of the fingerprint. Re-importing overlapping exports therefore yields the same ids on every device. The exact algorithm is `fingerprint_base` in [`tools/connector_ref.py`](../tools/connector_ref.py).

## Adding a connector

1. **Never commit real data.** Work with your real export only locally (e.g. in `/private/`, which is git-ignored).
2. Copy an existing definition to `definitions/<id>.yaml` and adapt it. The `# yaml-language-server: $schema=…` line gives you completion and validation in VS Code and other editors.
3. Create `fixtures/<id>/basic/input.<ext>`: a **synthetic** file with the exact structure of the real export (same encoding, delimiter, quoting, preamble, line endings), using made-up names, published test IBANs and invented amounts. Cover booked and pending rows, debits and credits, empty optional fields and two identical rows.
4. Generate the golden file and review every value by hand:

   ```bash
   python tools/validate.py --update-golden
   git diff connectors/fixtures/
   ```

5. Run `python tools/validate.py` until all checks pass, then open a PR. Mention how you obtained the export (menu path) and whether you checked it against a real file. That decides the status.

Requesting a connector without writing it: use the **Connector request** issue template and share only the header row.

## Reference interpreter

[`tools/connector_ref.py`](../tools/connector_ref.py) implements the DSL in Python and is the executable specification used in CI. The production engine (Rust crate `cf-connectors`, milestone M1) must produce identical `expected.json` output for every fixture.
