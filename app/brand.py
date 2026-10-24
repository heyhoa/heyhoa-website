"""Single source of truth for brand copy used across templates and docs."""

BRAND = {
    "name": "hey hoa",
    "short": "hey",
    "domain": "heyhoa.com",
    "email": "hello@heyhoa.com",
    "phone": "(800) 555-0199",
    "tagline": "You run the community. hey runs the books.",
    "one_liner": (
        "AI-first accounting and back office for self-managed HOAs and condos. "
        "Flat monthly price. No contracts. Financials on the 5th, every month."
    ),
    "promise": "Financials by the 5th. Every month. Or that month is free.",
    "colors": {
        "ink": "#080909",
        "paper": "#F0EDF4",
        "lime": "#C6FF00",
        "blue": "#2468FF",
        "red": "#FF0049",
        "muted": "#939098",
    },
}

PRICING = [
    {
        "slug": "books",
        "name": "Books",
        "price": 199,
        "unit_cap": "up to 30 doors",
        "per_door": "then $6/door",
        "tagline": "Accounting only. For boards who do everything else themselves.",
        "features": [
            "Monthly financial packet by the 5th",
            "Bank reconciliation and GL",
            "Dues billing and online payments",
            "Vendor bill pay (board approves, we pay)",
            "Year-end 1099s and tax-prep handoff",
            "Homeowner and board portals",
        ],
    },
    {
        "slug": "back-office",
        "name": "Back Office",
        "price": 349,
        "unit_cap": "up to 30 doors",
        "per_door": "then $9/door",
        "tagline": "Books plus the admin nobody on the board wants.",
        "featured": True,
        "features": [
            "Everything in Books",
            "Homeowner support line (phone, email, text) answered by hey",
            "Delinquency letters and collections workflow",
            "ARC request intake and routing",
            "Resale, escrow and lender documents",
            "Annual meeting notices, elections, minutes templates",
            "Document vault and homeowner directory",
        ],
    },
    {
        "slug": "board-plus",
        "name": "Board+",
        "price": 549,
        "unit_cap": "up to 30 doors",
        "per_door": "then $12/door",
        "tagline": "Back Office plus a named community coordinator.",
        "features": [
            "Everything in Back Office",
            "Named coordinator and quarterly board review",
            "Budget build and reserve-study coordination",
            "Vendor sourcing and bid summaries",
            "Violation tracking and notices",
            "Insurance renewal coordination",
        ],
    },
]

ADD_ONS = [
    ("Resale / estoppel certificate", "$150–$350 per transaction (paid by seller)"),
    ("Lender questionnaire", "$125 per request (paid by lender)"),
    ("Transfer / setup fee", "$0 — we eat onboarding"),
    ("Audit / review coordination", "Quoted per engagement"),
    ("Special assessment billing", "$2/door per cycle"),
    ("Paper statement mailing", "$1.25 per statement"),
]
