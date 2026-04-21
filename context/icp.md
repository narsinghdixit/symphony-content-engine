# PureFacts ICP Profiles

---

## WEALTH MANAGER ICP

### Firm Profile
- **Type**: RIAs, independent broker-dealers (IBDs), bank-owned wealth divisions, wirehouses
- **AUM range**: $1B–$100B+
- **Advisor count**: 50–5,000+
- **Revenue model**: Asset-based fees (advisory fees), trailing commissions, financial planning fees
- **Tech stack**: Typically fragmented — portfolio management (Black Diamond, Orion, Advent), CRM (Salesforce, Redtail), custodian integrations (Schwab, Fidelity, Pershing)
- **Deal size**: [PROTOTYPE ASSUMPTION] $150K–$1M+ ARR depending on AUM and complexity

### Key Personas

| Persona | Title | What They Care About |
|---------|-------|---------------------|
| Operations Leader | Head of Ops, VP Operations, COO | Reducing manual billing effort, eliminating reconciliation errors, scaling without adding headcount |
| Finance Leader | CFO, VP Finance | Revenue leakage quantification, margin protection, audit defensibility, EBITDA impact |
| Compliance Leader | CCO, Head of Compliance | Fee disclosure accuracy, audit trails, SEC/FINRA exam readiness, marketing rule compliance |
| Advisory Leader | VP Advisory Services, Head of Wealth | Advisor satisfaction, compensation transparency, retention, recruiting competitiveness |
| Technology Leader | CTO, VP Technology | Platform consolidation, integration reduction, data integrity, retirement of legacy systems |

### Pain Points (with data)

- **Revenue leakage**: Firms lose 1–5% of EBITDA to billing errors and pricing gaps (EY data). A $10B AUM firm can lose $3–5M per year.
- **Manual billing burden**: 72% of wealth firms use manual workarounds for billing complexity. Billing cycles take "three people two weeks every quarter."
- **Fee compression**: Average advisory fee falling — 83% of advisors expect to charge under 1% for $5M+ clients by 2026 (Cerulli). Every mispriced basis point compounds.
- **Revenue spillage**: Front-end pricing errors (undocumented discounts, missed household aggregations) create recurring revenue loss embedded in client agreements. Even 12 bps of mispricing on 20% of new business erodes tens of thousands annually per firm — compounding year over year.
- **Advisor over-discounting**: 89% of firms over $1B AUM discount stated fees. 70%+ of advisors discount without formal guardrails or approval workflows.
- **Compensation disputes**: Delayed, opaque payout reporting forces advisors into "shadow reconciliation" in spreadsheets. One-third of advisors rate firm operational support as only marginally valuable (J.D. Power 2025).
- **Regulatory exposure**: FINRA collected $59.8M in fines in 2024. SEC reported $8.2B in financial remedies in FY2024. Fee calculation errors, disclosure mismatches, and off-channel communications are top enforcement themes.
- **Talent war**: 109,000 advisors (37.5% of industry) planning retirement in 10 years. Compensation clarity and transparency are decisive in recruiting conversations.

### Pain Language (how they describe it)
- "We're leaving money on the table and we can't even quantify how much."
- "Billing takes three people two weeks every quarter — and we still find errors."
- "Advisors are discounting without guardrails. We have no visibility."
- "We found errors in last year's audit and had to issue refunds."
- "Our comp system is a black box — advisors don't trust the numbers."
- "We can't prove to an examiner that our fees match our disclosures."

### Buying Triggers
- Audit findings or SEC/FINRA exam deficiencies
- M&A integration (stitching together billing and comp across acquired firms)
- Platform migration (moving custodians or portfolio management systems)
- New CFO or COO demanding process modernization
- Board or PE sponsor pressure to quantify and close revenue leakage
- Advisor attrition linked to compensation opacity

---

## ASSET MANAGER ICP

### Firm Profile
- **Type**: Global asset managers, fund companies, institutional investment managers
- **AUM range**: $10B–$500B+
- **Domiciles**: Multi-jurisdiction (US, UK, EU, APAC)
- **Distribution model**: Institutional channels, sub-advisory, platform/marketplace, consultant-intermediated
- **Revenue model**: Management fees (basis points on AUM/NAV), performance fees, rebates, trailer fees
- **Tech stack**: Transfer agents, fund accounting systems, distribution platforms, often heavily customized and fragmented
- **Deal size**: [PROTOTYPE ASSUMPTION] $250K–$2M+ ARR depending on fund complexity and domicile count

### Key Personas

| Persona | Title | What They Care About |
|---------|-------|---------------------|
| Operations Leader | COO, Head of Fund Operations | Standardizing fee logic across domiciles, reducing exceptions and manual breaks, scaling without proportional headcount growth |
| Finance Leader | CFO, Head of Fund Finance | Fee realization rates, revenue recognition accuracy, margin protection, cost reduction mandates |
| Fund Admin Leader | Head of Fund Administration | Billing accuracy at NAV level, accrual precision, audit-ready calculations, reducing cycle times |
| Distribution Leader | Head of Distribution, Head of Institutional Sales | Channel economics, rebate governance, trailer fee accuracy, distributor oversight |
| Compliance Leader | CCO, Head of Regulatory | Cross-border regulatory compliance (SEC, FCA, ESMA), fee disclosure integrity, audit trail completeness |

### Pain Points (with data)

- **Fee compression is structural**: Margins tightening as average industry fee fell to 22 bps (BCG 2023). Small inconsistencies in fee application materially reduce realized revenue.
- **Cross-border complexity**: Multiple domiciles, fund structures, and regulatory regimes multiply the operational surface area. Fragmented systems and entity-level processes slow standardization.
- **Revenue leakage in execution**: Revenue is earned in agreements but lost in execution — billing breaks, fragmented data, weak controls delay collection. Firms lose 1–5% of EBITDA.
- **Rebate and trailer fee governance**: Managing rebate flows across distributors and entities without embedded validation creates overpayment risk and audit exposure.
- **Manual process dependency**: Spreadsheet-based fee calculations and reconciliations create single points of failure. One mis-keyed digit repeats across billing cycles undetected.
- **Regulatory scrutiny across jurisdictions**: SEC thematic sweeps, FCA enforcement, ESMA reporting all increasing focus on fee calculation integrity and disclosure accuracy.
- **Integration strain from M&A**: Consolidation means stitching together multiple custodians, billing models, and supervisory practices — a top SEC examination priority for 2026.

### Pain Language (how they describe it)
- "Our fee realization rate is slipping and we can't pinpoint where."
- "We're running 15 different billing processes across 8 domiciles."
- "The rebate reconciliation is held together with spreadsheets and prayer."
- "We need audit-ready evidence by design, not reconstructed after the fact."
- "Every new fund launch means another bespoke billing workflow."
- "Our NAV impact from billing errors is a board-level concern."

### Buying Triggers
- New fund launches requiring scalable fee logic
- Regulatory changes (MiFID updates, SEC examination priorities, FCA enforcement)
- Cost reduction mandates from leadership or PE sponsors
- Platform consolidation after M&A
- Audit findings on fee calculation or disclosure integrity
- Board pressure to quantify revenue leakage

---

## KEY SEGMENTATION DIFFERENCES

| Dimension | Wealth Manager | Asset Manager |
|-----------|---------------|---------------|
| Revenue unit | Advisory fee per client/household | Management fee per fund/mandate |
| Primary pain | Advisor behavior + billing errors | Cross-border complexity + manual processes |
| Language register | Advisor-centric, client-relationship focused | Fund-centric, institutional, NAV-level |
| Compliance frame | SEC/FINRA exams, ADV disclosures | Multi-jurisdiction (SEC + FCA + ESMA), fund governance |
| Decision speed | Faster, often driven by a single executive | Slower, committee-driven, multi-stakeholder |
| PureFacts angle | "Stop the leakage, align your advisors" | "Standardize fee logic, govern distribution economics" |
