import tempfile
import unittest
from pathlib import Path
from stat import S_IMODE

from wheel_control.profiles import (
    ProfileStore,
    WheelProfile,
    export_profile,
    import_profile,
)


class ProfileTests(unittest.TestCase):
    def test_invalid_numeric_and_name_values_are_rejected(self) -> None:
        for value in (float("inf"), float("nan"), None, [], True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                WheelProfile(name="Bad", gain=value).normalised()
        for name in (None, 42, [], "   "):
            with self.subTest(name=name), self.assertRaises(ValueError):
                WheelProfile(name=name).normalised()

    def test_non_utf8_store_recovers_and_import_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_bytes(b"\xff\xfe")
            self.assertEqual(ProfileStore(path).load()[0].name, "Default")
            with self.assertRaises(ValueError):
                import_profile(path)

    def test_profiles_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory) / "profiles.json")
            expected = [WheelProfile(name="Rally", rotation_range=540, gain=80)]
            store.save(expected)
            self.assertEqual(store.load(), expected)
            self.assertEqual(S_IMODE(store.path.stat().st_mode), 0o600)
            self.assertEqual(list(store.path.parent.glob(".profiles.*")), [])

    def test_corrupt_profile_file_returns_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text("not-json", encoding="utf-8")
            profiles = ProfileStore(path).load()
            self.assertEqual(profiles[0].name, "Default")

    def test_untrusted_values_are_normalised_or_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text(
                '{"profiles": ['
                '{"name": " Rally ", "rotation_range": 99999, "gain": -2},'
                '{"name": "Broken", "combine_pedals": "yes"}'
                "]}",
                encoding="utf-8",
            )
            profiles = ProfileStore(path).load()
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0].name, "Rally")
            self.assertEqual(profiles[0].rotation_range, 2700)
            self.assertEqual(profiles[0].gain, 0)

    def test_portable_profile_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rally.wheel-profile.json"
            expected = WheelProfile(name="Rally", rotation_range=540, gain=82)
            export_profile(expected, path)
            self.assertEqual(import_profile(path), expected)
            self.assertEqual(import_profile(path, "Gravel").name, "Gravel")
            self.assertEqual(S_IMODE(path.stat().st_mode), 0o600)

    def test_rejects_non_profile_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"version": 2}', encoding="utf-8")
            with self.assertRaises(ValueError):
                import_profile(path)


if __name__ == "__main__":
    unittest.main()
