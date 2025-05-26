"""Tests for pgraf_cypher.parsers module."""

import unittest
from unittest.mock import Mock

from pgraf_cypher import models
from pgraf_cypher.antlr import Cypher25Parser
from pgraf_cypher.parsers import (
    parse_call_clause,
    parse_expression,
    parse_filter_clause,
    parse_label_expression,
    parse_limit,
    parse_literal,
    parse_match_clause,
    parse_merge_clause,
    parse_node_pattern,
    parse_node_properties,
    parse_order_by,
    parse_pattern,
    parse_regular_query,
    parse_return_clause,
    parse_set_clause,
    parse_skip,
    parse_statement,
    parse_unwind_clause,
    parse_where_clause,
    parse_with_clause,
)


class TestExpression(unittest.TestCase):
    """Test cases for Expression parser function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_expression(None)
        self.assertEqual(result.type, models.ExpressionType.EMPTY)

    def test_literal_parsing(self):
        """Test literal value parsing."""
        # Test numeric literal
        ctx = Mock(spec=Cypher25Parser.NummericLiteralContext)
        ctx.getText.return_value = '42'
        result = parse_literal(ctx)
        self.assertEqual(result.type, 'integer')
        self.assertEqual(result.value, '42')

        # Test float literal
        ctx.getText.return_value = '3.14'
        result = parse_literal(ctx)
        self.assertEqual(result.type, 'float')
        self.assertEqual(result.value, '3.14')

        # Test string literal
        ctx = Mock(spec=Cypher25Parser.StringLiteralContext)
        ctx.getText.return_value = '"hello"'
        result = parse_literal(ctx)
        self.assertEqual(result.type, 'string')
        self.assertEqual(result.value, 'hello')

        # Test boolean literal
        ctx = Mock(spec=Cypher25Parser.BooleanLiteralContext)
        ctx.getText.return_value = 'true'
        result = parse_literal(ctx)
        self.assertEqual(result.type, 'boolean')
        self.assertEqual(result.value, True)

        ctx.getText.return_value = 'false'
        result = parse_literal(ctx)
        self.assertEqual(result.type, 'boolean')
        self.assertEqual(result.value, False)


class TestLabelExpression(unittest.TestCase):
    """Test cases for label expression parser function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_label_expression(None)
        self.assertEqual(result, [])

    def test_parse_single_label(self):
        """Test parsing a single label."""
        ctx = Mock(spec=Cypher25Parser.LabelExpressionContext)
        ctx.labelExpression4.return_value = Mock()
        label_expr4 = ctx.labelExpression4.return_value
        label_expr4.labelExpression3.return_value = [Mock()]
        label_expr3 = label_expr4.labelExpression3.return_value[0]
        label_expr3.labelExpression2.return_value = [Mock()]
        label_expr2 = label_expr3.labelExpression2.return_value[0]
        label_expr2.EXCLAMATION_MARK.return_value = None
        label_expr2.labelExpression1.return_value = Mock(
            spec=Cypher25Parser.LabelNameContext
        )
        label_expr1 = label_expr2.labelExpression1.return_value
        label_expr1.symbolicNameString.return_value = Mock()
        label_expr1.symbolicNameString.return_value.getText.return_value = (
            'Person'
        )

        result = parse_label_expression(ctx)
        self.assertEqual(result, ['Person'])

    def test_parse_any_label(self):
        """Test parsing ANY_LABEL."""
        ctx = Mock(spec=Cypher25Parser.LabelExpressionContext)
        ctx.labelExpression4.return_value = Mock()
        label_expr4 = ctx.labelExpression4.return_value
        label_expr4.labelExpression3.return_value = [Mock()]
        label_expr3 = label_expr4.labelExpression3.return_value[0]
        label_expr3.labelExpression2.return_value = [Mock()]
        label_expr2 = label_expr3.labelExpression2.return_value[0]
        label_expr2.EXCLAMATION_MARK.return_value = None
        label_expr2.labelExpression1.return_value = Mock(
            spec=Cypher25Parser.AnyLabelContext
        )

        result = parse_label_expression(ctx)
        self.assertEqual(result, ['ANY_LABEL'])

    def test_parse_not_label(self):
        """Test parsing NOT label."""
        ctx = Mock(spec=Cypher25Parser.LabelExpressionContext)
        ctx.labelExpression4.return_value = Mock()
        label_expr4 = ctx.labelExpression4.return_value
        label_expr4.labelExpression3.return_value = [Mock()]
        label_expr3 = label_expr4.labelExpression3.return_value[0]
        label_expr3.labelExpression2.return_value = [Mock()]
        label_expr2 = label_expr3.labelExpression2.return_value[0]
        label_expr2.EXCLAMATION_MARK.return_value = Mock()  # NOT operator
        label_expr2.labelExpression1.return_value = Mock(
            spec=Cypher25Parser.LabelNameContext
        )
        label_expr1 = label_expr2.labelExpression1.return_value
        label_expr1.symbolicNameString.return_value = Mock()
        label_expr1.symbolicNameString.return_value.getText.return_value = (
            'Person'
        )

        result = parse_label_expression(ctx)
        self.assertEqual(result, ['NOT Person'])


class TestNodeProperties(unittest.TestCase):
    """Test cases for parse_node_properties function."""

    def test_empty_properties(self):
        """Test with None context."""
        result = parse_node_properties(None)
        self.assertEqual(result, {})

    def test_with_properties(self):
        """Test parsing properties map."""
        # Test structure by checking empty properties returns empty dict
        # and that the function handles missing map correctly
        ctx = Mock(spec=Cypher25Parser.PropertiesContext)
        ctx.map.return_value = None
        result = parse_node_properties(ctx)
        self.assertEqual(result, {})


class TestNodePattern(unittest.TestCase):
    """Test cases for parse_node_pattern function."""

    def test_simple_node_pattern(self):
        """Test parsing a simple node pattern."""
        ctx = Mock(spec=Cypher25Parser.NodePatternContext)
        ctx.variable.return_value = Mock()
        ctx.variable.return_value.getText.return_value = 'n'
        ctx.labelExpression.return_value = None
        ctx.properties.return_value = None
        ctx.expression.return_value = None

        result = parse_node_pattern(ctx)
        self.assertEqual(result.variable, 'n')
        self.assertEqual(result.labels, [])
        self.assertEqual(result.properties, {})
        self.assertIsNone(result.where_expression)

    def test_node_pattern_with_labels(self):
        """Test parsing node pattern with labels."""
        ctx = Mock(spec=Cypher25Parser.NodePatternContext)
        ctx.variable.return_value = Mock()
        ctx.variable.return_value.getText.return_value = 'n'
        ctx.labelExpression.return_value = Mock()
        ctx.properties.return_value = None
        ctx.expression.return_value = None

        # Mock label expression parsing
        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_label_expression'
        ) as mock_label_parser:
            mock_label_parser.return_value = ['Person']
            result = parse_node_pattern(ctx)

        self.assertEqual(result.variable, 'n')
        self.assertEqual(result.labels, ['Person'])


class TestPattern(unittest.TestCase):
    """Test cases for parse_pattern function."""

    def test_simple_pattern(self):
        """Test parsing a simple pattern."""
        ctx = Mock(spec=Cypher25Parser.PatternContext)
        ctx.variable.return_value = None
        ctx.selector.return_value = None  # Mock the selector method
        ctx.anonymousPattern.return_value = Mock()
        anon_pattern = ctx.anonymousPattern.return_value
        anon_pattern.patternElement.return_value = Mock()
        pattern_element = anon_pattern.patternElement.return_value
        # Mock getText to return a string instead of Mock
        pattern_element.getText.return_value = '(n)'
        pattern_element.nodePattern.return_value = [Mock()]
        node_ctx = pattern_element.nodePattern.return_value[0]
        node_ctx.variable.return_value = Mock()
        node_ctx.variable.return_value.getText.return_value = 'n'
        node_ctx.labelExpression.return_value = None
        node_ctx.properties.return_value = None
        node_ctx.expression.return_value = None

        result = parse_pattern(ctx)
        self.assertIsNone(result.variable)
        self.assertEqual(len(result.elements), 1)
        self.assertEqual(len(result.elements[0].nodes), 1)
        self.assertEqual(result.elements[0].nodes[0].variable, 'n')


class TestStatement(unittest.TestCase):
    """Test cases for parse_statement function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_statement(None)
        self.assertIsNone(result.command)
        self.assertIsNone(result.regular_query)

    def test_parse_command_statement(self):
        """Test parsing a command statement."""
        ctx = Mock(spec=Cypher25Parser.StatementContext)
        ctx.command.return_value = Mock()
        ctx.command.return_value.getText.return_value = 'CREATE INDEX'
        ctx.regularQuery.return_value = None

        result = parse_statement(ctx)
        self.assertEqual(result.command, 'CREATE INDEX')
        self.assertIsNone(result.regular_query)

    def test_parse_regular_query_with_union(self):
        """Test parsing a regular query with union."""
        ctx = Mock(spec=Cypher25Parser.StatementContext)
        ctx.command.return_value = None
        ctx.regularQuery.return_value = Mock()
        regular_query_ctx = ctx.regularQuery.return_value
        regular_query_ctx.union.return_value = Mock()
        regular_query_ctx.when.return_value = None

        # Mock union context
        union_ctx = regular_query_ctx.union.return_value
        union_ctx.singleQuery.return_value = []
        union_ctx.children = []

        result = parse_statement(ctx)
        self.assertIsNone(result.command)
        self.assertIsNotNone(result.regular_query)
        self.assertIsNotNone(result.regular_query.union)
        self.assertIsNone(result.regular_query.when)

    def test_parse_regular_query_with_when(self):
        """Test parsing a regular query with when clause."""
        ctx = Mock(spec=Cypher25Parser.StatementContext)
        ctx.command.return_value = None
        ctx.regularQuery.return_value = Mock()
        regular_query_ctx = ctx.regularQuery.return_value
        regular_query_ctx.union.return_value = None
        regular_query_ctx.when.return_value = Mock()
        when_ctx = regular_query_ctx.when.return_value
        when_ctx.whenBranch.return_value = []  # Empty when branch list
        when_ctx.elseBranch.return_value = None

        result = parse_statement(ctx)

        self.assertIsNone(result.command)
        self.assertIsNotNone(result.regular_query)
        self.assertIsNone(result.regular_query.union)
        self.assertIsNotNone(result.regular_query.when)


class TestRegularQuery(unittest.TestCase):
    """Test cases for parse_regular_query function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_regular_query(None)
        self.assertIsNone(result.union)
        self.assertIsNone(result.when)

    def test_parse_union_query(self):
        """Test parsing a union query."""
        ctx = Mock(spec=Cypher25Parser.RegularQueryContext)
        ctx.union.return_value = Mock()
        ctx.when.return_value = None
        union_ctx = ctx.union.return_value
        union_ctx.singleQuery.return_value = [Mock(), Mock()]

        # Mock children with proper getText methods
        child1 = Mock()
        child1.getText.return_value = 'query1'
        child2 = Mock()
        child2.getText.return_value = 'UNION'
        child3 = Mock()
        child3.getText.return_value = 'ALL'
        child4 = Mock()
        child4.getText.return_value = 'query2'
        union_ctx.children = [child1, child2, child3, child4]

        # Mock single query parsing
        for single_query_mock in union_ctx.singleQuery.return_value:
            single_query_mock.clause.return_value = []
            single_query_mock.useClause.return_value = None
            single_query_mock.regularQuery.return_value = None

        result = parse_regular_query(ctx)
        self.assertIsNotNone(result.union)
        self.assertIsNone(result.when)
        self.assertEqual(len(result.union.single_queries), 2)
        self.assertEqual(result.union.union_type, 'ALL')

    def test_parse_when_query(self):
        """Test parsing a when query."""
        ctx = Mock(spec=Cypher25Parser.RegularQueryContext)
        ctx.union.return_value = None
        ctx.when.return_value = Mock()
        when_ctx = ctx.when.return_value
        when_ctx.whenBranch.return_value = [Mock()]
        when_ctx.elseBranch.return_value = None

        # Mock when branch
        when_branch_mock = when_ctx.whenBranch.return_value[0]
        when_branch_mock.expression.return_value = Mock()
        when_branch_mock.singleQuery.return_value = Mock()
        when_branch_mock.singleQuery.return_value.clause.return_value = []
        when_branch_mock.singleQuery.return_value.useClause.return_value = None
        when_branch_mock.singleQuery.return_value.regularQuery.return_value = (
            None
        )

        # Mock the Expression parser
        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr_parser:
            mock_expr_parser.return_value = models.VariableExpression(
                name='test'
            )
            result = parse_regular_query(ctx)

        self.assertIsNone(result.union)
        self.assertIsNotNone(result.when)
        self.assertEqual(len(result.when.when_branches), 1)
        self.assertIsNone(result.when.else_branch)


class TestOrderBy(unittest.TestCase):
    """Test cases for parse_order_by function."""

    def test_parse_order_by(self):
        """Test parsing ORDER BY clause."""
        ctx = Mock(spec=Cypher25Parser.OrderByContext)
        order_item1 = Mock()
        order_item1.expression.return_value = Mock()
        order_item1.ascToken.return_value = Mock()
        order_item1.descToken.return_value = None

        order_item2 = Mock()
        order_item2.expression.return_value = Mock()
        order_item2.ascToken.return_value = None
        order_item2.descToken.return_value = Mock()

        ctx.orderItem.return_value = [order_item1, order_item2]

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.VariableExpression(name='test')
            result = parse_order_by(ctx)

        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].direction, 'ASC')
        self.assertEqual(result.items[1].direction, 'DESC')


class TestLimit(unittest.TestCase):
    """Test cases for parse_limit function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        ctx = Mock(spec=Cypher25Parser.LimitContext)
        ctx.expression.return_value = None
        result = parse_limit(ctx)
        self.assertEqual(result.expression.type, models.ExpressionType.EMPTY)

    def test_parse_limit(self):
        """Test parsing LIMIT clause."""
        ctx = Mock(spec=Cypher25Parser.LimitContext)
        ctx.expression.return_value = Mock()

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.LiteralExpression(
                value=models.LiteralValue(type='integer', value=10)
            )
            result = parse_limit(ctx)

        self.assertEqual(result.expression.type, models.ExpressionType.LITERAL)


class TestSkip(unittest.TestCase):
    """Test cases for parse_skip function."""

    def test_parse_skip(self):
        """Test parsing SKIP clause."""
        ctx = Mock(spec=Cypher25Parser.SkipContext)
        ctx.expression.return_value = Mock()

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.LiteralExpression(
                value=models.LiteralValue(type='integer', value=5)
            )
            result = parse_skip(ctx)

        self.assertEqual(result.expression.type, models.ExpressionType.LITERAL)


class TestWithClause(unittest.TestCase):
    """Test cases for parse_with_clause function."""

    def test_parse_with_clause(self):
        """Test parsing WITH clause."""
        ctx = Mock(spec=Cypher25Parser.WithClauseContext)
        ctx.returnBody.return_value = Mock()
        ctx.whereClause.return_value = None

        return_body_ctx = ctx.returnBody.return_value
        return_body_ctx.DISTINCT.return_value = None
        return_body_ctx.returnItems.return_value = Mock()
        return_body_ctx.returnItems.return_value.returnItem.return_value = []
        return_body_ctx.orderBy.return_value = None
        return_body_ctx.skip.return_value = None
        return_body_ctx.limit.return_value = None

        result = parse_with_clause(ctx)
        self.assertIsInstance(result, models.WithClause)
        self.assertIsNone(result.where_expression)


class TestMergeClause(unittest.TestCase):
    """Test cases for parse_merge_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_merge_clause(None)
        self.assertIsInstance(result.pattern, models.Pattern)
        self.assertEqual(len(result.actions), 0)

    def test_parse_merge_clause(self):
        """Test parsing MERGE clause."""
        ctx = Mock(spec=Cypher25Parser.MergeClauseContext)
        ctx.pattern.return_value = Mock()
        ctx.mergeAction.return_value = []

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_pattern'
        ) as mock_pattern:
            mock_pattern.return_value = models.Pattern(elements=[])
            result = parse_merge_clause(ctx)

        self.assertIsInstance(result, models.MergeClause)
        self.assertEqual(len(result.actions), 0)


class TestFilterClause(unittest.TestCase):
    """Test cases for parse_filter_clause function."""

    def test_parse_filter_clause(self):
        """Test parsing FILTER clause."""
        ctx = Mock(spec=Cypher25Parser.FilterClauseContext)
        ctx.expression.return_value = Mock()

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.VariableExpression(name='x')
            result = parse_filter_clause(ctx)

        self.assertEqual(
            result.expression.type, models.ExpressionType.VARIABLE
        )


class TestSetClause(unittest.TestCase):
    """Test cases for parse_set_clause function."""

    def test_parse_set_clause(self):
        """Test parsing SET clause."""
        ctx = Mock(spec=Cypher25Parser.SetClauseContext)
        set_item_mock = Mock()
        set_item_mock.propertyExpression.return_value = Mock()
        set_item_mock.propertyExpression.return_value.getText.return_value = (
            'n.name'
        )
        set_item_mock.expression.return_value = Mock()
        ctx.setItem.return_value = [set_item_mock]

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.LiteralExpression(
                value=models.LiteralValue(type='string', value='"John"')
            )
            result = parse_set_clause(ctx)

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].type, 'SET_PROP')


class TestMatchClause(unittest.TestCase):
    """Test cases for parse_match_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_match_clause(None)
        self.assertFalse(result.optional)
        self.assertIsNone(result.match_mode)
        self.assertEqual(len(result.patterns), 0)
        self.assertEqual(len(result.hints), 0)
        self.assertIsNone(result.where_expression)

    def test_parse_match_clause(self):
        """Test parsing MATCH clause."""
        ctx = Mock(spec=Cypher25Parser.MatchClauseContext)
        ctx.OPTIONAL.return_value = None
        ctx.matchMode.return_value = None
        ctx.patternList.return_value = Mock()
        ctx.patternList.return_value.pattern.return_value = []
        ctx.hint.return_value = []
        ctx.whereClause.return_value = None

        result = parse_match_clause(ctx)
        self.assertIsInstance(result, models.MatchClause)
        self.assertFalse(result.optional)


class TestReturnClause(unittest.TestCase):
    """Test cases for parse_return_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_return_clause(None)
        self.assertIsInstance(result.return_body, models.ReturnBody)

    def test_parse_return_clause(self):
        """Test parsing RETURN clause."""
        ctx = Mock(spec=Cypher25Parser.ReturnClauseContext)
        ctx.returnBody.return_value = Mock()
        return_body_ctx = ctx.returnBody.return_value
        return_body_ctx.DISTINCT.return_value = None
        return_body_ctx.returnItems.return_value = Mock()
        return_body_ctx.returnItems.return_value.returnItem.return_value = []
        return_body_ctx.orderBy.return_value = None
        return_body_ctx.skip.return_value = None
        return_body_ctx.limit.return_value = None

        result = parse_return_clause(ctx)
        self.assertIsInstance(result, models.ReturnClause)


class TestWhereClause(unittest.TestCase):
    """Test cases for parse_where_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_where_clause(None)
        self.assertEqual(result.expression.type, models.ExpressionType.EMPTY)

    def test_parse_where_clause(self):
        """Test parsing WHERE clause."""
        ctx = Mock(spec=Cypher25Parser.WhereClauseContext)
        ctx.expression.return_value = Mock()

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.VariableExpression(name='x')
            result = parse_where_clause(ctx)

        self.assertEqual(
            result.expression.type, models.ExpressionType.VARIABLE
        )


class TestUnwindClause(unittest.TestCase):
    """Test cases for parse_unwind_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_unwind_clause(None)
        self.assertEqual(result.expression.type, models.ExpressionType.EMPTY)
        self.assertEqual(result.variable, '')

    def test_parse_unwind_clause(self):
        """Test parsing UNWIND clause."""
        ctx = Mock(spec=Cypher25Parser.UnwindClauseContext)
        ctx.expression.return_value = Mock()
        ctx.variable.return_value = Mock()
        ctx.variable.return_value.getText.return_value = 'x'

        with unittest.mock.patch(
            'pgraf_cypher.parsers.parse_expression'
        ) as mock_expr:
            mock_expr.return_value = models.VariableExpression(name='list')
            result = parse_unwind_clause(ctx)

        self.assertEqual(
            result.expression.type, models.ExpressionType.VARIABLE
        )
        self.assertEqual(result.variable, 'x')


class TestCallClause(unittest.TestCase):
    """Test cases for parse_call_clause function."""

    def test_parse_empty_context(self):
        """Test parsing with None context."""
        result = parse_call_clause(None)
        self.assertFalse(result.optional)
        self.assertEqual(result.procedure_name, '')
        self.assertEqual(len(result.arguments), 0)
        self.assertEqual(len(result.yield_items), 0)
        self.assertFalse(result.yield_all)
        self.assertIsNone(result.where_expression)

    def test_parse_call_clause(self):
        """Test parsing CALL clause."""
        ctx = Mock(spec=Cypher25Parser.CallClauseContext)
        ctx.OPTIONAL.return_value = None
        ctx.procedureName.return_value = Mock()
        ctx.procedureName.return_value.getText.return_value = 'db.labels'
        ctx.procedureArgument.return_value = []
        ctx.YIELD.return_value = None
        ctx.TIMES.return_value = None
        ctx.procedureResultItem.return_value = []
        ctx.whereClause.return_value = None

        result = parse_call_clause(ctx)
        self.assertIsInstance(result, models.CallClause)
        self.assertEqual(result.procedure_name, 'db.labels')


if __name__ == '__main__':
    unittest.main()
