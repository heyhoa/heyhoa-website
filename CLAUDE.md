# hey hoa

Flask 3 app: marketing site, board portal (`/board`), owner portal (`/me`), ops console (`/ops`), API and MCP.
Accounting lives in Caliber (FrontSteps) behind `AccountingProvider`; hey's own database holds everything else.
Agents run in lanes (`app/agents`), propose one action, and wait for a person in shadow mode.

## Rules that are not up for debate
- Strict cash basis. No receivable, payable or prepaid balances are stored.
- Software never moves money. Transfers, CDs and payments are executed by a person after a board decision.
- Owners never see delinquency, violations, other owners' balances or confidential invoices. Boards never see ops screens.
- API keys and secrets come from the environment, never from chat or code.
- No model identifiers in commits, PR text, code or comments.

## Product rules
- Keep it simple. The board's job is approve a bill, decide a question, read the package. Five nav entries for boards, four for owners, six for ops; everything else under More.
- Nothing to learn: no taglines, helper text or secondary labels in the portals. If a screen needs a sentence to make sense, fix the layout.
- One pattern everywhere: a list, click, a drawer, three buttons, an optional note.
- Plain words: bills, votes, owners behind, budget line. No GL, AP, AR, COA, quorum, memo.
- Phone first. Check the 390px screenshot before the desktop one. Tables that must work on a phone use the list component (`.inbox`), not `display: inline-block` hacks.
- Decide for UX, DX and AX together: the simplest screen, the smallest diff, and tools and prompts an agent can read without context.

## Code rules
- Portal component classes are prefixed (`ir-`, `inbox`, `drawer`, `firstmonth`) and scoped under `.shell`; grep `app/static/css/hey.css` before adding a class name. The marketing site owns the bare names.
- Portal pages extend `board/base.html`, `homeowner/base.html` or `ops/base.html`; drawers are macros in `board/_*_drawer.html`.
- Services hold logic (`app/services`), routes stay thin, templates stay dumb. Agents get data through tools in `app/agents/tools.py`.
- Every feature ships with a test in `tests/`. Run `rm -f instance/heyhoa.db; python3 -m pytest -q` before every commit; the mock invoice state is shared across tests, so do not assert on a specific vendor still being pending.
- Screenshots: start the app on a side port with `python3 -c "from app import create_app; create_app().run(port=NNNN)"` and stop it with `kill $(pgrep -f "port=NNNN")`. Never `pkill -f python3`.
- Commit with `git -c user.name="Claude" -c user.email="noreply@anthropic.com"` and the attribution trailers from the session. Push to the designated branch only.

## Where things are written down
- `docs/07-product-spec.md` product, `docs/13-operations-playbook.md` ops, `docs/17-data-model.md` data, `docs/09-roadmap-phases.md` what is next, `docs/04-brand-voice-style.md` voice and the spreadsheet rule.
