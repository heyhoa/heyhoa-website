"""Marketing copy that is easier to edit as data than as template markup."""

SERVICES = {
    "accounting": {
        "title": "HOA accounting",
        "eyebrow": "Books",
        "lede": "Clean books, reconciled every month, delivered by the 5th. The part of the job your treasurer never signed up for.",
        "bullets": [
            "Monthly financial packet: balance sheet, income vs budget, bank rec, AR aging, AP aging, GL detail",
            "Dues billing, ACH autopay, cards, lockbox, coupon books if you must",
            "Vendor bill intake: every invoice is read, coded and matched to the contract before the board sees it",
            "Bank reconciliation with every transaction tied to a document",
            "Year end: 1099s filed, audit or review package assembled, tax prep handoff",
            "Budget build with a draft from last year's actuals and the reserve study",
        ],
        "ai": "hey reads every invoice, bank line and owner message. It codes the transaction, checks it against the contract and the budget, and shows the board only the exceptions.",
    },
    "back-office": {
        "title": "Back office support",
        "eyebrow": "Back office",
        "lede": "Everything that lands in a volunteer's inbox at 9pm. We answer it, log it and route it.",
        "bullets": [
            "Homeowner support line: phone, email and text, answered in minutes, logged to the owner record",
            "Delinquency letters on the schedule your policy sets, with a human review before anything escalates",
            "ARC request intake, routing to your committee, decision letters",
            "Resale certificates, estoppels, lender questionnaires and escrow demands, turned around in 3 business days",
            "Annual meeting notices, proxies, ballots and minutes templates",
            "Document vault and owner directory, kept current from closings and move-ins",
        ],
        "ai": "Owner questions get an instant, sourced answer from your own documents and ledger. Anything hey is not sure about goes to a person, not to voicemail.",
    },
    "collections": {
        "title": "Collections",
        "eyebrow": "Collections",
        "lede": "Firm, fair and documented. Most balances clear before anyone needs an attorney.",
        "bullets": [
            "Late notice the day after the due date, not thirty days later",
            "A written collection policy the board adopts by resolution: rebill at 15 days, demand at 30, intent to lien at 60, lien at 75, further action at 90",
            "No lien and no attorney until the balance is $400 or 75 days, whichever comes first",
            "Collection fees charged to the late account, not spread across the neighbors",
            "Payment plans the owner can set up themselves in the portal",
            "Attorney handoff packet when the board votes to escalate",
            "Board sees stage, balance and next action for every late account on one screen",
        ],
        "ai": "hey drafts every notice from the owner's ledger and your policy, in your voice. A person signs off before it leaves.",
    },
}

FAQS = [
    ("Do we have to switch banks?", "Operating and reserve accounts are opened at our partner bank, in the association's name and tax ID, with your board as signers. That is what makes daily bank feeds and same-day reconciliation possible. If the board wants to keep a different bank, it is $50 per account per month."),
    ("Who holds the money?", "The association does. Accounts are in the association's name and tax ID at an FDIC-insured bank. We process payments from them only for bills the board has approved in the portal, insurance, taxes and our own invoice. Every disbursement is logged where the board can see it."),
    ("What does onboarding look like?", "Three weeks, typically. Week one we collect documents and bank access. Week two we rebuild your books in parallel. Week three we reconcile to your last statement and go live. You keep paying bills the old way until we say switch."),
    ("Is there a contract?", "Yes, a plain-language services agreement with Arizona governing law. Thirty days' notice, a 60-day cure period on either side, and your data exports in standard formats whenever you want it. No multi-year lock-in."),
    ("Who answers the phone?", "A person, during business hours. hey handles the first pass on email and text around the clock and hands anything it cannot source to a teammate."),
    ("What if we already use QuickBooks?", "We will migrate it. If your board wants to keep the file, we can keep it current as a mirror."),
    ("Do you manage the property?", "No. We do not inspect, do not run vendors on site, and do not attend meetings in person. You run the community. We run the back office. That is why we cost a third of a management company."),
    ("What size community is a fit?", "Fifteen to about two hundred doors, self managed. Smaller works if you just want the books done. Larger works if you have an on-site manager and need the accounting."),
    ("How is hey different from a remote management firm?", "Price, speed and transparency. Our pricing and our fee schedule are public. Financials land on the 5th or that month is free. Every number in your packet links to its source document."),
    ("Do you use AI on our data?", "Yes, and the agreement says so plainly. hey reads invoices, bank lines, documents and owner messages to draft and to check. A person reviews before any notice, letter or payment goes out. Model providers do not train on your data, and your records stay yours."),
]

REVIEWS = [
    ("The first month, they found $4,100 in duplicate landscaping payments our old firm never caught. That paid for the year.", "Dana W., Treasurer, 48-unit townhome community, TX"),
    ("Financials on the 5th. Every month. I used to chase our manager for three weeks.", "Luis C., President, 36-unit condo, CO"),
    ("Owners text a question and get an answer with a link to the bylaws in about a minute. The board group chat went quiet.", "Grace T., Secretary, 112-lot HOA, NC"),
    ("We left a full-service manager and cut our admin cost by 60%. Nothing got worse. Most things got better.", "Ken Y., Treasurer, 64-unit community, AZ"),
    ("Collections were awkward when neighbors did it. Now the letters go out on schedule, politely, and the balances clear.", "Riya P., President, 28-unit townhomes, GA"),
    ("Onboarding was three weeks. They rebuilt two years of books and reconciled to the penny.", "Omar H., Treasurer, 22-unit condo, WA"),
]

POSTS = {
    "myth-of-full-service-management": {
        "title": "The myth of full-service management",
        "date": "2026-10-10",
        "summary": "Most small communities pay for a manager who shows up once a month and a back office they never see. Here is what you actually need, and what it should cost.",
        "body": [
            "A full-service management contract for a 50-unit community usually runs $1,200 to $2,000 a month. Ask what that buys and you get a list: accounting, collections, owner communication, vendor coordination, meeting attendance, inspections.",
            "Look closer. Accounting is done in a central office by someone your board will never meet. Collections run on a schedule the software sets. Owner communication is a shared inbox. Vendor coordination means forwarding your email. The manager attends one meeting a month and drives through once.",
            "The parts a board cannot do itself are the first three. They are also the parts that do not need anyone on site. The parts that do need someone on site are the parts most boards are already doing: walking the property, picking the landscaper, deciding what to fix.",
            "Self-managed communities that outsource only the back office typically land between $300 and $700 a month and keep every decision in the room where it belongs.",
        ],
    },
    "financials-by-the-fifth": {
        "title": "Why we promise financials by the 5th",
        "date": "2026-09-22",
        "summary": "Late financials are the single most common complaint we hear from boards. Here is how we make the date, and what happens if we miss it.",
        "body": [
            "Boards tell us their packet shows up on the 20th, the 25th, sometimes the following month. By then the meeting has happened and the numbers are history.",
            "We close by the 5th because every transaction is coded the day it posts, not at month end. Bank feeds land daily. Invoices are read when they arrive. Reconciliation is a check, not a project.",
            "If a packet is late, that month is free. Not a credit, not an apology. Free. We have written it into the agreement because it is the only promise that changes how a firm behaves.",
        ],
    },
    "what-to-ask-before-you-switch": {
        "title": "Twelve questions to ask before you switch accountants",
        "date": "2026-09-02",
        "summary": "A checklist for treasurers comparing HOA accounting firms. Print it and bring it to the sales call.",
        "body": [
            "1. When will we receive monthly financials, and what happens if you miss it? 2. Can we see a sample packet? 3. Who reconciles the bank, and can we see the reconciliation? 4. How do owners pay, and what are the fees? 5. Who codes vendor invoices, and how do you catch duplicates? 6. How many board approvals does a payment need? 7. What is the collections schedule and who approves escalation? 8. How do we export our data if we leave? 9. What is the contract term? 10. What is the total monthly cost for our door count, including add-ons? 11. Who answers homeowner calls? 12. Can we talk to a current client our size?",
        ],
    },
}
