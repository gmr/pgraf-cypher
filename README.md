# PGraf Cypher

[![PyPI version](https://badge.fury.io/py/pgraf-cypher.svg)](https://badge.fury.io/py/pgraf-cypher)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://gmr.github.io/pgraf-cypher/)
[![Python Version](https://img.shields.io/pypi/pyversions/pgraf-cypher](https://pypi.org/project/pgraf-cypher/)
[![License](https://img.shields.io/github/license/gmr/pgraf-cypher)](https://github.com/gmr/pgraf-cypher/blob/main/LICENSE)

A Python library for translating Neo4j's Cypher query language to PostgreSQL SQL, designed to work with the [pgraf](https://github.com/gmr/pgraf) graph database toolkit.

[**📚 Documentation**](https://gmr.github.io/pgraf/) | [**🚀 Quick Start**](https://gmr.github.io/pgraf/installation/) | [**📖 API Reference**](https://gmr.github.io/pgraf/api/graph/)

## Overview

PGraf Cypher enables you to use familiar Cypher syntax to query graph data stored in PostgreSQL. It parses Cypher queries using ANTLR4 and translates them to PostgreSQL SQL that works with the pgraf schema, which stores graph data in nodes and edges tables with JSONB properties.

## Requirements

- Python 3.12+
- PostgreSQL 12+ with the pgvector extension
- The [pgraf](https://github.com/gmr/pgraf) schema installed in your database

## Installation

```bash
pip install pgraf-cypher
```

For development:
```bash
git clone https://github.com/gmr/pgraf-cypher.git
cd pgraf-cypher
pip install -e .[dev]
```

## Database Setup

This library requires the pgraf schema to be installed in your PostgreSQL database. See the [pgraf project](https://github.com/gmr/pgraf) for full setup instructions, or use the provided schema:

```bash
psql -d your_database -f schema/pgraf.sql
```

## Quick Start

### Basic Usage

```python
import asyncio
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

async def main():
    # Initialize with your PostgreSQL connection
    cypher = PGrafCypher(
        PostgresDsn('postgresql://user:pass@localhost/db'),
        schema='pgraf'
    )

    await cypher.initialize()

    # Execute a Cypher query
    query = """
    MATCH (u:User {email: "alice@example.com"})-[:FOLLOWS]->(friend:User)
    RETURN friend.name, friend.email
    ORDER BY friend.name
    LIMIT 10
    """

    async with cypher.execute(query) as cursor:
        async for row in cursor:
            print(f"Friend: {row[0]} ({row[1]})")

    await cypher.aclose()

asyncio.run(main())
```

### Translation Only

You can also use the library to translate Cypher to SQL without executing:

```python
from pgraf_cypher import PGrafCypher

cypher_query = """
MATCH (u:User {email: "alice@example.com"})-[:FOLLOWS]->(friend:User)
RETURN friend.name, friend.email
ORDER BY friend.name
LIMIT 10
"""

sql, parameters = PGrafCypher.translate(cypher_query)
print(f"SQL: {sql}")
print(f"Parameters: {parameters}")
```

## Example

Here's a more complex example showing relationship patterns and filtering:

```python
# Find messages in private DM threads between two specific users
cypher_query = """
MATCH (u1:User {email: "foo@aweber.com"})-[:author]->(m1:SlackMessage)
MATCH (u2:User {email: "bar@aweber.com"})-[:author]->(m2:SlackMessage)
WHERE m1.thread_ts = m2.thread_ts
  AND m1 <> m2
  AND EXISTS {
    MATCH (m1)-[:channel]->(:SlackChannel {name: "@privatedm"})
  }
  AND EXISTS {
    MATCH (m2)-[:channel]->(:SlackChannel {name: "@privatedm"})
  }
RETURN m1, m2
ORDER BY m1.ts DESC
LIMIT 100
"""

sql, parameters = PGrafCypher.translate(cypher_query)
```

This translates to PostgreSQL SQL that queries the `nodes` and `edges` tables, filtering on labels and JSONB properties, and performing the necessary joins to find the relationship patterns.

## Supported Cypher Features

- **MATCH** patterns with node and relationship filtering
- **WHERE** clauses with property comparisons and EXISTS subqueries
- **RETURN** with column selection and aliases
- **ORDER BY** with ASC/DESC
- **LIMIT** and **SKIP**
- Node label filtering (e.g., `:User`, `:SlackMessage`)
- Property filtering with equality (e.g., `{email: "user@example.com"}`)
- Relationship patterns (e.g., `-[:FOLLOWS]->`, `-[:author]->`)
- Variable binding and reuse
- Comparison operators (`=`, `<>`, `<`, `>`, etc.)

## Schema Assumptions

The translation assumes your PostgreSQL database uses the pgraf schema:

- **nodes** table: `id` (UUID), `labels` (TEXT[]), `properties` (JSONB)
- **edges** table: `source` (UUID), `target` (UUID), `labels` (TEXT[]), `properties` (JSONB)

Node labels like `:User` are stored in the `labels` array, and properties like `{email: "user@example.com"}` are stored as JSONB in the `properties` column.

## Development

Run tests:
```bash
python -m unittest discover tests --buffer --verbose
```

Format and lint:
```bash
ruff format
ruff check --fix
mypy pgraf_cypher
```

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
