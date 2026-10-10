# Validation

## 0.1.2 hardware motion

183 tests passed in the isolated Fedora 44 GTK/Wayland suite. Added cases cover
zero, missing, invalid and positive RPM readings; active/hidden/reduced-motion
frame callback lifecycle; and stale/error readback cancellation. Existing
navigation, language, layout and explicit hardware-write boundaries still pass.
No physical fan, power-profile or RGB changes were performed.

The test suite distinguishes pure parsing/safety tests, embedded GTK lifecycle tests and real hardware observations. Demo telemetry is never treated as physical force-feedback validation.

| Area | Automated checks |
| --- | --- |
| Shared shell | Navigation, active-page lifecycle, preference persistence, language and reduced-motion changes |
| Diagnostics | Fixed command arguments, Flatpak identifiers/scopes, disk thresholds, failure isolation, SMART freshness/range/warnings |
| Animation | Progressive result scrolling/fades, short results, scrolling bounds, manual interruption, resizing and reduced motion |
| Hardware | Fan-helper ownership/mode boundaries, channel revalidation and curve validation; CSV/JSON fidelity; pause/close lifecycle |
| Wheel | Discovery/model/permissions, input decoding, profiles and mode changes; embedded host ownership and cleanup; explicit writes |
| Languages | Both source languages, live binding updates, formatted findings, literal profile names/identifiers and translated live statuses |

Run all tests in an isolated compositor so test windows and input never interfere with the user's desktop. GitHub Actions uses a private headless Weston session through `packaging/run_checks.sh`; it fails if the compositor cannot start. A headless RPM build runs the non-visual suite and explicitly skips GTK tests when no display is available. A passing RPM build alone does not validate animations.

```bash
packaging/run_checks.sh
python3 packaging/build_rpm.py --output dist
```

The compositor test runner requires Weston and `dbus-run-session`, in addition to the application dependencies. GTK page tests replace physical write functions with mocks. Normal source startup uses real read-only hardware sampling and device discovery; settings are only applied through explicit user actions.

Release validation should include opening all three pages, switching languages with unsaved values, starting a real diagnostic scan, manually interrupting automatic scrolling, and checking the package's desktop entry. Physical wheel force feedback, every recognized wheel model, every GPU driver and unsupported motherboard fans require separate hardware validation.

The source packager uses an explicit allowlist and excludes working directories, bytecode, local measurement files and VCS data. Release artifacts include SHA-256 checksums. Existing source repositories are preserved.

## 0.1.1 interaction coverage

The isolated GTK suite has 180 tests. New cases cover finite card entrance callbacks, expanded/collapsed content with unsaved entry values, cancellation on reduced motion and close, diagnostic-card animation ownership, CSS parsing and desktop animation-preference changes while the window is open. The supported-size layout check covers both 960 × 620 and 1280 × 900.

The original minimum-size test also failed on the unchanged 0.1.0 source in this Fedora test environment. Reducing sidebar spacing restored the supported minimum size; the assertion was preserved. Shared animations do not interpolate wheel telemetry or execute hardware writes.
