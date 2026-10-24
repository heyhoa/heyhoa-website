# 04 · Brand voice & style

Reference: Block's Dessa page (block.xyz/dessa). What we borrow: a handwritten lowercase script wordmark dropped **inside** a large, tight sans-serif headline as if it were a person's name; one clean sans-serif family for everything; generous type sizes that hold up on a phone; one accent; short declarative headlines with a turn in the second line ("You learned to talk by listening. So did dessa."). What we do not borrow: the research-lab tone. We are a service for tired volunteers.

## The mark
- `hey` is a handwritten lowercase script. Source of truth: `brand/hey-mark.svg` (traced from the original PNG; 2 paths, evenodd). Variants: `-white`, `-lime`, `-currentcolor`, and square tiles `hey-tile-lime.svg`, `hey-tile-lime-rounded.svg`, `hey-tile-dark.svg`.
- The company name is written **hey hoa**, lowercase, in body copy. In headlines the script mark replaces the word "hey" and is sized to the x-height plus a little (`.hey { height: .92em }` inline; `.98em` in h1).
- The mark is a name, so it can be a subject: "**hey** runs the books." "Say **hey**." "Ask **hey**." Never "the hey".
- Clear space: the height of the "h" ascender on all sides. Minimum size: 24px tall on screen.
- Never outline it, add a drop shadow, rotate it, or set it in a different script font.

## Headline formula
Sentence one states what the board already does or knows. Sentence two turns, with `hey` doing the work.
- You run the community. **hey** runs the books.
- You learned to pay dues by mail. **hey** didn't.
- Your treasurer has a day job. **hey** doesn't.
- Boards decide. **hey** does the paperwork.
Keep headlines under 12 words. Period at the end. No exclamation marks anywhere in the brand.

## Color
| Token | Hex | Use |
|---|---|---|
| ink | `#080909` | Type, primary dark buttons, portal sidebar, optional dark sections |
| paper | `#F0EDF4` | Type on ink; near-white page tint |
| lime | `#C6FF00` | One accent: primary buttons, the mark on dark tiles, check marks, progress. Never body text, never large fills behind text except buttons and the CTA card |
| blue | `#2468FF` | Links on light backgrounds, info pills |
| red | `#FF0049` | Errors, "no" lists, overdue |
| muted | `#939098` | Secondary text on ink |
Everything is light by default: white page, ink type, soft grey (`#F6F5F8`) cards, lime only on buttons and the CTA card. `theme-dark` exists as an opt-in for a single section or a launch page; the portal sidebar is always ink.

## Type
- **One family: Figtree** (Google Fonts). It is the closest free match to Cash Sans, the face Dessa uses: friendly rounded grotesque, single-story g, slanted terminals.
- **Headlines:** Figtree 500 (medium, not bold), letter-spacing −0.035em at h1, −0.03em below, line-height 1.0–1.04. h1 is `clamp(2.75rem, 11vw, 5.75rem)`, so about 43px on a phone and 92px on a desktop.
- **Body:** Figtree 400, 18px, line-height 1.5. Lede paragraphs `clamp(1.2rem, 4.8vw, 1.45rem)`. Nothing on a phone is smaller than 16px except table labels.
- **Mono (labels, numbers, eyebrows):** Space Grotesk, uppercase eyebrows at 0.78rem with 0.08em tracking.
- Numbers in tables use tabular figures, right-aligned.

## Voice
**Plain. Warm. Short. Certain.** We write like the most competent person on the board who also happens to be kind.
- Lead with the answer. Then the source. Then the next step.
- One idea per sentence. Verbs over nouns. "We reconcile the bank" not "bank reconciliation is performed."
- Name the promise and the penalty together: "by the 5th or the month is free."
- Say what we are not: not a law firm, not a CPA firm, not a property manager. It builds trust and keeps us legal.
- No exclamation marks, no emoji in marketing, no "leverage", "seamless", "robust", "solutions", "empower", "cutting-edge AI".
- "AI" appears in body copy sparingly; `hey` the character carries it. Explain what it did ("read the invoice, matched the contract") not what it is.
- Numbers are specific: "28% above the 12-month average", not "unusually high".
- Owners are "owners" or "homeowners", never "residents" or "users". Boards are "the board" or "your board". The product is "the portal".

### Do / don't
| Do | Don't |
|---|---|
| "Financials by the 5th. Or the month is free." | "Timely, accurate financial reporting you can count on!" |
| "hey read the invoice and matched it to the contract." | "Our AI-powered platform leverages machine learning to…" |
| "We never hold your money." | "Bank-grade security." |
| "Public pricing. Month to month." | "Contact us for a customized quote." |
| "I'm not finding that in your documents, so I won't guess." | "Great question! I'd be happy to help with that!" |

## `hey` as a character (in the portals)
- Speaks in first person, lowercase name, no avatar beyond the mark.
- Always cites: "(CC&Rs §7.2)", "(ledger, Oct 6)".
- Admits limits in one sentence and routes to a person.
- Drafts are labeled DRAFT until a human sends them.
- Never jokes about money owed.

## Copy bank
Taglines: "You run the community. hey runs the books." · "Say hey to your new back office." · "The treasurer finally gets a night off." · "Books, back office, and a promise with a penalty."
CTAs: "Get a quote in 3 minutes" · "See the board portal" · "Download a sample packet" · "Ask hey".
Trust lines: "We never hold funds." · "Two board approvals on every payment." · "Your data exports any time." · "Month to month."

## Imagery
Real communities: townhome rows, small condo courtyards, a pool gate, a mailbox bank. Daylight, no drone shots, no stock handshake. Existing stock images are placeholders until we shoot the first customer's community (with permission).
