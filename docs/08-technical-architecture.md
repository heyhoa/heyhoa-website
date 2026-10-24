# 08 · Technical architecture

## Stack
- **Flask 3** application factory, blueprints per app surface, Jinja templates, one CSS file (`app/static/css/hey.css`), one JS file, no front-end build step.
- **SQLAlchemy** (SQLite in dev, Postgres in prod) for local tables: leads, messages, portal requests, announcements, audit log.
- **Provider interface** (`app/integrations/base.py`) for all accounting data. Implementations: `mock.py` (demo), `frontsteps.py` (FrontSteps / Caliber CAPI2). Selected by `ACCOUNTING_PROVIDER`.
- **AI** (`app/ai/`) via the Anthropic Python SDK; demo mode without a key.
- **Auth**: session role + demo persona now; Phase 2 adds magic-link email login and FrontSteps `/api/v2/login` validation.

## Repository layout
```
run.py / wsgi.py            entry points
app/__init__.py             create_app, filters, CLI (flask seed)
app/config.py               env-driven config (.env.example)
app/brand.py                brand copy + pricing tiers (single source for site and docs)
app/models.py               local tables
app/services/               leads (scoring), auth (role_required), seed
app/integrations/           base (interface), registry, mock, frontsteps
app/ai/                     prompts, assistant (live + demo)
app/blueprints/marketing    public site + content.py (services, FAQs, reviews, posts)
app/blueprints/auth         login/logout
app/blueprints/homeowner    /me/*
app/blueprints/board        /board/*
app/blueprints/api          /api/* (health, provider ping, ask, leads)
app/templates/              base.html (dark), portal/base.html (light shell), partials/hey-mark.html
app/static/                 css, js, img, brand svgs
brand/                      logo SVG sources
docs/                       this plan; docs/api holds the FrontSteps swagger
scripts/                    gen_frontsteps_reference.py
tests/                      smoke tests for every route
```

## Request flow
Template → route → `get_provider()` → provider method → dataclasses → template. Routes never import a vendor client directly. Mutations (approve invoice, create request) go through the provider and are also written to `AuditLog` / `PortalRequest` locally so we have our own history even if the vendor API is append-only.

## FrontSteps / Caliber API (CAPI2)
- Spec: `docs/api/frontsteps-caliber-v2.swagger.json` (Swagger 2.0, "Caliber API v2", 310 paths). Human-readable: `docs/10-frontsteps-api-reference.md` (regenerate with `python scripts/gen_frontsteps_reference.py`).
- Sandbox base: `https://frontsteps.cloud/CAPI2_APISandbox`. Tenants: `https://<tenant>.frontsteps.cloud/CAPI2_<Tenant>`.
- Auth: `apiKey` header. Optional HTTP Basic (owner/board credentials) scopes `clientlist` to one association.
- Responses are typed `Object` in the spec. `frontsteps.py` parses defensively (`_g`, `_list`) and isolates all key-name assumptions in `_map_*` helpers. First job with a real key: hit `/api/v2/ping`, `/api/v2/clientlist`, one `client/{id}/chartofaccounts`, one `unitaccount/{id}/ledger/0/2026-01-01`, and fix the mappings.

### Endpoint map by portal feature
| Feature | Endpoints |
|---|---|
| Community list / profile | `GET clientlist`, `GET client/{id}`, `GET client/{id}/factsheet`, `GET client/{id}/logo` |
| Owners & units | `GET client/{id}/units`, `client/{id}/owners/current`, `unit/{id}/currentowners`, `contact/{id}` |
| Homeowner ledger / statements | `GET unitaccount/{id}`, `unitaccount/{id}/ledger/{tAcct}/{from}`, `unitaccount/{id}/statements`, `unitaccount/{id}/openchargessummary/{tAcct}` |
| Autopay | `GET/PUT/POST unitaccount/{id}/ach`, `.../achpaymentplan`, `GET .../achoptions` |
| Online payment | `GET paymentproviders` (hosted redirect), `POST payment`, `POST paymentaccepted`, `POST payment/{id}/void` |
| Financials | `GET client/{id}/chartofaccounts`, `client/{id}/transactionaccounts`, `client/{id}/transactions/{tAcct}/{since}`, `client/{id}/appliedpayments/{start}/{end}`, `client/{id}/charges/{since}` |
| AP approvals | `GET client/{id}/invoices?histType`, `invoice/{id}/details`, `invoice/{id}/lineitems`, `invoice/{id}/documents`, `POST invoice`, `POST invoice/{id}/{clientContactId}/action` |
| Delinquencies / fines | `GET client/{id}/delinquencies`, `unitaccount/{id}/delinquencies`, `POST postfine` |
| Maintenance | `GET client/{id}/maintenance[/all]`, `client/{id}/workorders/open`, `POST unit/{id}/servicerequest`, `maintenance/{id}/*` |
| ARC | `GET architectural/types`, `client/{id}/architecturalitems`, `unitaccount/{id}/architectural`, `POST architectural/savenew`, `POST architectural/boardapprove`, `POST architectural/note`, document upload endpoints |
| Violations | `GET client/{id}/violations/open`, `violation/{id}/*`, `POST violation` |
| Documents | `GET client/{id}/documents`, `document/{id}`, `unitaccount/{id}/documents` |
| Vendors / 1099 | `GET vendorlist`, `vendor/{id}`, `vendor/{id}/insurance`, `vendor/{id}/payments/{days}`, `client/{id}/1099adj/{year}`, `POST vendor` |
| Resale / escrow | `GET client/{id}/resale`, `unit/{id}/resale`, `POST unit/{id}/escrowdocsalert`, `POST unitaccount/{unitId}/addnewowner` |
| Auth | `GET login` (Basic), `POST requestnewuseraccount`, `POST resetpassword`, `GET contact/multipass` |
| Health | `GET ping`, `GET time`, `GET mgmtco` |

## Financials pipeline
`flask snapshot-coa` runs nightly (cron) and copies every community's chart of accounts into `coa_snapshots`. `services/financials.py` derives the balance sheet (lifetime `Balance`), the YTD income statement (`FYBalance`), monthly activity (Δ `FYBalance` between snapshots) and budget vs actual (`budget_lines`). Bank reconciliation lives in Caliber with the First Citizens integration; we verify cash GL vs statement and show the status. See doc 12 for the full capability map and doc 13 for the close runbook.

## Adding a second backend
Implement `AccountingProvider` in `app/integrations/<vendor>.py`, register it in `registry.py`, run the smoke tests with `ACCOUNTING_PROVIDER=<vendor>`. The UI does not change.

## AI layer
- `ask()` assembles a bounded context (community facts, governing-doc excerpts, owner ledger or GL snapshot) and calls Claude with a cached system prompt. In Phase 3 the governing documents move to a retrieval index so citations come from the actual PDF text.
- Every AI output that leaves the building passes a human: drafts are stored, a person clicks send. Invoice notes are advisory; two board approvals release money.
- Logging: inputs, outputs, model, and the rule applied are written to `AuditLog` (Phase 2).

## Security & compliance (Phase 2 before real data)
Magic-link auth + session hardening; CSRF on all POSTs (Flask-WTF); role checks on every route (present); secrets via env; PII minimization in AI context; encrypted at rest (managed Postgres); no card data (hosted processor page); audit log immutable; backups daily; data export endpoint for boards.

## Deploy
- Dev: `pip install -r requirements.txt && flask --app run run --debug` (seed with `flask --app run seed`).
- Prod: Gunicorn behind a managed host (Render/Fly/Railway) with Postgres; `ACCOUNTING_PROVIDER=frontsteps`, `ANTHROPIC_API_KEY`, `SECRET_KEY`. Static via the same app for now; CDN later.
- CI: `pytest -q` on every push (GitHub Actions, Phase 1 task).
