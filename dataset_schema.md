# Dataset Schema

This document defines the schema for task seeds produced by the repository mining pipeline.

## Top Level Structure

The output JSON file contains three top level fields.

| Field | Type | Description |
|-------|------|-------------|
| metadata | object | Repository level information |
| task_seeds | array | List of extracted task seed objects |
| generated_at | string | ISO 8601 timestamp of generation |

## Metadata Object

| Field | Type | Description |
|-------|------|-------------|
| name | string | Repository full name in owner/repo format |
| url | string | Clone URL of the repository |
| primary_language | string | Most frequently occurring programming language |
| file_count | integer | Total number of source files indexed |
| languages_detected | object | Map of language name to file count |

## Task Seed Object

| Field | Type | Description |
|-------|------|-------------|
| repository | string | Repository full name |
| language | string | Primary language of the repository |
| task_id | string | Unique identifier (repo-shortsha format) |
| task_type | string | One of: bug_fix, feature, refactor, docs, test, config, other |
| description | string | Commit message describing the task |
| files_involved | array of strings | File paths modified in the commit |
| difficulty | string | One of: easy, medium, hard |
| commit_sha | string | Full SHA of the source commit |
| diff_stats | object | Diff statistics (see below) |
| evaluation | object | Evaluation specification (see below) |
| expected_outcome | string | Natural language description of correct result |

## Diff Stats Object

| Field | Type | Description |
|-------|------|-------------|
| additions | integer | Total lines added |
| deletions | integer | Total lines deleted |
| files_changed | integer | Number of files with changes |

## Evaluation Object

| Field | Type | Description |
|-------|------|-------------|
| type | string | Evaluation method (currently diff_match) |
| expected_files_modified | array of strings | Files that should be changed to complete the task |

## Task Type Definitions

**bug_fix**: A commit that corrects incorrect behavior in existing code.

**feature**: A commit that adds new functionality or capabilities.

**refactor**: A commit that restructures existing code without changing external behavior.

**docs**: A commit that modifies documentation, comments, or README files.

**test**: A commit that adds or modifies test cases.

**config**: A commit that changes build configuration, CI pipelines, or dependency specifications.

**other**: A commit that does not match any of the above categories.

## Difficulty Estimation

Difficulty is estimated using the following heuristics.

**easy**: Single file change with fewer than 20 total line modifications.

**medium**: Two to four files changed, or 20 to 200 total line modifications.

**hard**: Five or more files changed, or more than 200 total line modifications.
