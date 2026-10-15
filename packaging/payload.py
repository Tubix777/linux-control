"""Unprivileged staging shared by non-RPM packages. No installer side effects."""
from pathlib import Path
import shutil
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def version():
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]


def stage(destination):
    destination = Path(destination)
    library = destination / "usr/share/uzeyir-doctor/src"
    for source in sorted((ROOT / "src").rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo"):
            continue
        if source.is_symlink():
            raise ValueError("Package payload refuses symlinks")
        target = library / source.relative_to(ROOT / "src")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    pairs = [(ROOT / "packaging/linux-control", "usr/bin/uzeyir-doctor"),
             (ROOT / "packaging/linux-control", "usr/bin/linux-control"),
             (ROOT / "share/io.github.Tubix777.LinuxControl.desktop", "usr/share/applications/io.github.Tubix777.LinuxControl.desktop"),
             (ROOT / "share/io.github.Tubix777.LinuxControl.svg", "usr/share/icons/hicolor/scalable/apps/io.github.Tubix777.LinuxControl.svg")]
    pairs += [(p, "usr/share/licenses/uzeyir-doctor/" + p.name)
              for p in [ROOT / "COPYING", *sorted((ROOT / "licenses").glob("*.txt"))]]
    pairs += [(ROOT / name, "usr/share/doc/uzeyir-doctor/" + Path(name).name)
              for name in ("README.md", "ATTRIBUTION.md", "docs/install.md", "docs/permissions.md", "docs/validation.md")]
    for source, name in pairs:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o755 if name.startswith("usr/bin/") else 0o644)
    for directory in destination.rglob("*"):
        if directory.is_dir():
            directory.chmod(0o755)

