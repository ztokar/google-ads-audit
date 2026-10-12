"""Read-only audit query runner for the installed official Google Ads MCP server."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from connection import PROJECT, CREDENTIALS, SERVER

sys.stdout.reconfigure(encoding="utf-8")

def unpack(result):
    data = result.model_dump()
    failed = data.get("is_error", data.get("isError", False))
    structured = data.get("structured_content", data.get("structuredContent"))
    if structured is not None:
        value = structured.get("result", structured)
    else:
        chunks = [x.get("text", "") for x in data.get("content", []) if x.get("type") == "text"]
        try:
            value = json.loads("\n".join(chunks))
        except ValueError:
            value = "\n".join(chunks)
    return {"ok": not failed, "data": value}

async def run(args):
    if not PROJECT:
        raise RuntimeError("Run configure.py --project YOUR_PROJECT_ID before querying.")
    if args.customer:
        args.customer = args.customer.replace("-", "")
    jobs = json.loads(args.jobs.read_text(encoding="utf-8")) if args.jobs else []
    env = dict(os.environ)
    env.update(GOOGLE_PROJECT_ID=PROJECT, GOOGLE_CLOUD_PROJECT=PROJECT,
               GOOGLE_APPLICATION_CREDENTIALS=str(CREDENTIALS))
    for key in ("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "GOOGLE_ADS_DEVELOPER_TOKEN",
                "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID", "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"):
        env.pop(key, None)
    env["FASTMCP_SHOW_SERVER_BANNER"] = "false"
    results = {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    async with stdio_client(StdioServerParameters(command=str(SERVER), env=env)) as (read, write):
        async with ClientSession(read, write) as session:
            async with asyncio.timeout(120):
                await session.initialize()
            semaphore = asyncio.Semaphore(4)
            async def call(name, payload):
                async with semaphore:
                    try:
                        async with asyncio.timeout(90):
                            return unpack(await session.call_tool(name, payload))
                    except Exception as error:
                        return {"ok": False, "data": str(error)}
            if args.metadata:
                results["metadata"] = await call("metadata_get_resource_metadata", {"resource_name":args.metadata})
                save()
                print("Metadata saved; success:", results["metadata"]["ok"])
                return
            if args.discover:
                listed = await call("customers_list_accessible_customers", {})
                if not listed["ok"]:
                    raise RuntimeError(listed["data"])
                fields = ["customer.id", "customer.descriptive_name", "customer.manager",
                          "customer.currency_code", "customer.time_zone"]
                meta = await call("metadata_get_resource_metadata", {"resource_name": "customer"})
                if not meta["ok"] or not all(x in json.dumps(meta) for x in fields):
                    raise RuntimeError("Account discovery metadata was not validated.")
                async def identify(cid):
                    result = await call("search_search", {"customer_id":cid, "resource":"customer", "fields":fields, "limit":1})
                    if result["ok"]:
                        return [row for row in result["data"] if args.discover.lower() in row.get("customer.descriptive_name", "").lower()]
                    return []
                matches = await asyncio.gather(*(identify(cid) for cid in listed["data"]))
                results["matches"] = [row for group in matches for row in group]
                save()
                print(json.dumps(results, ensure_ascii=False))
                return
            resources = sorted({job["resource"] for job in jobs} | {
                field.split(".", 1)[0] for job in jobs for field in job["fields"]
                if not field.startswith(("metrics.", "segments."))})
            metadata = {}
            async def getmeta(resource):
                metadata[resource] = await call("metadata_get_resource_metadata", {"resource_name":resource})
            await asyncio.gather(*(getmeta(resource) for resource in resources))
            results["metadata"] = metadata
            async def execute(job):
                key = job["key"]
                meta = metadata[job["resource"]]
                raw = json.dumps(metadata)
                missing = [field for field in job["fields"] if field not in raw]
                if missing or not meta["ok"]:
                    result = {"ok":False, "data":{"metadata_unconfirmed_fields":missing, "metadata_ok":meta["ok"]}}
                else:
                    payload = {k:v for k,v in job.items() if k != "key"}
                    payload["customer_id"] = args.customer
                    result = await call("search_search", payload)
                results[key] = {"query":job, **result}
                save()
                size = len(result["data"]) if isinstance(result["data"], list) else None
                print(json.dumps({"query":key,"ok":result["ok"],"rows":size,
                                  "error":None if result["ok"] else result["data"]}), flush=True)
            await asyncio.gather(*(execute(job) for job in jobs))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--discover")
    p.add_argument("--metadata")
    p.add_argument("--customer")
    p.add_argument("--jobs", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not args.discover and not args.metadata and not (args.customer and args.jobs):
        p.error("Use --discover NAME or --customer ID --jobs FILE")
    asyncio.run(run(args))
