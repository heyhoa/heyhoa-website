# hey hoa

AI-first accounting and back office for self-managed HOAs and condos. One Flask codebase, three surfaces:

- **Marketing site** at `/` (dark theme, public pricing, quote form)
- **Homeowner portal** at `/me` (pay, ledger, requests, ARC, documents, ask hey)
- **Board portal** at `/board` (financials, approve payments, delinquencies, ARC, vendors, announcements, meetings)
- **hey ops** at `/ops` (the admin console: work items, six agent lanes, review queue, messages, audit)

Accounting data comes through a provider interface; `mock` ships realistic demo data, `frontsteps` talks to the FrontSteps / Caliber CAPI2 API.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # defaults: mock provider, demo AI
flask --app run seed            # creates instance/heyhoa.db with demo rows
flask --app run run --debug     # http://127.0.0.1:5000
pytest -q                       # every route renders
```

Demo logins (no password): `/login/board?demo=1`, `/login/homeowner?demo=1` and `/login/ops?demo=1`. In ops, click "Run daily agents now" to populate the review queue from demo data.

Set `ANTHROPIC_API_KEY` to make `hey` answer with Claude instead of the rule-based demo. Set `ACCOUNTING_PROVIDER=frontsteps` plus `FRONTSTEPS_API_KEY` to read real association data.

## Agents on the other side

`python -m app.mcp_server` exposes the same capabilities as the portals over MCP, scoped by token (homeowner, board, vendor, realtor, public). Owners' and boards' own assistants file requests, check balances, approve invoices and order closing documents; every write becomes a reviewed work item in hey ops. Discovery at `/.well-known/hey-agent.json`; each community has a public page at `/c/<slug>` and a JSON twin at `/c/<slug>.json`.

## The plan

Start at [docs/00-README.md](docs/00-README.md). Business model, marketing, go-to-market, brand, launch plan, outreach campaigns, product spec, architecture, and the phased roadmap with checkboxes are all there. Brand assets are in `brand/`.

## Layout

```
app/            Flask application (blueprints, templates, static, integrations, ai)
brand/          hey mark SVGs
docs/           plan + FrontSteps API spec and generated reference
scripts/        tooling (API reference generator, GitHub issue creator)
tests/          smoke tests
```
