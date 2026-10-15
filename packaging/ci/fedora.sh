#!/usr/bin/env bash
set -euo pipefail
dnf -y install python3 python3-gobject python3-cairo python3-pyudev gtk4 libadwaita librsvg2 weston dbus-daemon rpm-build desktop-file-utils tar gzip findutils
packaging/run_checks.sh
python3 packaging/build_rpm.py --output dist
rpm -Uvh --replacepkgs dist/uzeyir-control-*.noarch.rpm
bash packaging/verify_installed.sh
