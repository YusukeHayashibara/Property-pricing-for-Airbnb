# Contributing

This is a group project for **SSC0957 — Practical Data Science II**. This guide sets the shared workflow so the team can work in parallel without stepping on each other.

## Getting started

```bash
git clone https://github.com/YusukeHayashibara/Property-pricing-for-Airbnb.git
cd Property-pricing-for-Airbnb

# Option A: conda
conda env create -f environment.yml
conda activate airbnb-pricing-rio

# Option B: venv + pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # fill in API keys locally, never commit .env
```

## Branching model

- `main` — always working/presentable. Protected: no direct pushes.
- `feature/<short-description>` — new functionality (e.g. `feature/itbi-collector`).
- `fix/<short-description>` — bug fixes.
- `docs/<short-description>` — documentation-only changes.

Branch off the latest `main`, keep branches short-lived, and open a PR as soon as there's something reviewable.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(collection): add Inside Airbnb loader
fix(cleaning): handle missing lat/lon in ITBI records
docs: update data dictionary for price index
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Pull requests

1. Open a PR into `main` using the template in `.github/PULL_REQUEST_TEMPLATE.md`.
2. Link the related issue (if any).
3. Requires **at least 1 approval** from a teammate before merging.
4. CI (lint + tests, see `.github/workflows/ci.yml`) must pass.
5. Squash-merge to keep `main` history readable.

## Code style

- Format with `black`, imports sorted with `isort`, linted with `flake8`.
- Run before committing:
  ```bash
  black src tests
  isort src tests
  flake8 src tests
  ```
- Notebooks: clear outputs before committing (`jupyter nbconvert --clear-output`) and keep exploratory code in `notebooks/`; promote reusable logic to `src/`.

## Project structure conventions

- `src/` — importable, tested code, organized by pipeline stage (`collection`, `cleaning`, `features`, `modeling`, `visualization`).
- `notebooks/` — numbered, prefixed by stage and author initials, e.g. `01_collection_itbi_ab.ipynb`.
- `data/` — never commit raw or processed data; see `data/README.md`.
- `docs/` — project-level documentation (timeline, methodology, data dictionary, team roles).
- `obsidian-vault/` — shared knowledge base for meeting notes, literature review, and day-to-day decisions. Open the folder directly as an Obsidian vault.

## Team coordination

- Weekly sync: log notes in `obsidian-vault/06 - Meetings/`.
- Track tasks/issues on GitHub Issues; use labels `data`, `modeling`, `viz`, `docs`, `infra`.
- Roles and responsibilities are documented in `docs/TEAM.md`.

## Reporting issues

Use the templates under `.github/ISSUE_TEMPLATE/`. Include what data source / module is affected and how to reproduce the problem.
