# Advanced Queries

This guide covers complex Cypher patterns, performance optimization, and advanced use cases.

## Multi-hop Relationships

### Two-hop Paths

Find friends of friends:

```cypher
MATCH (me:User {email: "alice@example.com"})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(fof:User)
WHERE me <> fof  -- Exclude self
RETURN fof.name, COUNT(*) as mutual_friends
ORDER BY mutual_friends DESC
LIMIT 10
```

### Variable Length Paths

```cypher
-- Find all users within 3 degrees of separation
MATCH (start:User {email: "alice@example.com"})-[:FOLLOWS*1..3]->(connected:User)
RETURN DISTINCT connected.name, connected.email
```

## Complex Pattern Matching

### Triangular Relationships

Find mutual followers:

```cypher
MATCH (a:User)-[:FOLLOWS]->(b:User)-[:FOLLOWS]->(c:User)-[:FOLLOWS]->(a)
WHERE a.id < b.id AND b.id < c.id  -- Avoid duplicates
RETURN a.name, b.name, c.name
```

### Convergent Patterns

Find users who both follow the same person:

```cypher
MATCH (a:User)-[:FOLLOWS]->(target:User)<-[:FOLLOWS]-(b:User)
WHERE a <> b
RETURN target.name, a.name, b.name
ORDER BY target.name
```

## Existence Patterns

### EXISTS Subqueries

Find users who have posted but never commented:

```cypher
MATCH (u:User)
WHERE EXISTS {
  MATCH (u)-[:POSTED]->(p:Post)
}
AND NOT EXISTS {
  MATCH (u)-[:COMMENTED]->(c:Comment)
}
RETURN u.name, u.email
```

### Complex Existence Checks

Find active projects with no recent activity:

```cypher
MATCH (p:Project {status: "active"})
WHERE NOT EXISTS {
  MATCH (p)<-[:WORKED_ON]-(u:User)
  WHERE u.last_activity > "2024-01-01"
}
RETURN p.name, p.created_at
ORDER BY p.created_at
```

## Advanced Filtering

### Property-based Filtering

```cypher
MATCH (u:User)
WHERE u.age BETWEEN 25 AND 65
  AND u.department IN ["Engineering", "Product", "Design"]
  AND u.salary > 50000
RETURN u.name, u.department, u.salary
ORDER BY u.salary DESC
```

### Pattern-based Filtering

```cypher
MATCH (u:User)-[r:WORKS_ON]->(p:Project)
WHERE r.start_date > "2024-01-01"
  AND r.role IN ["Lead", "Senior"]
  AND p.budget > 100000
RETURN u.name, p.name, r.role
```

## Aggregation Patterns

### Nested Aggregations

Find departments with the highest average project budgets:

```cypher
MATCH (u:User)-[:WORKS_ON]->(p:Project)
RETURN u.department,
       COUNT(DISTINCT p) as project_count,
       AVG(p.budget) as avg_budget,
       SUM(p.budget) as total_budget
ORDER BY avg_budget DESC
```

### Conditional Aggregations

```cypher
MATCH (u:User)-[:POSTED]->(p:Post)
RETURN u.name,
       COUNT(p) as total_posts,
       COUNT(CASE WHEN p.likes > 10 THEN 1 END) as popular_posts,
       AVG(p.likes) as avg_likes
ORDER BY popular_posts DESC
```

## Performance Optimization

### Query Planning

Always analyze your generated SQL:

```python
async def analyze_query():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    # Get the translated SQL
    sql, params = PGrafCypher.translate("""
    MATCH (u:User)-[:FOLLOWS]->(friend:User)
    WHERE u.department = "Engineering"
    RETURN u.name, COUNT(friend) as friend_count
    ORDER BY friend_count DESC
    LIMIT 10
    """)

    # Analyze with EXPLAIN
    explain_sql = f"EXPLAIN ANALYZE {sql}"
    async with cypher.execute(explain_sql) as cursor:
        async for row in cursor:
            print(row[0])

    await cypher.aclose()
```

### Index Optimization

Create targeted indexes for your query patterns:

```sql
-- Index for user department queries
CREATE INDEX user_department_idx ON pgraf.nodes
USING BTREE ((properties->>'department'))
WHERE 'User' = ANY(labels);

-- Index for post creation date
CREATE INDEX post_created_at_idx ON pgraf.nodes
USING BTREE ((properties->>'created_at'))
WHERE 'Post' = ANY(labels);

-- Composite index for user status queries
CREATE INDEX user_active_dept_idx ON pgraf.nodes
USING BTREE ((properties->>'department'), (properties->>'active'))
WHERE 'User' = ANY(labels);

-- Index for relationship types
CREATE INDEX edges_labels_source_idx ON pgraf.edges
USING BTREE (source, labels);
```

### Query Rewriting

Sometimes manual optimization helps:

```cypher
-- Instead of this expensive pattern:
MATCH (u:User)-[:FOLLOWS*2..3]->(distant:User)
RETURN u.name, distant.name

-- Use this more efficient approach:
MATCH (u:User)-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(distant:User)
WHERE u <> distant
RETURN u.name, distant.name
UNION
MATCH (u:User)-[:FOLLOWS]->(f1:User)-[:FOLLOWS]->(f2:User)-[:FOLLOWS]->(distant:User)
WHERE u <> distant
RETURN u.name, distant.name
```

## Pagination Strategies

### Offset-based Pagination

```cypher
-- Page 3, 20 items per page
MATCH (u:User)
RETURN u.name, u.email
ORDER BY u.name
SKIP 40 LIMIT 20
```

### Cursor-based Pagination

More efficient for large datasets:

```cypher
-- First page
MATCH (u:User)
RETURN u.name, u.email, u.id
ORDER BY u.name, u.id
LIMIT 20

-- Next page (using last ID from previous page)
MATCH (u:User)
WHERE u.name > "LastName" OR (u.name = "LastName" AND u.id > "last-uuid")
RETURN u.name, u.email, u.id
ORDER BY u.name, u.id
LIMIT 20
```

## Real-time Query Patterns

### Recent Activity Feeds

```cypher
MATCH (me:User {id: "my-uuid"})-[:FOLLOWS]->(friend:User)-[:POSTED]->(post:Post)
WHERE post.created_at > datetime() - duration('P7D')  -- Last 7 days
RETURN friend.name, post.title, post.content, post.created_at
ORDER BY post.created_at DESC
LIMIT 50
```

### Trending Content

```cypher
MATCH (p:Post)
WHERE p.created_at > datetime() - duration('P1D')  -- Last 24 hours
RETURN p.title, p.likes, p.comments,
       (p.likes + p.comments * 2) as score  -- Custom trending score
ORDER BY score DESC
LIMIT 20
```

## Graph Analytics

### Centrality Measures

Find most connected users:

```cypher
MATCH (u:User)
OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower:User)
RETURN u.name,
       COUNT(DISTINCT following) as following_count,
       COUNT(DISTINCT follower) as follower_count,
       COUNT(DISTINCT following) + COUNT(DISTINCT follower) as total_connections
ORDER BY total_connections DESC
LIMIT 20
```

### Community Detection

Find tight-knit groups:

```cypher
MATCH (a:User)-[:FOLLOWS]->(b:User)-[:FOLLOWS]->(c:User)-[:FOLLOWS]->(a)
WITH a, b, c
MATCH (a)-[:WORKS_ON]->(p1:Project)<-[:WORKS_ON]-(b)-[:WORKS_ON]->(p2:Project)<-[:WORKS_ON]-(c)
RETURN a.name, b.name, c.name,
       COUNT(DISTINCT p1) + COUNT(DISTINCT p2) as shared_projects
ORDER BY shared_projects DESC
```

## Error Handling

### Graceful Degradation

```python
async def robust_query(user_email: str):
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    try:
        # Try complex query first
        complex_query = """
        MATCH (u:User {email: $email})-[:FOLLOWS*1..3]->(suggestions:User)
        WHERE NOT (u)-[:FOLLOWS]->(suggestions)
        RETURN suggestions.name, COUNT(*) as connection_strength
        ORDER BY connection_strength DESC
        LIMIT 10
        """

        # Simplified query as fallback
        simple_query = """
        MATCH (u:User {email: $email})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(suggestion:User)
        WHERE NOT (u)-[:FOLLOWS]->(suggestion) AND u <> suggestion
        RETURN DISTINCT suggestion.name
        LIMIT 10
        """

        # Use the complex query, fall back to simple
        try:
            async with cypher.execute(complex_query.replace('$email', f'"{user_email}"')) as cursor:
                results = [row async for row in cursor]
                if results:
                    return results
        except Exception as e:
            print(f"Complex query failed: {e}")

        # Fallback to simple query
        async with cypher.execute(simple_query.replace('$email', f'"{user_email}"')) as cursor:
            return [row async for row in cursor]

    finally:
        await cypher.aclose()
```

## Memory Management

### Streaming Large Results

```python
async def process_large_dataset():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    # Process in batches to avoid memory issues
    batch_size = 1000
    offset = 0

    while True:
        query = f"""
        MATCH (u:User)-[:POSTED]->(p:Post)
        RETURN u.id, p.id, p.content
        ORDER BY u.id, p.created_at
        SKIP {offset} LIMIT {batch_size}
        """

        batch_results = []
        async with cypher.execute(query) as cursor:
            async for row in cursor:
                batch_results.append(row)

        if not batch_results:
            break

        # Process batch
        await process_batch(batch_results)
        offset += batch_size

    await cypher.aclose()
```

## Next Steps

- **[Examples](../examples/complex-patterns.md)** - See these patterns in action
- **[Real-world Use Cases](../examples/real-world.md)** - Complete application examples
- **[API Reference](../api/pgraf-cypher.md)** - Detailed API documentation
