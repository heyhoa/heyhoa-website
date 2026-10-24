# Outreach

The sales lane in hey does the drafting and the calendar; a founder does the sending (shadow mode) until deliverability and tone are proven.

## Files
- `leads_template.csv` — columns the importer expects. Fill from Texas management certificates (Tex. Prop. Code § 209.004, county clerk + TREC database) or Arizona Corporation Commission filings; keep only self-managed boards (contact is a person or the association, not a management company).
- `scripts/outreach_import.py` — loads a CSV into leads, creates a sales work item per lead (touch 1 drafted) and schedules touches 2–5 on sequence A (days 4, 7, 11, 14). Everything lands in hey ops → Review queue for approval.

## Run
```bash
python scripts/outreach_import.py outreach/leads_template.csv --source "tx-mgmt-certs-2026-11"
flask --app run agents-daily     # each day: runs follow-ups that are due (also the Render cron)
```
Then open `/ops/review`, read each draft, edit if needed, approve. Mark a lead `contacted` or `lost` in `/ops/leads` to stop its sequence.

## Rules (doc 06)
Tue–Thu, 8–10am local. Plain text. One link. Personalize line one. Reply within the hour in business hours. Unsubscribe on request immediately.
