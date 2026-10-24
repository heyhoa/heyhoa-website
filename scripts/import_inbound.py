"""Turn exported mail (and call/text logs) into an eval corpus for hey.

Input, any mix:
  *.mbox            Gmail Takeout, Thunderbird, or `readpst -e` output converted to mbox
  folder of *.eml   Outlook "Save as", readpst -e, Apple Mail
  *.csv             call logs / text exports with columns: date, direction, from, to, body[, subject]

Output: corpus/inbound.jsonl (one message per line), threads reconstructed
by subject + participants, PII lightly redacted (emails, phones, dollar
account numbers), plus corpus/summary.json with counts by month and sender
domain. Nothing leaves the machine; review the JSONL before sharing.

Usage: python scripts/import_inbound.py path/to/export [more paths...] --out corpus --redact
"""
from __future__ import annotations

import argparse
import csv
import email
import hashlib
import json
import mailbox
import re
import sys
from collections import Counter
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}")
ACCT_RE = re.compile(r"\b(?:acct|account|routing)\s*#?\s*\d{4,}\b", re.I)


def redact(text: str) -> str:
    text = EMAIL_RE.sub(lambda m: "email:" + hashlib.sha1(m.group(0).lower().encode()).hexdigest()[:8], text)
    text = PHONE_RE.sub("[phone]", text)
    text = ACCT_RE.sub("[account]", text)
    return text


def _hdr(msg, name):
    raw = msg.get(name, "")
    try:
        return str(make_header(decode_header(raw)))
    except Exception:  # noqa: BLE001
        return raw


def _body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get("Content-Disposition", "").startswith("attachment"):
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                except Exception:  # noqa: BLE001
                    continue
        return ""
    try:
        return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "replace")
    except Exception:  # noqa: BLE001
        return str(msg.get_payload())


def _strip_quotes(body: str) -> str:
    out = []
    for line in body.splitlines():
        if line.startswith(">") or re.match(r"^On .+ wrote:$", line.strip()) or line.strip().startswith("-----Original Message-----"):
            break
        out.append(line)
    return "\n".join(out).strip()


def from_message(msg, our_domains: set[str]) -> dict | None:
    frm = parseaddr(_hdr(msg, "From"))[1].lower()
    to = [parseaddr(a)[1].lower() for a in (_hdr(msg, "To") + "," + _hdr(msg, "Cc")).split(",") if "@" in a]
    try:
        date = parsedate_to_datetime(msg.get("Date")).isoformat()
    except Exception:  # noqa: BLE001
        date = ""
    subject = _hdr(msg, "Subject")
    body = _strip_quotes(_body(msg))
    if not body and not subject:
        return None
    direction = "out" if frm.split("@")[-1] in our_domains else "in"
    thread_key = re.sub(r"^(re|fwd?|fw):\s*", "", subject.strip().lower())
    thread_key = hashlib.sha1((thread_key + "|" + "|".join(sorted({frm, *to}))).encode()).hexdigest()[:10]
    attachments = [p.get_filename() for p in msg.walk() if p.get_filename()] if msg.is_multipart() else []
    return {"date": date, "direction": direction, "from": frm, "to": to, "subject": subject, "body": body[:6000], "thread": thread_key, "attachments": attachments, "channel": "email"}


def read_mbox(path: Path, our_domains):
    for msg in mailbox.mbox(str(path)):
        rec = from_message(msg, our_domains)
        if rec:
            yield rec


def read_eml_dir(path: Path, our_domains):
    for p in sorted(path.rglob("*.eml")):
        with open(p, "rb") as f:
            rec = from_message(email.message_from_binary_file(f), our_domains)
        if rec:
            yield rec


def read_csv(path: Path, our_domains):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            body = r.get("body") or r.get("text") or r.get("transcript") or r.get("notes") or ""
            yield {"date": r.get("date") or r.get("timestamp") or "", "direction": (r.get("direction") or "in").lower()[:3], "from": (r.get("from") or "").lower(), "to": [(r.get("to") or "").lower()],
                   "subject": r.get("subject") or r.get("reason") or "", "body": body[:6000], "thread": hashlib.sha1((r.get("from", "") + r.get("to", "")).encode()).hexdigest()[:10], "attachments": [], "channel": r.get("channel") or ("call" if "transcript" in r else "sms")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default="corpus")
    ap.add_argument("--redact", action="store_true")
    ap.add_argument("--our-domains", default="heyhoa.com,heywoodrealty.com", help="comma list; mail from these domains is 'out'")
    args = ap.parse_args()
    ours = {d.strip().lower() for d in args.our_domains.split(",") if d.strip()}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    n, months, domains, channels, threads = 0, Counter(), Counter(), Counter(), set()
    with open(out / "inbound.jsonl", "w", encoding="utf-8") as fo:
        for raw in args.paths:
            p = Path(raw)
            it = read_mbox(p, ours) if p.suffix == ".mbox" or (p.is_file() and p.suffix == "") else read_csv(p, ours) if p.suffix == ".csv" else read_eml_dir(p, ours)
            for rec in it:
                if args.redact:
                    rec["body"] = redact(rec["body"])
                    rec["subject"] = redact(rec["subject"])
                    rec["from"] = redact(rec["from"])
                    rec["to"] = [redact(t) for t in rec["to"]]
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                months[rec["date"][:7] or "unknown"] += 1
                domains[rec["from"].split("@")[-1] if "@" in rec["from"] else "n/a"] += 1
                channels[rec["channel"]] += 1
                threads.add(rec["thread"])
    summary = {"messages": n, "threads": len(threads), "by_month": dict(sorted(months.items())), "by_channel": dict(channels), "top_sender_domains": domains.most_common(15), "redacted": args.redact}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if n == 0:
        sys.exit("no messages found; check the path and format")


if __name__ == "__main__":
    main()
