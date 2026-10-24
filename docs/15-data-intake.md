# 15 · Delivering three months of real inbound, efficiently

Goal: every owner, board and vendor message Heywood received over ~90 days, plus what was sent back. That is hey's eval set and the first real test of the agent lanes. Thirty minutes of export on your side; the importer does the rest.

## The fastest route, by system
| Where it lives | Export | Time |
|---|---|---|
| **Google Workspace / Gmail** | Google Takeout → select only Mail → filter by label or date if you like → `.mbox` download. Include the Sent folder (that is "what was done about it"). | 10 min + download |
| **Microsoft 365 / Outlook** | Outlook desktop → File → Open & Export → Export to a file → `.pst` for the shared support mailbox and the Sent folder. We convert `.pst` with `readpst -e` into `.eml` files. Or: Microsoft Purview content search → export, if IT prefers. | 15 min |
| **A shared support mailbox** (support@…) | Same as above from the mailbox owner, or add the founder as a delegate and export from there. | 10 min |
| **Phone calls** | Carrier or VoIP portal (RingCentral, Google Voice, Twilio): export call log CSV with date, direction, from, to, duration; add voicemail transcripts if the system has them. If calls were logged in Caliber notes, export the notes report. | 10 min |
| **Texts** | Google Voice: Takeout → Voice (texts as HTML/JSON). RingCentral: Messages export. iPhone: iMazing or a CSV from the carrier. One CSV with date, direction, from, to, body. | 10–20 min |
| **Caliber notes** | Caliber → reports → owner notes / client notes for the period → CSV. These are the "what was done" trail for anything not answered by email. | 10 min |

Do not annotate anything by hand. The Sent folder, replies in threads and Caliber notes already say what happened.

## What we do with it
```bash
python scripts/import_inbound.py path/to/mail.mbox path/to/calls.csv path/to/texts.csv --out corpus --redact
```
- Produces `corpus/inbound.jsonl` (one message per line, threads reconstructed, quoted replies stripped) and `corpus/summary.json` (counts by month, channel and sender domain).
- `--redact` hashes email addresses and masks phone and account numbers so the corpus can be shared with the team and used for evals without personal data. Keep the unredacted export on your machine; we only need the JSONL.
- Attachments are listed by filename, not included. Invoices and statements come separately through the books-review flow.

## Then
1. hey classifies every inbound into the lane/category taxonomy; we review the distribution and fix the taxonomy where it is wrong.
2. For each thread with a human reply, the reply becomes the gold answer; hey drafts blind, and we score agreement. That number, by category, is the first honest measure of what hey can do alone.
3. Threads where hey is wrong become the escalation list and the community-brain gaps to fill in onboarding.

## How to get it to us
Upload the `.mbox` / `.pst` / CSVs to the repo's private storage (ask for the link) or run the importer locally and send `corpus/inbound.jsonl` and `summary.json`. The importer is pure Python, no dependencies, and prints the summary at the end.
