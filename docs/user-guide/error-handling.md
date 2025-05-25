# Error Handling

This guide covers comprehensive error handling strategies when using PGraf Cypher.

## Common Error Types

### Translation Errors

These occur when Cypher cannot be parsed or translated:

```python
from pgraf_cypher import PGrafCypher

try:
    sql, params = PGrafCypher.translate("INVALID CYPHER SYNTAX")
except ValueError as e:
    print(f"Translation error: {e}")
    # Handle invalid Cypher syntax
except Exception as e:
    print(f"Unexpected translation error: {e}")
```

### Connection Errors

Database connection issues:

```python
import psycopg
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

async def handle_connection_errors():
    try:
        cypher = PGrafCypher(PostgresDsn('postgresql://user:wrong@localhost/db'))
        await cypher.initialize()
    except psycopg.OperationalError as e:
        print(f"Connection failed: {e}")
        # Handle connection failure
    except Exception as e:
        print(f"Unexpected connection error: {e}")
```

### Query Execution Errors

Runtime SQL execution errors:

```python
async def handle_execution_errors():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    try:
        async with cypher.execute("MATCH (n) RETURN n.nonexistent_property") as cursor:
            async for row in cursor:
                print(row)
    except psycopg.ProgrammingError as e:
        print(f"SQL error: {e}")
        # Handle SQL execution error
    except psycopg.DataError as e:
        print(f"Data error: {e}")
        # Handle data type conversion error
    finally:
        await cypher.aclose()
```

## Specific Error Scenarios

### Invalid Cypher Syntax

```python
def validate_cypher_query(query: str) -> bool:
    """Validate Cypher syntax before execution."""
    try:
        PGrafCypher.translate(query)
        return True
    except ValueError as e:
        print(f"Invalid Cypher: {e}")
        return False
    except Exception as e:
        print(f"Validation error: {e}")
        return False

# Usage
if validate_cypher_query("MATCH (n:User) RETURN n.name"):
    print("Query is valid")
else:
    print("Query has syntax errors")
```

### Unsupported Features

```python
def check_feature_support(query: str) -> tuple[bool, str | None]:
    """Check if query uses supported Cypher features."""

    unsupported_patterns = [
        ('CREATE', 'CREATE operations not supported'),
        ('SET', 'SET operations not supported'),
        ('DELETE', 'DELETE operations not supported'),
        ('MERGE', 'MERGE operations not supported'),
        ('shortestPath', 'shortestPath function not supported'),
        ('UNION', 'UNION operations not supported'),
    ]

    query_upper = query.upper()
    for pattern, message in unsupported_patterns:
        if pattern in query_upper:
            return False, message

    return True, None

# Usage
supported, error_msg = check_feature_support("CREATE (n:User) RETURN n")
if not supported:
    print(f"Unsupported feature: {error_msg}")
```

### Schema Validation

```python
async def validate_schema():
    """Verify pgraf schema exists and is correct."""
    import psycopg

    try:
        conn = await psycopg.AsyncConnection.connect(db_url)

        # Check if pgraf schema exists
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'pgraf'
            """)
            if not await cursor.fetchone():
                raise ValueError("pgraf schema not found")

        # Check required tables
        required_tables = ['nodes', 'edges', 'embeddings']
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'pgraf'
            """)
            existing_tables = {row[0] for row in await cursor.fetchall()}

            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                raise ValueError(f"Missing tables: {missing_tables}")

        await conn.close()
        return True

    except psycopg.Error as e:
        print(f"Schema validation failed: {e}")
        return False
```

## Robust Query Execution

### Retry Logic

```python
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

async def retry_query(
    func: Callable[[], T],
    max_retries: int = 3,
    delay: float = 1.0
) -> T:
    """Retry query execution with exponential backoff."""

    for attempt in range(max_retries):
        try:
            return await func()
        except psycopg.OperationalError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Query failed (attempt {attempt + 1}): {e}")
            await asyncio.sleep(delay * (2 ** attempt))
        except Exception as e:
            # Don't retry on non-transient errors
            raise

# Usage
async def execute_with_retry():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    async def query_func():
        async with cypher.execute("MATCH (n:User) RETURN COUNT(n)") as cursor:
            return await cursor.fetchone()

    try:
        result = await retry_query(query_func)
        print(f"User count: {result[0]}")
    finally:
        await cypher.aclose()
```

### Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
breaker = CircuitBreaker()

async def protected_query():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    async def query_func():
        async with cypher.execute("MATCH (n) RETURN COUNT(n)") as cursor:
            return await cursor.fetchone()

    try:
        result = await breaker.call(query_func)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Query failed: {e}")
    finally:
        await cypher.aclose()
```

## Graceful Degradation

### Fallback Queries

```python
async def get_user_recommendations(user_id: str) -> list[dict]:
    """Get user recommendations with fallback strategies."""
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    try:
        # Primary strategy: Complex collaborative filtering
        complex_query = """
        MATCH (u:User {id: $user_id})-[:FOLLOWS]->(friend:User)-[:LIKES]->(item:Item)
        WHERE NOT (u)-[:LIKES]->(item)
        RETURN item.name, COUNT(*) as score
        ORDER BY score DESC
        LIMIT 10
        """

        async with cypher.execute(complex_query.replace('$user_id', f'"{user_id}"')) as cursor:
            results = []
            async for row in cursor:
                results.append({'name': row[0], 'score': row[1]})

            if results:
                return results

    except Exception as e:
        print(f"Complex recommendation failed: {e}")

    try:
        # Fallback 1: Simple popularity-based
        simple_query = """
        MATCH (item:Item)<-[:LIKES]-(u:User)
        RETURN item.name, COUNT(*) as popularity
        ORDER BY popularity DESC
        LIMIT 10
        """

        async with cypher.execute(simple_query) as cursor:
            results = []
            async for row in cursor:
                results.append({'name': row[0], 'score': row[1]})

            if results:
                return results

    except Exception as e:
        print(f"Simple recommendation failed: {e}")

    finally:
        await cypher.aclose()

    # Final fallback: Empty list
    return []
```

### Partial Results

```python
async def get_user_activity(user_id: str) -> dict:
    """Get user activity with partial results on failure."""
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    activity = {
        'posts': [],
        'likes': [],
        'follows': [],
        'errors': []
    }

    queries = [
        ('posts', "MATCH (u:User {id: $id})-[:POSTED]->(p:Post) RETURN p.title, p.created_at"),
        ('likes', "MATCH (u:User {id: $id})-[:LIKES]->(item) RETURN item.name, item.type"),
        ('follows', "MATCH (u:User {id: $id})-[:FOLLOWS]->(friend:User) RETURN friend.name")
    ]

    for activity_type, query in queries:
        try:
            formatted_query = query.replace('$id', f'"{user_id}"')
            async with cypher.execute(formatted_query) as cursor:
                activity[activity_type] = [row async for row in cursor]
        except Exception as e:
            activity['errors'].append(f"{activity_type}: {str(e)}")

    await cypher.aclose()
    return activity
```

## Logging and Monitoring

### Query Logging

```python
import logging
import time

logger = logging.getLogger(__name__)

class QueryLogger:
    def __init__(self, cypher: PGrafCypher):
        self.cypher = cypher

    async def execute_with_logging(self, query: str):
        start_time = time.time()

        try:
            # Log query start
            logger.info(f"Executing query: {query[:100]}...")

            # Get SQL translation
            sql, params = PGrafCypher.translate(query)
            logger.debug(f"Generated SQL: {sql}")
            logger.debug(f"Parameters: {params}")

            # Execute query
            async with self.cypher.execute(query) as cursor:
                results = [row async for row in cursor]

            # Log success
            duration = time.time() - start_time
            logger.info(f"Query completed in {duration:.3f}s, {len(results)} rows")

            return results

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(f"Query failed after {duration:.3f}s: {e}")
            raise

# Usage
async def logged_query():
    cypher = PGrafCypher(db_url)
    await cypher.initialize()

    logger_wrapper = QueryLogger(cypher)

    try:
        results = await logger_wrapper.execute_with_logging(
            "MATCH (n:User) RETURN n.name LIMIT 10"
        )
        return results
    finally:
        await cypher.aclose()
```

### Performance Monitoring

```python
import psutil
import time
from dataclasses import dataclass

@dataclass
class QueryMetrics:
    query: str
    duration: float
    memory_usage: float
    row_count: int
    success: bool
    error: str | None = None

class PerformanceMonitor:
    def __init__(self):
        self.metrics: list[QueryMetrics] = []

    async def execute_with_monitoring(self, cypher: PGrafCypher, query: str) -> QueryMetrics:
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            async with cypher.execute(query) as cursor:
                results = [row async for row in cursor]

            duration = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            metrics = QueryMetrics(
                query=query[:100],
                duration=duration,
                memory_usage=end_memory - start_memory,
                row_count=len(results),
                success=True
            )

            self.metrics.append(metrics)
            return metrics

        except Exception as e:
            duration = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            metrics = QueryMetrics(
                query=query[:100],
                duration=duration,
                memory_usage=end_memory - start_memory,
                row_count=0,
                success=False,
                error=str(e)
            )

            self.metrics.append(metrics)
            raise

    def get_stats(self) -> dict:
        if not self.metrics:
            return {}

        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]

        return {
            'total_queries': len(self.metrics),
            'successful_queries': len(successful),
            'failed_queries': len(failed),
            'success_rate': len(successful) / len(self.metrics) * 100,
            'avg_duration': sum(m.duration for m in successful) / len(successful) if successful else 0,
            'max_duration': max((m.duration for m in successful), default=0),
            'avg_memory_usage': sum(m.memory_usage for m in successful) / len(successful) if successful else 0
        }
```

## Best Practices

### Error Handling Hierarchy

1. **Validate early**: Check syntax and features before execution
2. **Use specific exceptions**: Catch specific error types, not bare Exception
3. **Implement fallbacks**: Have simpler queries as backup
4. **Log appropriately**: Log errors with context for debugging
5. **Monitor performance**: Track query performance and failures
6. **Graceful degradation**: Return partial results when possible

### Example: Complete Error Handling

```python
async def robust_user_search(search_term: str) -> dict:
    """Comprehensive user search with full error handling."""

    # Input validation
    if not search_term or len(search_term) < 2:
        return {'error': 'Search term must be at least 2 characters', 'results': []}

    # Query validation
    query = f"MATCH (u:User) WHERE u.name CONTAINS '{search_term}' RETURN u.name, u.email LIMIT 20"
    if not validate_cypher_query(query):
        return {'error': 'Invalid search query', 'results': []}

    cypher = PGrafCypher(db_url)

    try:
        await cypher.initialize()

        # Schema validation
        if not await validate_schema():
            return {'error': 'Database schema invalid', 'results': []}

        # Execute with retry
        async def search_func():
            async with cypher.execute(query) as cursor:
                return [{'name': row[0], 'email': row[1]} async for row in cursor]

        results = await retry_query(search_func)
        return {'results': results, 'count': len(results)}

    except psycopg.Error as e:
        logger.error(f"Database error in user search: {e}")
        return {'error': 'Database error', 'results': []}

    except Exception as e:
        logger.error(f"Unexpected error in user search: {e}")
        return {'error': 'Internal error', 'results': []}

    finally:
        try:
            await cypher.aclose()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
```

## Next Steps

- **[Advanced Queries](advanced-queries.md)** - Complex patterns and optimization
- **[Examples](../examples/real-world.md)** - See error handling in real applications
- **[Development](../development/testing.md)** - Testing error scenarios
