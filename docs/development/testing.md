# Testing

Comprehensive testing guide for PGraf Cypher development and usage.

## Test Structure

The test suite is organized into several categories:

```
tests/
├── __init__.py
├── test_main.py          # Main API tests
├── test_parsers.py       # Parser unit tests
├── test_models.py        # Model validation tests
├── test_to_sql.py        # SQL generation tests
├── test_integration.py   # Full integration tests
└── fixtures/             # Test data and utilities
    ├── sample_data.sql
    └── test_base.py
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python -m unittest discover tests --buffer --verbose

# Run specific test file
python -m unittest tests.test_main --verbose

# Run specific test case
python -m unittest tests.test_main.CypherTestCase.test_nodes --verbose

# Run with pattern matching
python -m unittest discover -p "test_*integration*" --verbose
```

### Test Coverage

```bash
# Run tests with coverage
coverage run -m unittest discover tests --buffer --verbose

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
open htmlcov/index.html  # View in browser
```

### Performance Testing

```bash
# Run performance benchmarks
python -m tests.benchmark_queries

# Profile specific queries
python -m cProfile -o profile.stats tests/test_performance.py
python -m pstats profile.stats
```

## Unit Tests

### Model Tests

Test Pydantic model validation and behavior:

```python
import unittest
from pgraf_cypher.models import NodePattern, RelationshipPattern, MatchClause

class TestModels(unittest.TestCase):
    def test_node_pattern_validation(self):
        # Valid node pattern
        pattern = NodePattern(
            variable="user",
            labels=["User", "Admin"],
            properties={"active": True, "age": 25}
        )

        self.assertEqual(pattern.variable, "user")
        self.assertEqual(len(pattern.labels), 2)
        self.assertTrue(pattern.properties["active"])

    def test_node_pattern_optional_fields(self):
        # Minimal node pattern
        pattern = NodePattern()

        self.assertIsNone(pattern.variable)
        self.assertEqual(pattern.labels, [])
        self.assertEqual(pattern.properties, {})

    def test_relationship_pattern_validation(self):
        rel = RelationshipPattern(
            variable="follows",
            labels=["FOLLOWS"],
            direction="->",
            properties={"since": "2024-01-01"}
        )

        self.assertEqual(rel.direction, "->")
        self.assertIn("FOLLOWS", rel.labels)

    def test_invalid_relationship_direction(self):
        with self.assertRaises(ValueError):
            RelationshipPattern(direction="invalid")
```

### Parser Tests

Test ANTLR parse tree to model conversion:

```python
import unittest
from pgraf_cypher.parsers import CypherParser
from pgraf_cypher.models import Query, MatchClause

class TestParsers(unittest.TestCase):
    def setUp(self):
        self.parser = CypherParser()

    def test_simple_match_parsing(self):
        cypher = "MATCH (n:User) RETURN n"
        query = self.parser.parse(cypher)

        self.assertIsInstance(query, Query)
        self.assertEqual(len(query.clauses), 2)  # MATCH + RETURN

        match_clause = query.clauses[0]
        self.assertIsInstance(match_clause, MatchClause)

    def test_property_parsing(self):
        cypher = 'MATCH (u:User {name: "Alice", age: 30}) RETURN u'
        query = self.parser.parse(cypher)

        match_clause = query.clauses[0]
        pattern = match_clause.patterns[0]

        self.assertEqual(pattern.properties["name"], "Alice")
        self.assertEqual(pattern.properties["age"], 30)

    def test_relationship_parsing(self):
        cypher = "MATCH (a)-[:FOLLOWS]->(b) RETURN a, b"
        query = self.parser.parse(cypher)

        # Verify relationship structure
        match_clause = query.clauses[0]
        self.assertEqual(len(match_clause.patterns), 1)

        pattern = match_clause.patterns[0]
        self.assertEqual(len(pattern.elements), 3)  # node-rel-node
```

### SQL Generation Tests

Test model to SQL translation:

```python
import unittest
from pgraf_cypher.to_sql import SQLGenerator
from pgraf_cypher.models import NodePattern, MatchClause

class TestSQLGeneration(unittest.TestCase):
    def setUp(self):
        self.generator = SQLGenerator()

    def test_simple_node_sql(self):
        pattern = NodePattern(
            variable="n",
            labels=["User"],
            properties={"active": True}
        )

        sql = self.generator.translate_node_pattern(pattern)

        self.assertIn("pgraf.nodes", sql)
        self.assertIn("'User' = ANY(labels)", sql)
        self.assertIn("properties->>'active'", sql)

    def test_relationship_join_sql(self):
        # Test complex relationship patterns
        cypher = "MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.name, b.name"
        sql, params = self.generator.translate(cypher)

        self.assertIn("JOIN pgraf.edges", sql)
        self.assertIn("'FOLLOWS' = ANY", sql)
        self.assertEqual(len(params), 0)  # No parameters in this query

    def test_where_clause_sql(self):
        cypher = "MATCH (u:User) WHERE u.age > 25 RETURN u"
        sql, params = self.generator.translate(cypher)

        self.assertIn("WHERE", sql)
        self.assertIn("(properties->>'age')::numeric > 25", sql)
```

## Integration Tests

### Database Integration

Test against real PostgreSQL database:

```python
import asyncio
import unittest
from tests.fixtures.test_base import DatabaseTestCase

class TestDatabaseIntegration(DatabaseTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.setup_sample_data()

    async def test_simple_query_execution(self):
        cypher = "MATCH (u:User) RETURN u.name ORDER BY u.name"

        async with self.cypher.execute(cypher) as cursor:
            results = [row async for row in cursor]

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0], "Alice")
        self.assertEqual(results[1][0], "Bob")
        self.assertEqual(results[2][0], "Charlie")

    async def test_relationship_query(self):
        cypher = """
        MATCH (a:User)-[:FOLLOWS]->(b:User)
        RETURN a.name, b.name
        ORDER BY a.name, b.name
        """

        async with self.cypher.execute(cypher) as cursor:
            results = [row async for row in cursor]

        # Verify relationship data
        self.assertTrue(len(results) > 0)
        self.assertIsInstance(results[0][0], str)
        self.assertIsInstance(results[0][1], str)

    async def test_aggregation_query(self):
        cypher = """
        MATCH (u:User)
        RETURN COUNT(u) as user_count
        """

        async with self.cypher.execute(cypher) as cursor:
            result = await cursor.fetchone()

        self.assertEqual(result[0], 3)  # Expected user count

    async def test_error_handling(self):
        # Test invalid Cypher syntax
        with self.assertRaises(Exception):
            cypher = "INVALID CYPHER SYNTAX"
            async with self.cypher.execute(cypher) as cursor:
                await cursor.fetchall()
```

### Test Database Setup

Create a base class for database tests:

```python
# tests/fixtures/test_base.py
import asyncio
import unittest
from pgraf_cypher import PGrafCypher
from pydantic import PostgresDsn

class DatabaseTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_url = PostgresDsn('postgresql://user:pass@localhost/pgraf_test')

    async def asyncSetUp(self):
        self.cypher = PGrafCypher(self.db_url)
        await self.cypher.initialize()
        await self.cleanup_test_data()

    async def asyncTearDown(self):
        await self.cleanup_test_data()
        await self.cypher.aclose()

    async def setup_sample_data(self):
        """Create sample test data."""
        # Insert test users
        users = [
            {"id": "user1", "name": "Alice", "email": "alice@test.com"},
            {"id": "user2", "name": "Bob", "email": "bob@test.com"},
            {"id": "user3", "name": "Charlie", "email": "charlie@test.com"}
        ]

        for user in users:
            await self.create_test_node("User", user)

        # Insert test relationships
        relationships = [
            ("user1", "user2", "FOLLOWS"),
            ("user2", "user3", "FOLLOWS"),
            ("user1", "user3", "FOLLOWS")
        ]

        for source, target, label in relationships:
            await self.create_test_edge(source, target, label)

    async def create_test_node(self, label: str, properties: dict):
        """Helper to create test nodes."""
        # Implementation depends on your data creation approach
        pass

    async def create_test_edge(self, source: str, target: str, label: str):
        """Helper to create test edges."""
        # Implementation depends on your data creation approach
        pass

    async def cleanup_test_data(self):
        """Clean up test data."""
        # Remove test data to ensure clean state
        pass
```

## Test Data Management

### Sample Data SQL

Create reusable test data:

```sql
-- tests/fixtures/sample_data.sql
INSERT INTO pgraf.nodes (id, labels, properties) VALUES
    (gen_random_uuid(), ARRAY['User'], '{"name": "Alice", "email": "alice@test.com", "age": 30}'),
    (gen_random_uuid(), ARRAY['User'], '{"name": "Bob", "email": "bob@test.com", "age": 25}'),
    (gen_random_uuid(), ARRAY['User'], '{"name": "Charlie", "email": "charlie@test.com", "age": 35}'),
    (gen_random_uuid(), ARRAY['Post'], '{"title": "Hello World", "content": "First post", "likes": 5}'),
    (gen_random_uuid(), ARRAY['Post'], '{"title": "Tech Update", "content": "Latest tech news", "likes": 12}');

-- Add relationships after nodes are created
WITH users AS (
    SELECT id, properties->>'name' as name
    FROM pgraf.nodes
    WHERE 'User' = ANY(labels)
)
INSERT INTO pgraf.edges (source, target, labels, properties)
SELECT
    a.id, b.id, ARRAY['FOLLOWS'], '{}'::jsonb
FROM users a, users b
WHERE a.name = 'Alice' AND b.name = 'Bob';
```

### Test Fixtures

Create parameterized tests:

```python
import unittest
from parameterized import parameterized

class TestCypherTranslation(unittest.TestCase):

    @parameterized.expand([
        ("simple_match", "MATCH (n) RETURN n", "SELECT"),
        ("labeled_match", "MATCH (n:User) RETURN n", "'User' = ANY"),
        ("property_match", "MATCH (n {name: 'Alice'}) RETURN n", "properties->>'name'"),
        ("relationship", "MATCH (a)-[:FOLLOWS]->(b) RETURN a, b", "JOIN pgraf.edges"),
    ])
    def test_query_translation(self, name, cypher, expected_sql_fragment):
        sql, params = PGrafCypher.translate(cypher)
        self.assertIn(expected_sql_fragment, sql,
                     f"Expected '{expected_sql_fragment}' in SQL for {name}")
```

## Performance Testing

### Benchmark Queries

Test query performance:

```python
import time
import asyncio
from typing import List

class PerformanceBenchmark:
    def __init__(self, cypher: PGrafCypher):
        self.cypher = cypher

    async def benchmark_query(self, cypher: str, iterations: int = 10) -> dict:
        """Benchmark a query over multiple iterations."""
        times = []

        for _ in range(iterations):
            start = time.time()

            async with self.cypher.execute(cypher) as cursor:
                results = [row async for row in cursor]

            end = time.time()
            times.append(end - start)

        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times),
            'iterations': iterations
        }

    async def run_benchmark_suite(self) -> dict:
        """Run a suite of benchmark queries."""
        queries = {
            'simple_match': "MATCH (n:User) RETURN n LIMIT 100",
            'relationship': "MATCH (a:User)-[:FOLLOWS]->(b) RETURN a.name, b.name LIMIT 100",
            'aggregation': "MATCH (u:User) RETURN u.department, COUNT(*) GROUP BY u.department",
            'complex_pattern': """
                MATCH (a:User)-[:FOLLOWS]->(b:User)-[:POSTED]->(p:Post)
                WHERE p.created_at > '2024-01-01'
                RETURN a.name, COUNT(p)
                ORDER BY COUNT(p) DESC
                LIMIT 50
            """
        }

        results = {}
        for name, query in queries.items():
            results[name] = await self.benchmark_query(query)

        return results

# Usage
async def run_benchmarks():
    cypher = PGrafCypher(test_db_url)
    await cypher.initialize()

    benchmark = PerformanceBenchmark(cypher)
    results = await benchmark.run_benchmark_suite()

    for query_name, metrics in results.items():
        print(f"{query_name}: {metrics['avg_time']:.3f}s avg")

    await cypher.aclose()
```

### Load Testing

Test with large datasets:

```python
async def test_large_dataset_performance():
    """Test performance with large amounts of data."""

    # Create large test dataset
    await create_large_test_dataset(nodes=10000, edges=50000)

    # Test various query patterns
    test_queries = [
        "MATCH (n:User) RETURN COUNT(n)",
        "MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN COUNT(*)",
        "MATCH (u:User) WHERE u.age > 25 RETURN u.name LIMIT 100",
        "MATCH (a:User)-[:FOLLOWS*2]->(c:User) RETURN a.name, c.name LIMIT 100"
    ]

    for query in test_queries:
        start = time.time()
        async with cypher.execute(query) as cursor:
            results = [row async for row in cursor]
        duration = time.time() - start

        print(f"Query: {query[:50]}...")
        print(f"Duration: {duration:.3f}s")
        print(f"Results: {len(results)} rows")
        print("---")
```

## Continuous Integration

### GitHub Actions Setup

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: pgraf_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -e .[dev]

    - name: Setup database
      run: |
        psql -h localhost -U postgres -d pgraf_test -f schema/pgraf.sql
      env:
        PGPASSWORD: postgres

    - name: Run tests
      run: |
        coverage run -m unittest discover tests --buffer --verbose
        coverage xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Best Practices

### Test Organization

1. **Isolate tests**: Each test should be independent
2. **Use descriptive names**: Test names should explain what they test
3. **Test edge cases**: Include boundary conditions and error cases
4. **Mock external dependencies**: Use mocks for external services
5. **Keep tests fast**: Unit tests should run quickly

### Test Data

1. **Minimal data**: Use the smallest dataset that tests the feature
2. **Clean setup/teardown**: Ensure tests don't interfere with each other
3. **Realistic data**: Use data that reflects real-world usage
4. **Version test data**: Track changes to test datasets

### Assertion Strategies

```python
# Good: Specific assertions
self.assertEqual(len(results), 3)
self.assertIn("JOIN pgraf.edges", sql)
self.assertTrue(user.active)

# Better: Custom assertion helpers
def assertValidCypherTranslation(self, cypher: str, expected_fragments: List[str]):
    sql, params = PGrafCypher.translate(cypher)
    for fragment in expected_fragments:
        self.assertIn(fragment, sql)

# Best: Domain-specific assertions
def assertTranslatesTo(self, cypher: str, expected_sql_pattern: str):
    sql, params = PGrafCypher.translate(cypher)
    self.assertRegex(sql, expected_sql_pattern)
```

## Debugging Tests

### Debug Failed Tests

```bash
# Run single test with verbose output
python -m unittest tests.test_main.TestTranslation.test_complex_query -v

# Run with debugger
python -m pdb -m unittest tests.test_main.TestTranslation.test_complex_query

# Print SQL for debugging
def test_query_debug(self):
    cypher = "MATCH (n:User) RETURN n"
    sql, params = PGrafCypher.translate(cypher)
    print(f"Generated SQL: {sql}")  # This will show in test output
    self.assertIn("SELECT", sql)
```

### Test Database Inspection

```python
async def inspect_test_database(self):
    """Helper to inspect database state during tests."""

    # Check node count
    async with self.cypher.execute("SELECT COUNT(*) FROM pgraf.nodes") as cursor:
        count = await cursor.fetchone()
        print(f"Nodes in database: {count[0]}")

    # Check relationships
    async with self.cypher.execute("SELECT COUNT(*) FROM pgraf.edges") as cursor:
        count = await cursor.fetchone()
        print(f"Edges in database: {count[0]}")

    # Show sample data
    async with self.cypher.execute("SELECT * FROM pgraf.nodes LIMIT 5") as cursor:
        async for row in cursor:
            print(f"Node: {row}")
```

Testing is crucial for maintaining code quality and ensuring PGraf Cypher works correctly across different scenarios and PostgreSQL environments.
