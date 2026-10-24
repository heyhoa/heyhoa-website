"""Generate docs/10-frontsteps-api-reference.md from the committed Swagger spec.

Run: python scripts/gen_frontsteps_reference.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs/api/frontsteps-caliber-v2.swagger.json"
OUT = ROOT / "docs/10-frontsteps-api-reference.md"

# Which tags matter for which phase of our build.
PHASE_FOR_TAG = {
    "Login": "P2 portals auth", "Client": "P2 board portal", "ClientContact": "P2 board users",
    "Contact": "P2 homeowner users", "Unit": "P2 homeowner portal", "UnitAccount": "P2 homeowner ledger / autopay",
    "Invoice": "P3 AP approvals", "Payment": "P3 AR / payments", "Accounting": "P3 fines",
    "Vendor": "P3 vendors / 1099", "Architectural": "P3 ARC workflow", "Maintenance": "P3 requests",
    "CommonArea": "P3 requests", "Group": "P3 sub-associations", "Violation": "P4 compliance",
    "Misc": "P2 health / payment providers", "MgmtCo": "P2 branding", "BillingRecord": "P3 billing",
    "OtherPayee": "P3 AP", "Pet": "P4 directory", "FamilyMember": "P4 directory", "ClientContactGroup": "P4 committees", "CCR": "P4 governing docs",
}


def main():
    d = json.loads(SPEC.read_text())
    paths = d["paths"]
    tags = {}
    for p, ops in paths.items():
        for m, o in ops.items():
            for t in o.get("tags", ["Untagged"]):
                tags.setdefault(t, []).append((m.upper(), p, o))
    lines = [
        "# FrontSteps / Caliber API v2 reference (generated)",
        "",
        f"Source: `docs/api/frontsteps-caliber-v2.swagger.json` — title **{d['info']['title']}**, version {d['info']['version']}.",
        f"Base URL: `https://{d['host']}{d['basePath']}` (sandbox). Production tenants use `https://<tenant>.frontsteps.cloud/CAPI2_<Tenant>`.",
        "",
        "Auth: header `apiKey: <key>`. Owner/board-scoped reads also accept HTTP Basic (username:password) which narrows `clientlist` to that user's association.",
        "",
        f"{len(paths)} paths, {sum(len(v) for v in tags.values())} operations, {len(d.get('definitions', {}))} schema definitions.",
        "",
        "Regenerate with `python scripts/gen_frontsteps_reference.py`.",
        "",
        "## Endpoints by resource",
        "",
    ]
    for t in sorted(tags):
        lines.append(f"### {t}  ·  {len(tags[t])} ops  ·  used in: {PHASE_FOR_TAG.get(t, 'later')}")
        lines.append("")
        lines.append("| Method | Path | Summary |")
        lines.append("|---|---|---|")
        for m, p, o in tags[t]:
            summ = (o.get("summary") or o.get("description") or "").strip().replace("\n", " ").replace("|", "/")
            lines.append(f"| `{m}` | `{p}` | {summ[:110]} |")
        lines.append("")
    lines.append("## Schema definitions")
    lines.append("")
    for name, schema in sorted(d.get("definitions", {}).items()):
        props = ", ".join(schema.get("properties", {}).keys())
        lines.append(f"- **{name}**: {props}")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
