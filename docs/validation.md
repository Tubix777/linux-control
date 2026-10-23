# Validation

## 0.5.0 Graphite validation — 24 October 2026

The 257-test native suite passes in a private Fedora 44 KWin/Wayland
session (only the dpkg-deb tool test is skipped on this host). The production
stylesheet parses without warnings. Native Pango reports the bundled Inter
family; the upstream font and complete OFL notice are in the release source.

All pages were rendered in Turkish and English at 960 × 620 and 1320 × 900.
This includes module downloads, keyboard focus, the update dialog and compact
Flatpak controls. Public images and the finite navigation recording are taken
from real GTK widgets using explicit synthetic fixtures, with a demo wheel and
no local logs, private profiles or device serials. The GIF is a scaled recording;
the application itself uses GTK's frame clock and the desktop renderer.

Motion tests cover pixel continuity when interrupted, live input picking,
rapid navigation, manual scan-scroll interruption, resize/hide/close and both
reduced-motion preferences. State and language tests retain selected values.
The wheel regression also checks that visible numeric labels match unapplied
slider values after a language change, and that demo metadata follows the language.

Distribution jobs repeat the native suite, build and install the matching
package and open every installed view plus the update dialog. Zorin uses its
Ubuntu base; these checks do not exercise a physical wheel, fan or real system
authorization.

## 0.4.0 interaction validation

The native test suite now checks exact rendered pixels before a transition and
when it is interrupted, intermediate frames, transformed input picking, rapid
retargeting, unsaved values, expanded evidence, copy-feedback timer cleanup,
keyboard focus, resize, hide, close and both reduced-motion preferences.
Public preview images use synthetic fixtures, not local diagnostic output.
Private KWin/Wayland visual review covers compact and wide windows; package
workflows repeat the checks and installed views on all five distro environments.


## 0.3.1 distribution and rename validation

Ubuntu 24.04 (GTK 4.14 / Adw 1.5), Ubuntu 26.04 (GTK 4.22 / Adw 1.9),
Deepin 25 (GTK 4.18 / Adw 1.5), Fedora 44 and current Arch (GTK 4.24 / Adw 1.10)
are checked in isolated containers and private Weston sessions. DEB jobs run
216 tests without GUI skips; Fedora/Arch skip only the dpkg-deb-specific build
test. Every installed package opens all six native views and verifies SVG
decoding. Zorin 18 is covered through its Ubuntu 24.04 base, not a separately
installed Zorin desktop. Debian 13 and other derivatives require the declared
minimum libraries; physical hardware and other architectures remain separate.

New checks cover package ownership/modes, bundled fonts/licenses, the absence
of privileged installation scripts, DEB dependencies/checksums, offline Arch
source pinning, complete release artifacts, identical Fedora/Arch source
archives, download format classification and name/legacy identity consistency.

Download pages choose DEB/Arch/RPM from the OS family before the GTK loop starts.
Older libadwaita clamp content is explicitly expanded and verified against the
available page width. The DEB explicitly requires its SVG loader. Wheel switch rows now use the GTK
list container required by newer libadwaita, preserving their state and writes.
The application is Uzeyir Control; the Python module, settings directory and
desktop application ID stay stable for upgrade compatibility.

## 0.2.1 motion

208 tests passed in an isolated Fedora 44 KWin/Wayland session, including GUI
checks without skips. New cases cover paint-only geometry stability, unsaved
entries, remapping, finite scan completion, hidden/closed/reduced activity,
format-row handler cleanup, actual pending scan lifecycle, filter rebuilds and
directional navigation. Existing input latency, hardware-write boundaries,
manual scroll interruption and compact/wide layout checks remain in place.

Six native views and a real read-only scan were visually inspected; a native
frame recording was captured. No physical fan or force-feedback writes were run.

## 0.2.0 redesign and distribution pages

200 tests passed in the isolated Fedora 44 GTK/KWin Wayland suite, with no GUI
skips. The six native views were checked at 960 × 620 and 1280 × 900. Assertions
cover both compact hardware columns and wheel panel orientation, as well as
horizontal clipping and the supported minimum height.

New checks cover official repository/asset URLs, filename integrity, draft and
preview releases, oversized/unexpected responses, source versus portable
archives, offline fallback, background release requests, navigation during
pending requests, close-time callback cancellation, package-format preservation,
unsaved actual wheel settings and Flatpak selection through download navigation,
and attention filtering that retains unverified findings. Empty filtered results
remain visible and release their animation callback. Scan scrolling leaves the
result heading and filter fully visible.

Real read-only hardware, empty wheel, diagnostic and three distribution pages
were rendered and inspected. The app's HTTP reader returned public metadata for
Anvil v0.15.0-alpha, Wheel v0.1.1 and the existing Linux Control release. Native
icons are rendered at their intended size and display scale. Manrope is bundled
with its OFL notice and loaded within the process. No physical fan, RGB, power
profile, force-feedback or device-permission changes were performed.

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

Release source is generated once and reused byte-for-byte across distributions. Each builder checks the public file list, file permissions and source contents before accepting it. This avoids zlib/zlib-ng compressed-stream differences without weakening source consistency checks.

## Update coverage

Update tests use synthetic release metadata and package bytes. They cover numeric
version order, correct app/OS selection, untrusted URLs, missing digests, checksum
and size failures, cancellation, retry, queued callbacks, explicit installation,
PackageKit authorization flags, native installer results and installed-version
verification. Real system authorization is not bypassed or exercised by GUI tests.
The installed package smoke check opens the update dialog without network requests.

## Release checks, 18 October 2026

The 257-test suite passed in Ubuntu 24.04/26.04, Deepin 25, Fedora 44 and Arch.
Fedora/Arch skip only the dpkg-deb-specific tool test; a separate full compositor
run includes the GUI tests that the headless RPM build check skips. All installed
views and the update dialog open from the native packages. An immediate dialog
close regression covers libadwaita 1.5 as well as newer versions. These checks use
isolated containers and do not claim physical hardware or system-authentication coverage.
