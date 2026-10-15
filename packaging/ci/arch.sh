#!/usr/bin/env bash
set -euo pipefail
pacman -Syu --noconfirm --needed base-devel python python-gobject python-cairo python-pyudev gtk4 libadwaita fontconfig librsvg desktop-file-utils weston dbus
packaging/run_checks.sh
# makepkg must run without root; its build directory is isolated from checkout.
id -u builder >/dev/null 2>&1 || useradd -m builder
mkdir -p /tmp/uzeyir-build
cp -a . /tmp/uzeyir-build/
chown -R builder:builder /tmp/uzeyir-build
runuser -u builder -- bash -euc 'cd /tmp/uzeyir-build; python3 packaging/build_arch.py --output dist'
mkdir -p dist
cp /tmp/uzeyir-build/dist/uzeyir-control-* dist/
pacman -U --noconfirm dist/uzeyir-control-*.pkg.tar.zst
desktop-file-validate /usr/share/applications/io.github.Tubix777.LinuxControl.desktop
bash packaging/verify_installed.sh
