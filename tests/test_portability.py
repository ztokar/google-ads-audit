import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]

class Portability(unittest.TestCase):
    def test_credentials_are_outside_checkout_and_project_has_no_personal_default(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(Path, "home", return_value=Path(tmp)):
            spec = importlib.util.spec_from_file_location("audit_connection_test", ROOT / "connection.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.PROJECT, "")
            self.assertEqual(module.CREDENTIALS, Path(tmp) / ".config/google-ads-audit/credentials.json")
            self.assertFalse(module.CREDENTIALS.is_relative_to(ROOT))
            with self.assertRaisesRegex(ValueError, "configure.py"):
                module.login(Path(tmp) / "missing.json")

    def test_account_local_query_generation_has_finite_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(ROOT / "build_queries.py"), "--timezone", "America/New_York", "--output", tmp], check=True, capture_output=True)
            period = json.loads((Path(tmp) / "period.json").read_text())
            jobs = json.loads((Path(tmp) / "queries.json").read_text())
            self.assertEqual(period["days"], 90)
            self.assertGreaterEqual(len(jobs), 30)
            for job in jobs:
                if any(x.startswith("metrics.") for x in job["fields"]):
                    self.assertTrue(any("segments.date BETWEEN" in x for x in job.get("conditions", [])), job["key"])

if __name__ == "__main__":
    unittest.main()
