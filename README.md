# Long Context Coding Evaluation Dataset

A benchmark dataset pipeline for evaluating LLM coding agents on real world, multi file, long context software engineering tasks.

## Motivation

Large language models are increasingly used as coding agents that read, modify, and generate code across entire repositories. However, most evaluation benchmarks test LLMs on isolated, self contained problems: a single function, a short algorithm, or a standalone script. These benchmarks do not reflect the complexity of real software engineering, where a single task may require reading dozens of files, understanding module boundaries, and reasoning about how a change in one file propagates to others.

Long context windows (100K+ tokens) have made it technically possible for LLMs to ingest entire codebases. But having a large context window does not mean the model can effectively use it. There is a critical gap between context capacity and context reasoning, and very few benchmarks target this gap in the coding domain.

## The Problem with Current Benchmarks

Existing coding benchmarks share several limitations that make them poor measures of real world coding ability.

**Isolated scope.** Benchmarks like HumanEval and MBPP present single function problems with clear input/output specifications. Real software tasks rarely look like this.

**Synthetic construction.** Many benchmarks are hand authored or generated, which introduces distributional bias. The problems are cleaner, simpler, and more self contained than what developers actually encounter.

**No cross file reasoning.** A bug fix that requires understanding an interface defined in one file, implemented in another, and tested in a third is a common engineering task. No major benchmark systematically tests this.

**No grounding in real commit history.** Software engineering tasks emerge from real development activity: bug reports, feature requests, refactoring decisions. Commit history is a rich, underutilized source of ground truth for what constitutes a meaningful coding task.

## What This Project Does

This project builds an automated pipeline that mines real GitHub repositories and extracts structured evaluation tasks grounded in actual development history. Each task seed captures a multi file coding challenge derived from a real commit, complete with the files involved, the type of change, and the reasoning required.

The output is a structured dataset of task seeds that can be used to evaluate coding agents on long context, multi file software engineering problems.

## Key Features

**Real repository mining.** The pipeline clones and analyzes actual open source repositories rather than relying on synthetic problem generation.

**Commit history analysis.** Each candidate task is derived from a real git commit, preserving the intent and scope of actual development work.

**Automatic task classification.** Commits are classified into task types (bug fix, feature addition, refactoring, documentation, testing) using commit message analysis and diff heuristics.

**Multi file extraction.** The pipeline identifies which files were involved in each change and captures cross file relationships.

**Structured output.** Results are emitted as JSON conforming to a well defined schema, ready for downstream consumption by evaluation harnesses.

**Configurable difficulty estimation.** Tasks are scored for difficulty based on the number of files changed, the size of the diff, and the complexity of cross file dependencies.

## System Overview

The pipeline operates in four stages.

```
[GitHub Repository]
        |
        v
  Clone and Index
  (clone repo, enumerate files, detect languages)
        |
        v
  Commit Analysis
  (parse git log, extract diffs, classify task types)
        |
        v
  Task Seed Extraction
  (identify multi file changes, estimate difficulty,
   build structured task descriptions)
        |
        v
  Structured Output
  (JSON dataset conforming to schema)
```

## How It Works

**Step 1: Repository ingestion.** The pipeline clones a target repository and indexes its file tree. It detects the primary languages used and builds a file manifest with path, size, and language metadata.

**Step 2: Commit parsing.** The full git history is parsed. For each commit, the pipeline extracts the commit message, author, timestamp, and the list of files modified. Diffs are analyzed to determine the nature and extent of each change.

**Step 3: Task classification.** Each commit is classified into one or more task types using a rule based classifier that examines commit message patterns and diff characteristics. Categories include bug fix, feature addition, refactoring, documentation update, test addition, and configuration change.

**Step 4: Task seed generation.** Commits that meet minimum complexity thresholds (multi file changes, non trivial diff size) are promoted to task seeds. Each seed includes the repository context, the files involved, the task type, a natural language description derived from the commit message, and a difficulty estimate.

**Step 5: Output.** The final dataset is written as a JSON file conforming to the schema defined in `dataset_schema.md`.

## Example Output

```json
{
  "repository": "expressjs/express",
  "language": "JavaScript",
  "task_id": "express-a1b2c3d",
  "task_type": "bug_fix",
  "description": "Fix middleware ordering bug causing route handler to execute before authentication check",
  "files_involved": [
    "lib/router/index.js",
    "lib/router/layer.js",
    "test/router.test.js"
  ],
  "difficulty": "medium",
  "commit_sha": "a1b2c3d4e5f6",
  "diff_stats": {
    "additions": 23,
    "deletions": 8,
    "files_changed": 3
  },
  "evaluation": {
    "type": "diff_match",
    "expected_files_modified": [
      "lib/router/index.js",
      "lib/router/layer.js"
    ]
  },
  "expected_outcome": "Middleware executes in registration order regardless of async resolution timing"
}
```

## Dataset Schema

Each task seed in the dataset contains the following fields.

| Field | Type | Description |
|-------|------|-------------|
| repository | string | Full name of the source repository (owner/repo) |
| language | string | Primary programming language of the repository |
| task_id | string | Unique identifier for the task seed |
| task_type | string | Classification of the task (bug_fix, feature, refactor, docs, test, config) |
| description | string | Natural language description of the task derived from the commit |
| files_involved | list of strings | Paths of all files modified in the source commit |
| difficulty | string | Estimated difficulty (easy, medium, hard) based on scope and complexity |
| commit_sha | string | SHA of the source commit |
| diff_stats | object | Summary statistics of the diff (additions, deletions, files changed) |
| evaluation | object | Evaluation criteria including type and expected files modified |
| expected_outcome | string | Description of the correct behavior after the task is completed |

The full schema specification is in `dataset_schema.md`.

## Installation

Requires Python 3.9 or later and git installed on the system.

```bash
git clone https://github.com/sanjitchitturi/long-context-eval-prototype.git
cd long-context-eval-prototype
pip install -e .
```

## Usage

**Mine a single repository:**

```bash
python repo_miner.py --repo https://github.com/expressjs/express --output results/express.json
```

**Mine multiple repositories from a list:**

```bash
python repo_miner.py --repo-list example_repos.json --output results/
```

**Filter by task type:**

```bash
python repo_miner.py --repo https://github.com/pallets/flask --task-type bug_fix --output results/flask_bugs.json
```

**Validate output against schema:**

```bash
python scripts/validate_output.py results/express.json
```

## Design Decisions

**Why mine real repositories instead of generating synthetic tasks?**
Synthetic benchmarks suffer from distributional bias. The problems are too clean. Real repositories contain the messy, interconnected code that LLMs struggle with in practice. Mining real commits ensures that every task in the dataset corresponds to a problem that a human developer actually needed to solve.

**Why use commit history as the source of ground truth?**
A commit represents a discrete, completed unit of work with a known before state and after state. This gives us a natural ground truth for evaluation: the task is to produce a change equivalent to what the original developer committed. Commit messages provide intent, diffs provide scope, and the surrounding code provides context.

**Why classify commits into task types?**
Different task types stress different capabilities. A bug fix requires reading code carefully and finding a logical error. A refactoring task requires understanding code structure well enough to reorganize it without changing behavior. A feature addition requires synthesizing new code that integrates with existing abstractions. Classification enables targeted evaluation of specific capabilities.

**Why estimate difficulty?**
Not all multi file changes are equally hard. A two file rename is simpler than a three file architectural refactor. Difficulty estimation based on diff size, file count, and cross file dependency complexity allows researchers to stratify their evaluations and identify capability thresholds.

**Why JSON output?**
JSON is the most portable structured format for dataset interchange. It is natively supported by every major programming language and evaluation framework, and it is human readable for inspection and debugging.