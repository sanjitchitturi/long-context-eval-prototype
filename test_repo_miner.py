"""Tests for the repository mining pipeline."""

import unittest

from repo_miner import (
    DiffStats,
    classify_task_type,
    compute_diff_stats,
    estimate_difficulty,
    get_primary_language,
    is_candidate_task,
    build_task_seed,
)


class TestClassifyTaskType(unittest.TestCase):

    def test_bug_fix_detection(self):
        self.assertEqual(classify_task_type("Fix null pointer in parser"), "bug_fix")
        self.assertEqual(classify_task_type("Resolve race condition"), "bug_fix")
        self.assertEqual(classify_task_type("Patch memory leak"), "bug_fix")

    def test_feature_detection(self):
        self.assertEqual(classify_task_type("Add support for WebSocket"), "feature")
        self.assertEqual(classify_task_type("Implement rate limiting"), "feature")

    def test_refactor_detection(self):
        self.assertEqual(classify_task_type("Refactor auth module"), "refactor")
        self.assertEqual(classify_task_type("Rename internal methods"), "refactor")

    def test_docs_detection(self):
        self.assertEqual(classify_task_type("Update README"), "docs")
        self.assertEqual(classify_task_type("Update documentation for API"), "docs")

    def test_test_detection(self):
        self.assertEqual(classify_task_type("Improve unit test coverage for parser"), "test")
        self.assertEqual(classify_task_type("Improve test coverage"), "test")

    def test_config_detection(self):
        self.assertEqual(classify_task_type("Update CI configuration"), "config")
        self.assertEqual(classify_task_type("Bump dependency versions"), "config")

    def test_unknown_returns_other(self):
        self.assertEqual(classify_task_type("Initial commit"), "other")
        self.assertEqual(classify_task_type("WIP"), "other")


class TestComputeDiffStats(unittest.TestCase):

    def test_basic_computation(self):
        file_stats = [
            {"additions": 10, "deletions": 5, "path": "a.py"},
            {"additions": 20, "deletions": 3, "path": "b.py"},
        ]
        stats = compute_diff_stats(file_stats)
        self.assertEqual(stats.additions, 30)
        self.assertEqual(stats.deletions, 8)
        self.assertEqual(stats.files_changed, 2)

    def test_empty_input(self):
        stats = compute_diff_stats([])
        self.assertEqual(stats.additions, 0)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.files_changed, 0)


class TestEstimateDifficulty(unittest.TestCase):

    def test_easy(self):
        stats = DiffStats(additions=5, deletions=3, files_changed=1)
        self.assertEqual(estimate_difficulty(stats, 1), "easy")

    def test_medium(self):
        stats = DiffStats(additions=50, deletions=30, files_changed=3)
        self.assertEqual(estimate_difficulty(stats, 3), "medium")

    def test_hard_by_files(self):
        stats = DiffStats(additions=10, deletions=10, files_changed=6)
        self.assertEqual(estimate_difficulty(stats, 6), "hard")

    def test_hard_by_changes(self):
        stats = DiffStats(additions=150, deletions=100, files_changed=2)
        self.assertEqual(estimate_difficulty(stats, 2), "hard")


class TestGetPrimaryLanguage(unittest.TestCase):

    def test_returns_most_frequent(self):
        counts = {"Python": 50, "JavaScript": 30, "Go": 10}
        self.assertEqual(get_primary_language(counts), "Python")

    def test_empty_returns_unknown(self):
        self.assertEqual(get_primary_language({}), "Unknown")


class TestIsCandidateTask(unittest.TestCase):

    def test_qualifies(self):
        commit = {
            "files": [
                {"additions": 10, "deletions": 5, "path": "src/a.py"},
                {"additions": 20, "deletions": 3, "path": "src/b.py"},
            ]
        }
        self.assertTrue(is_candidate_task(commit))

    def test_too_few_files(self):
        commit = {
            "files": [
                {"additions": 10, "deletions": 5, "path": "src/a.py"},
            ]
        }
        self.assertFalse(is_candidate_task(commit))

    def test_ignores_vendor_files(self):
        commit = {
            "files": [
                {"additions": 10, "deletions": 5, "path": "src/a.py"},
                {"additions": 20, "deletions": 3, "path": "vendor/lib.py"},
            ]
        }
        self.assertFalse(is_candidate_task(commit))


class TestBuildTaskSeed(unittest.TestCase):

    def test_produces_valid_seed(self):
        commit = {
            "sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            "message": "Fix timeout bug in request handler",
            "author": "dev",
            "date": "2024-01-15T10:00:00Z",
            "files": [
                {"additions": 10, "deletions": 5, "path": "src/handler.py"},
                {"additions": 3, "deletions": 1, "path": "tests/test_handler.py"},
            ],
        }
        seed = build_task_seed(commit, "owner/repo", "Python")
        self.assertEqual(seed.repository, "owner/repo")
        self.assertEqual(seed.language, "Python")
        self.assertEqual(seed.task_id, "repo-a1b2c3d")
        self.assertEqual(seed.task_type, "bug_fix")
        self.assertEqual(len(seed.files_involved), 2)
        self.assertEqual(seed.diff_stats.additions, 13)


if __name__ == "__main__":
    unittest.main()
