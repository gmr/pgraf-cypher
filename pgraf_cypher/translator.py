import typing

import pydantic
from psycopg import sql

from pgraf_cypher import models


def snippet(value: str) -> sql.SQL:
    return sql.SQL(value)  # type: ignore


class Query(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    columns: list[sql.Composable] = pydantic.Field(default_factory=list)
    table_aliases: list[str] = pydantic.Field(default_factory=list)
    tables: list[sql.Composable] = pydantic.Field(default_factory=list)
    edge_labels: list[str] = pydantic.Field(default_factory=list)
    edge_direction: typing.Literal['incoming', 'outgoing', 'both'] = 'incoming'
    where: list[sql.Composable] = pydantic.Field(default_factory=list)
    group_by: list[sql.Identifier] = pydantic.Field(default_factory=list)
    order_by: list[tuple[sql.Identifier, typing.Literal['ASC', 'DESC']]] = (
        pydantic.Field(default_factory=list)
    )
    limit: int | None = None
    join_order: list[int] = pydantic.Field(default_factory=list)


class Translator:
    def __init__(
        self,
        schema: str = 'pgraf',
        nodes_table: str = 'nodes',
        edges_table: str = 'edges',
    ) -> None:
        self._schema = sql.Identifier(schema)
        self._nodes_table = sql.Identifier(nodes_table)
        self._edges_table = sql.Identifier(edges_table)

    def translate(
        self, cypher: models.CypherQuery
    ) -> tuple[sql.Composable, dict[str, typing.Any]]:
        # print(cypher.model_dump_json(indent=2))
        parameters: dict[str, typing.Any] = {}
        queries: list[tuple[sql.Composable, list[str]]] = []
        previous_where: list[sql.Composable] = []
        for _pattern_offset, pattern in enumerate(cypher.match_patterns):
            for _element_offset, element in enumerate(pattern.elements):
                query = Query()
                for _node_offset, node in enumerate(element.nodes):
                    if node.variable:
                        query.table_aliases.append(node.variable)
                    query.columns += [
                        snippet(f'{node.variable}.id AS {node.variable}_id'),
                        snippet(
                            f'{node.variable}.properties '
                            f'AS {node.variable}_properties'
                        ),
                        snippet(
                            f'{node.variable}.labels AS {node.variable}_labels'
                        ),
                        snippet(
                            f'{node.variable}.mimetype '
                            f'AS {node.variable}_mimetype'
                        ),
                        snippet(
                            f'{node.variable}.content '
                            f'AS {node.variable}_content'
                        ),
                    ]
                    if node.variable:
                        query.tables.append(
                            self._table_alias(self._nodes_table, node.variable)
                        )
                    for label in node.labels:
                        if label.startswith('`'):
                            label = label.strip('`')
                        query.where.append(
                            snippet(
                                f"{node.variable}.labels && ARRAY['{label}']"
                            )
                        )
                for relationship in element.relationships:
                    query.edge_labels = relationship.labels
                    query.edge_direction = relationship.direction
                for where in cypher.where:
                    for operand in where.operands:
                        if self._has_table(operand, query.table_aliases):
                            expr = self._process_expression(
                                operand, parameters
                            )
                            if expr not in previous_where:
                                query.where.append(expr)
                                previous_where.append(expr)
                queries.append(
                    (self._render_query(query), query.table_aliases)
                )

        if not queries:
            return sql.SQL('SELECT 1'), parameters
        elif len(queries) == 1:
            return queries[0][0], parameters

        cte_tables: dict[str, set[str]] = {}
        ctes = []
        for offset, (rendered_query, table_aliases) in enumerate(queries):
            name = f'cte_{offset}'
            cte_tables[name] = set(table_aliases)
            ctes.append(
                snippet(f'{name} AS (') + rendered_query + snippet(')')
            )

        final_query: sql.Composable = sql.SQL('WITH ') + sql.SQL(',\n').join(
            ctes
        )

        columns: list[sql.Composable] = []
        if getattr(cypher.return_clause, 'return_body', None):
            for item in cypher.return_clause.return_body.items:
                column_tables = self._expression_tables(item.expression)
                for cte, tables in cte_tables.items():
                    if tables.intersection(column_tables):
                        columns.append(
                            self._process_column(
                                cte, item.alias, item.expression
                            )
                        )

        join: list[sql.Composable] = []
        for where in cypher.where:
            for operand in where.operands:
                expr = self._process_expression(operand, parameters)
                if expr not in previous_where:
                    expr = self._process_expression(
                        operand, parameters, cte_tables
                    )
                    join.append(expr)
                    previous_where.append(expr)

        final_query += snippet('\n SELECT ')
        final_query += sql.SQL(', ').join(columns)

        for offset, cte in enumerate(cte_tables.keys()):
            if offset == 0:
                final_query += snippet(f' FROM {cte}')
            else:
                final_query += snippet(f' JOIN {cte} ON ')
                final_query += sql.SQL(' AND ').join(join)

        return final_query, parameters

    def _expression_tables(self, expr: models.ExpressionUnion) -> set[str]:
        tables: set[str] = set()
        if hasattr(expr, 'operands') and expr.operands:
            for operand in expr.operands:
                tables |= self._expression_tables(operand)
        elif isinstance(expr, models.FunctionExpression):
            for arg in expr.arguments:
                tables |= self._expression_tables(arg)
        elif isinstance(expr, models.PropertyAccessExpression):
            tables |= self._expression_tables(expr.object)
        elif isinstance(expr, models.LiteralExpression):
            pass
        elif isinstance(expr, models.ComparisonExpression):
            if expr.left:
                tables |= self._expression_tables(expr.left)
            if expr.right:
                tables |= self._expression_tables(expr.right)
        elif hasattr(expr, 'type') and hasattr(expr, 'name'):
            tables.add(expr.name)
        else:
            raise TypeError(f'Unsupported expression type: {expr}')
        return tables

    def _has_table(
        self, expr: models.ExpressionUnion, tables: list[str]
    ) -> bool:
        # expr is always a single expression, not a list
        if hasattr(expr, 'type') and hasattr(expr, 'name'):
            return expr.name in tables
        if hasattr(expr, 'operands') and expr.operands:
            return all(
                self._has_table(operand, tables) for operand in expr.operands
            )
        elif hasattr(expr, 'left') and hasattr(expr.left, 'object'):
            return expr.left.object.name in tables
        elif hasattr(expr, 'right') and hasattr(expr.right, 'object'):
            return expr.left.object.name in tables
        elif hasattr(expr, 'object'):
            return expr.object.name in tables
        elif isinstance(expr, models.LiteralExpression):
            return True
        return False

    @staticmethod
    def _process_column(
        cte_name: str, alias: str | None, expression: models.ExpressionUnion
    ) -> sql.SQL:
        if expression.type == models.ExpressionType.VARIABLE:
            value = snippet(f'{cte_name}.{expression.name}_properties')
        elif expression.type == models.ExpressionType.PROPERTY_ACCESS:
            value = snippet(
                f"{cte_name}.{expression.object.name}_properties->>'{expression.property}'"
            )
            if alias is None:
                alias = f'{expression.object.name}_{expression.property}'
        elif expression.type == models.ExpressionType.FUNCTION:
            if len(expression.arguments) == 1:
                value = snippet(
                    f'{cte_name}.{expression.arguments[0].name}_{expression.name}'
                )
            else:
                raise ValueError('Multiple arguments not supported')
        else:
            raise TypeError(f'Unsupported expression type: {expression.type}')
        if alias is not None:
            return snippet(f'{value.as_string()} AS {alias}')
        return value

    def _process_expression(
        self,
        expression: models.ExpressionUnion,
        parameters: dict[str, typing.Any],
        cte_tables: dict[str, set[str]] | None = None,
    ) -> sql.Composable:
        temp: list[sql.Composable] = []
        if expression.type == models.ExpressionType.OPERATOR:
            for operand in expression.operands:
                temp.append(
                    self._process_expression(operand, parameters, cte_tables)
                )
            return snippet(f' {expression.operator} ').join(temp)

        elif expression.type == models.ExpressionType.COMPARISON:
            operator = (
                expression.operator[0]
                if isinstance(expression.operator, list)
                else expression.operator
            )
            if expression.operands:
                for operand in expression.operands:
                    temp.append(
                        self._process_expression(
                            operand, parameters, cte_tables
                        )
                    )
                joined_operands = snippet(f' {operator} ').join(temp)
                return joined_operands

            if (
                expression.left
                and expression.left.type
                == models.ExpressionType.PROPERTY_ACCESS
            ):
                cte = self._cte_name(cte_tables, expression.left.object.name)
                if cte:
                    temp.append(
                        snippet(
                            f"{cte}.{expression.left.object.name}_properties->>'{expression.left.property}'"
                        )
                    )
                else:
                    temp.append(
                        snippet(
                            f"{expression.left.object.name}.properties->>'{expression.left.property}'"
                        )
                    )
            else:
                raise TypeError(f'Unsupported expression type: {expression}')

            if (
                expression.right
                and expression.right.type == models.ExpressionType.LITERAL
            ):
                value = expression.right.value
                if not value:
                    raise ValueError(
                        f'Literal expression has no value: {expression.right}'
                    )
            else:
                raise TypeError(f'Unsupported expression type: {expression}')

            val = value.value
            if expression.operator == 'CONTAINS':
                temp.append(snippet(' ILIKE '))
                val = f'%{value.value}%'
            elif expression.operator == 'STARTS WITH':
                temp.append(snippet(' ILIKE '))
                val = f'{value.value}%'
            elif expression.operator == 'ENDS WITH':
                temp.append(snippet(' ILIKE '))
                val = f'%{value.value}'
            elif expression.operator in {
                '=',
                '!=',
                '<>',
                '<=',
                '>=',
                '<',
                '>',
                '~=',
            }:
                temp.append(snippet(f' {expression.operator} '))
            elif expression.operator in {'IS NULL', 'IS NOT NULL'}:
                temp.append(snippet(f' {expression.operator} '))
                val = None
            else:
                raise TypeError(f'Unsupported operator: {expression.operator}')

            if val:
                param = self._parameter_name(parameters, str(val))
                parameters[param] = val
                temp.append(sql.Placeholder(param))
            return sql.Composed(temp)

        elif expression.type == models.ExpressionType.LITERAL:
            if not expression.value:
                return sql.SQL('NULL')
            if expression.value.type == 'string':
                param = self._parameter_name(
                    parameters, str(expression.value.value)
                )
                parameters[param] = expression.value.value
                return sql.Placeholder(param)
            else:
                return snippet(str(expression.value.value))

        elif expression.type == models.ExpressionType.PROPERTY_ACCESS:
            cte = self._cte_name(cte_tables, expression.object.name)
            if cte:
                return snippet(
                    f"{cte}.{expression.object.name}_properties->>'{expression.property}'"
                )
            return snippet(
                f"{expression.object.name}.properties->>'{expression.property}'"
            )

        elif expression.type == models.ExpressionType.VARIABLE:
            cte = self._cte_name(cte_tables, expression.name)
            if cte:
                return snippet(f'{cte}.{expression.name}_id')
            return snippet(f'{expression.name}.id')

        elif expression.type == models.ExpressionType.EXISTS:
            pass

        raise TypeError(f'Unsupported operand type: {expression.type}')

    @staticmethod
    def _cte_name(
        cte_tables: dict[str, set[str]] | None, table: str
    ) -> str | None:
        if not cte_tables:
            return None
        for name, tables in cte_tables.items():
            if table in tables:
                return name
        return None

    @staticmethod
    def _render_query(query: Query) -> sql.Composed:
        """Render the SQL statement for the given query."""
        statement: sql.Composable = snippet('SELECT ')
        statement += sql.SQL(', ').join(query.columns)
        statement += snippet(' FROM ')
        for offset, table in enumerate(query.tables):
            if offset > 0:
                statement += snippet(' JOIN ')
            statement += table
            if offset > 0 and query.edge_labels:
                if query.edge_direction == 'incoming':
                    statement += snippet(' ON edges.source = ')
                elif query.edge_direction == 'outgoing':
                    statement += snippet(' ON edges.target = ')
                else:
                    statement += snippet('ON edges.source = edges.target = ')
                statement += snippet(query.table_aliases[offset] + '.id ')
            elif query.edge_labels:
                statement += snippet(' JOIN ')
                statement += snippet('pgraf.edges AS edges ')
                if query.edge_direction == 'incoming':
                    statement += snippet('ON edges.target = ')
                elif query.edge_direction == 'outgoing':
                    statement += snippet(' ON edges.source = ')
                else:
                    statement += snippet(' ON edges.source = edges.target = ')
                statement += snippet(query.table_aliases[offset] + '.id ')
                for label in query.edge_labels:
                    if label.startswith('`'):
                        label = label.strip('`')
                    statement += snippet(
                        f"AND edges.labels && ARRAY['{label}'] "
                    )
        if query.where:
            statement += sql.SQL(' WHERE ')
            statement += sql.SQL(' AND ').join(query.where)
        return statement

    @staticmethod
    def _needs_recursive_cte(query: models.CypherQuery) -> bool:
        """Check if the query requires a recursive CTE."""
        for quantifier in query.quantifiers:
            if (
                quantifier
                and quantifier.to_value is not None
                and quantifier.to_value > 1
            ):
                return True
        for pattern in query.match_patterns:
            for element in pattern.elements:
                for rel in element.relationships:
                    if rel.path_length and (
                        (rel.path_length.get('max') or 1) > 1
                        or (rel.path_length.get('min') or 1) > 1
                    ):
                        return True
        return False

    @staticmethod
    def _needs_shortest_path(query: models.CypherQuery) -> bool:
        """Check if the query requires shortest path computation."""
        for pattern in query.match_patterns:
            if pattern.variable == 'SHORTEST_PATH':
                return True
        return bool(
            query.parenthesized_patterns
            and any(
                p.variable == 'SHORTEST_PATH'
                for p in query.parenthesized_patterns
            )
        )

    @staticmethod
    def _parameter_name(
        parameters: dict[str, typing.Any], value_in: str
    ) -> str:
        for key, value in parameters.items():
            if value == value_in:
                return key
        return f'p{len(parameters.keys())}'

    def _table_alias(
        self, table: sql.Identifier, alias: str
    ) -> sql.Composable:
        return sql.Composed(
            [
                self._schema,
                sql.SQL('.'),
                table,
                sql.SQL(' AS '),
                sql.Identifier(alias),
            ]
        )
