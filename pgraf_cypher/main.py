import contextlib
import logging
import typing

import antlr4  # type: ignore
import psycopg
import pydantic
import sqlparse  # type: ignore
from pgraf import postgres

from pgraf_cypher import antlr, listener, models, translator

LOGGER = logging.getLogger(__name__)

Model = typing.TypeVar('Model', bound=pydantic.BaseModel)
AsyncCursor = psycopg.AsyncCursor[Model | tuple[typing.Any, ...]]


class PGrafCypher:
    """Add Cypher language support to pgraf"""

    def __init__(
        self,
        url: pydantic.PostgresDsn,
        schema: str = 'pgraf',
        node_table: str = 'nodes',
        edges_table: str = 'edges',
        pool_min_size: int = 1,
        pool_max_size: int = 10,
    ) -> None:
        self._translator = translator.Translator(
            schema, node_table, edges_table
        )
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
        cypher = self._convert(query)
        sql, params = self._translator.translate(cypher)
        LOGGER.debug('SQL: %s', sql)
        LOGGER.debug('Params: %s', params)
        async with self._postgres.execute(sql, params, row_class) as cursor:
            yield cursor

    def translate(
        self, query: str, pretty: bool = False
    ) -> tuple[str, dict[str, typing.Any]]:
        """
        Parse a Cypher query and translate it to a PostgreSQL query.

        Args:
            query: The Cypher query string
            pretty: Pretty print the resulting query

        Returns:
            The converted PostgreSQL query string

        """
        cypher = self._convert(query)
        sql, params = self._translator.translate(cypher)
        if pretty:
            return sqlparse.format(
                sql.as_string(), 'UTF-8', reindent=True, keyword_case='upper'
            ), params
        return sql.as_string(), params

    @staticmethod
    def _convert(query: str) -> models.CypherQuery:
        """
        Parse a Cypher query and translate it to a PostgreSQL query.
        """
        cypher = query.strip()
        if not cypher:
            raise ValueError('Empty query')
        parser = antlr.Cypher25Parser(
            antlr4.CommonTokenStream(
                antlr.Cypher25Lexer(antlr4.InputStream(cypher))
            )
        )
        tree = parser.statements()
        walker = antlr4.ParseTreeWalker()
        converter = listener.CypherListener()
        walker.walk(converter, tree)
        return converter.query
