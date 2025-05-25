# Installation

This guide walks you through installing PGraf Cypher and its dependencies.

## Requirements

Before installing PGraf Cypher, ensure you have:

- **Python 3.12+**
- **PostgreSQL 12+** with the pgvector extension
- The **[pgraf](https://github.com/gmr/pgraf)** schema installed in your database

## Install from PyPI

The simplest way to install PGraf Cypher is using pip:

```bash
pip install pgraf-cypher
```

This installs PGraf Cypher and its core dependencies:

- `antlr4-python3-runtime` - ANTLR4 runtime for parsing Cypher
- `psycopg` - PostgreSQL adapter for Python
- `pydantic` - Data validation and serialization
- `asyncstdlib` - Async utilities

## Development Installation

If you want to contribute to PGraf Cypher or run the latest development version:

```bash
# Clone the repository
git clone https://github.com/gmr/pgraf-cypher.git
cd pgraf-cypher

# Install in development mode with dev dependencies
pip install -e .[dev]
```

This includes additional tools for development:

- `pytest` - Testing framework
- `mypy` - Type checking
- `ruff` - Code formatting and linting
- `pre-commit` - Git hooks for code quality

## PostgreSQL Setup

### Install pgvector Extension

PGraf Cypher requires the pgvector extension for vector similarity operations:

```sql
-- Connect to your database as superuser
CREATE EXTENSION IF NOT EXISTS vector;
```

### Install pgraf Schema

You need the pgraf schema in your PostgreSQL database. You can either:

1. **Install the full pgraf package** (recommended):
   ```bash
   pip install pgraf
   ```

2. **Use the schema SQL directly**:
   ```bash
   # Download and run the schema
   psql -d your_database -f schema/pgraf.sql
   ```

## Verify Installation

Test that everything is working:

```python
from pgraf_cypher import PGrafCypher

# Test translation (doesn't require database connection)
sql, params = PGrafCypher.translate('MATCH (n) RETURN n LIMIT 1')
print("Translation successful!")
print(f"SQL: {sql}")
```

If this runs without errors, you're ready to go!

## Next Steps

- **[Database Setup](database-setup.md)** - Configure your PostgreSQL database
- **[Quick Start](quickstart.md)** - Run your first Cypher query
- **[Basic Usage](../user-guide/basic-usage.md)** - Learn the core concepts

## Troubleshooting

### Import Errors

If you get import errors, ensure you have Python 3.12+ and all dependencies installed:

```bash
python --version  # Should be 3.12+
pip list | grep pgraf-cypher
```

### PostgreSQL Connection Issues

If you can't connect to PostgreSQL:

1. Verify PostgreSQL is running
2. Check your connection string format
3. Ensure your user has appropriate permissions
4. Verify the pgraf schema exists

### ANTLR4 Issues

If you get ANTLR4-related errors, try reinstalling:

```bash
pip uninstall antlr4-python3-runtime
pip install antlr4-python3-runtime>=4.13.2
```
