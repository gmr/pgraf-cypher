import logging
import typing

import antlr4
from psycopg import sql

from pgraf_cypher import models, parsers
from pgraf_cypher.antlr import Cypher25Parser

LOGGER = logging.getLogger(__name__)


class CypherToSQL(antlr4.ParseTreeListener):
    def __init__(self,
                 schema: str = 'pgraf',
                 nodes_table: str = 'nodes',
                 edges_table: str = 'edges') -> None:
        self._ctes: list[sql.Composable] = []
        self._schema = sql.Identifier(schema)
        self._edges_table = sql.Identifier(edges_table)
        self._nodes_table = sql.Identifier(nodes_table)
        self._matches: list[models.Pattern] = []
        self._parameters: set[str] = set()
        self._where: list[models.Expression] = []

    def translate(self) -> tuple[str, dict[str, typing.Any]]:
        """Return the SQL statement and parameters."""
        value: list[sql.Composable] = [sql.SQL('SELECT ')]
        variables = [
            'a',
            'b',
            'c',
            'd',
            'e',
            'f',
            'g',
            'h',
            'i',
            'j',
            'k',
            'l',
            'm',
        ]

        where: list[list[sql.Composable]] = []
        parameters: dict[str, typing.Any] = {}
        for pattern in self._matches:
            for element in pattern.elements:
                for node in element.nodes:
                    if node.variable:
                        prefix = sql.Identifier(node.variable)
                    else:
                        prefix = sql.Identifier(variables.pop(0))
                    value.append(prefix)
                    value.append(sql.SQL('.*'))
                    for key, val in (node.properties or {}).items():
                        parameter_name = self._parameter_name()
                        parameters[parameter_name] = val
                        where.append(
                            [prefix,
                             sql.SQL('.'),
                             sql.Identifier('properties'),
                             sql.SQL('->>'),
                             sql.Literal(key),
                             sql.SQL(' = '),
                             sql.Placeholder(parameter_name)])
                    for label in node.labels or []:
                        parameter_name = self._parameter_name()
                        parameters[parameter_name] = label
                        where.append([
                            prefix,
                            sql.SQL('.'),
                            sql.Identifier('labels'),
                            sql.SQL(' = ANY('),
                            sql.Placeholder(parameter_name),
                            sql.SQL(')')
                        ])
                    value.append(sql.SQL(' FROM '))
                    value += self._table_alias(self._nodes_table, node.variable)
                    if where:
                        value.append(sql.SQL(' WHERE '))
                        temp = [sql.Composed(expr) for expr in where]
                        value.append(sql.SQL(' AND ').join(temp))
        return sql.Composed(value).as_string(), parameters

    def _parameter_name(self) -> str:
        name = f'p{len(self._parameters)}'
        self._parameters.add(name)
        return name

    def _table_alias(self, table: sql.Identifier, alias: str) -> sql.Composable:
        return sql.Composed([
            self._schema,
            sql.SQL('.'),
            table,
            sql.SQL(' AS '),
            sql.Identifier(alias)
        ])



    def _build_cte_statement(self, pattern: models.Pattern) -> sql.Composable:
        print(f'In build CTE ', pattern)

    def enterMatchClause(self, ctx: Cypher25Parser.MatchClauseContext) -> None:
        patterns = []
        if ctx.patternList():
            for value in ctx.patternList().pattern():
                patterns.append(parsers.pattern(value))
        self._matches += patterns

    def enterWhereClause(
        self, ctx: Cypher25Parser.WhereClauseContext
    ) -> None:
        if ctx.expression():
            self._where.append(parsers.Expression().parse(ctx.expression()))
