# Complex Patterns

Advanced Cypher patterns for sophisticated graph queries and analytics.

## Multi-hop Relationship Patterns

### Friend Recommendations

Find friends of friends who aren't already connected:

```cypher
MATCH (me:User {email: "alice@example.com"})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(recommendation:User)
WHERE NOT (me)-[:FOLLOWS]->(recommendation)
  AND me <> recommendation
RETURN recommendation.name,
       recommendation.email,
       COUNT(friend) as mutual_connections
ORDER BY mutual_connections DESC
LIMIT 10
```

**Generated SQL approach:**
```sql
-- Simplified representation of the complex JOIN pattern
SELECT
    rec.properties->>'name' as name,
    rec.properties->>'email' as email,
    COUNT(DISTINCT friend.id) as mutual_connections
FROM pgraf.nodes me
JOIN pgraf.edges e1 ON me.id = e1.source
JOIN pgraf.nodes friend ON e1.target = friend.id
JOIN pgraf.edges e2 ON friend.id = e2.source
JOIN pgraf.nodes rec ON e2.target = rec.id
WHERE 'User' = ANY(me.labels)
  AND me.properties->>'email' = 'alice@example.com'
  AND 'FOLLOWS' = ANY(e1.labels)
  AND 'User' = ANY(friend.labels)
  AND 'FOLLOWS' = ANY(e2.labels)
  AND 'User' = ANY(rec.labels)
  AND NOT EXISTS (
    SELECT 1 FROM pgraf.edges direct
    WHERE direct.source = me.id
      AND direct.target = rec.id
      AND 'FOLLOWS' = ANY(direct.labels)
  )
  AND me.id != rec.id
GROUP BY rec.id, rec.properties->>'name', rec.properties->>'email'
ORDER BY COUNT(DISTINCT friend.id) DESC
LIMIT 10
```

### Shortest Path Simulation

Since PGraf Cypher doesn't support native shortest path, we can simulate it:

```cypher
-- 2-hop paths
MATCH path1 = (start:User {id: "user1"})-[:FOLLOWS*2]->(end:User {id: "user2"})
RETURN "2-hop" as path_type, COUNT(*) as path_count
UNION ALL
-- 3-hop paths
MATCH path2 = (start:User {id: "user1"})-[:FOLLOWS*3]->(end:User {id: "user2"})
RETURN "3-hop" as path_type, COUNT(*) as path_count
ORDER BY path_count
LIMIT 1
```

## Influence and Network Analysis

### Influence Score Calculation

Calculate user influence based on followers and engagement:

```cypher
MATCH (u:User)
OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower:User)
OPTIONAL MATCH (u)-[:POSTED]->(p:Post)<-[:LIKES]-(liker:User)
OPTIONAL MATCH (u)-[:POSTED]->(p2:Post)<-[:SHARED]-(sharer:User)
RETURN u.name,
       COUNT(DISTINCT follower) as followers,
       COUNT(DISTINCT liker) as total_likes,
       COUNT(DISTINCT sharer) as total_shares,
       (COUNT(DISTINCT follower) * 1.0 +
        COUNT(DISTINCT liker) * 0.5 +
        COUNT(DISTINCT sharer) * 2.0) as influence_score
ORDER BY influence_score DESC
LIMIT 20
```

### Community Detection

Find tightly connected user groups:

```cypher
MATCH (a:User)-[:FOLLOWS]->(b:User)-[:FOLLOWS]->(c:User)-[:FOLLOWS]->(a)
WHERE a.department = b.department AND b.department = c.department
WITH a.department as dept, COUNT(*) as triangles
WHERE triangles > 5
RETURN dept, triangles
ORDER BY triangles DESC
```

## Content Analysis Patterns

### Trending Topics

Identify trending topics based on recent activity:

```cypher
MATCH (p:Post)-[:TAGGED]->(t:Tag)
WHERE p.created_at > datetime() - duration('P7D')
OPTIONAL MATCH (p)<-[:LIKES]-(u:User)
OPTIONAL MATCH (p)<-[:SHARED]-(s:User)
RETURN t.name,
       COUNT(DISTINCT p) as post_count,
       COUNT(DISTINCT u) as like_count,
       COUNT(DISTINCT s) as share_count,
       (COUNT(DISTINCT p) + COUNT(DISTINCT u) * 0.5 + COUNT(DISTINCT s) * 2.0) as trend_score
ORDER BY trend_score DESC
LIMIT 10
```

### Content Recommendation Engine

```cypher
MATCH (user:User {id: "target_user"})-[:LIKES]->(liked:Post)-[:TAGGED]->(tag:Tag)
WITH user, tag, COUNT(liked) as user_tag_affinity
ORDER BY user_tag_affinity DESC
LIMIT 5

MATCH (tag)<-[:TAGGED]-(recommended:Post)
WHERE NOT (user)-[:LIKES]->(recommended)
  AND recommended.created_at > datetime() - duration('P30D')
OPTIONAL MATCH (recommended)<-[:LIKES]-(other:User)
RETURN recommended.title,
       recommended.author_name,
       tag.name as matching_tag,
       user_tag_affinity,
       COUNT(other) as popularity
ORDER BY user_tag_affinity DESC, popularity DESC
LIMIT 20
```

## Temporal Pattern Analysis

### Activity Timeline

Track user activity over time:

```cypher
MATCH (u:User {id: "user123"})-[:POSTED]->(p:Post)
WITH u, p,
     CASE
       WHEN p.created_at > datetime() - duration('P1D') THEN "today"
       WHEN p.created_at > datetime() - duration('P7D') THEN "this_week"
       WHEN p.created_at > datetime() - duration('P30D') THEN "this_month"
       ELSE "older"
     END as time_bucket
RETURN time_bucket,
       COUNT(p) as post_count,
       AVG(p.likes) as avg_likes
ORDER BY
  CASE time_bucket
    WHEN "today" THEN 1
    WHEN "this_week" THEN 2
    WHEN "this_month" THEN 3
    ELSE 4
  END
```

### Peak Activity Hours

```cypher
MATCH (u:User)-[:POSTED]->(p:Post)
WHERE p.created_at > datetime() - duration('P30D')
WITH p,
     toInteger(substring(toString(p.created_at), 11, 2)) as hour
RETURN hour,
       COUNT(p) as post_count,
       COUNT(DISTINCT u) as active_users
ORDER BY hour
```

## Advanced Filtering Patterns

### Conditional Existence Patterns

Find users who are active but haven't posted recently:

```cypher
MATCH (u:User)
WHERE u.last_login > datetime() - duration('P7D')
  AND NOT EXISTS {
    MATCH (u)-[:POSTED]->(p:Post)
    WHERE p.created_at > datetime() - duration('P30D')
  }
  AND EXISTS {
    MATCH (u)-[:LIKES|COMMENTS|SHARES]->(content)
    WHERE content.created_at > datetime() - duration('P7D')
  }
RETURN u.name, u.email, u.last_login
ORDER BY u.last_login DESC
```

### Complex Property Filtering

```cypher
MATCH (u:User)
WHERE u.age BETWEEN 25 AND 45
  AND u.location IN ["New York", "San Francisco", "London"]
  AND u.skills CONTAINS "Python"
  AND u.experience_years >= 5
  AND EXISTS {
    MATCH (u)-[:WORKS_AT]->(c:Company)
    WHERE c.industry IN ["Technology", "Finance"]
      AND c.size > "500"
  }
RETURN u.name, u.location, u.experience_years
ORDER BY u.experience_years DESC
```

## Graph Metrics and Analytics

### Clustering Coefficient

Measure how connected a user's network is:

```cypher
MATCH (u:User {id: "target_user"})-[:FOLLOWS]->(friend:User)
WITH u, COLLECT(friend) as friends, COUNT(friend) as friend_count
WHERE friend_count > 1

UNWIND friends as f1
UNWIND friends as f2
WHERE f1 <> f2

OPTIONAL MATCH (f1)-[:FOLLOWS]->(f2)
WITH u, friend_count, COUNT(*) as total_pairs,
     SUM(CASE WHEN f1 IS NOT NULL AND f2 IS NOT NULL THEN 1 ELSE 0 END) as connected_pairs

RETURN u.name,
       friend_count,
       connected_pairs,
       total_pairs,
       (connected_pairs * 1.0 / total_pairs) as clustering_coefficient
```

### Reach Analysis

Calculate how many users someone can reach in N steps:

```cypher
// Direct reach (1 hop)
MATCH (u:User {id: "influencer123"})-[:FOLLOWS]->(direct:User)
WITH u, COUNT(DISTINCT direct) as reach_1

// 2-hop reach
MATCH (u)-[:FOLLOWS*1..2]->(indirect:User)
WITH u, reach_1, COUNT(DISTINCT indirect) as reach_2

// 3-hop reach
MATCH (u)-[:FOLLOWS*1..3]->(extended:User)
RETURN u.name,
       reach_1,
       reach_2,
       COUNT(DISTINCT extended) as reach_3
```

## Performance Optimization Patterns

### Materialized Views Simulation

For frequently computed metrics, consider pre-computing:

```python
# Python code to create materialized metrics
async def update_user_metrics():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    # Pre-compute follower counts
    follower_query = """
    MATCH (u:User)
    OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower:User)
    RETURN u.id, COUNT(follower) as follower_count
    """

    # Store results in a metrics table or update user properties
    async with cypher.execute(follower_query) as cursor:
        async for row in cursor:
            user_id, count = row
            # Update user with follower_count property
            await update_user_property(user_id, 'follower_count', count)

    await cypher.aclose()
```

### Selective Querying

Use early filtering to improve performance:

```cypher
-- Good: Filter early
MATCH (u:User)
WHERE u.active = true
  AND u.created_at > "2024-01-01"
MATCH (u)-[:POSTED]->(p:Post)
WHERE p.likes > 10
RETURN u.name, COUNT(p)

-- Less efficient: Filter late
MATCH (u:User)-[:POSTED]->(p:Post)
WHERE u.active = true
  AND u.created_at > "2024-01-01"
  AND p.likes > 10
RETURN u.name, COUNT(p)
```

## Real-time Pattern Detection

### Anomaly Detection

Detect unusual activity patterns:

```cypher
MATCH (u:User)-[:POSTED]->(p:Post)
WHERE p.created_at > datetime() - duration('P1D')
WITH u, COUNT(p) as daily_posts, AVG(p.likes) as avg_likes
WHERE daily_posts > 20 OR avg_likes > 1000
RETURN u.name, daily_posts, avg_likes,
       CASE
         WHEN daily_posts > 20 THEN "High volume"
         WHEN avg_likes > 1000 THEN "Viral content"
         ELSE "Normal"
       END as anomaly_type
ORDER BY daily_posts DESC, avg_likes DESC
```

### Trend Detection

Identify emerging patterns:

```cypher
// Compare current week vs previous week
WITH datetime() - duration('P7D') as week_ago,
     datetime() - duration('P14D') as two_weeks_ago

MATCH (t:Tag)<-[:TAGGED]-(p:Post)
WHERE p.created_at > two_weeks_ago

WITH t,
     SUM(CASE WHEN p.created_at > week_ago THEN 1 ELSE 0 END) as current_week,
     SUM(CASE WHEN p.created_at <= week_ago THEN 1 ELSE 0 END) as previous_week

WHERE previous_week > 0
RETURN t.name,
       current_week,
       previous_week,
       (current_week * 1.0 / previous_week) as growth_ratio
ORDER BY growth_ratio DESC
LIMIT 10
```

## Integration Patterns

### Data Export for Analytics

Export graph data for external analytics tools:

```cypher
// Export user network for NetworkX analysis
MATCH (a:User)-[r:FOLLOWS]->(b:User)
RETURN a.id as source,
       b.id as target,
       r.created_at as relationship_date,
       a.department as source_dept,
       b.department as target_dept
```

### ETL Pipeline Queries

Queries designed for data pipeline processing:

```cypher
// Daily batch processing query
MATCH (u:User)
WHERE u.last_processed < date() - duration('P1D')
OPTIONAL MATCH (u)-[:POSTED]->(p:Post)
WHERE p.created_at >= date() - duration('P1D')
RETURN u.id,
       u.name,
       COUNT(p) as daily_posts,
       COLLECT(p.id) as post_ids
ORDER BY u.id
```

## Next Steps

- **[Real-world Use Cases](real-world.md)** - Complete application examples
- **[Advanced Queries](../user-guide/advanced-queries.md)** - Performance optimization
- **[API Reference](../api/pgraf-cypher.md)** - Detailed documentation
