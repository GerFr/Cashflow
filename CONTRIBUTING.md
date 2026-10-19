# Contributing to Cashflow

Thanks for your interest! Cashflow is in its planning phase (milestone M0). The most valuable contributions right now are:

* **Feedback on the [Lastenheft](docs/LASTENHEFT.md)**: missing features, unclear acceptance criteria, wrong priorities.
* **Answers to the [open questions](docs/LASTENHEFT.md#10-open-questions)**.
* **Knowledge about bank exports**: how does your bank's export look? Open a *Connector request* issue (header row only, never real data), or contribute a definition with a synthetic fixture ([connectors/README.md](connectors/README.md)).
* **Ontology improvements**: see [ontology/README.md](ontology/README.md).

## Privacy first

Financial data is sensitive. **Never** commit, attach or paste real bank exports, receipts, IBANs, card numbers or names, not even "just a few rows". Use the git-ignored `/private/` folder for your own files.

## Tracking features

* Every feature has an ID in the Lastenheft (e.g. `LF-ANA-01`). Reference it in issues, commits and pull requests.
* New ideas start as an issue using the **Feature request** template. Once agreed, the feature gets a row in the Lastenheft with priority and milestone.
* A pull request that completes a feature updates its status in the Lastenheft (see its §8 *Acceptance*).

## Workflow

1. Open an issue for anything non-trivial before you start.
2. Fork, create a branch, make focused commits.
3. Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:` …) and reference feature IDs.
4. Sign off your commits (`git commit -s`) to certify the [Developer Certificate of Origin](https://developercertificate.org/).
5. Run the checks locally:

   ```bash
   pip install -r tools/requirements.txt
   python tools/validate.py
   ```

6. Open a pull request.

Architecturally significant changes need an ADR in [docs/adr/](docs/adr/). A new feature goes into the Lastenheft; its technical requirements go into the [Pflichtenheft](docs/SPECIFICATION.md) together with a row in its traceability matrix (§17).

## Licence of contributions

By contributing you agree that your contribution is licensed under the licence of the directory you change: [AGPL-3.0-or-later](LICENSE) in general, [CC BY 4.0](ontology/LICENSE) inside `ontology/`.
