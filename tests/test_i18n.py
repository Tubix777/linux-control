"""Language changes preserve evidence and retranslate live UI state."""
import unittest
from linux_control.i18n import Translator
from doctor.core import services_finding, Result
from doctor.hardware import parse_nvme_health


class Label:
    def set_label(self, value):
        self.text = value


class TranslationTests(unittest.TestCase):
    def test_both_source_languages_and_live_binding(self):
        translator = Translator("tr")
        label = translator.bind(Label(), "Apply")
        self.assertEqual(label.text, "Uygula")
        seen = []
        translator.connect(lambda: seen.append(translator.language))
        translator.set_language("en")
        self.assertEqual(label.text, "Apply")
        self.assertEqual(translator("Sorun Teşhisi"), "Diagnostics")
        self.assertEqual(seen, ["en"])
        translator.set_language("xx")
        self.assertEqual(translator.language, "en")

    def test_formatted_finding_keeps_counts_and_evidence(self):
        finding = services_finding(Result(0, "example.service loaded failed failed\n"), False)
        result = Translator("en").dynamic(finding.explanation)
        self.assertTrue(result.startswith("1 failed services found."))
        self.assertEqual(finding.evidence, ["example.service"])

    def test_profile_names_and_braces_are_literal(self):
        translator = Translator("tr")
        message = "Loaded Connected {range} — press Apply to send to wheel"
        self.assertEqual(translator.dynamic(message), "Connected {range} yüklendi — direksiyona göndermek için Uygula'ya bas")
        evidence = "/org/freedesktop/UDisks2/drives/unknown; example.service"
        self.assertEqual(translator.dynamic(evidence), evidence)

    def test_live_direction_and_force_feedback_state(self):
        translator = Translator("tr")
        self.assertEqual(translator.dynamic("D-pad: up-right"), "Yön tuşu: sağ-yukarı")
        self.assertEqual(translator.dynamic("83% — near limit"), "83% — sınıra yakın")
        self.assertEqual(translator.dynamic("Buttons: 288, 290"), "Tuşlar: 288, 290")

    def test_parameterized_messages_and_power_profiles(self):
        translator = Translator("en")
        self.assertEqual(translator("Kanal {channel}", channel=2), "Channel 2")
        self.assertEqual(translator("balanced"), "Balanced")
        self.assertEqual(Translator("tr")("balanced"), "Dengeli")

    def test_smart_warning_and_exhaustion_paragraphs(self):
        translator = Translator("en")
        for warnings in ([], ["spare"], None):
            properties = {"SmartUpdated": 999}
            if warnings is not None:
                properties["SmartCriticalWarning"] = warnings
            result = parse_nvme_health("Disk Model", {"percent_used": 101}, properties, now=1000)
            text = translator.dynamic(result.explanation)
            self.assertNotEqual(text, result.explanation)
            self.assertNotIn("üreticinin", text.lower())
            self.assertEqual(result.metric, 0)


if __name__ == "__main__":
    unittest.main()
