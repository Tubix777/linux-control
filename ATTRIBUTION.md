# Attribution and licenses

Linux Control application code is distributed under **GPL-3.0-or-later**. The complete GPL text is in [COPYING](COPYING). Included components and fonts retain the individual licenses and original copyright notices listed below.

| Component | Origin | Included version | License |
| --- | --- | --- | --- |
| Wheel Control | [Tubix777/wheel-control](https://github.com/Tubix777/wheel-control) | 0.1.1 | GPL-3.0-or-later; [license copy](licenses/Wheel-Control-GPL-3.0.txt) |
| Anvil Control reusable hardware modules | [Tubix777/anvil-control](https://github.com/Tubix777/anvil-control) | 0.14.0-alpha | MIT; [license copy](licenses/Anvil-Control-MIT.txt) |
| Fedora Doctor | Local prototype by Tubix777 and contributors | 0.1.0 | Released with this combined application under GPL-3.0-or-later |
| Combined GTK shell, hardware page and integration | Tubix777 and contributors | 0.2.0 | GPL-3.0-or-later |
| Inter variable font | [Google Fonts / Inter](https://github.com/google/fonts/tree/main/ofl/inter) | Pinned snapshot, 2026-10-24 | OFL-1.1; [license copy](licenses/Inter-OFL.txt) |

The original repositories and installed applications are independent. This repository vendors reusable modules and adapts their interfaces to one GTK window. It does not include Anvil's Qt interface, privileged fan helper or polkit policy. Existing packaged Anvil fan support can be reused when its original safety checks pass.

## Typography

Inter is bundled from the Google Fonts repository under the SIL Open Font
License 1.1. The copyright notice and full license are preserved in
`licenses/Inter-OFL.txt`. The font is registered only in the application
process; no system font installation or desktop font setting is changed.

The exact upstream commit and bundled font digest are recorded in
[Inter source provenance](licenses/Inter-source.txt).
