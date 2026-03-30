from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
    ".toml": "TOML",
    ".xml": "XML",
}

TASK_PATTERNS = {
    "bug_fix": re.compile(r"\b(fix|bug|error|crash|broken|regression)\b", re.IGNORECASE),
    "feature": re.compile(r"\b(add|support|implement|feature|enable)\b", re.IGNORECASE),
    "refactor": re.compile(r"\b(refactor|cleanup|simplify|rework)\b", re.IGNORECASE),
    "dependency_update": re.compile(r"\b(update|upgrade|bump|dependency|deps)\b", re.IGNORECASE),
    "test_related": re.compile(r"\b(test|tests|coverage|assert)\b", re.IGNORECASE),
    "performance": re.compile(r"\b(perf|performance|optimi[sz]e|faster|speed)\b", re.IGNORECASE),
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "target",
    ".mypy_cache",
    ".pytest_cache",
}


@dataclass
class CommitInfo:
    commit_hash: str
    author: str
    date: str
    subject: str
    files_changed: list[str]


@dataclass
class TaskSeed:
    task_id: str
    task_type: str
    title: str
    summary: str
    commit_hash: str
    files_changed: list[str]
    reasoning_scope: str


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def ensure_repo(repo_url: str | None, repo_path: Path | None, clone_dir: Path) -> Path:
    if repo_path:
        if not (repo_path / ".git").exists():
            raise ValueError(f"{repo_path} does not look like a git repository")
        return repo_path.resolve()

    if not repo_url:
        raise ValueError("Provide either --repo-path or --repo-url")

    clone_dir.mkdir(parents=True, exist_ok=True)
    repo_name = Path(repo_url.rstrip("/")).stem
    destination = (clone_dir / repo_name).resolve()

    if destination.exists() and (destination / ".git").exists():
        return destination

    run_git(["clone", "--depth", "200", repo_url, str(destination)])
    return destination


def iter_repo_files(repo_path: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file_name in files:
            yield Path(root) / file_name


def analyze_files(repo_path: Path) -> dict:
    ext_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    total_files = 0

    for path in iter_repo_files(repo_path):
        total_files += 1
        ext = path.suffix.lower() or "[no_extension]"
        ext_counts[ext] += 1
        if ext in LANGUAGE_BY_EXTENSION:
            language_counts[LANGUAGE_BY_EXTENSION[ext]] += 1

    return {
        "total_files": total_files,
        "top_extensions": ext_counts.most_common(15),
        "estimated_languages": language_counts.most_common(10),
    }


def get_recent_commits(repo_path: Path, limit: int) -> list[CommitInfo]:
    log_output = run_git(
        [
            "log",
            f"--max-count={limit}",
            "--date=short",
            "--pretty=format:%H%x1f%an%x1f%ad%x1f%s",
            "--name-only",
        ],
        cwd=repo_path,
    )

    commits: list[CommitInfo] = []
    current_meta: tuple[str, str, str, str] | None = None
    current_files: list[str] = []

    for line in log_output.splitlines() + [""]:
        if "\x1f" in line:
            if current_meta is not None:
                commit_hash, author, date, subject = current_meta
                commits.append(CommitInfo(commit_hash, author, date, subject, current_files))
            current_meta = tuple(line.split("\x1f", 3))  # type: ignore[assignment]
            current_files = []
        elif line.strip():
            current_files.append(line.strip())
        else:
            if current_meta is not None:
                commit_hash, author, date, subject = current_meta
                commits.append(CommitInfo(commit_hash, author, date, subject, current_files))
                current_meta = None
                current_files = []

    # remove accidental duplicates caused by sentinel flush
    unique: list[CommitInfo] = []
    seen: set[str] = set()
    for commit in commits:
        if commit.commit_hash not in seen:
            seen.add(commit.commit_hash)
            unique.append(commit)
    return unique


def classify_task(subject: str) -> str | None:
    for task_type, pattern in TASK_PATTERNS.items():
        if pattern.search(subject):
            return task_type
    return None


def reasoning_scope(files_changed: list[str]) -> str:
    unique_dirs = {str(Path(p).parent) for p in files_changed if p}
    if len(files_changed) >= 8 or len(unique_dirs) >= 4:
        return "high"
    if len(files_changed) >= 4 or len(unique_dirs) >= 2:
        return "medium"
    return "low"


def build_task_seeds(commits: list[CommitInfo]) -> list[TaskSeed]:
    seeds: list[TaskSeed] = []
    counter = 1
    for commit in commits:
        task_type = classify_task(commit.subject)
        if not task_type:
            continue
        seeds.append(
            TaskSeed(
                task_id=f"task_{counter:03d}",
                task_type=task_type,
                title=commit.subject,
                summary=(
                    "Candidate task inferred from commit history. Review the files changed and "
                    "reconstruct the engineering problem as a benchmark task."
                ),
                commit_hash=commit.commit_hash,
                files_changed=commit.files_changed[:20],
                reasoning_scope=reasoning_scope(commit.files_changed),
            )
        )
        counter += 1
    return seeds


def get_repo_summary(repo_path: Path, commit_limit: int) -> dict:
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    commit_count = run_git(["rev-list", "--count", "HEAD"], cwd=repo_path)
    file_analysis = analyze_files(repo_path)
    recent_commits = get_recent_commits(repo_path, limit=commit_limit)
    task_seeds = build_task_seeds(recent_commits)

    return {
        "repository_path": str(repo_path),
        "repository_name": repo_path.name,
        "current_branch": branch,
        "commit_count_estimate": int(commit_count),
        "file_analysis": file_analysis,
        "recent_commits": [asdict(c) for c in recent_commits],
        "candidate_task_seeds": [asdict(t) for t in task_seeds],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine a git repository for long-context evaluation task seeds.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo-url", help="Remote git repository URL")
    source.add_argument("--repo-path", type=Path, help="Path to a local git repository")
    parser.add_argument("--clone-dir", type=Path, default=Path(".cache/repos"), help="Directory for shallow clones")
    parser.add_argument("--output", type=Path, help="Path to write JSON output")
    parser.add_argument("--commit-limit", type=int, default=50, help="Number of recent commits to inspect")
    parser.add_argument("--print-json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--clean-clone", action="store_true", help="Delete existing cloned repo before cloning again")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    clone_dir = args.clone_dir.resolve()
    if args.clean_clone and args.repo_url:
        repo_name = Path(args.repo_url.rstrip("/")).stem
        destination = clone_dir / repo_name
        if destination.exists():
            shutil.rmtree(destination)

    repo_path = ensure_repo(args.repo_url, args.repo_path, clone_dir)
    summary = get_repo_summary(repo_path, commit_limit=args.commit_limit)

    output_text = json.dumps(summary, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text + "\n", encoding="utf-8")

    if args.print_json or not args.output:
        print(output_text)


if __name__ == "__main__":
    main()
