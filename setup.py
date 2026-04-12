from setuptools import setup, find_packages

setup(
    name="long-context-eval-prototype",
    version="0.1.0",
    description="Benchmark dataset pipeline for evaluating LLM coding agents on long context tasks",
    author="Sanjit Chitturi",
    python_requires=">=3.9",
    py_modules=["repo_miner"],
    install_requires=[
        "gitpython>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "repo-miner=repo_miner:main",
        ],
    },
)
