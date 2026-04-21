# Asset Multiplication Prompt

You are generating a campaign kit of 10 marketing assets from a source document extraction (EXTRACT) and PureFacts context files. Every asset must meet the quality rules in AGENTS.md.

## Inputs

- **EXTRACT**: The structured briefing from `01-extract.md` (thesis, claims, data, quotes, counterintuitive insight, PureFacts relevance)
- **Context files**: All 5 files in `/context/` (company, icp, positioning, competitors, brand-voice)

## Global Rules

- Read `/context/brand-voice.md` before writing anything. Internalize the banned phrases and style rules.
- Each asset is self-contained. A reader should understand it without seeing the other 9.
- Do not reference the source document by title in the assets (the reader has not read it). Instead, present the insights as PureFacts' point of view.
- Use Markdown formatting. Include a YAML-style metadata block at the top of each asset: asset type, target ICP, word count target, author/voice.

## CTA Links (use real URLs, never placeholders)

Every CTA must use a real PureFacts URL. Pick from this list based on the asset type and the action:

- **Schedule a meeting / book assessment / book a call**: `https://purefacts.com/contact/`
- **Read full analysis / get the data / download report**: `https://purefacts.com/resources/`
- **Learn more / about PureFacts (general)**: `https://purefacts.com/`
- **Wealth manager pages**: `https://purefacts.com/who-we-serve/wealth-management/`
- **Asset manager pages**: `https://purefacts.com/who-we-serve/asset-management/`
- **Solutions / platform overview**: `https://purefacts.com/platform/`
- **Case studies (revenue leakage)**: `https://purefacts.com/how-a-leading-wealth-manager-unlocked-over-13m-in-annual-value-by-replacing-legacy-infrastructure/`
- **Case studies (asset manager billing)**: `https://purefacts.com/asset-manager-billing-cycle-time/`

Format CTAs as Markdown links: `[Schedule a 20-minute revenue assessment](https://purefacts.com/contact/)` -- NEVER as plain text like `[Book a time]` or `[LINK]`.

---

## Asset 1: linkedin-narsingh.md

**Metadata**: type: linkedin-post | icp: general (wealth + asset mgmt leaders) | words: 150–220 | voice: Narsingh

**Voice**: Use the Narsingh voice from `brand-voice.md`. Punchy, idea-first, mildly contrarian. Short paragraphs (1–2 sentences). Direct address.

**Structure**:
- Hook (first 2 lines visible before "see more"): Lead with the counterintuitive insight from EXTRACT. Make it a bold, specific claim — not a question.
- Body: 2–3 short paragraphs. Back the claim with one data point from EXTRACT and one proof point from `positioning.md`. Connect to a PureFacts-adjacent theme without naming PureFacts.
- Close: End with a sharp question or challenge directed at the reader. No CTA, no hashtag spam. Maximum 3 hashtags at the very end if appropriate.

**Pull from context**: `brand-voice.md` (Narsingh voice), `positioning.md` (market framing)
**Pull from EXTRACT**: counterintuitive insight, 1–2 data points

**Do**: Write like a practitioner sharing a hard-won insight, not a vendor pitching.
**Don't**: Mention PureFacts by name. Don't use "I'm excited to share." Don't open with a question.

---

## Asset 2: linkedin-ceo.md

**Metadata**: type: linkedin-post | icp: general (C-suite financial services) | words: 150–220 | voice: Rob Madej (CEO)

**Voice**: Use the CEO voice from `brand-voice.md`. Measured, industry-forward, founder gravitas. Speaks to peers about where the market is heading, not about products.

**Structure**:
- Hook: Lead with a macro trend or industry shift that the source document illuminates. Frame it as "what I'm watching."
- Body: 2–3 paragraphs connecting the document's thesis to a broader industry trajectory. Reference one data point. Subtly position PureFacts' worldview (revenue optimization as a strategic imperative) without hard-selling.
- Close: Forward-looking statement about what this means for the industry. Optionally mention PureFacts is working on this problem.

**Pull from context**: `brand-voice.md` (CEO voice), `company.md` (leadership credibility), `positioning.md` (why-now narrative)
**Pull from EXTRACT**: thesis, 1 data point, target audience

**Do**: Sound like a CEO writing during a flight, not a marketing team ghostwriting.
**Don't**: Use product names. Don't be salesy. Don't use more than one statistic.

---

## Asset 3: nurture-email-1-wealth.md

**Metadata**: type: nurture-email | icp: wealth manager (Head of Ops / CFO) | words: 120–180 | voice: PureFacts corporate | funnel: top

**Structure**:
- Subject line: Short, curiosity-driven, references a specific pain or stat. No clickbait.
- Preview text: One sentence that complements (not repeats) the subject line.
- Body: Open with a pain point from `icp.md` (wealth manager section). Introduce one insight from EXTRACT that reframes the problem. No product pitch — this is educational.
- CTA: Soft. "Read the full analysis" or "See the data" with a [LINK] placeholder.
- Signature: From Narsingh, Director of Product Marketing, PureFacts

**Pull from context**: `icp.md` (wealth manager pain language), `brand-voice.md` (corporate voice)
**Pull from EXTRACT**: 1 core claim, 1 data point

**Do**: Write a subject line you would actually open. Use "you" language.
**Don't**: Mention PureFacts products. Don't use "Dear [First Name]" — use "Hi [First Name],". Don't exceed 180 words in the body.

---

## Asset 4: nurture-email-2-wealth.md

**Metadata**: type: nurture-email | icp: wealth manager (Head of Ops / CFO) | words: 120–180 | voice: PureFacts corporate | funnel: middle

**Structure**:
- Subject line: Implies momentum or a shift ("what leading firms are doing about X")
- Preview text: Complements subject line.
- Body: Acknowledge the problem is real (callback to email 1 theme). Pivot to "here is what leading firms are doing." Introduce PureFacts obliquely through a result: reference the 85% dispute reduction or $13M value unlock from `company.md`, framed as "one firm we work with" without naming PureFacts.
- CTA: Medium. "See how one firm solved this" or "Get the case study" with [LINK] placeholder.
- Signature: From Narsingh.

**Pull from context**: `icp.md` (wealth manager), `company.md` (proof points), `positioning.md` (value props)
**Pull from EXTRACT**: thesis, data points that quantify the cost of inaction

**Do**: Create the feeling of "I should look into this." Use social proof.
**Don't**: Name-drop PureFacts products yet. Don't repeat email 1 verbatim.

---

## Asset 5: nurture-email-3-wealth.md

**Metadata**: type: nurture-email | icp: wealth manager (Head of Ops / CFO) | words: 120–180 | voice: PureFacts corporate | funnel: bottom

**Structure**:
- Subject line: Direct, implies a next step ("quick question about [their pain]")
- Preview text: Short, personal.
- Body: Concise. Acknowledge the reader has been thinking about this problem. Name PureFacts directly for the first time. One sentence on what PureFacts does (from `positioning.md` core positioning). One sentence on a relevant proof point. Ask for 20 minutes.
- CTA: Hard. "Can I get 20 minutes on your calendar this week? [CALENDAR LINK]"
- Signature: From Narsingh, with title and phone number placeholder.

**Pull from context**: `positioning.md` (core positioning, one proof point), `icp.md` (wealth manager persona), `brand-voice.md`
**Pull from EXTRACT**: the PureFacts relevance connection (section 7 of extract)

**Do**: Be direct and respectful. The reader's time matters more than your pitch.
**Don't**: Write more than 150 words in the body. Don't rehash emails 1 and 2.

---

## Asset 6: bdr-sequence-asset-mgr.md

**Metadata**: type: bdr-outbound-sequence | icp: asset manager (COO / CFO / Head of Fund Admin) | words: 90 max per touch | voice: BDR (professional, concise)

**Structure**: 3 touches, each with subject line + body. Clearly label Touch 1, Touch 2, Touch 3.

- **Touch 1 (cold open)**: Lead with a specific, relevant data point or insight from EXTRACT that an asset management executive would care about. Ask one question that implies the prospect has this problem. Do not mention PureFacts.
- **Touch 2 (value add, 3–4 days later)**: Follow up with a proof point from `company.md` framed as a result ("a $50B AUM firm we work with..."). One sentence on what PureFacts does. Ask if it is worth a 15-minute conversation.
- **Touch 3 (breakup, 5–7 days later)**: Short. Acknowledge they are busy. Restate the core value prop in one sentence. Offer to send a one-pager instead of asking for a meeting. Leave the door open.

**Pull from context**: `icp.md` (asset manager section — use THEIR language, not wealth manager language), `competitors.md` (displacement angle for in-house/spreadsheets), `company.md` (proof points)
**Pull from EXTRACT**: 1 data point per touch, PureFacts relevance

**Do**: Use asset manager vocabulary ("fee realization," "NAV impact," "fund administration"). Keep each touch under 90 words.
**Don't**: Use wealth manager language. Don't be cute or clever. Don't write more than 90 words per touch.

---

## Asset 7: sales-one-pager.md

**Metadata**: type: sales-one-pager | icp: both (wealth + asset mgr) | words: 350–500 | voice: PureFacts corporate

**Structure** (4 sections, clearly labeled):
1. **THE PROBLEM**: 3–4 bullets describing the pain. Use data from EXTRACT and `icp.md`. Make it visceral — the reader should feel the cost of their current state.
2. **THE SOLUTION**: What PureFacts does, from `positioning.md`. 3–4 bullets. Focus on outcomes, not features. "PureFees calculates X" becomes "Recover the 1–5% of revenue leaking through billing errors."
3. **THE PROOF**: Key metrics from `company.md` ($15T AuA, 200+ clients, $13M value unlock, 85% dispute reduction). Include one result relevant to the source document topic.
4. **NEXT STEP**: Single clear CTA. "Schedule a 20-minute revenue assessment" with [LINK] placeholder.

**Pull from context**: All 5 context files. This is the asset that draws from everything.
**Pull from EXTRACT**: data points for the Problem section, thesis for framing

**Do**: Make it scannable. A reader should get the point in 15 seconds.
**Don't**: Exceed one page if printed. Don't use paragraphs — use bullets and short headers.

---

## Asset 8: objection-handling.md

**Metadata**: type: objection-handler | icp: internal (sales team) | words: 400–600 | voice: direct, practical

**Structure**: Identify the top 5 objections that the source document's topic helps counter. For each:

- **Objection**: The exact words a prospect would say (e.g., "We already handle billing in-house and it works fine.")
- **Why they say it**: 1 sentence on the underlying concern.
- **Response**: 2–3 sentences. Lead with empathy, pivot to reframe, land with a proof point. Use data from EXTRACT and `positioning.md`.
- **Proof point**: A specific stat or client result from `company.md` or EXTRACT.

**Pull from context**: `competitors.md` (displacement angles), `positioning.md` (value props), `company.md` (proof points), `icp.md` (what each persona actually cares about)
**Pull from EXTRACT**: data points and claims that directly counter each objection

**Do**: Write responses a real AE would actually say on a call. Conversational, not scripted.
**Don't**: Be defensive. Don't bash competitors by name (reframe instead).

---

## Asset 9: blog-post.md

**Metadata**: type: blog-post | icp: both (skews wealth mgr) | words: 600–800 | voice: PureFacts corporate

**Structure**:
- **Title**: SEO-aware, specific, includes a number or bold claim. Not clickbait. **HARD LIMIT: 65 characters or fewer** (HubSpot CMS template constraint and SEO best practice). Aim for 50-60 chars.
- **Opening hook** (2–3 sentences): Start with the counterintuitive insight from EXTRACT. Make the reader feel the stakes.
- **Section 1 — The Problem** (~200 words): Expand the insight with data from EXTRACT and context. Use pain language from `icp.md`.
- **Section 2 — Why This Matters Now** (~150 words): Connect to `positioning.md` why-now narrative. Why should the reader care today, not next quarter?
- **Section 3 — A Better Approach** (~200 words): Introduce PureFacts' philosophy (not a product pitch — a point of view). Reference proof points from `company.md`.
- **Closing** (~100 words): Summarize the key takeaway. CTA to learn more, download a resource, or schedule a conversation. [LINK] placeholder.

**Pull from context**: `brand-voice.md` (corporate voice), `positioning.md`, `company.md`, `icp.md`
**Pull from EXTRACT**: counterintuitive insight (hook), thesis (framing), data points (evidence), core claims (section structure)

**Do**: Write something you would actually share on LinkedIn. Every paragraph should earn its place.
**Don't**: Exceed 800 words. Don't save the good stuff for the end — front-load value. Don't write an intro paragraph that could be deleted without losing anything.

---

## Asset 10: enablement-talking-points.md

**Metadata**: type: enablement | icp: internal (AEs for discovery and demo) | words: 300–450 | voice: direct, practical

**Structure** (4 labeled sections, all bullets):

1. **DISCOVERY QUESTIONS** (5–7 bullets): Questions an AE should ask prospects to surface the pains this source document addresses. Each question should sound natural, not interrogative. Example: "How long does your quarterly billing cycle take end-to-end today?"

2. **KEY TALKING POINTS** (5–7 bullets): What to say when the prospect confirms the pain. Each is a complete sentence an AE can say verbatim. Ground in EXTRACT and `positioning.md`.

3. **PROOF POINTS** (4–5 bullets): Stats and client results from `company.md` and EXTRACT, pre-formatted for verbal delivery. E.g., "We work with over 200 financial institutions managing $15 trillion collectively. One client recovered $13 million in annual value in year one."

4. **COMPETITIVE HANDLES** (3–4 bullets): If the prospect mentions a competitor or their current solution, here is how to respond. Pull from `competitors.md` displacement angles.

**Pull from context**: All 5 context files.
**Pull from EXTRACT**: data points, core claims, PureFacts relevance

**Do**: Write for someone who will say these words out loud in 10 minutes. Keep each bullet to 1–2 sentences.
**Don't**: Use marketing jargon. Don't include anything that sounds like a slide deck.
