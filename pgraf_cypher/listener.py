import logging

import antlr4  # type: ignore

from pgraf_cypher import models, parsers
from pgraf_cypher.antlr import Cypher25Parser

LOGGER = logging.getLogger(__name__)


class CypherListener(antlr4.ParseTreeListener):
    def __init__(self) -> None:
        self._inside_exists = False
        self._query = models.CypherQuery()

    @property
    def query(self) -> models.CypherQuery:
        """Return the parsed Cypher query."""
        return self._query

    def enterReturnClause(
        self, ctx: Cypher25Parser.ReturnClauseContext
    ) -> None:
        self._query.return_clause = parsers.parse_return_clause(ctx)

    def enterExistsExpression(
        self, ctx: Cypher25Parser.ExistsExpressionContext
    ) -> None:
        """Mark that we're entering an EXISTS expression."""
        self._inside_exists = True

    def exitExistsExpression(
        self, ctx: Cypher25Parser.ExistsExpressionContext
    ) -> None:
        """Mark that we're exiting an EXISTS expression."""
        self._inside_exists = False

    def enterMatchClause(self, ctx: Cypher25Parser.MatchClauseContext) -> None:
        """Handle MATCH clauses."""
        if self._inside_exists:  # Dont process MATCH inside EXISTS expressions
            return
        match = parsers.parse_match_clause(ctx)
        if match.optional:
            self._query.optional_matches.append(match)
        else:
            self._query.match_patterns += match.patterns
        if match.where_expression:
            self._query.where.append(match.where_expression)

    def enterPattern(self, ctx: Cypher25Parser.PatternContext) -> None:
        pattern = parsers.parse_pattern(ctx)
        if not pattern:
            return
        # If this pattern has nodes with variables and we're processing
        # parenthesized patterns, store it for use in recursive CTE generation
        if pattern.elements and any(
            node.variable
            for element in pattern.elements
            for node in element.nodes
        ):
            self._query.parenthesized_patterns.append(pattern)

    def enterQuantifier(self, ctx: Cypher25Parser.QuantifierContext) -> None:
        self._query.quantifiers.append(parsers.parse_quantifier(ctx))

    def enterParenthesizedPath(
        self, ctx: Cypher25Parser.ParenthesizedPathContext
    ) -> None:
        self._query.parenthesized_paths.append(
            parsers.parse_parenthesized_path(ctx)
        )

    def enterWhereClause(self, ctx: Cypher25Parser.WhereClauseContext) -> None:
        """Handle standalone WHERE clauses, checking if this WHERE clause is
        part of a parent context (like MATCH). If so, it will be handled by
        the parent context

        """
        if (
            ctx.parentCtx
            and hasattr(ctx.parentCtx, '__class__')
            and isinstance(ctx.parentCtx, models.MatchClause)
        ):
            return
        where_clause = parsers.parse_where_clause(ctx)
        if where_clause and where_clause.expression:
            self._query.where.append(where_clause.expression)

    def enterWithClause(self, ctx: Cypher25Parser.WithClauseContext) -> None:
        """Handle WITH clauses."""
        with_clause = parsers.parse_with_clause(ctx)
        if with_clause:
            self._query.with_clauses.append(with_clause)

    def enterUnion(self, ctx: Cypher25Parser.UnionContext) -> None:
        """Handle UNION clauses."""
        union = parsers.parse_union(ctx)
        if union and len(union.single_queries) > 1:
            self._query.union = union
