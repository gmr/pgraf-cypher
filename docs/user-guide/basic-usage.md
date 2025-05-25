# Basic Usage

Learn the fundamental concepts of using PGraf Cypher to translate and execute Cypher queries against PostgreSQL.

## Core Concepts

### The PGrafCypher Class

The main interface is the `PGrafCypher` class which provides two primary functions:

1. **Translation**: Convert Cypher to SQL without execution
2. **Execution**: Translate and execute queries against PostgreSQL

```python
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

# Create instance
cypher = PGrafCypher(
    url=PostgresDsn('postgresql://user:pass@localhost/db'),
    schema='pgraf',  # Optional, defaults to 'pgraf'
    pool_min_size=1,  # Optional connection pool settings
    pool_max_size=10
)
```

### Translation vs Execution

#### Translation Only

Use `translate()` for just converting Cypher to SQL:

```python
# Static method - no database connection needed
sql, parameters = PGrafCypher.translate("""
    MATCH (u:User {active: true})-[:OWNS]->(p:Project)
    WHERE p.created_at > $since
    RETURN u.name, COUNT(p) as project_count
    ORDER BY project_count DESC
    LIMIT 10
""")

print(f"Generated SQL: {sql}")
print(f"Parameters: {parameters}")
```

This is useful for:
- Debugging query translation
- Integrating with existing database code
- Understanding the generated SQL
- Performance analysis

#### Full Execution

Use `execute()` for running queries against the database:

```python
async def run_query():
    await cypher.initialize()  # Connect to database

    async with cypher.execute(query) as cursor:
        async for row in cursor:
            print(row)

    await cypher.aclose()  # Clean up connections
```

## Working with Data Types

### Node Properties

Node properties are stored as JSONB and can be accessed in Cypher:

```python
# Query nodes with specific properties
query = """
MATCH (u:User)
WHERE u.age > 25 AND u.department = 'Engineering'
RETURN u.name, u.email, u.age
"""
```

This translates to:
```sql
SELECT
    n_0.properties->>'name' as name,
    n_0.properties->>'email' as email,
    n_0.properties->>'age' as age
FROM pgraf.nodes n_0
WHERE 'User' = ANY(n_0.labels)
  AND (n_0.properties->>'age')::int > 25
  AND n_0.properties->>'department' = 'Engineering'
```

### Labels

Labels are stored as PostgreSQL arrays and can be queried:

```python
# Multiple labels
query = "MATCH (n:User:Premium) RETURN n.name"

# Label existence
query = "MATCH (n) WHERE n:User OR n:Admin RETURN n"
```

### Relationships

Relationships are stored in the edges table with source/target UUIDs:

```python
# Simple relationship
query = "MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.name, b.name"

# Relationship with properties
query = """
MATCH (a:User)-[r:RATED {score: 5}]->(m:Movie)
RETURN a.name, m.title
"""
```

## Parameter Binding

PGraf Cypher supports parameterized queries for security and performance:

```python
# In your Cypher query, use $ parameters
query = """
MATCH (u:User {department: $dept})-[:WORKS_ON]->(p:Project)
WHERE p.budget > $min_budget
RETURN u.name, p.name, p.budget
ORDER BY p.budget DESC
"""

# Translation automatically handles parameters
sql, parameters = PGrafCypher.translate(query)

# Parameters dict will contain the extracted values
print(parameters)  # {'dept': None, 'min_budget': None}
```

When executing, you can provide parameter values:

```python
# Note: Parameter substitution in execution requires the pgraf library
# For now, you can substitute in the SQL manually or use string formatting
```

## Result Handling

### Row Format

Query results come back as tuples by default:

```python
async with cypher.execute("MATCH (n:User) RETURN n.name, n.email") as cursor:
    async for row in cursor:
        name, email = row
        print(f"User: {name} ({email})")
```

### Custom Row Classes

You can use Pydantic models for type-safe results:

```python
from pydantic import BaseModel

class UserResult(BaseModel):
    name: str
    email: str

async with cypher.execute(query, row_class=UserResult) as cursor:
    async for user in cursor:
        print(f"User: {user.name} ({user.email})")
        # user is now a typed UserResult instance
```

## Connection Management

### Async Context

Always use async context management:

```python
async def good_example():
    cypher = PGrafCypher(url)
    await cypher.initialize()

    try:
        async with cypher.execute(query) as cursor:
            # Process results
            pass
    finally:
        await cypher.aclose()

# Or use async context manager (if available in your version)
async def better_example():
    async with PGrafCypher(url) as cypher:
        async with cypher.execute(query) as cursor:
            # Process results
            pass
```

### Connection Pool

PGraf Cypher uses connection pooling for efficiency:

```python
cypher = PGrafCypher(
    url,
    pool_min_size=2,   # Minimum connections
    pool_max_size=20   # Maximum connections
)
```

## Error Handling

### Translation Errors

Catch syntax and unsupported feature errors:

```python
try:
    sql, params = PGrafCypher.translate("INVALID CYPHER SYNTAX")
except ValueError as e:
    print(f"Translation error: {e}")
```

### Execution Errors

Handle database and connection errors:

```python
import psycopg

async def safe_query():
    try:
        async with cypher.execute(query) as cursor:
            async for row in cursor:
                process(row)
    except psycopg.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Performance Tips

### Query Optimization

1. **Use specific labels**: `MATCH (u:User)` is faster than `MATCH (u)`
2. **Filter early**: Put filters in WHERE rather than post-processing
3. **Limit results**: Always use LIMIT for exploratory queries
4. **Index properties**: Create indexes on frequently queried JSONB properties

### Database Indexes

Add indexes for better performance:

```sql
-- Index on commonly queried properties
CREATE INDEX user_email_idx ON pgraf.nodes
USING BTREE ((properties->>'email'))
WHERE 'User' = ANY(labels);

-- Index on labels for faster label filtering
CREATE INDEX nodes_labels_idx ON pgraf.nodes USING GIN (labels);

-- Index on edge relationships
CREATE INDEX edges_labels_idx ON pgraf.edges USING GIN (labels);
```

### Connection Reuse

Reuse PGrafCypher instances rather than creating new ones:

```python
# Good: Reuse connection
class GraphService:
    def __init__(self, url):
        self.cypher = PGrafCypher(url)

    async def initialize(self):
        await self.cypher.initialize()

    async def find_users(self):
        async with self.cypher.execute("MATCH (u:User) RETURN u") as cursor:
            return [row async for row in cursor]

# Bad: Create new connection each time
async def find_users():
    cypher = PGrafCypher(url)  # Expensive!
    await cypher.initialize()
    # ... query
    await cypher.aclose()
```

## Best Practices

1. **Always initialize and close**: Use proper async lifecycle management
2. **Use parameters**: Never concatenate user input into queries
3. **Handle errors gracefully**: Wrap database operations in try/catch
4. **Monitor performance**: Use EXPLAIN on generated SQL for optimization
5. **Test translations**: Verify generated SQL matches expectations
6. **Keep queries simple**: Complex queries are harder to debug and optimize

## Next Steps

- **[Cypher Features](cypher-features.md)** - Learn what Cypher constructs are supported
- **[Advanced Queries](advanced-queries.md)** - Complex patterns and optimizations
- **[Examples](../examples/simple-queries.md)** - See practical query examples
- **[Error Handling](error-handling.md)** - Comprehensive error handling strategies
