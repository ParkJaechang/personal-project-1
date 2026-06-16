from pathlib import Path
import unittest


class RunServiceScriptTests(unittest.TestCase):
    def test_prepends_venv_scripts_to_path_before_running_service(self):
        script = Path("scripts/run-service.ps1").read_text(encoding="utf-8")

        path_update = '$env:PATH = "$VenvScripts;$env:PATH"'
        service_start = "& $Python -m soop_clip_downloader"

        self.assertIn('$VenvScripts = Join-Path $ProjectRoot ".venv\\Scripts"', script)
        self.assertIn(path_update, script)
        self.assertLess(script.index(path_update), script.index(service_start))


if __name__ == "__main__":
    unittest.main()
