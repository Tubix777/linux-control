#!/usr/bin/env python3
"""Build a deterministic source archive with an explicit public-file allowlist."""
import argparse
import gzip
import io
import os
from pathlib import Path
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = ("src", "tests", "share", "packaging", "docs", ".github", "licenses", "COPYING", "README.md", "ATTRIBUTION.md", "PLAN.md", "AGENTS.md", "pyproject.toml", "run.sh", ".gitignore")


def build(destination: Path) -> Path:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"uzeyir-doctor-{version}.tar.gz"
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    files = []
    for name in PUBLIC_FILES:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file() and not any(part == "__pycache__" for part in item.parts) and item.suffix not in (".pyc", ".pyo"))
    with archive.open("wb") as output, gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=epoch) as compressed, tarfile.open(fileobj=compressed, mode="w") as tar:
        for path in sorted(files):
            if path.is_symlink():
                raise ValueError(f"Source archive refuses symlinks: {path.relative_to(ROOT)}")
            info = tar.gettarinfo(str(path), arcname=f"uzeyir-doctor-{version}/{path.relative_to(ROOT)}")
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = epoch
            info.mode = 0o755 if os.access(path, os.X_OK) else 0o644
            tar.addfile(info, io.BytesIO(path.read_bytes()))
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(build(args.output))
