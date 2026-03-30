# Long Context Eval Prototype

A small Python prototype for the GSoC idea **Long Context Complex Reasoning Coding Evaluation Dataset**.

This prototype focuses on the first practical step of the project: **repository mining**.
It can:

- clone a repository locally with Git
- collect lightweight repository metadata
- inspect recent commits
- identify candidate long-context task seeds from commit history
- export results as JSON

## Why this prototype exists

The full GSoC project aims to build a dataset of realistic long-context software engineering tasks from large open source repositories. This prototype shows an initial, working pipeline for:

1. collecting repository data
2. extracting signals from commit history
3. generating structured task candidates that can later be reviewed and refined

## Repository structure

```
long-context-eval-prototype/
├── README.md
├── .gitignore
├── requirements.txt
├── config/
│   └── example_repos.json
├── outputs/
│   └── sample_report.json
└── src/
    └── repo_miner.py
```

## Features

- shallow clone of remote Git repositories
- local repository analysis
- file extension and language estimation
- recent commit mining
- candidate task extraction using commit-message heuristics
- JSON export for later dataset curation

## Quick start

### 1. Clone or copy this repository

```bash
git clone <your-repo-url>
cd long-context-eval-prototype
```

### 2. Run against an existing local repository

```bash
python src/repo_miner.py --repo-path /path/to/local/repo --output outputs/report.json
```

### 3. Run against a remote Git repository

```bash
python src/repo_miner.py --repo-url https://github.com/pallets/flask.git --clone-dir .cache/repos --output outputs/report.json
```

### 4. Print results to stdout as well

```bash
python src/repo_miner.py --repo-url https://github.com/pallets/flask.git --print-json
```

## Output schema

The output JSON includes:

- repository path
- current branch
- commit count estimate
- top file extensions
- estimated languages
- recent commits
- candidate task seeds

Example task seed fields:

- `task_id`
- `task_type`
- `title`
- `summary`
- `commit_hash`
- `files_changed`
- `reasoning_scope`

## Limitations

This is intentionally a small prototype. It does not yet:

- use the GitHub API
- inspect issues or pull requests
- parse ASTs with Tree-sitter
- build full evaluation tasks automatically
- run Dockerized task environments

Those would be natural next steps for the full GSoC project.

## Suggested next steps

- integrate GitHub API issue and PR mining
- add Tree-sitter based cross-file dependency analysis
- score task difficulty using repository graph statistics
- store metadata in SQLite
- generate dataset entries in the final benchmark schema

## License

MIT
