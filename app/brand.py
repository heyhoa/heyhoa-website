"""Single source of truth for brand copy used across templates and docs."""

BRAND = {
    "name": "hey hoa",
    "short": "hey",
    "domain": "heyhoa.com",
    "legal_entity": "Heywood Realty & Investment, Inc.",
    "legal_state": "Arizona",
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

# Fee schedule. Mirrors Exhibit A of the services agreement (docs/11), with the
# items Exhibit A bills to the association folded into the flat tier price.
ASSOCIATION_FEES = [
    ("Client setup / onboarding", "Included"),
    ("Statements, e-statements, portal, document storage", "Included"),
    ("1099 / 1096 filing and tax file prep", "Included (Books and up)"),
    ("Online invoice approval, vendor insurance tracking", "Included"),
    ("Meeting minutes drafts", "Included (Back Office and up)"),
    ("ARC form administration", "Included (Back Office and up)"),
    ("Compliance violation letters", "Included on Board+, otherwise $5 each"),
    ("Board meeting attendance (video)", "$125 per hour, 1 week notice"),
    ("Paper statement mailing", "$1.25 per statement + postage"),
    ("Certified letter", "$45"),
    ("Non-partner bank account", "$50 per account per month"),
    ("Special assessment or loan setup", "$500 setup + $2 per door per cycle"),
    ("Online voting setup and admin", "$300 per election"),
    ("Registered agent / corporation report filing", "$135 per year / $75 per filing"),
    ("Audits, records requests, litigation support, custom reports", "Quoted, billed monthly"),
]

OWNER_FEES = [
    ("Late notice (past due)", "$0"),
    ("Rebill notice (15 days)", "$45"),
    ("Pre-legal demand (30 days)", "$45"),
    ("Intent to lien (60 days)", "$105"),
    ("Lien recording and notice (75 days)", "$205"),
    ("Lien release", "$95"),
    ("Intent to further legal action (90 days)", "$45"),
    ("Attorney referral and file turnover", "$215"),
    ("Payment plan setup / breach notice", "$75 / $45"),
    ("NSF or chargeback", "$49"),
    ("Resale / disclosure package", "$275 (statutory cap applies) · rush $100"),
    ("Lender questionnaire standard / custom", "$250 / $350"),
    ("Lender refinance statement", "$150"),
]

# Backwards-compatible alias used by older templates.
ADD_ONS = ASSOCIATION_FEES

# Exhibit B collection ladder (days past due -> step). Lien or attorney only
# once balance >= $400 or account >= 75 days past due.
COLLECTION_STAGES = [
    ("late_notice", 1, "Late notice", 0),
    ("rebill", 15, "Rebill notice", 45),
    ("demand", 30, "Pre-legal demand", 45),
    ("intent_to_lien", 60, "Intent to lien", 105),
    ("lien", 75, "Lien recorded", 205),
    ("further_action", 90, "Intent to further legal action", 45),
    ("attorney", 91, "Attorney referral", 215),
]
LIEN_THRESHOLD = {"balance": 400, "days": 75}
