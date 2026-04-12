"""Repository mining pipeline for long context coding evaluation dataset generation.

Clones GitHub repositories, analyzes commit history, classifies tasks,
and outputs structured evaluation seeds as JSON.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TASK_TYPE_PATTERNS = {
    "bug_fix": [
        r"\bfix(?:es|ed)?\b",
        r"\bbug\b",
        r"\bpatch\b",
        r"\bresolve[sd]?\b",
        r"\bcorrect(?:s|ed)?\b",
        r"\brepair\b",
    ],
    "feature": [
        r"\badd(?:s|ed)?\b",
        r"\bimplement(?:s|ed)?\b",
        r"\bintroduce[sd]?\b",
        r"\bnew\b",
        r"\bsupport\b",
    ],
    "refactor": [
        r"\brefactor(?:s|ed|ing)?\b",
        r"\brestructure[sd]?\b",
        r"\brename[sd]?\b",
        r"\bmove[sd]?\b",
        r"\bclean\s?up\b",
        r"\bsimplif(?:y|ied|ies)\b",
    ],
    "docs": [
        r"\bdoc(?:s|umentation)?\b",
        r"\breadme\b",
        r"\bcomment(?:s|ed)?\b",
        r"\btypedoc\b",
        r"\bchangelog\b",
    ],
    "test": [
        r"\btest(?:s|ing|ed)?\b",
        r"\bspec(?:s)?\b",
        r"\bcoverage\b",
        r"\bassert(?:s|ion)?\b",
    ],
    "config": [
        r"\bconfig(?:ure|uration)?\b",
        r"\bci\b",
        r"\byaml\b",
        r"\btoml\b",
        r"\bdependenc(?:y|ies)\b",
        r"\bbump\b",
        r"\bupgrade[sd]?\b",
    ],
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
}

IGNORE_PATTERNS = [
    r"\.git/",
    r"node_modules/",
    r"__pycache__/",
    r"\.egg-info/",
    r"vendor/",
    r"dist/",
    r"build/",
    r"\.min\.",
    r"package-lock\.json",
    r"yarn\.lock",
    r"go\.sum",
]


@dataclass
class DiffStats:
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0


@dataclass
class TaskSeed:
    repository: str = ""
    language: str = ""
    task_id: str = ""
    task_type: str = ""
    description: str = ""
    files_involved: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    commit_sha: str = ""
    diff_stats: DiffStats = field(default_factory=DiffStats)
    evaluation: dict = field(default_factory=dict)
    expected_outcome: str = ""


@dataclass
class RepoMetadata:
    name: str = ""
    url: str = ""
    primary_language: str = ""
    file_count: int = 0
    languages_detected: dict[str, int] = field(default_factory=dict)


def clone_repository(repo_url: str, target_dir: str) -> Path:
    repo_path = Path(target_dir) / repo_url.rstrip("/").split("/")[-1]
    if repo_path.exists():
        logger.info("Repository already cloned at %s", repo_path)
        return repo_path
    logger.info("Cloning %s", repo_url)
    subprocess.run(
        ["git", "clone", "--depth", "500", repo_url, str(repo_path)],
        check=True,
        capture_output=True,
    )
    return repo_path


def detect_languages(repo_path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(repo_path))
        if any(re.search(p, rel) for p in IGNORE_PATTERNS):
            continue
        ext = file_path.suffix.lower()
        if ext in LANGUAGE_EXTENSIONS:
            lang = LANGUAGE_EXTENSIONS[ext]
            counts[lang] = counts.get(lang, 0) + 1
    return counts


def get_primary_language(lang_counts: dict[str, int]) -> str:
    if not lang_counts:
        return "Unknown"
    return max(lang_counts, key=lang_counts.get)


def parse_git_log(repo_path: Path, max_commits: int = 500) -> list[dict]:
    separator = "---COMMIT_SEP---"
    field_sep = "---FIELD_SEP---"
    fmt = field_sep.join(["%H", "%s", "%an", "%aI"])
    result = subprocess.run(
        [
            "git", "log",
            f"--max-count={max_commits}",
            f"--format={separator}{fmt}",
            "--numstat",
        ],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    raw_commits = result.stdout.split(separator)
    for raw in raw_commits:
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.split("\n")
        header = lines[0]
        parts = header.split(field_sep)
        if len(parts) < 4:
            continue
        sha, message, author, date = parts[0], parts[1], parts[2], parts[3]
        file_stats = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            stat_parts = line.split("\t")
            if len(stat_parts) == 3:
                adds, dels, filepath = stat_parts
                file_stats.append({
                    "additions": int(adds) if adds != "-" else 0,
                    "deletions": int(dels) if dels != "-" else 0,
                    "path": filepath,
                })
        commits.append({
            "sha": sha,
            "message": message,
            "author": author,
            "date": date,
            "files": file_stats,
        })
    return commits


def classify_task_type(commit_message: str) -> str:
    message_lower = commit_message.lower()
    scores: dict[str, int] = {}
    for task_type, patterns in TASK_TYPE_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, message_lower))
        if score > 0:
            scores[task_type] = score
    if not scores:
        return "other"
    return max(scores, key=scores.get)


def compute_diff_stats(file_stats: list[dict]) -> DiffStats:
    total_adds = sum(f["additions"] for f in file_stats)
    total_dels = sum(f["deletions"] for f in file_stats)
    return DiffStats(
        additions=total_adds,
        deletions=total_dels,
        files_changed=len(file_stats),
    )


def estimate_difficulty(diff_stats: DiffStats, file_count: int) -> str:
    total_changes = diff_stats.additions + diff_stats.deletions
    if file_count <= 1 and total_changes < 20:
        return "easy"
    if file_count >= 5 or total_changes > 200:
        return "hard"
    return "medium"


def is_candidate_task(
    commit: dict,
    min_files: int = 2,
    min_changes: int = 5,
) -> bool:
    file_stats = commit["files"]
    if len(file_stats) < min_files:
        return False
    relevant_files = [
        f for f in file_stats
        if not any(re.search(p, f["path"]) for p in IGNORE_PATTERNS)
    ]
    if len(relevant_files) < min_files:
        return False
    total = sum(f["additions"] + f["deletions"] for f in relevant_files)
    return total >= min_changes


def build_task_seed(
    commit: dict,
    repo_name: str,
    primary_language: str,
) -> TaskSeed:
    file_stats = [
        f for f in commit["files"]
        if not any(re.search(p, f["path"]) for p in IGNORE_PATTERNS)
    ]
    file_paths = [f["path"] for f in file_stats]
    diff_stats = compute_diff_stats(file_stats)
    task_type = classify_task_type(commit["message"])
    difficulty = estimate_difficulty(diff_stats, len(file_paths))
    short_sha = commit["sha"][:7]
    task_id = f"{repo_name.split('/')[-1]}-{short_sha}"
    return TaskSeed(
        repository=repo_name,
        language=primary_language,
        task_id=task_id,
        task_type=task_type,
        description=commit["message"],
        files_involved=file_paths,
        difficulty=difficulty,
        commit_sha=commit["sha"],
        diff_stats=diff_stats,
        evaluation={
            "type": "diff_match",
            "expected_files_modified": file_paths,
        },
        expected_outcome=f"Apply changes consistent with: {commit['message']}",
    )


def mine_repository(
    repo_url: str,
    work_dir: str,
    max_commits: int = 500,
    min_files: int = 2,
    min_changes: int = 5,
    task_type_filter: Optional[str] = None,
) -> dict:
    repo_path = clone_repository(repo_url, work_dir)
    repo_name = "/".join(repo_url.rstrip("/").split("/")[-2:])
    lang_counts = detect_languages(repo_path)
    primary_language = get_primary_language(lang_counts)
    metadata = RepoMetadata(
        name=repo_name,
        url=repo_url,
        primary_language=primary_language,
        file_count=sum(lang_counts.values()),
        languages_detected=lang_counts,
    )
    logger.info(
        "Indexed %s: %d files, primary language %s",
        repo_name, metadata.file_count, primary_language,
    )
    commits = parse_git_log(repo_path, max_commits)
    logger.info("Parsed %d commits", len(commits))
    task_seeds = []
    for commit in commits:
        if not is_candidate_task(commit, min_files, min_changes):
            continue
        seed = build_task_seed(commit, repo_name, primary_language)
        if task_type_filter and seed.task_type != task_type_filter:
            continue
        task_seeds.append(seed)
    logger.info("Extracted %d task seeds", len(task_seeds))
    return {
        "metadata": asdict(metadata),
        "task_seeds": [asdict(s) for s in task_seeds],
        "generated_at": datetime.utcnow().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Mine GitHub repositories for long context evaluation tasks",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="URL of a single repository to mine",
    )
    parser.add_argument(
        "--repo-list",
        type=str,
        help="Path to a JSON file containing a list of repository URLs",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for the generated dataset (file or directory)",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=500,
        help="Maximum number of commits to analyze per repository",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=2,
        help="Minimum number of files changed to qualify as a candidate task",
    )
    parser.add_argument(
        "--min-changes",
        type=int,
        default=5,
        help="Minimum total line changes to qualify as a candidate task",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        choices=list(TASK_TYPE_PATTERNS.keys()) + ["other"],
        help="Filter results to a specific task type",
    )
    args = parser.parse_args()

    if not args.repo and not args.repo_list:
        parser.error("Provide either --repo or --repo-list")

    repos = []
    if args.repo:
        repos.append(args.repo)
    if args.repo_list:
        with open(args.repo_list) as f:
            data = json.load(f)
            if isinstance(data, list):
                repos.extend(data)
            elif "repositories" in data:
                repos.extend(data["repositories"])

    with tempfile.TemporaryDirectory() as work_dir:
        for repo_url in repos:
            logger.info("Processing %s", repo_url)
            result = mine_repository(
                repo_url=repo_url,
                work_dir=work_dir,
                max_commits=args.max_commits,
                min_files=args.min_files,
                min_changes=args.min_changes,
                task_type_filter=args.task_type,
            )
            output_path = Path(args.output)
            if output_path.suffix == ".json":
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path.mkdir(parents=True, exist_ok=True)
                repo_slug = repo_url.rstrip("/").split("/")[-1]
                output_path = output_path / f"{repo_slug}.json"
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(
                "Wrote %d task seeds to %s",
                len(result["task_seeds"]),
                output_path,
            )


if __name__ == "__main__":
    main()
