"""The monthly financial package, as the founders defined it.

Board package: ten sections, in this order. Homeowner package: the first four.
Strict cash basis throughout. Bank statements come from First Citizens
Client Connect and are attached as received; we never generate them.
"""
BOARD_SECTIONS = [
    ("cover", "Branded cover sheet"),
    ("update", "Monthly update and change summary"),
    ("budget", "Budget comparison / P&L"),
    ("balance", "Balance sheet"),
    ("aged", "Aged owner balance report"),
    ("collections", "Collection report"),
    ("prepaid", "Prepaid report"),
    ("register", "Check register / AP distributions"),
    ("recon", "Bank reconciliation(s)"),
    ("statements", "Bank statement(s)"),
]
HOMEOWNER_SECTIONS = BOARD_SECTIONS[:4]


def sections(audience: str) -> list[tuple[str, str]]:
    return HOMEOWNER_SECTIONS if audience == "homeowner" else BOARD_SECTIONS
