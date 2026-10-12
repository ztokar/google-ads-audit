"""Store a project profile outside the repository; display optional Codex config."""
import argparse, json, os, re
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--project", required=True)
a = p.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", a.project):
    p.error("Use a Google Cloud project ID, not its display name or number.")
config = Path.home() / ".config" / "google-ads-audit"
config.mkdir(parents=True, exist_ok=True)
profile = config / "config.json"
if profile.exists() and json.loads(profile.read_text()).get("project_id") != a.project:
    raise SystemExit("A different project is already configured. Review the existing profile before replacing it.")
profile.write_text(json.dumps({"project_id": a.project}, indent=2))
server = Path(__file__).resolve().parent / ".venv" / ("Scripts/google-ads-mcp.exe" if os.name == "nt" else "bin/google-ads-mcp")
print("Project profile saved. Optional Codex MCP configuration:")
print("[mcp_servers.google-ads-audit]")
print("command = " + json.dumps(str(server)))
print("startup_timeout_sec = 120")
print("tool_timeout_sec = 90")
print("[mcp_servers.google-ads-audit.env]")
print("GOOGLE_PROJECT_ID = " + json.dumps(a.project))
print("GOOGLE_CLOUD_PROJECT = " + json.dumps(a.project))
print("GOOGLE_APPLICATION_CREDENTIALS = " + json.dumps(str(config / "credentials.json")))
