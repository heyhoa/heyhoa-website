"""Import an outreach CSV into leads and the sales lane.

Usage: python scripts/outreach_import.py outreach/leads.csv --source "tx-mgmt-certs-2026-11" [--dry-run]
Each row becomes a Lead (source = --source) and a sales work item with touch 1 drafted,
plus scheduled follow-ups. Review and send from /ops/review.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.services.leads import create_lead  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--source", default="outbound")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    app = create_app()
    with app.test_request_context():
        rows = list(csv.DictReader(open(args.csv, newline="", encoding="utf-8")))
        print(f"{len(rows)} rows")
        for r in rows:
            if not r.get("email"):
                print("skip (no email):", r.get("community_name"))
                continue
            if args.dry_run:
                print("would import:", r["community_name"], r["email"])
                continue
            lead = create_lead(r, source=args.source)
            print(f"lead {lead.id} score {lead.score}: {lead.community_name} <{lead.email}>")


if __name__ == "__main__":
    main()
