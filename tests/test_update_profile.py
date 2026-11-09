import argparse
import io
import json
import tempfile
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import update_profile as profile


class GitHubSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(redirect_stdout(io.StringIO()))

    def test_pagination_and_public_original_repository_metrics(self):
        first_page = [
            {"name": f"project-{index}", "language": "Python", "stargazers_count": 1}
            for index in range(97)
        ] + [
            {"name": "private", "private": True, "language": "PHP", "stargazers_count": 900},
            {"name": "fork", "fork": True, "language": "PHP", "stargazers_count": 800},
            {"name": "archived", "archived": True, "language": "PHP", "stargazers_count": 2},
        ]
        last_page = [
            {"name": "latest", "language": "TypeScript", "stargazers_count": 3},
            {"name": "no-language", "language": None, "stargazers_count": None},
        ]
        calendar = {"totalContributions": 42, "weeks": []}
        with (
            patch.object(profile, "OWNER", "test-owner"),
            patch.object(profile, "request_json", side_effect=[{"public_repos": 101}, first_page, last_page]) as request,
            patch.object(profile, "fetch_contributions", return_value=calendar),
        ):
            snapshot = profile.fetch_github_snapshot()

        self.assertEqual(request.call_count, 3)
        self.assertEqual(request.call_args_list[1].args[0],
                         "https://api.github.com/users/test-owner/repos?type=owner&sort=pushed&per_page=100&page=1")
        self.assertEqual(request.call_args_list[2].args[0],
                         "https://api.github.com/users/test-owner/repos?type=owner&sort=pushed&per_page=100&page=2")
        self.assertEqual(snapshot["public_repos"], 101)
        self.assertEqual(snapshot["original_projects"], 100)
        self.assertEqual(snapshot["stars"], 102)
        self.assertEqual(snapshot["top_language"], "Python")
        self.assertEqual(snapshot["languages"], {"Python": 97, "TypeScript": 1})
        self.assertEqual(len(snapshot["repositories"]), 100)
        self.assertNotIn("private", [repo["name"] for repo in snapshot["repositories"]])
        self.assertNotIn("fork", [repo["name"] for repo in snapshot["repositories"]])
        self.assertEqual(profile.repo_metadata(snapshot, "NO-LANGUAGE")["language"], "Multi-stack")
        self.assertEqual(snapshot["contributions"], calendar)

    def test_contribution_failure_does_not_discard_repository_data(self):
        with (
            patch.object(profile, "request_json", side_effect=[{"public_repos": 0}, []]),
            patch.object(profile, "fetch_contributions", side_effect=urllib.error.URLError("offline")),
        ):
            snapshot = profile.fetch_github_snapshot()
        self.assertEqual(snapshot["contributions"], {})
        self.assertEqual(snapshot["public_repos"], 0)
        self.assertEqual(snapshot["stars"], 0)
        self.assertEqual(snapshot["top_language"], "N/A")

    def test_malformed_rest_responses_are_rejected(self):
        for responses in ([[]], [{}, {}]):
            with self.subTest(responses=responses), patch.object(profile, "request_json", side_effect=responses):
                with self.assertRaises(RuntimeError):
                    profile.fetch_github_snapshot()

    def test_no_token_skips_graphql(self):
        with patch.object(profile, "GITHUB_TOKEN", ""), patch.object(profile, "request_json") as request:
            self.assertEqual(profile.fetch_contributions(), {})
        request.assert_not_called()

    def test_graphql_errors_are_rejected_even_with_partial_data(self):
        with (
            patch.object(profile, "GITHUB_TOKEN", "test-token"),
            patch.object(profile, "request_json", return_value={"errors": [{"message": "denied"}], "data": {}}),
        ):
            with self.assertRaises(RuntimeError):
                profile.fetch_contributions()


class SvgRenderingTests(unittest.TestCase):
    def test_external_text_is_escaped_in_stats_and_project_cards(self):
        external_text = '<script> & "quoted"'
        stats = profile.render_stats_svg({
            "top_language": external_text, "languages": {external_text: 1},
        })
        project = dict(profile.PROJECTS[0], title=external_text, description=external_text, label=external_text)
        card = profile.render_project_svg(project, {"language": external_text})
        for svg in (stats, card):
            with self.subTest(svg=svg[:80]):
                root = ET.fromstring(svg)
                self.assertIn(external_text, list(root.itertext()))
                self.assertNotIn("<script>", svg)
                self.assertIsNone(root.find(".//{http://www.w3.org/2000/svg}script"))


class ProfileRefreshTests(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.readme = root / "README.md"
        self.stats = root / "assets/live-stats.svg"
        self.activity = root / "assets/activity-loop.gif"
        self.projects = root / "assets/projects"
        self.original_readme = (
            "# Profile\n\n<!--START_SECTION:waka-->\nold statistics\n"
            "<!--END_SECTION:waka-->\n\nKeep this footer.\n"
        )
        self.readme.write_text(self.original_readme, encoding="utf-8")
        self.stats.parent.mkdir(parents=True)
        self.stats.write_bytes(b"previous stats")
        self.activity.write_bytes(b"previous animation")
        self.projects.mkdir()
        for project in profile.PROJECTS:
            (self.projects / project["file"]).write_bytes(b"previous project")
        self.snapshot = {
            "public_repos": 7, "original_projects": 5, "stars": 11,
            "top_language": "Python", "languages": {"Python": 3},
            "repositories": [], "contributions": {},
        }
        self.enterContext(patch.multiple(
            profile, README_PATH=self.readme, STATS_PATH=self.stats,
            ACTIVITY_PATH=self.activity, PROJECTS_PATH=self.projects, WAKATIME_API_KEY="",
        ))
        self.args = self.enterContext(patch.object(profile, "parse_args", return_value=argparse.Namespace(snapshot=None)))
        self.github = self.enterContext(patch.object(profile, "fetch_github_snapshot", return_value=self.snapshot))
        self.enterContext(patch.object(profile, "request_json", side_effect=AssertionError("Unexpected network request")))
        self.enterContext(redirect_stdout(io.StringIO()))

    def asset_bytes(self):
        return {path: path.read_bytes() for path in (self.stats, self.activity, *self.projects.iterdir())}

    def test_github_outage_preserves_all_published_files(self):
        before = self.asset_bytes()
        for error in (urllib.error.URLError("offline"), ValueError("invalid JSON"), RuntimeError("invalid response")):
            with self.subTest(error=error):
                self.github.side_effect = error
                self.assertEqual(profile.main(), 0)
                self.assertEqual(self.asset_bytes(), before)
                self.assertEqual(self.readme.read_text(encoding="utf-8"), self.original_readme)

    def test_github_failure_does_not_block_wakatime_refresh(self):
        before = self.asset_bytes()
        self.github.side_effect = urllib.error.URLError("offline")
        with (
            patch.object(profile, "WAKATIME_API_KEY", "test-key"),
            patch.object(profile, "fetch_wakatime", return_value={"human_readable_total": "2 hrs", "languages": []}),
        ):
            self.assertEqual(profile.main(), 0)
        expected_block = "**Last 7 days:** 2 hrs\n\n```text\nNo WakaTime language activity was recorded.\n```"
        self.assertEqual(self.readme.read_text(encoding="utf-8"),
                         self.original_readme.replace("old statistics", expected_block))
        self.assertEqual(self.asset_bytes(), before)

    def test_wakatime_outage_preserves_readme_but_refreshes_assets(self):
        for error in (urllib.error.URLError("offline"), ValueError("invalid JSON"), RuntimeError("invalid response")):
            with self.subTest(error=error), patch.object(profile, "WAKATIME_API_KEY", "test-key"), patch.object(
                profile, "fetch_wakatime", side_effect=error
            ):
                self.assertEqual(profile.main(), 0)
                self.assertEqual(self.readme.read_text(encoding="utf-8"), self.original_readme)
        self.assertIn("PUBLIC REPOS", self.stats.read_text(encoding="utf-8"))
        for project in profile.PROJECTS:
            ET.fromstring((self.projects / project["file"]).read_bytes())

    def test_missing_wakatime_markers_leave_readme_untouched(self):
        self.readme.write_text("# No markers\n", encoding="utf-8")
        with patch.object(profile, "WAKATIME_API_KEY", "test-key"), patch.object(profile, "fetch_wakatime", return_value={}):
            self.assertEqual(profile.main(), 0)
        self.assertEqual(self.readme.read_text(encoding="utf-8"), "# No markers\n")

    def test_offline_snapshot_refresh_is_idempotent_and_preserves_animation(self):
        snapshot_path = self.readme.parent / "snapshot.json"
        snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")
        self.args.return_value.snapshot = snapshot_path
        with patch.object(profile, "fetch_wakatime") as wakatime:
            self.assertEqual(profile.main(), 0)
        self.github.assert_not_called()
        wakatime.assert_not_called()
        self.assertEqual(self.activity.read_bytes(), b"previous animation")
        self.assertEqual(self.readme.read_text(encoding="utf-8"), self.original_readme)
        for path in (self.stats, *self.projects.iterdir()):
            ET.fromstring(path.read_bytes())
        before = self.asset_bytes()
        with patch.object(Path, "write_bytes", side_effect=AssertionError("Unchanged assets must not be rewritten")):
            self.assertEqual(profile.main(), 0)
        self.assertEqual(self.asset_bytes(), before)

    def test_missing_pillow_preserves_animation_with_available_calendar(self):
        self.snapshot["contributions"] = {"weeks": [{"contributionDays": [
            {"date": "2026-01-01", "weekday": 4, "contributionCount": 3},
        ]}]}
        with patch.object(profile, "Image", None):
            self.assertEqual(profile.main(), 0)
        self.assertEqual(self.activity.read_bytes(), b"previous animation")
        ET.fromstring(self.stats.read_bytes())


if __name__ == "__main__":
    unittest.main()
