# Contributing

* **Never commit real financial data**: no real bank exports, receipts, IBANs, card numbers or names, not even a few rows. Keep personal files in the git-ignored `/private/` folder. Test files are synthetic.
* Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:` …).
* Run the checks before opening a pull request:

  ```bash
  cd cashflow
  uv run ruff check && uv run ruff format --check
  uv run pytest
  ```

* A big design change gets a short entry in [docs/DECISIONS.md](docs/DECISIONS.md).
* Adding a bank: see [connectors/README.md](connectors/README.md).

By contributing you agree that your contribution is licensed under the licence of the directory you change: [AGPL-3.0-or-later](LICENSE) in general, [CC BY 4.0](ontology/LICENSE) inside `ontology/`.
