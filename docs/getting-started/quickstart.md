# Quick Start

Get up and running with PGraf Cypher in minutes. This guide assumes you have PostgreSQL set up with the pgraf schema.

## Your First Query

Let's start with a simple example that translates Cypher to SQL:

```python
from pgraf_cypher import PGrafCypher

# Simple node query
cypher = 'MATCH (n:User) RETURN n.name LIMIT 5'
sql, parameters = PGrafCypher.translate(cypher)

print(f"SQL: {sql}")
print(f"Parameters: {parameters}")
```

This will output something like:
```sql
SELECT n_0.properties->>'name' as name
FROM pgraf.nodes n_0
WHERE 'User' = ANY(n_0.labels)
LIMIT 5
```

## Executing Queries

Now let's execute a query against a real database:

```python
import asyncio
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

async def run_query():
    # Connect to your database
    cypher = PGrafCypher(
        PostgresDsn('postgresql://user:pass@localhost/your_db'),
        schema='pgraf'
    )

    await cypher.initialize()

    # Execute a query
    query = """
    MATCH (u:User)
    RETURN u.name, u.email
    ORDER BY u.name
    LIMIT 10
    """

    async with cypher.execute(query) as cursor:
        print("Users in the database:")
        async for row in cursor:
            print(f"- {row[0]} ({row[1]})")

    await cypher.aclose()

# Run the example
asyncio.run(run_query())
```

## Working with Relationships

Let's query relationships between nodes:

```python
async def find_friends():
    cypher = PGrafCypher(
        PostgresDsn('postgresql://user:pass@localhost/your_db')
    )
    await cypher.initialize()

    # Find friends of a specific user
    query = """
    MATCH (u:User {email: "alice@example.com"})-[:FOLLOWS]->(friend:User)
    RETURN friend.name, friend.email
    ORDER BY friend.name
    """

    async with cypher.execute(query) as cursor:
        print("Alice's friends:")
        async for row in cursor:
            print(f"- {row[0]} ({row[1]})")

    await cypher.aclose()

asyncio.run(find_friends())
```

## Complex Pattern Matching

Here's a more complex example that finds mutual connections:

```python
async def mutual_followers():
    cypher = PGrafCypher(
        PostgresDsn('postgresql://user:pass@localhost/your_db')
    )
    await cypher.initialize()

    # Find users who follow each other
    query = """
    MATCH (a:User)-[:FOLLOWS]->(b:User)-[:FOLLOWS]->(a)
    WHERE a.email < b.email  // Avoid duplicates
    RETURN a.name, b.name
    ORDER BY a.name, b.name
    """

    async with cypher.execute(query) as cursor:
        print("Mutual followers:")
        async for row in cursor:
            print(f"- {row[0]} ↔ {row[1]}")

    await cypher.aclose()

asyncio.run(mutual_followers())
```

## Adding Sample Data

If you don't have data in your database yet, here's how to add some:

```python
import asyncio
import uuid
from pgraf import Graph  # You'll need: pip install pgraf
from pydantic import PostgresDsn

async def setup_sample_data():
    graph = Graph(PostgresDsn('postgresql://user:pass@localhost/your_db'))
    await graph.initialize()

    # Create some users
    alice_id = uuid.uuid4()
    bob_id = uuid.uuid4()
    charlie_id = uuid.uuid4()

    await graph.add_node(
        alice_id,
        labels=['User'],
        properties={'name': 'Alice', 'email': 'alice@example.com'}
    )

    await graph.add_node(
        bob_id,
        labels=['User'],
        properties={'name': 'Bob', 'email': 'bob@example.com'}
    )

    await graph.add_node(
        charlie_id,
        labels=['User'],
        properties={'name': 'Charlie', 'email': 'charlie@example.com'}
    )

    # Create relationships
    await graph.add_edge(
        alice_id, bob_id,
        labels=['FOLLOWS'],
        properties={}
    )

    await graph.add_edge(
        bob_id, charlie_id,
        labels=['FOLLOWS'],
        properties={}
    )

    await graph.add_edge(
        charlie_id, alice_id,
        labels=['FOLLOWS'],
        properties={}
    )

    print("Sample data created!")
    await graph.aclose()

asyncio.run(setup_sample_data())
```

## Complete Example

Here's a complete script that ties everything together:

```python
import asyncio
import uuid
from pgraf import Graph
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

async def complete_example():
    db_url = PostgresDsn('postgresql://user:pass@localhost/your_db')

    # Set up sample data using pgraf
    print("Setting up sample data...")
    graph = Graph(db_url)
    await graph.initialize()

    # Create nodes and relationships (code from above)
    # ... (add the sample data code here)

    await graph.aclose()

    # Query using PGraf Cypher
    print("\nQuerying with Cypher...")
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    # Run some queries
    queries = [
        "MATCH (n:User) RETURN n.name ORDER BY n.name",
        "MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.name, b.name",
        "MATCH (a:User)-[:FOLLOWS*2]->(c:User) RETURN a.name, c.name"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        async with cypher.execute(query) as cursor:
            async for row in cursor:
                print(f"  {row}")

    await cypher.aclose()

asyncio.run(complete_example())
```

## What's Next?

Now that you've run your first queries, explore more advanced features:

- **[Basic Usage Guide](../user-guide/basic-usage.md)** - Learn core concepts
- **[Cypher Features](../user-guide/cypher-features.md)** - See what Cypher constructs are supported
- **[Examples](../examples/simple-queries.md)** - More practical examples
- **[Advanced Queries](../user-guide/advanced-queries.md)** - Complex patterns and optimizations

## Troubleshooting

### Connection Issues

If you can't connect to your database:

```python
# Test basic connection
import psycopg
conn = psycopg.connect("postgresql://user:pass@localhost/your_db")
print("Connection successful!")
conn.close()
```

### No Results

If your queries return no results:

1. Verify you have data: `SELECT COUNT(*) FROM pgraf.nodes;`
2. Check your labels: `SELECT DISTINCT unnest(labels) FROM pgraf.nodes;`
3. Verify the schema: `SET search_path = pgraf, public;`

### Translation Errors

If Cypher translation fails:

1. Check your Cypher syntax against [Neo4j documentation](https://neo4j.com/docs/cypher-manual/current/)
2. See [supported features](../user-guide/cypher-features.md) for what's implemented
3. Try simpler queries first to isolate the issue
