# Connectors

Connectors turn the exports of banks, cards and payment services into Cashflow's **canonical transaction record**. Tabular exports (CSV) are described by **YAML definitions**, so a new bank needs no code.

```
connectors/
├── schema/connector.schema.json   JSON Schema of the definition language (v0.1)
├── definitions/<id>.yaml          one definition per export format
└── fixtures/<id>/<case>/          synthetic input.<ext> + expected.json (golden output)
```

| Id | Provider / format | Status |
|---|---|---|
| [`de.sparkasse.csv-camt-v2`](definitions/de.sparkasse.csv-camt-v2.yaml) | Sparkasse "CSV-CAMT V2" | `draft` |
| [`de.dkb.csv-2023`](definitions/de.dkb.csv-2023.yaml) | DKB, CSV layout since 2023 | `draft` |

Status: `draft` = written from documentation, never checked against a real export · `community` = checked against a real export · `verified` = also has fixtures from an anonymised real export.

## How a definition works

A definition says how to decode the file (`input`: encoding, delimiter, header row, preamble), how to read numbers and dates (`locale`), how to recognise the format (`detect`), which rows to skip (`filters`), how each canonical field is filled (`fields`: from a column, a constant or the preamble, with transforms, regex, value maps and cases), and how the sign is expressed (`direction`).

* Annotated example: [`definitions/de.dkb.csv-2023.yaml`](definitions/de.dkb.csv-2023.yaml).
* Every key is described in the [JSON Schema](schema/connector.schema.json); the `# yaml-language-server` line gives completion in editors.
* The exact semantics are defined by the reference interpreter [`tools/connector_ref.py`](../tools/connector_ref.py). The app's Kotlin engine must produce the same `expected.json` for every fixture.

## The canonical record

Amounts are absolute decimal strings; `direction` (`debit`/`credit`) carries the sign. Absent values are omitted.

* **Generated:** `id` (UUIDv8 from the fingerprint), `fingerprint`, `row_number`, `direction`.
* **Required:** `booking_date`, `amount`, `currency`, and `account_iban` or `account_external_id`.
* **Optional:** `value_date`, `transaction_datetime`, `status` (default `booked`), `counterparty_name/iban/bic`, `remittance_information`, `booking_text`, `creditor_id`, `mandate_reference`, `end_to_end_id`, `merchant_category_code`, `original_amount/currency`, `exchange_rate`, `fee_amount`, `external_id`, `related_external_id`, `category_hint`.

Per file the result also lists the `accounts` seen, `balances` from the preamble and `skipped_rows`. The fingerprint rules are in [DESIGN.md](../docs/DESIGN.md#identity-and-de-duplication).

## Adding a connector

1. **Never commit real data.** Keep your real export in `/private/` (git-ignored).
2. Copy an existing definition to `definitions/<id>.yaml` and adapt it.
3. Create `fixtures/<id>/basic/input.<ext>`: a **synthetic** file with exactly the structure of the real export (encoding, delimiter, quoting, preamble), made-up names, test IBANs and invented amounts. Include debits and credits, a pending row, empty optional fields and two identical rows.
4. Generate the golden file and check every value by hand:

   ```bash
   python tools/validate.py --update-golden
   git diff connectors/fixtures/
   ```

5. Run `python tools/validate.py` until it passes, then open a pull request.
