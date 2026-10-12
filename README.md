# Google Ads Audit for Codex

Give this repository to Codex. It contains a purchase-aware Google Ads audit skill, setup helpers and a read-only query runner using Google's official Google Ads MCP server.

## Start here

Paste this into Codex:

> Set up the Google Ads audit workflow from this repository on my computer. Read AGENTS.md and SETUP.md, do the technical setup for me, and guide me through my own Google sign-in and required permissions. Then list my accessible accounts and audit the account I select. Keep the account unchanged. Separate purchases from calls, carts and checkout events, identify brand traffic where possible, and tell me what attribution evidence is missing.

Codex needs a local environment with terminal access. The scripts support Windows, macOS and Linux paths. This is a workflow repository, not a published one-click plugin. No hosted service or OpenAI API key is required by these scripts; normal Codex usage and any Google account/API requirements still apply.

## What you get

- Last 90 complete days using the account's own time zone.
- Campaign, keyword, search-term, targeting, asset and conversion checks.
- Explicit purchase-only versus lead/soft-event reporting.
- Brand separation with hidden-term limitations disclosed.
- Provisional scoring, evidence coverage and a 30-day action plan.
- Raw query evidence saved locally; no automatic emails, sharing or campaign changes.

Ask follow-ups such as “Which conversions are actual purchases?”, “How much spend was on brand traffic?”, or “What must we verify before spending more?”

**Ads attribution is not proof of paid sales.** Order-level verification requires separately authorized access to the store or CRM. Zero conversions do not automatically mean broken tracking or wasted spend. Hidden search terms cannot be assumed non-brand.

## Technical setup

See [SETUP.md](SETUP.md). Codex should handle the terminal commands. You handle Google sign-in, identity checks and permission approvals.

The official server is pinned to upstream commit `9a78cbdceebae71a6bc8483bdec333695834ef9c` (version 0.0.5) for reproducibility. Its tools retrieve accounts, resource metadata and reporting data. This repository does not vendor Google's server. Review upgrades against its current documentation before changing the pin.

## Privacy

Use your own Google Cloud project and your own account. Credentials and the project profile live outside this repository at `~/.config/google-ads-audit/`. Audit outputs, virtual environments and credential filenames are excluded from Git. Never commit a downloaded OAuth client JSON, refresh token, customer report or account export.

Google's Ads OAuth permission is broader than reading. The pinned server only exposes reading tools, but its credentials must still be protected. Prefer read-only Google Ads user access wherever appropriate. Treat reports and account data as private.

## References

- [Official Google Ads MCP server](https://github.com/googleads/google-ads-mcp)
- [Google Ads API access levels](https://developers.google.com/google-ads/api/docs/access-levels)
- [Codex MCP configuration](https://developers.openai.com/codex/mcp/)

## Validation

The original workflow was used for live account audits. This portable package passed query-generation and credential-isolation tests, a local Windows dependency installation/check, and a server handshake exposing exactly the three expected read-only tools. It must be verified with each new user's own login and a live account read before the setup is called complete. Cross-platform path support does not mean a fresh Mac or Linux installation has been tested.
