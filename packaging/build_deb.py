#!/usr/bin/env python3
"""Build an architecture-independent DEB without installing or running as root."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
from payload import ROOT, source_epoch, stage, version

DEPENDENCIES = ("python3 (>= 3.11), python3-gi, python3-cairo, python3-gi-cairo, "
                "python3-pyudev, gir1.2-gtk-4.0 (>= 4.12), gir1.2-adw-1 (>= 1.5), fontconfig, librsvg2-common")


def build(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    scratch = ROOT / "work"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deb-", dir=scratch) as directory:
        payload = Path(directory) / "package"
        stage(payload)
        copyright_file = payload / "usr/share/doc/uzeyir-control/copyright"
        copyright_file.write_text((ROOT / "ATTRIBUTION.md").read_text() + "\n\n" +
            "\n\n".join(p.read_text() for p in [ROOT / "COPYING", *sorted((ROOT / "licenses").glob("*.txt"))]))
        files = sorted(p for p in payload.rglob("*") if p.is_file())
        installed_size = (sum(p.stat().st_size for p in files) + 1023) // 1024
        control = payload / "DEBIAN"
        control.mkdir(mode=0o755)
        (control / "control").write_text(f"""Package: uzeyir-control
Version: {version()}-1
Section: utils
Priority: optional
Architecture: all
Maintainer: Uzeyir Control contributors <tuna@kale.gen.tr>
Homepage: https://github.com/Tubix777/linux-control
Bugs: https://github.com/Tubix777/linux-control/issues
Installed-Size: {installed_size}
Depends: {DEPENDENCIES}
Provides: linux-control
Conflicts: linux-control
Replaces: linux-control
Recommends: udisks2
Suggests: flatpak, lm-sensors, power-profiles-daemon
Description: Native hardware, racing wheel and diagnostics control center
 GTK 4/libadwaita application with local hardware monitoring, explicit wheel
 controls and read-only system diagnostics. Includes Turkish/English UI,
 monochrome design, animations and reduced-motion support.
 No privileged helper, device-permission rule or background service is installed.
""")
        (control / "md5sums").write_text("".join(
            hashlib.md5(p.read_bytes(), usedforsecurity=False).hexdigest() + "  " +
            str(p.relative_to(payload)) + "\n" for p in files))
        result = destination / f"uzeyir-control_{version()}-1_all.deb"
        subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(payload), str(result)],
                       env={**os.environ, "SOURCE_DATE_EPOCH": str(source_epoch())}, check=True)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    print(build(parser.parse_args().output))
