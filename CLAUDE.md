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

## Project Architecture

This project converts Neo4j's Cypher query language to PostgreSQL SQL. It uses ANTLR4 for parsing Cypher syntax and transforms it to SQL that works with a PostgreSQL schema (specifically designed for graph data).

### Core Components
- **ANTLR Parser**: Files in `pgraf_cypher/antlr/` define the grammar and generate lexer/parser for Cypher 2.5
- **Model Layer**: `pgraf_cypher/models.py` contains Pydantic models representing different parts of a Cypher query
- **Parser Layer**: `pgraf_cypher/parsers.py` converts ANTLR parse trees to model objects
- **SQL Translation**: `pgraf_cypher/to_sql.py` converts models to PostgreSQL SQL statements
- **Main Interface**: `pgraf_cypher/main.py` provides the public API through the `PGrafCypher` class

### Data Flow
1. Cypher query string is parsed using ANTLR4 to generate a parse tree
2. The parse tree is walked and converted to model objects
3. The model objects are then translated to SQL and parameters
4. The resulting SQL can be executed against a PostgreSQL database with the graph schema

### Database Schema Assumptions
The SQL translation assumes a PostgreSQL schema with at least:
- `nodes` table for graph vertices
- `edges` table for relationships between nodes
- A specific schema format with properties stored as JSON
