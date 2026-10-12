"""Dedicated Google Ads login and MCP connection checks on Windows."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PROFILE = Path.home() / ".config" / "google-ads-audit" / "config.json"
PROJECT = json.loads(PROFILE.read_text()).get("project_id", "") if PROFILE.exists() else ""
CONFIG = Path.home() / ".config" / "google-ads-audit"
CREDENTIALS = CONFIG / "credentials.json"
SERVER = Path(__file__).parent / ".venv" / ("Scripts/google-ads-mcp.exe" if os.name == "nt" else "bin/google-ads-mcp")


def login(client_file: Path) -> None:
    if not PROJECT:
        raise ValueError("Run configure.py --project YOUR_PROJECT_ID first.")
    from google_auth_oauthlib.flow import InstalledAppFlow

    client = json.loads(client_file.read_text(encoding="utf-8-sig"))
    if "installed" not in client:
        raise ValueError("A Desktop app OAuth client file is required.")
    if client["installed"].get("project_id") != PROJECT:
        raise ValueError("OAuth client belongs to a different project.")
    CONFIG.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_config(
        client, scopes=["https://www.googleapis.com/auth/adwords"]
    )
    credentials = flow.run_local_server(
        host="localhost", port=0, access_type="offline", prompt="consent", timeout_seconds=600,
        authorization_prompt_message="Complete Google sign-in in the browser.",
        success_message="Google Ads sign-in complete. You can close this tab.",
    )
    if not credentials.refresh_token:
        raise RuntimeError("Google did not return a refresh token; login was not saved.")
    data = json.loads(credentials.to_json())
    data["type"] = "authorized_user"
    data["quota_project_id"] = PROJECT
    CREDENTIALS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if os.name != "nt":
        CREDENTIALS.chmod(0o600)
    print("Dedicated Google Ads credentials saved. Other Google logins were preserved.")


async def check(live: bool, probe: bool = False) -> None:
    if not PROJECT:
        raise ValueError("Run configure.py --project YOUR_PROJECT_ID first.")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = dict(os.environ)
    env.update(GOOGLE_PROJECT_ID=PROJECT, GOOGLE_CLOUD_PROJECT=PROJECT,
               GOOGLE_APPLICATION_CREDENTIALS=str(CREDENTIALS))
    for key in ("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "GOOGLE_ADS_DEVELOPER_TOKEN",
                "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID", "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"):
        env.pop(key, None)
    params = StdioServerParameters(command=str(SERVER), env=env)
    async with asyncio.timeout(120):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                names = [tool.name for tool in tools]
                expected = ("search", "list_accessible_customers", "get_resource_metadata")
                if len(names) != 3 or not all(any(name.endswith(x) for name in names) for x in expected):
                    raise RuntimeError(f"Unexpected tool inventory: {names}")
                print(json.dumps({"mcp_handshake": "passed", "tools": names,
                                  "credentials_present": CREDENTIALS.exists()}))
                if live:
                    if not CREDENTIALS.exists():
                        raise RuntimeError("Google Ads sign-in is still required.")
                    name = next(x for x in names if x.endswith("list_accessible_customers"))
                    result = await session.call_tool(name, {})
                    if getattr(result, "is_error", getattr(result, "isError", False)):
                        print(result.model_dump_json())
                        raise RuntimeError("Account listing failed; check Google login and API access level.")
                    print(result.model_dump_json())
                    if probe:
                        payload = result.model_dump()
                        accounts = payload.get("structured_content", {}).get("result", [])
                        if not accounts:
                            raise RuntimeError("No accessible accounts returned.")
                        metadata = await session.call_tool(
                            next(x for x in names if x.endswith("get_resource_metadata")),
                            {"resource_name": "customer"})
                        fields = ["customer.id", "customer.descriptive_name", "customer.currency_code",
                                  "customer.time_zone", "customer.manager"]
                        raw_metadata = metadata.model_dump_json()
                        if not all(field in raw_metadata for field in fields):
                            raise RuntimeError("Required customer fields were not confirmed by metadata.")
                        snapshot = await session.call_tool(
                            next(x for x in names if x.endswith("search")),
                            {"customer_id": accounts[0], "resource": "customer", "fields": fields, "limit": 1})
                        print(snapshot.model_dump_json())
                        if getattr(snapshot, "is_error", getattr(snapshot, "isError", False)):
                            raise RuntimeError("Live account snapshot failed.")
                        print("Live metadata and account snapshot checks passed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    login_cmd = commands.add_parser("login")
    login_cmd.add_argument("--client", type=Path, required=True)
    check_cmd = commands.add_parser("check")
    check_cmd.add_argument("--live", action="store_true")
    check_cmd.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.command == "login":
        login(args.client)
    else:
        asyncio.run(check(args.live or args.probe, args.probe))


if __name__ == "__main__":
    main()
