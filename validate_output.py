"""Validate pipeline output against the dataset schema."""

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = ["metadata", "task_seeds", "generated_at"]

REQUIRED_METADATA = ["name", "url", "primary_language", "file_count", "languages_detected"]

REQUIRED_TASK_SEED = [
    "repository",
    "language",
    "task_id",
    "task_type",
    "description",
    "files_involved",
    "difficulty",
    "commit_sha",
    "diff_stats",
    "evaluation",
    "expected_outcome",
]

VALID_TASK_TYPES = ["bug_fix", "feature", "refactor", "docs", "test", "config", "other"]

VALID_DIFFICULTIES = ["easy", "medium", "hard"]


def validate(data: dict) -> list[str]:
    errors = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"Missing top level field: {key}")

    if "metadata" in data:
        meta = data["metadata"]
        for key in REQUIRED_METADATA:
            if key not in meta:
                errors.append(f"Missing metadata field: {key}")

    if "task_seeds" in data:
        seeds = data["task_seeds"]
        if not isinstance(seeds, list):
            errors.append("task_seeds must be a list")
        else:
            for i, seed in enumerate(seeds):
                for key in REQUIRED_TASK_SEED:
                    if key not in seed:
                        errors.append(f"Task seed {i}: missing field {key}")
                if seed.get("task_type") not in VALID_TASK_TYPES:
                    errors.append(
                        f"Task seed {i}: invalid task_type '{seed.get('task_type')}'"
                    )
                if seed.get("difficulty") not in VALID_DIFFICULTIES:
                    errors.append(
                        f"Task seed {i}: invalid difficulty '{seed.get('difficulty')}'"
                    )
                if not isinstance(seed.get("files_involved"), list):
                    errors.append(f"Task seed {i}: files_involved must be a list")

    return errors


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    errors = validate(data)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)

    seed_count = len(data.get("task_seeds", []))
    print(f"Validation passed. {seed_count} task seeds found.")


if __name__ == "__main__":
    main()
