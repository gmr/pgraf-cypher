# Cypher Features

This page documents which Cypher language features are supported by PGraf Cypher and how they map to PostgreSQL SQL.

## Supported Features ✅

### MATCH Patterns

#### Basic Node Matching
```cypher
MATCH (n)                    -- All nodes
MATCH (n:User)              -- Nodes with User label
MATCH (n:User:Admin)        -- Nodes with both labels
MATCH (u {name: "Alice"})   -- Node with property
```

#### Relationship Matching
```cypher
MATCH (a)-[r]->(b)          -- Any directed relationship
MATCH (a)-[r:FOLLOWS]->(b)  -- Specific relationship type
MATCH (a)<-[r]-(b)          -- Reverse direction
MATCH (a)-[r]-(b)           -- Undirected relationship
```

#### Complex Patterns
```cypher
MATCH (a)-[:FOLLOWS]->(b)-[:FOLLOWS]->(c)  -- Chain relationships
MATCH (a)-[:FOLLOWS]->(b)<-[:FOLLOWS]-(c)  -- Converging patterns
```

### WHERE Clauses

#### Property Comparisons
```cypher
WHERE n.age > 25
WHERE n.name = "Alice"
WHERE n.active = true
WHERE n.score >= 4.5
```

#### Label Tests
```cypher
WHERE n:User
WHERE NOT n:Admin
WHERE n:User OR n:Guest
```

#### Logical Operators
```cypher
WHERE n.age > 25 AND n.department = "Engineering"
WHERE n.active = true OR n.vip = true
WHERE NOT n.deleted
```

#### Property Existence
```cypher
WHERE EXISTS(n.email)
WHERE n.phone IS NOT NULL
```

#### Pattern Existence
```cypher
WHERE EXISTS { MATCH (n)-[:FOLLOWS]->(friend) }
WHERE NOT EXISTS { MATCH (n)-[:BLOCKED]->(other) }
```

### RETURN Statements

#### Basic Returns
```cypher
RETURN n                    -- Return entire node
RETURN n.name              -- Return property
RETURN n.name AS user_name -- Return with alias
```

#### Aggregation Functions
```cypher
RETURN COUNT(n)
RETURN COUNT(DISTINCT n.department)
RETURN AVG(n.age)
RETURN SUM(n.score)
RETURN MIN(n.created_at)
RETURN MAX(n.updated_at)
```

#### Expressions
```cypher
RETURN n.first_name + " " + n.last_name AS full_name
RETURN n.age * 12 AS age_in_months
```

### ORDER BY

```cypher
ORDER BY n.name
ORDER BY n.name ASC
ORDER BY n.age DESC
ORDER BY n.department, n.name  -- Multiple columns
```

### LIMIT and SKIP

```cypher
LIMIT 10
SKIP 20
SKIP 20 LIMIT 10  -- Pagination
```

### Variables and Aliases

```cypher
MATCH (user:User)-[:FOLLOWS]->(friend:User)
WHERE user.active = true
RETURN user.name, friend.name
```

## Partially Supported Features ⚠️

### Variable Length Paths

Basic variable length paths work but with limitations:

```cypher
-- Supported
MATCH (a)-[:FOLLOWS*1..3]->(b) RETURN a, b

-- Limited support for complex patterns
MATCH (a)-[:FOLLOWS*]->(b) WHERE b.name = "Alice"
```

### CASE Expressions

Simple CASE expressions are supported:

```cypher
RETURN CASE
  WHEN n.age < 18 THEN "Minor"
  WHEN n.age < 65 THEN "Adult"
  ELSE "Senior"
END AS age_group
```

## Unsupported Features ❌

### Advanced Path Operations

```cypher
-- Not supported
MATCH p = (a)-[:FOLLOWS*]->(b)
RETURN length(p), nodes(p), relationships(p)

-- Not supported
MATCH path = shortestPath((a)-[:FOLLOWS*]-(b))
```

### SET and DELETE Operations

```cypher
-- Not supported - PGraf Cypher is read-only
SET n.age = 30
DELETE n
CREATE (n:User {name: "Alice"})
MERGE (n:User {email: "alice@example.com"})
```

### Advanced Functions

```cypher
-- Not supported
RETURN id(n), labels(n), keys(n)
RETURN type(r), startNode(r), endNode(r)
RETURN toString(n.age), toInteger(n.score)
```

### Subqueries and UNION

```cypher
-- Not supported
CALL {
  MATCH (n:User) RETURN n
}

-- Not supported
MATCH (n:User) RETURN n.name
UNION
MATCH (n:Admin) RETURN n.name
```

### Map Projections

```cypher
-- Not supported
RETURN n {.name, .email, age: n.age + 1}
```

## SQL Translation Examples

Here's how common Cypher patterns translate to SQL:

### Simple Node Query

**Cypher:**
```cypher
MATCH (u:User {active: true})
RETURN u.name, u.email
ORDER BY u.name
LIMIT 10
```

**Generated SQL:**
```sql
SELECT
    n_0.properties->>'name' as name,
    n_0.properties->>'email' as email
FROM pgraf.nodes n_0
WHERE 'User' = ANY(n_0.labels)
  AND n_0.properties->>'active' = 'true'
ORDER BY n_0.properties->>'name'
LIMIT 10
```

### Relationship Query

**Cypher:**
```cypher
MATCH (a:User)-[:FOLLOWS]->(b:User)
WHERE a.department = 'Engineering'
RETURN a.name, b.name
```

**Generated SQL:**
```sql
SELECT
    a_0.properties->>'name' as name,
    b_1.properties->>'name' as name
FROM pgraf.nodes a_0
JOIN pgraf.edges e_0 ON a_0.id = e_0.source
JOIN pgraf.nodes b_1 ON e_0.target = b_1.id
WHERE 'User' = ANY(a_0.labels)
  AND 'FOLLOWS' = ANY(e_0.labels)
  AND 'User' = ANY(b_1.labels)
  AND a_0.properties->>'department' = 'Engineering'
```

### Aggregation Query

**Cypher:**
```cypher
MATCH (u:User)-[:AUTHORED]->(p:Post)
RETURN u.name, COUNT(p) as post_count
ORDER BY post_count DESC
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'name' as name,
    COUNT(p_1.*) as post_count
FROM pgraf.nodes u_0
JOIN pgraf.edges e_0 ON u_0.id = e_0.source
JOIN pgraf.nodes p_1 ON e_0.target = p_1.id
WHERE 'User' = ANY(u_0.labels)
  AND 'AUTHORED' = ANY(e_0.labels)
  AND 'Post' = ANY(p_1.labels)
GROUP BY u_0.id, u_0.properties->>'name'
ORDER BY COUNT(p_1.*) DESC
```

## Data Type Handling

### Property Types

PGraf Cypher handles PostgreSQL JSONB types appropriately:

| Cypher Type | JSONB Storage | SQL Access |
|-------------|---------------|------------|
| String | `"value"` | `properties->>'key'` |
| Number | `123` | `(properties->>'key')::numeric` |
| Boolean | `true`/`false` | `(properties->>'key')::boolean` |
| Array | `[1,2,3]` | `properties->'key'` |
| Object | `{"nested": "value"}` | `properties->'key'` |

### Label Handling

Labels are stored as PostgreSQL TEXT arrays:

```sql
-- Single label check
WHERE 'User' = ANY(n.labels)

-- Multiple label check
WHERE 'User' = ANY(n.labels) AND 'Admin' = ANY(n.labels)

-- Label existence
WHERE array_length(n.labels, 1) > 0
```

## Performance Considerations

### Indexed Properties

For better performance, create indexes on frequently queried properties:

```sql
-- Index for user email lookups
CREATE INDEX user_email_idx ON pgraf.nodes
USING BTREE ((properties->>'email'))
WHERE 'User' = ANY(labels);

-- Partial index for active users
CREATE INDEX active_users_idx ON pgraf.nodes
USING BTREE ((properties->>'department'))
WHERE 'User' = ANY(labels)
  AND properties->>'active' = 'true';
```

### Query Optimization

1. **Specific labels**: Use specific labels rather than matching all nodes
2. **Early filtering**: Put selective filters early in WHERE clauses
3. **Limit results**: Always use LIMIT for exploratory queries
4. **Index usage**: Ensure generated SQL uses available indexes

## Extending Support

PGraf Cypher is actively developed. To request support for additional Cypher features:

1. Check existing [GitHub issues](https://github.com/gmr/pgraf-cypher/issues)
2. Create a new issue with your use case
3. Provide example Cypher queries and expected behavior
4. Consider contributing a pull request

## Next Steps

- **[Advanced Queries](advanced-queries.md)** - Complex patterns and optimization
- **[Examples](../examples/simple-queries.md)** - Practical query examples
- **[API Reference](../api/pgraf-cypher.md)** - Detailed API documentation
