#!/usr/bin/env bash
set -euo pipefail
pacman -Syu --noconfirm --needed base-devel python python-gobject python-cairo python-pyudev gtk4 libadwaita fontconfig librsvg desktop-file-utils weston dbus
packaging/run_checks.sh
# makepkg must run without root; its build directory is isolated from checkout.
id -u builder >/dev/null 2>&1 || useradd -m builder
arch_build="$(mktemp -d /tmp/uzeyir-build.XXXXXX)"
trap 'rm -rf "$arch_build"' EXIT
cp -a . "$arch_build/"
chown -R builder:builder "$arch_build"
runuser -u builder -- bash -euc 'cd "$1"; python3 packaging/build_arch.py --output dist' arch-build "$arch_build"
mkdir -p dist
cp "$arch_build"/dist/uzeyir-control-* dist/
pacman -U --noconfirm dist/uzeyir-control-*.pkg.tar.zst
desktop-file-validate /usr/share/applications/io.github.Tubix777.LinuxControl.desktop
bash packaging/verify_installed.sh
