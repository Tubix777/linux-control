#!/usr/bin/env python3
"""Publish verified tag assets with GitHub CLI; retries preserve existing assets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tomllib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--assets", type=Path, default=Path("dist"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    if args.tag != "v" + version and not args.tag.startswith("v" + version + "-"):
        raise SystemExit("Release tag does not match the package version")
    repository = os.environ.get("GITHUB_REPOSITORY", "Tubix777/linux-control")
    def command(*arguments):
        return ["gh", "release", *arguments, "--repo", repository]
    files = sorted(args.assets.glob("*.rpm")) + sorted(args.assets.glob("*.tar.gz")) + [args.assets / "SHA256SUMS"]
    if not all(file.is_file() for file in files) or len(files) < 4:
        raise SystemExit("Source, RPM, source RPM and SHA256SUMS assets are required")
    view = subprocess.run(command("view", args.tag, "--json", "assets,isDraft"), capture_output=True, text=True)
    if view.returncode:
        subprocess.run(command("create", args.tag, "--verify-tag", "--draft", "--prerelease", "--title", f"Linux Control {args.tag}", "--notes-file", str(root / "docs/release-notes.md")), check=True)
        existing = set()
        is_draft = True
    else:
        data = json.loads(view.stdout)
        existing = {asset["name"] for asset in data["assets"]}
        is_draft = data["isDraft"]
    for file in files:
        if file.name not in existing:
            subprocess.run(command("upload", args.tag, str(file)), check=True)
    if is_draft:
        subprocess.run(command("edit", args.tag, "--draft=false"), check=True)


if __name__ == "__main__":
    main()
