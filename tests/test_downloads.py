"""Distribution metadata stays source-backed and cannot become a shell action."""
import io
import json
import unittest
from linux_control import __version__
from linux_control.downloads import (Asset, MAX_RESPONSE, REPOSITORIES, ReleaseError,
                                     bundled_release, fetch_release, official_url, parse_release)


def payload(module="wheel"):
    repo = REPOSITORIES[module]
    return {"tag_name": "v1.0.0", "html_url": f"https://github.com/{repo}/releases/tag/v1.0.0",
            "assets": [{"name": "app-1.0.rpm", "browser_download_url": f"https://github.com/{repo}/releases/download/v1.0.0/app-1.0.rpm", "size": 2048}]}


class DistributionTests(unittest.TestCase):
    def test_all_bundled_module_links_belong_to_the_correct_repository(self):
        for module, repository in REPOSITORIES.items():
            release = bundled_release(module)
            self.assertEqual(release.repository, repository)
            self.assertTrue(official_url(release.url, repository))
            self.assertTrue(release.assets)
            self.assertIn("rpm", release.formats)
            self.assertTrue(all(official_url(asset.url, repository, asset=True) for asset in release.assets))

    def test_doctor_is_distributed_in_the_current_combined_package(self):
        release = bundled_release("doctor")
        self.assertEqual(release.tag, "v" + __version__)
        self.assertTrue(all(asset.name.startswith("linux-control-" + __version__) for asset in release.assets))

    def test_external_hosts_credentials_and_encoded_traversal_are_rejected(self):
        repository = REPOSITORIES["wheel"]
        for url in (f"http://github.com/{repository}/releases/tag/v1",
                    f"https://github.com.evil.invalid/{repository}/releases/tag/v1",
                    f"https://user@github.com/{repository}/releases/tag/v1",
                    f"https://github.com/{repository}/releases/tag/%2e%2e/other",
                    f"https://github.com/{repository}/releases/tag/v1?x=1",
                    f"https://github.com/{repository}/releases/tag/v1#other",
                    "https://github.com/another/project/releases/tag/v1"):
            self.assertFalse(official_url(url, repository), url)

    def test_unsafe_asset_names_urls_and_duplicate_files_are_not_offered(self):
        data = payload()
        original = data["assets"][0]
        data["assets"] += [dict(original), {**original, "name": "app;echo.rpm"},
                           {**original, "name": "different.rpm"},
                           {**original, "name": "other.rpm", "browser_download_url": "https://example.org/other.rpm"}]
        release = parse_release(data, REPOSITORIES["wheel"])
        self.assertEqual(len(release.assets), 1)

    def test_source_rpm_has_no_install_command(self):
        self.assertEqual(Asset("app.rpm", "").install_command, "sudo dnf install ./app.rpm")
        self.assertEqual(Asset("app.deb", "").install_command, "sudo apt install ./app.deb")
        for name in ("app.src.rpm", "app.tar.gz", "app$(echo).rpm", "../app.rpm"):
            self.assertIsNone(Asset(name, "").install_command)

    def test_source_archives_are_not_presented_as_portable_applications(self):
        self.assertEqual(Asset("linux-control-0.2.0.tar.gz", "").kind, "source")
        self.assertEqual(Asset("anvil-control-0.15.0-linux-x86_64.tar.gz", "").kind, "portable")
        self.assertEqual(bundled_release("doctor").formats, ("rpm", "source"))

    def test_alpha_release_is_marked_as_preview_even_without_api_flag(self):
        data = payload()
        data["tag_name"] = "v1.0.0-alpha"
        self.assertTrue(parse_release(data, REPOSITORIES["wheel"]).preview)

    def test_fetch_includes_previews_and_skips_drafts(self):
        requests = []
        def opener(request, timeout):
            requests.append((request.full_url, timeout))
            return io.BytesIO(json.dumps([{**payload(), "draft": True}, {**payload(), "prerelease": True}]).encode())
        release = fetch_release("wheel", opener)
        self.assertTrue(release.preview)
        self.assertEqual(requests, [("https://api.github.com/repos/Tubix777/wheel-control/releases?per_page=10", 8)])

    def test_oversized_and_unexpected_responses_fail_without_another_request(self):
        for raw in (b" " * (MAX_RESPONSE + 1), b"{}", b"[]"):
            with self.assertRaises(ReleaseError):
                fetch_release("hardware", lambda *_args, **_kwargs: io.BytesIO(raw))
