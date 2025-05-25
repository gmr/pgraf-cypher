# Database Setup

This guide shows you how to set up your PostgreSQL database to work with PGraf Cypher.

## Prerequisites

- PostgreSQL 12+ installed and running
- Superuser access to create extensions
- Basic familiarity with PostgreSQL administration

## Step 1: Create Database

First, create a database for your graph data (or use an existing one):

```sql
CREATE DATABASE my_graph_db;
\c my_graph_db
```

## Step 2: Install Extensions

PGraf requires the `vector` extension for similarity search capabilities:

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

!!! info "Installing pgvector"
    If you don't have pgvector installed, see the [pgvector installation guide](https://github.com/pgvector/pgvector#installation).

## Step 3: Install PGraf Schema

You have two options for installing the schema:

### Option A: Using the PGraf Package

Install the full pgraf package which includes schema management:

```bash
pip install pgraf
```

Then use it to set up your schema:

```python
import asyncio
from pgraf import Graph
from pydantic import PostgresDsn

async def setup_schema():
    graph = Graph(PostgresDsn('postgresql://user:pass@localhost/my_graph_db'))
    await graph.initialize()
    # Schema is automatically created
    await graph.aclose()

asyncio.run(setup_schema())
```

### Option B: Manual Schema Installation

Alternatively, you can install the schema directly using the provided SQL file:

```bash
# From the pgraf-cypher repository
psql -d my_graph_db -f schema/pgraf.sql
```

## Step 4: Verify Schema

Confirm the schema was created correctly:

```sql
-- Switch to the pgraf schema
SET search_path = pgraf, public;

-- Check tables exist
\dt

-- Should show:
-- nodes
-- edges
-- embeddings
```

Verify the table structure:

```sql
-- Check nodes table
\d nodes
```

You should see:
- `id` (UUID, Primary Key)
- `created_at` (TIMESTAMP WITH TIME ZONE)
- `modified_at` (TIMESTAMP WITH TIME ZONE)
- `labels` (TEXT[])
- `properties` (JSONB)
- `mimetype` (TEXT)
- `content` (TEXT)
- `vector` (TSVECTOR)

## Understanding the Schema

### Nodes Table

The `nodes` table stores graph vertices:

```sql
-- Example node
INSERT INTO pgraf.nodes (id, labels, properties)
VALUES (
    gen_random_uuid(),
    ARRAY['User'],
    '{"name": "Alice", "email": "alice@example.com"}'::jsonb
);
```

### Edges Table

The `edges` table stores relationships between nodes:

```sql
-- Example edge (relationship)
INSERT INTO pgraf.edges (source, target, labels, properties)
VALUES (
    'source-node-uuid',
    'target-node-uuid',
    ARRAY['FOLLOWS'],
    '{}'::jsonb
);
```

### Key Features

- **JSONB Properties**: Flexible schema for node and edge properties
- **Array Labels**: Multiple labels per node/edge
- **UUID Primary Keys**: Globally unique identifiers
- **Vector Search**: Full-text search with tsvector
- **Embeddings Support**: Vector similarity search with pgvector

## Sample Data

Let's insert some sample data to test with:

```sql
-- Insert sample users
INSERT INTO pgraf.nodes (id, labels, properties) VALUES
(gen_random_uuid(), ARRAY['User'], '{"name": "Alice", "email": "alice@example.com"}'),
(gen_random_uuid(), ARRAY['User'], '{"name": "Bob", "email": "bob@example.com"}'),
(gen_random_uuid(), ARRAY['User'], '{"name": "Charlie", "email": "charlie@example.com"}');

-- Get the UUIDs for creating relationships
WITH users AS (
    SELECT id, properties->>'name' as name
    FROM pgraf.nodes
    WHERE 'User' = ANY(labels)
)
INSERT INTO pgraf.edges (source, target, labels, properties)
SELECT
    a.id as source,
    b.id as target,
    ARRAY['FOLLOWS'] as labels,
    '{}'::jsonb as properties
FROM users a, users b
WHERE a.name = 'Alice' AND b.name = 'Bob';
```

## Connection String Format

Your PostgreSQL connection string should follow this format:

```python
from pydantic import PostgresDsn

# Basic connection
url = PostgresDsn('postgresql://username:password@localhost:5432/my_graph_db')

# With additional parameters
url = PostgresDsn('postgresql://user:pass@localhost/db?sslmode=require')
```

## Common Issues

### Permission Errors

If you get permission errors:

```sql
-- Grant necessary permissions
GRANT USAGE ON SCHEMA pgraf TO your_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA pgraf TO your_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA pgraf TO your_user;
```

### Schema Not Found

If you get "schema pgraf does not exist":

1. Verify you're connected to the right database
2. Check the schema was created: `\dn pgraf`
3. Ensure your user has access to the schema

### Extension Issues

If pgvector extension fails to install:

1. Check you have superuser privileges
2. Verify pgvector is installed on your system
3. Try: `SELECT * FROM pg_available_extensions WHERE name = 'vector';`

## Next Steps

With your database set up, you're ready to:

- **[Try the Quick Start](quickstart.md)** - Run your first Cypher query
- **[Learn Basic Usage](../user-guide/basic-usage.md)** - Understand core concepts
- **[Explore Examples](../examples/simple-queries.md)** - See practical queries
