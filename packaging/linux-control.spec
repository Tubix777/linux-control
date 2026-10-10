Name:           linux-control
Version:        0.1.2
Release:        1%{?dist}
Summary:        Native hardware, racing wheel and diagnostics control center
License:        GPL-3.0-or-later AND MIT
URL:            https://github.com/Tubix777/linux-control
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3
BuildRequires:  python3-gobject
BuildRequires:  python3-cairo
BuildRequires:  python3-pyudev
BuildRequires:  gtk4
BuildRequires:  libadwaita
BuildRequires:  desktop-file-utils
Requires:       python3
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       python3-pyudev
Requires:       gtk4
Requires:       libadwaita
Recommends:     udisks2

%description
Linux Control combines live hardware monitoring, racing-wheel configuration,
local system diagnostics and Flatpak permission checks in one GTK 4 window.
It uses a monochrome interface, live Turkish/English selection and optional
reduced motion. Unsupported hardware is reported without invented readings.

%prep
%autosetup

%build
# Pure Python sources; no build-time network access or wheel build required.

%install
install -d %{buildroot}%{_datadir}/linux-control/src
cp -a src/. %{buildroot}%{_datadir}/linux-control/src/
find %{buildroot}%{_datadir}/linux-control -type d -name __pycache__ -prune -exec rm -rf {} +
install -Dm0755 packaging/linux-control %{buildroot}%{_bindir}/linux-control
install -Dm0644 share/io.github.Tubix777.LinuxControl.desktop %{buildroot}%{_datadir}/applications/io.github.Tubix777.LinuxControl.desktop
install -Dm0644 share/io.github.Tubix777.LinuxControl.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/io.github.Tubix777.LinuxControl.svg

%check
PYTHONPATH=src GDK_BACKEND=broadway GTK_A11Y=none %{__python3} -m unittest discover -s tests -v
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.Tubix777.LinuxControl.desktop

%files
%license COPYING licenses/*.txt
%doc README.md ATTRIBUTION.md docs/permissions.md docs/validation.md
%{_bindir}/linux-control
%{_datadir}/linux-control/
%{_datadir}/applications/io.github.Tubix777.LinuxControl.desktop
%{_datadir}/icons/hicolor/scalable/apps/io.github.Tubix777.LinuxControl.svg

%changelog
* Sat Oct 10 2026 Linux Control contributors - 0.1.2-1
- Add read-only circuit/fan activity illustration with bounded visible-only motion
- Stop activity on stale readings, polling errors, pause, page hide and reduced motion

* Sat Oct 10 2026 Tubix777 and contributors - 0.1.1-1
- Add shared card, menu, control and expansion animations
- Follow desktop reduced-motion changes immediately
- Keep compact sidebar within the supported minimum window size

* Fri Oct 09 2026 Tubix777 and contributors - 0.1.0-1
- Integrate hardware, wheel and diagnostics in a single native window
- Add shared Turkish/English language selection and reduced motion
- Preserve explicit writes, safe fan helper checks and honest SMART estimates
