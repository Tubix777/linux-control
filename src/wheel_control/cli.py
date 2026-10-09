from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .devices import discover_wheels
from .diagnostics import build_diagnostics
from .model import WheelDevice
from .profiles import ProfileStore, WheelProfile, export_profile, import_profile


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wheel-control-cli",
        description="Inspect racing-wheel support without opening the graphical application.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("list", help="list detected wheels")
    doctor = subcommands.add_parser("doctor", help="print a diagnostics report")
    doctor.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )
    subcommands.add_parser("profiles", help="list saved profiles")
    export_parser = subcommands.add_parser(
        "export-profile", help="write one saved profile to a portable JSON file"
    )
    export_parser.add_argument("name", help="saved profile name")
    export_parser.add_argument("path", help="destination .json file")
    import_parser = subcommands.add_parser(
        "import-profile", help="add a profile from a portable JSON file"
    )
    import_parser.add_argument("path", help="source .json file")
    import_parser.add_argument("--name", help="override the profile name")
    import_parser.add_argument(
        "--replace", action="store_true", help="replace a profile with the same name"
    )
    apply_profile_parser = subcommands.add_parser(
        "apply-profile", help="apply a saved profile without opening the GUI"
    )
    apply_profile_parser.add_argument("name", help="profile name")
    apply_profile_parser.add_argument(
        "--device", help="device identifier from the list command"
    )
    apply_profile_parser.add_argument(
        "--dry-run", action="store_true", help="show changes without writing them"
    )
    return parser


def _doctor_text(report: dict) -> str:
    lines = [
        f"Wheel Control {report['wheel_control_version']}",
        f"Kernel: {report['system']['kernel']}",
        f"Session: {report['system']['session_type'] or 'unknown'}",
    ]
    devices = report["devices"]
    if not devices:
        lines.append("Devices: none")
        return "\n".join(lines)
    lines.append(f"Devices: {len(devices)}")
    for device in devices:
        controls = sorted(
            set(device["attributes"]) | set(device["force_feedback_controls"])
        )
        lines.extend(
            [
                f"- {device['name']} ({device['usb_id']})",
                f"  node: {device['event_node']}",
                f"  driver: {device['driver']}",
                f"  firmware: {device['firmware_revision'] or 'unknown'}",
                f"  controls: {', '.join(controls) if controls else 'none'}",
            ]
        )
        for recommendation in device.get("recommendations", []):
            lines.append(f"  hint: {recommendation['message']}")
    return "\n".join(lines)


def profile_values(
    profile: WheelProfile, minimum_range: int = 40, maximum_range: int = 2700
) -> dict[str, int]:
    profile = profile.normalised(minimum_range, maximum_range)
    return {
        "range": profile.rotation_range,
        "gain": round(profile.gain * 65535 / 100),
        "autocenter": round(profile.autocenter * 65535 / 100),
        "combine_pedals": int(profile.combine_pedals),
        "spring_level": profile.spring_level,
        "damper_level": profile.damper_level,
        "friction_level": profile.friction_level,
        "ffb_leds": int(profile.ffb_leds),
    }


def apply_profile(
    device: WheelDevice, profile: WheelProfile, dry_run: bool = False
) -> list[str]:
    changed = []
    for control, value in profile_values(
        profile, device.minimum_range, device.maximum_range
    ).items():
        if not device.supports(control):
            continue
        changed.append(f"{control}={value}")
        if not dry_run:
            device.write_attribute(control, value)
    return changed


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command in {"export-profile", "import-profile"}:
        store = ProfileStore()
        profiles = store.load()
        if args.command == "export-profile":
            profile = next(
                (
                    item
                    for item in profiles
                    if item.name.casefold() == args.name.casefold()
                ),
                None,
            )
            if profile is None:
                print(
                    f"wheel-control-cli: profile not found: {args.name}",
                    file=sys.stderr,
                )
                return 1
            try:
                export_profile(profile, Path(args.path))
            except (OSError, ValueError) as exc:
                print(f"wheel-control-cli: export failed: {exc}", file=sys.stderr)
                return 2
            print(f"Exported {profile.name} to {args.path}")
            return 0
        try:
            profile = import_profile(Path(args.path), args.name)
        except (OSError, ValueError) as exc:
            print(f"wheel-control-cli: import failed: {exc}", file=sys.stderr)
            return 2
        duplicate = next(
            (
                index
                for index, item in enumerate(profiles)
                if item.name.casefold() == profile.name.casefold()
            ),
            None,
        )
        if duplicate is not None and not args.replace:
            print(
                f"wheel-control-cli: profile already exists: {profile.name}; "
                "use --replace",
                file=sys.stderr,
            )
            return 1
        if duplicate is None:
            profiles.append(profile)
        else:
            profiles[duplicate] = profile
        try:
            store.save(profiles)
        except (OSError, ValueError) as exc:
            print(f"wheel-control-cli: import failed: {exc}", file=sys.stderr)
            return 2
        print(f"Imported {profile.name}")
        return 0
    if args.command == "profiles":
        for profile in ProfileStore().load():
            print(
                f"{profile.name}\trange={profile.rotation_range}\t"
                f"gain={profile.gain}%\tautocenter={profile.autocenter}%"
            )
        return 0
    try:
        devices = discover_wheels()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"wheel-control-cli: discovery failed: {exc}", file=sys.stderr)
        return 2
    if args.command == "list":
        if not devices:
            print("No racing wheels detected")
            return 1
        for device in devices:
            controls = sorted(set(device.attributes) | device.ff_capabilities)
            print(
                f"{device.identifier}\t{device.name}\t{device.driver}\t"
                f"{','.join(controls) or '-'}"
            )
        return 0
    if args.command == "apply-profile":
        if args.device is None and len(devices) > 1:
            print(
                "wheel-control-cli: multiple wheels found; select one with --device",
                file=sys.stderr,
            )
            return 1
        profiles = ProfileStore().load()
        profile = next(
            (item for item in profiles if item.name.casefold() == args.name.casefold()),
            None,
        )
        if profile is None:
            print(f"wheel-control-cli: profile not found: {args.name}", file=sys.stderr)
            return 1
        device = next(
            (
                item
                for item in devices
                if args.device is None or item.identifier == args.device
            ),
            None,
        )
        if device is None:
            print("wheel-control-cli: matching wheel not found", file=sys.stderr)
            return 1
        try:
            changed = apply_profile(device, profile, dry_run=args.dry_run)
        except PermissionError:
            print(
                "wheel-control-cli: permission denied; install the udev rule",
                file=sys.stderr,
            )
            return 2
        except OSError as exc:
            print(f"wheel-control-cli: could not apply profile: {exc}", file=sys.stderr)
            return 2
        if not changed:
            print("No profile controls are supported by the active driver")
            return 1
        action = "Would apply" if args.dry_run else "Applied"
        print(f"{action} {profile.name} to {device.name}: {', '.join(changed)}")
        return 0
    report = build_diagnostics(devices)
    print(
        json.dumps(report, indent=2, ensure_ascii=False)
        if args.json
        else _doctor_text(report)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
