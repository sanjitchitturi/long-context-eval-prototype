# Long Context Coding Evaluation Dataset Prototype

## Overview
This repository contains an early prototype for a long context and complex reasoning coding evaluation dataset. The goal of this project is to create a benchmark that evaluates coding agents on realistic software engineering tasks that require understanding large codebases, multiple files, and architectural dependencies.

Current coding benchmarks often focus on small and isolated problems. Real world software engineering requires working with large repositories, understanding dependencies, and making changes across multiple modules. This project aims to build a dataset that reflects those real development conditions.

This repository contains a prototype that focuses on repository mining, metadata extraction, and task seed generation from large repositories.

## Project Goals
The main goals of this project are:

- Collect large open source repositories
- Analyze repository structure and commit history
- Identify candidate areas for long context engineering tasks
- Generate structured dataset entries
- Build a reproducible dataset generation pipeline
- Support evaluation of coding agents on multi file and architectural tasks

## Current Prototype Features
The current prototype includes the following features:

- Clone repositories using Git
- Extract repository metadata
- Analyze commit history
- Identify frequently modified files
- Generate structured JSON reports
- Prepare data for future task generation

This prototype is an initial step toward building a full dataset generation and evaluation pipeline.

## Repository Structure
long-context-eval-prototype/

README.md  
requirements.txt  
.gitignore  

src/  
repo_miner.py  

config/  
example_repos.json  

outputs/  
sample_report.json  

docs/  
dataset_schema.md  

## How It Works
The prototype works in the following steps:

1. Clone a repository or use an existing local repository.
2. Extract repository metadata such as number of files, commits, and contributors.
3. Analyze commit history to identify frequently modified files.
4. Generate a structured JSON report containing repository information and candidate files for task creation.
5. Store the report for future dataset generation and evaluation.

This information will later be used to generate long context engineering tasks that involve multiple files and modules.

## Dataset Schema
The planned dataset will store tasks in a structured JSON format. Each dataset entry will include:

- Repository name
- Programming language
- Task ID
- Task type
- Task description
- Files involved
- Difficulty level
- Evaluation method
- Expected outcome

More details are described in the documentation inside the docs folder.

## Future Work
The next steps for this project include:

- Automatic task generation from issues and commits
- Dependency analysis using code parsing tools
- Task difficulty classification
- Evaluation pipeline for running tasks
- Integration with coding agent evaluation systems
- Benchmark reporting and failure analysis

## Running the Prototype
Install dependencies:

pip install -r requirements.txt

Run the repository miner on a local repository:

python src/repo_miner.py --repo-path /path/to/local/repo --output outputs/report.json

Run using a remote repository:

python src/repo_miner.py --repo-url https://github.com/example/repo.git --clone-dir .cache/repos --output outputs/report.json

## Purpose of This Repository
This repository is part of a larger project to build a long context coding evaluation dataset for realistic software engineering tasks. The prototype demonstrates the initial pipeline for repository analysis and dataset preparation.

## License
This project is for research and evaluation purposes and will be released under an open source license.
