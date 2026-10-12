# Instructions for Codex

This repository is a local read-only Google Ads audit workflow. Read README.md, SETUP.md and skills/google-ads-audit/SKILL.md before setup or analysis.

- Handle technical work; explain access steps plainly. User completes sign-in, verification and consent.
- Use the user's own Google project and Ads access. Never invent project IDs or customer IDs.
- Keep credentials outside the repository. Never print or commit them. Reports and account data stay private.
- Default to the local query runner; optional MCP registration must preserve existing Codex configuration.
- Check authentication before expensive work and verify a real selected account snapshot.
- Read resource metadata before queries. A query error is Unknown, not zero.
- Report account-local complete dates, lag, row limits and privacy suppression.
- Purchases, calls, carts, checkouts and page views are separate outcomes. Actual sales require independently verified paid orders.
- Identify own-brand traffic across all campaigns where available; never label hidden traffic non-brand.
- Do not equate non-converting spend with waste or sum overlapping spend breakdowns.
- Health scores are provisional when evidence is incomplete. Explain scope and evidence coverage.
- Reports are drafts for user review. No client sending, campaign edits, spending or publication without authorization.
- Finish with appropriate data QC and clean disposable scratch files. Preserve evidence and deliverables.
