# Contributing

Thank you for your interest in contributing to PGraf Cypher! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 12+ with pgvector extension
- Git

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/gmr/pgraf-cypher.git
cd pgraf-cypher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Database Setup for Testing

```bash
# Start PostgreSQL with Docker (optional)
docker compose up -d

# Or use your existing PostgreSQL instance
# Create test database
createdb pgraf_cypher_test

# Install schema
psql -d pgraf_cypher_test -f schema/pgraf.sql
```

## Development Workflow

### Code Style

PGraf Cypher follows strict code style guidelines:

```bash
# Format code
ruff format

# Check linting
ruff check --fix

# Type checking
mypy pgraf_cypher

# Run all checks
ruff format && ruff check --fix && mypy pgraf_cypher
```

### Running Tests

```bash
# Run all tests
python -m unittest discover tests --buffer --verbose

# Run specific test
python -m unittest tests.test_main.CypherTestCase.test_nodes

# Run with coverage
coverage run -m unittest discover tests --buffer --verbose
coverage report
coverage html  # Generate HTML report
```

### Adding New Features

1. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first** (TDD approach):
   ```python
   # In tests/test_new_feature.py
   class TestNewFeature(unittest.TestCase):
       def test_new_cypher_construct(self):
           cypher = "MATCH (n) WHERE n.new_property EXISTS RETURN n"
           sql, params = PGrafCypher.translate(cypher)
           self.assertIn("EXISTS", sql)
   ```

3. **Implement the feature**:
   - Update ANTLR grammar if needed (`pgraf_cypher/antlr/`)
   - Add models (`pgraf_cypher/models.py`)
   - Update parser (`pgraf_cypher/parsers.py`)
   - Update SQL translation (`pgraf_cypher/to_sql.py`)

4. **Update documentation**:
   - Add to supported features list
   - Include examples
   - Update API docs if needed

### Testing Guidelines

#### Unit Tests

Test individual components in isolation:

```python
import unittest
from pgraf_cypher.models import MatchClause, NodePattern

class TestModels(unittest.TestCase):
    def test_node_pattern_creation(self):
        pattern = NodePattern(
            variable="n",
            labels=["User"],
            properties={"name": "Alice"}
        )
        self.assertEqual(pattern.variable, "n")
        self.assertEqual(pattern.labels, ["User"])
```

#### Integration Tests

Test complete Cypher-to-SQL translation:

```python
class TestTranslation(unittest.TestCase):
    def test_complex_query_translation(self):
        cypher = """
        MATCH (u:User)-[:FOLLOWS]->(friend:User)
        WHERE u.age > 25
        RETURN u.name, COUNT(friend) as friend_count
        ORDER BY friend_count DESC
        LIMIT 10
        """

        sql, params = PGrafCypher.translate(cypher)

        # Verify SQL structure
        self.assertIn("JOIN", sql)
        self.assertIn("GROUP BY", sql)
        self.assertIn("ORDER BY", sql)
        self.assertIn("LIMIT", sql)
```

#### Database Tests

Test against real PostgreSQL:

```python
import asyncio
from tests.test_base import DatabaseTestCase

class TestDatabase(DatabaseTestCase):
    async def test_query_execution(self):
        await self.setup_test_data()

        cypher = "MATCH (u:User) RETURN u.name ORDER BY u.name"

        async with self.cypher.execute(cypher) as cursor:
            results = [row async for row in cursor]

        self.assertEqual(len(results), 3)  # Expected number of users
```

## Contributing Areas

### 1. Cypher Feature Support

Help expand supported Cypher constructs:

- **High Priority**:
  - Variable length paths (`-[:REL*1..3]->`)
  - More aggregation functions
  - CASE expressions
  - String functions

- **Medium Priority**:
  - Map projections
  - List comprehensions
  - Date/time functions
  - Mathematical functions

- **Research Needed**:
  - Shortest path algorithms
  - Graph algorithms (PageRank, centrality)
  - Subqueries and UNION

### 2. Performance Optimization

Improve query translation and execution:

- **SQL Optimization**: Generate more efficient SQL
- **Index Hints**: Suggest optimal indexes
- **Query Caching**: Cache translation results
- **Parallel Execution**: Support parallel query execution

### 3. Developer Experience

Enhance tooling and documentation:

- **Better Error Messages**: More helpful parse errors
- **Query Debugger**: Visual query translation tool
- **VS Code Extension**: Syntax highlighting and completion
- **More Examples**: Real-world use cases

### 4. Testing and Quality

Expand test coverage:

- **Edge Cases**: Test unusual query patterns
- **Performance Tests**: Benchmark query performance
- **Compatibility Tests**: Test with different PostgreSQL versions
- **Load Tests**: Test with large datasets

## Code Architecture

### Parser Pipeline

```
Cypher Query → ANTLR Lexer → ANTLR Parser → Parse Tree →
AST Models → SQL Generator → PostgreSQL SQL
```

### Key Modules

- **`antlr/`**: Generated ANTLR4 lexer and parser
- **`models.py`**: Pydantic models for AST representation
- **`parsers.py`**: Parse tree to AST conversion
- **`to_sql.py`**: AST to SQL translation
- **`main.py`**: Public API

### Adding New Cypher Constructs

1. **Update Grammar** (if needed):
   ```antlr
   // In Cypher25Parser.g4
   newConstruct
       : 'NEW' 'KEYWORD' expression
       ;
   ```

2. **Add Model**:
   ```python
   # In models.py
   class NewConstruct(BaseModel):
       keyword: str
       expression: Expression
   ```

3. **Update Parser**:
   ```python
   # In parsers.py
   def visitNewConstruct(self, ctx):
       return NewConstruct(
           keyword=ctx.KEYWORD().getText(),
           expression=self.visit(ctx.expression())
       )
   ```

4. **Add SQL Translation**:
   ```python
   # In to_sql.py
   def translate_new_construct(self, construct: NewConstruct) -> str:
       return f"/* SQL for {construct.keyword} */"
   ```

## Documentation

### API Documentation

Use docstrings with Google style:

```python
def translate_query(query: str) -> tuple[str, dict]:
    """Translate Cypher query to PostgreSQL SQL.

    Args:
        query: The Cypher query string to translate

    Returns:
        A tuple of (sql_string, parameters_dict)

    Raises:
        ValueError: If the query cannot be parsed

    Example:
        >>> sql, params = translate_query("MATCH (n) RETURN n")
        >>> print(sql)
        SELECT * FROM pgraf.nodes n_0
    """
```

### User Documentation

Update relevant documentation files:

- **Feature docs**: `docs/user-guide/cypher-features.md`
- **Examples**: `docs/examples/`
- **API reference**: Auto-generated from docstrings

## Pull Request Process

### Before Submitting

1. **Run all checks**:
   ```bash
   ruff format
   ruff check --fix
   mypy pgraf_cypher
   python -m unittest discover tests --buffer --verbose
   ```

2. **Update documentation** if needed

3. **Add tests** for new functionality

4. **Update CHANGELOG.md** with your changes

### PR Guidelines

- **Clear title**: Describe what the PR does
- **Description**: Explain the motivation and approach
- **Link issues**: Reference related GitHub issues
- **Small changes**: Keep PRs focused and reviewable
- **Tests included**: All new code should have tests

### Example PR Description

```markdown
## Add support for EXISTS patterns in WHERE clauses

### Changes
- Add ExistsPattern model to represent EXISTS { ... } patterns
- Update parser to handle EXISTS syntax
- Implement SQL translation using EXISTS subqueries
- Add comprehensive tests

### Related Issues
Fixes #42

### Testing
- Added unit tests for model creation
- Added integration tests for SQL generation
- Added database tests with sample data
- All existing tests pass

### Documentation
- Updated cypher-features.md with EXISTS examples
- Added to simple-queries.md examples
```

## Getting Help

- **GitHub Issues**: Ask questions or report bugs
- **Discussions**: General discussion and ideas
- **Code Review**: Request feedback on your changes

## Recognition

Contributors will be:

- Listed in AUTHORS.md
- Mentioned in release notes
- Invited to maintainer team (for significant contributions)

Thank you for contributing to PGraf Cypher! 🚀
