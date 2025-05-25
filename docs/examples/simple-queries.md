# Simple Queries

This page shows basic Cypher query patterns and their PostgreSQL SQL translations.

## Node Queries

### Find All Nodes

**Cypher:**
```cypher
MATCH (n) RETURN n LIMIT 10
```

**Generated SQL:**
```sql
SELECT n_0.*
FROM pgraf.nodes n_0
LIMIT 10
```

**Usage:**
```python
from pgraf_cypher import PGrafCypher

sql, params = PGrafCypher.translate("MATCH (n) RETURN n LIMIT 10")
print(sql)
```

### Find Nodes by Label

**Cypher:**
```cypher
MATCH (u:User) RETURN u.name, u.email
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'name' as name,
    u_0.properties->>'email' as email
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
```

**Usage:**
```python
async def find_users():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    query = "MATCH (u:User) RETURN u.name, u.email"
    async with cypher.execute(query) as cursor:
        async for row in cursor:
            name, email = row
            print(f"User: {name} ({email})")

    await cypher.aclose()
```

### Find Nodes by Properties

**Cypher:**
```cypher
MATCH (u:User {department: "Engineering", active: true})
RETURN u.name
```

**Generated SQL:**
```sql
SELECT u_0.properties->>'name' as name
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
  AND u_0.properties->>'department' = 'Engineering'
  AND u_0.properties->>'active' = 'true'
```

## Property Queries

### String Properties

**Cypher:**
```cypher
MATCH (u:User)
WHERE u.name = "Alice"
RETURN u
```

**Generated SQL:**
```sql
SELECT u_0.*
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
  AND u_0.properties->>'name' = 'Alice'
```

### Numeric Comparisons

**Cypher:**
```cypher
MATCH (u:User)
WHERE u.age > 25 AND u.age < 65
RETURN u.name, u.age
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'name' as name,
    u_0.properties->>'age' as age
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
  AND (u_0.properties->>'age')::numeric > 25
  AND (u_0.properties->>'age')::numeric < 65
```

### Boolean Properties

**Cypher:**
```cypher
MATCH (u:User)
WHERE u.active = true AND u.verified = false
RETURN u.name
```

**Generated SQL:**
```sql
SELECT u_0.properties->>'name' as name
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
  AND (u_0.properties->>'active')::boolean = true
  AND (u_0.properties->>'verified')::boolean = false
```

## Relationship Queries

### Simple Relationships

**Cypher:**
```cypher
MATCH (a:User)-[:FOLLOWS]->(b:User)
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
```

### Bidirectional Relationships

**Cypher:**
```cypher
MATCH (a:User)-[:FRIENDS]-(b:User)
RETURN a.name, b.name
```

**Generated SQL:**
```sql
SELECT
    a_0.properties->>'name' as name,
    b_1.properties->>'name' as name
FROM pgraf.nodes a_0
JOIN pgraf.edges e_0 ON (a_0.id = e_0.source OR a_0.id = e_0.target)
JOIN pgraf.nodes b_1 ON (
    (e_0.source = a_0.id AND e_0.target = b_1.id) OR
    (e_0.target = a_0.id AND e_0.source = b_1.id)
)
WHERE 'User' = ANY(a_0.labels)
  AND 'FRIENDS' = ANY(e_0.labels)
  AND 'User' = ANY(b_1.labels)
  AND a_0.id != b_1.id
```

### Relationship Properties

**Cypher:**
```cypher
MATCH (u:User)-[r:RATED {score: 5}]->(m:Movie)
RETURN u.name, m.title
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'name' as name,
    m_1.properties->>'title' as title
FROM pgraf.nodes u_0
JOIN pgraf.edges r_0 ON u_0.id = r_0.source
JOIN pgraf.nodes m_1 ON r_0.target = m_1.id
WHERE 'User' = ANY(u_0.labels)
  AND 'RATED' = ANY(r_0.labels)
  AND r_0.properties->>'score' = '5'
  AND 'Movie' = ANY(m_1.labels)
```

## Filtering and Ordering

### WHERE Clauses

**Cypher:**
```cypher
MATCH (u:User)
WHERE u.age > 18 AND (u.department = "Engineering" OR u.role = "Manager")
RETURN u.name
ORDER BY u.name
```

**Generated SQL:**
```sql
SELECT u_0.properties->>'name' as name
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
  AND (u_0.properties->>'age')::numeric > 18
  AND (
    u_0.properties->>'department' = 'Engineering'
    OR u_0.properties->>'role' = 'Manager'
  )
ORDER BY u_0.properties->>'name'
```

### LIMIT and SKIP

**Cypher:**
```cypher
MATCH (u:User)
RETURN u.name
ORDER BY u.created_at DESC
SKIP 20 LIMIT 10
```

**Generated SQL:**
```sql
SELECT u_0.properties->>'name' as name
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
ORDER BY u_0.properties->>'created_at' DESC
LIMIT 10 OFFSET 20
```

## Aggregation

### Count Queries

**Cypher:**
```cypher
MATCH (u:User)
RETURN COUNT(u) as user_count
```

**Generated SQL:**
```sql
SELECT COUNT(*) as user_count
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
```

### Group By

**Cypher:**
```cypher
MATCH (u:User)
RETURN u.department, COUNT(u) as count
ORDER BY count DESC
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'department' as department,
    COUNT(*) as count
FROM pgraf.nodes u_0
WHERE 'User' = ANY(u_0.labels)
GROUP BY u_0.properties->>'department'
ORDER BY COUNT(*) DESC
```

### Relationship Counts

**Cypher:**
```cypher
MATCH (u:User)-[:FOLLOWS]->(friend:User)
RETURN u.name, COUNT(friend) as friend_count
ORDER BY friend_count DESC
LIMIT 10
```

**Generated SQL:**
```sql
SELECT
    u_0.properties->>'name' as name,
    COUNT(friend_1.*) as friend_count
FROM pgraf.nodes u_0
JOIN pgraf.edges e_0 ON u_0.id = e_0.source
JOIN pgraf.nodes friend_1 ON e_0.target = friend_1.id
WHERE 'User' = ANY(u_0.labels)
  AND 'FOLLOWS' = ANY(e_0.labels)
  AND 'User' = ANY(friend_1.labels)
GROUP BY u_0.id, u_0.properties->>'name'
ORDER BY COUNT(friend_1.*) DESC
LIMIT 10
```

## Practical Examples

### User Profile Query

**Cypher:**
```cypher
MATCH (u:User {email: "alice@example.com"})
RETURN u.name, u.email, u.department, u.created_at
```

**Usage:**
```python
async def get_user_profile(email: str):
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    query = """
    MATCH (u:User {email: $email})
    RETURN u.name, u.email, u.department, u.created_at
    """

    # Note: Parameter substitution would need to be handled manually
    # or through the pgraf library
    manual_query = f"""
    MATCH (u:User {{email: "{email}"}})
    RETURN u.name, u.email, u.department, u.created_at
    """

    async with cypher.execute(manual_query) as cursor:
        async for row in cursor:
            return {
                'name': row[0],
                'email': row[1],
                'department': row[2],
                'created_at': row[3]
            }

    await cypher.aclose()
    return None
```

### Recent Activity

**Cypher:**
```cypher
MATCH (u:User)-[:POSTED]->(p:Post)
WHERE p.created_at > "2024-01-01"
RETURN u.name, p.title, p.created_at
ORDER BY p.created_at DESC
LIMIT 20
```

### Social Network Query

**Cypher:**
```cypher
MATCH (me:User {email: "me@example.com"})-[:FOLLOWS]->(friend:User)-[:POSTED]->(post:Post)
WHERE post.created_at > "2024-01-01"
RETURN friend.name, post.title, post.created_at
ORDER BY post.created_at DESC
LIMIT 10
```

## Best Practices

### Use Specific Labels
```cypher
-- Good: Specific label
MATCH (u:User) RETURN u.name

-- Avoid: Generic matching
MATCH (n) WHERE n.type = "user" RETURN n.name
```

### Filter Early
```cypher
-- Good: Filter in WHERE
MATCH (u:User)
WHERE u.active = true
RETURN u.name

-- Less efficient: Filter after RETURN
MATCH (u:User)
RETURN u.name, u.active
-- Then filter in application code
```

### Use LIMIT
```cypher
-- Always limit exploratory queries
MATCH (n) RETURN n LIMIT 100

-- Even better: specific filtering + limit
MATCH (u:User) WHERE u.created_at > "2024-01-01" RETURN u LIMIT 50
```

## Next Steps

- **[Complex Patterns](complex-patterns.md)** - Multi-hop relationships and advanced patterns
- **[Real-world Use Cases](real-world.md)** - Complete application examples
- **[Advanced Queries](../user-guide/advanced-queries.md)** - Performance optimization techniques
