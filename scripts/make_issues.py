"""Create one GitHub issue per unchecked roadmap box, grouped by phase milestone.

Usage: GITHUB_TOKEN=... python scripts/make_issues.py owner/repo [--dry-run]
Idempotent: skips boxes whose exact title already exists as an open issue.
"""
import os
import re
import sys
from pathlib import Path

import requests

ROADMAP = Path(__file__).resolve().parent.parent / "docs/09-roadmap-phases.md"


def parse():
    phase = None
    for line in ROADMAP.read_text().splitlines():
        m = re.match(r"^## (Phase \d+) — (.+)$", line)
        if m:
            phase = f"{m.group(1)}: {m.group(2).split('(')[0].strip()}"
            continue
        m = re.match(r"^- \[ \] (.+)$", line)
        if m and phase:
            yield phase, m.group(1).strip()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    repo = sys.argv[1]
    dry = "--dry-run" in sys.argv
    token = os.environ.get("GITHUB_TOKEN")
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"} if token else {}
    api = f"https://api.github.com/repos/{repo}"
    existing = set()
    milestones = {}
    if not dry:
        for issue in requests.get(f"{api}/issues?state=open&per_page=100", headers=h, timeout=30).json():
            existing.add(issue["title"])
        for ms in requests.get(f"{api}/milestones?state=all&per_page=100", headers=h, timeout=30).json():
            milestones[ms["title"]] = ms["number"]
    for phase, title in parse():
        if title in existing:
            continue
        if dry:
            print(f"[{phase}] {title}")
            continue
        if phase not in milestones:
            ms = requests.post(f"{api}/milestones", json={"title": phase}, headers=h, timeout=30).json()
            milestones[phase] = ms["number"]
        r = requests.post(f"{api}/issues", json={"title": title, "milestone": milestones[phase], "labels": [phase.split(":")[0].lower().replace(" ", "-")]}, headers=h, timeout=30)
        print(r.status_code, title)


if __name__ == "__main__":
    main()
