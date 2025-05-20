# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Run all tests: `python -m unittest discover tests --buffer --verbose`
- Run a single test: `python -m unittest tests.test_main.CypherTestCase.test_nodes`
- Run tests with coverage: `coverage run -m unittest discover tests --buffer --verbose`
- Format code: `ruff format`
- Lint code: `ruff check --fix`
- Type check: `mypy pgraf_cypher`

## Code Style Guidelines
- Follow PEP 8 style with 79-char line length
- Use single quotes for strings (except docstrings which use triple double-quotes)
- Import modules instead of names (e.g., `from urllib import parse` and use `parse.urlsplit()`)
- Use Python 3.12+ style type hints with explicit `| None` for optional types
- Always call superclass method when extending
- Use Pydantic models for data structures
- Include detailed docstrings for public methods
- Use underscores for internal/private attributes (_foo)
- Use ruff for formatting and linting (automatically applied by pre-commit)
- Implement adequate test coverage (>90% target)