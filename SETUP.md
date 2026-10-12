# Setup instructions for Codex

Use the user's operating system and local tools. Do not ask a nontechnical user to execute terminal commands you can run yourself. Inspect before replacing existing configuration. Never use somebody else's project or credentials.

## 1. Install locally

Clone this repository into a normal workspace. Check for Git and Python 3.11 or newer; install from official sources if needed with the user's authorization. Run `python bootstrap.py` (on some systems use `python3` or the Windows Python launcher). It creates `.venv` and installs the official server pinned in requirements.txt.

For later commands use `.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on macOS/Linux. The examples below use `VENV_PYTHON` as a descriptive placeholder, not a literal command.

## 2. Set up the user's Google access

Check current upstream setup guidance at https://github.com/googleads/google-ads-mcp first because Google's access requirements can change.

Guide the user through selecting or creating their own Google Cloud project, enabling Google Ads API, setting up Google Auth Platform consent, and creating a Desktop OAuth client. The user signs in and approves permissions. Ask before new security-sensitive permissions, app publication or legally binding agreements. Do not enable billing unless it is required and separately approved. Do not promise automatic Explorer approval.

For testing, add the actual sign-in email as a test user if needed. Explain that Google's Testing mode can require reauthorization; do not silently publish the app. Production-account API access may require Explorer access or a developer-token workflow according to current Google guidance. Resolve test-only or permission errors before long reporting work.

Save the Desktop client JSON outside the repo. Run:

```
VENV_PYTHON configure.py --project ACTUAL_PROJECT_ID
VENV_PYTHON connection.py login --client ABSOLUTE_PATH_TO_DESKTOP_CLIENT_JSON
VENV_PYTHON connection.py check --live
```

Credentials are dedicated to this workflow and do not overwrite the user's general Google application-default login. On Windows restrict access to the credential directory to the user and SYSTEM after login; on Unix credentials are saved mode 600. Never display token contents. Protect the Desktop client JSON as well.

The helper expects the OAuth client and configured project to match. It uses the Ads OAuth scope. If the installed server needs another approved authentication configuration, consult upstream rather than weakening security or reusing a third party's credentials. The runner deliberately removes inherited developer-token and login-customer overrides; a setup requiring them must be explicitly adapted and tested.

## 3. Choose connection mode

The simplest path is the local `audit_runner.py`, which starts and stops the official MCP server for each batch. No global Codex MCP registration is needed.

Optional: `configure.py` prints a Codex TOML block with executable and credential-file paths, not tokens. Review the user's existing `~/.codex/config.toml`, then merge the block without clobbering existing servers. Do not auto-register a remote OAuth service. Restart Codex when necessary. Follow current Codex MCP docs for tools and configuration.

Read `skills/google-ads-audit/SKILL.md` directly for audits. Optionally copy the skill to the user's `.agents/skills/google-ads-audit` only after checking for an existing version. The repository itself supplies all instructions and references.

## 4. Verify and select the account

Use the live check to list accounts. Obtain a real business name or customer ID from the user, then:

```
VENV_PYTHON audit_runner.py --discover BUSINESS_NAME --output audits/account.json
```

Ask when multiple accounts match. Never select by position alone. Discovery finds directly accessible accounts; manager-only access may require a documented manager workflow. A successful account list alone is not a completed setup: verify a metadata-backed customer snapshot for the selected account.

## 5. Run and interpret the audit

Use the verified account time zone:

```
VENV_PYTHON build_queries.py --timezone ACCOUNT_TIME_ZONE --output audits/RUN_DATE
VENV_PYTHON audit_runner.py --customer ACTUAL_CUSTOMER_ID --jobs audits/RUN_DATE/queries.json --output audits/RUN_DATE/data.json
```

Read every query's `ok` value. Repair metadata-supported incompatibilities or disclose unknowns. Resource metadata validation is not proof all fields can be combined. The runner saves raw evidence, not an automatically completed audit report.

Follow the skill to write `audits/account-name-RUN_DATE.md`. Reconcile spend, clicks, impressions and conversions between aggregate and segmented queries. Read full conversion actions and actual campaign goals before assessing CPA or ROAS. Separate reported purchase credits from unique paid orders. Pull purchase-only campaign data, conversion-date data and complete available Search/PMax term sets as needed. Remove row limits for brand calculations when feasible; report suppressed terms and channel coverage. Never claim exact brand removal from an incomplete query sample.

Show the report to the user. Do not send it to anyone or change campaigns without explicit authorization.
