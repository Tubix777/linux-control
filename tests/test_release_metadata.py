"""A release tag must identify the version actually packaged and installed."""
import re
import tomllib
import unittest
from pathlib import Path
from linux_control import __version__


class ReleaseMetadataTests(unittest.TestCase):
    def test_python_project_and_rpm_versions_agree(self):
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / "pyproject.toml").read_text())
        rpm = re.search(r"^Version:\s+(\S+)", (root / "packaging/linux-control.spec").read_text(), re.MULTILINE)
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(rpm.group(1), __version__)
        self.assertIn("resources/*.svg", project["tool"]["setuptools"]["package-data"]["linux_control"])


if __name__ == "__main__":
    unittest.main()
