import contextlib
import logging
import re
import typing

import antlr4
import psycopg
import pydantic
from pgraf import postgres

from pgraf_cypher import antlr, to_sql

Model = typing.TypeVar('Model', bound=pydantic.BaseModel)
AsyncCursor = psycopg.AsyncCursor[Model | tuple[typing.Any, ...]]


class PGrafCypher:
    """Add Cypher language support to pgraf"""

    def __init__(
        self,
        url: pydantic.PostgresDsn,
        schema: str = 'pgraf',
        pool_min_size: int = 1,
        pool_max_size: int = 10,
    ) -> None:
        self._schema = schema
        self._postgres = postgres.Postgres(url, pool_min_size, pool_max_size)

    async def initialize(self) -> None:
        """Ensure the database is connected and ready to go."""
        await self._postgres.initialize()

    async def aclose(self) -> None:
        """Close the Postgres connection pool."""
        await self._postgres.aclose()

    @contextlib.asynccontextmanager
    async def execute(
        self, query: str, row_class: type[pydantic.BaseModel] | None = None
    ) -> typing.AsyncIterator[AsyncCursor]:
        """
        Execute a Cypher query against the pgraf database.

        """
        sql, parameters = self.translate(query)
        async with self._postgres.execute(
            sql, parameters, row_class
        ) as cursor:
            yield cursor

    @staticmethod
    def translate(query: str) -> tuple[str, dict[str, typing.Any]]:
        """
        Parse a Cypher query and translate it to a PostgreSQL query.

        Args:
            query: The Cypher query string

        Returns:
            A SQL Composable object representing the equivalent PostgreSQL
            query
        """
        # Preprocess query for special patterns that ANTLR doesn't handle well
        preprocessed_query = query.strip()
        if not preprocessed_query:
            raise ValueError('Empty query')

        # Handle raw SHORTEST_PATH queries by wrapping them in MATCH
        if preprocessed_query.startswith('SHORTEST_PATH('):
            preprocessed_query = f'MATCH {preprocessed_query}'

        parser = antlr.Cypher25Parser(
            antlr4.CommonTokenStream(
                antlr.Cypher25Lexer(antlr4.InputStream(preprocessed_query))
            )
        )
        tree = parser.statements()
        walker = antlr4.ParseTreeWalker()
        converter = to_sql.CypherToSQL()
        walker.walk(converter, tree)
        query, parameters = converter.translate()
        return re.sub(r'\s+', ' ', query).strip(), parameters


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    query1 = """\
    MATCH (u1:User {email: "foo@aweber.com"})-[:author]->(m1:SlackMessage)
    MATCH (u2:User {email: "bar@aweber.com"})-[:author]->(m2:SlackMessage)
    WHERE m1.thread_ts = m2.thread_ts
      AND m1 <> m2
      AND NOT EXISTS {
        MATCH (m1)-[:channel]->(:SlackChannel {name: "@privatedm"})
      }
      AND NOT EXISTS {
        MATCH (m2)-[:channel]->(:SlackChannel {name: "@privatedm"})
      }
    RETURN m1, m2
    ORDER BY m1.ts DESC
    LIMIT 100        
    """
    print(PGrafCypher.translate(query1))
