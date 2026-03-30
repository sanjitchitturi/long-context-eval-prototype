# Dataset Schema (Draft)

Each dataset entry will contain the following fields:

- repository: Name of repository
- language: Primary programming language
- task_id: Unique task identifier
- task_type: bug_fix | feature | refactor | test_fix
- description: Description of the task
- files_involved: List of files required for the task
- difficulty: easy | medium | hard
- evaluation: How the task will be evaluated (tests, build, etc.)
- expected_outcome: Expected result after task completion

This schema will be used to store tasks in JSON format for automated evaluation.
