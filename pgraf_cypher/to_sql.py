import logging
import typing

import antlr4
from psycopg import sql

from pgraf_cypher import models, parsers
from pgraf_cypher.antlr import Cypher25Parser

LOGGER = logging.getLogger(__name__)


class CypherToSQL(antlr4.ParseTreeListener):
    def __init__(
        self,
        schema: str = 'pgraf',
        nodes_table: str = 'nodes',
        edges_table: str = 'edges',
    ) -> None:
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
                            [
                                prefix,
                                sql.SQL('.'),
                                sql.Identifier('properties'),
                                sql.SQL('->>'),
                                sql.Literal(key),
                                sql.SQL(' = '),
                                sql.Placeholder(parameter_name),
                            ]
                        )
                    for label in node.labels or []:
                        parameter_name = self._parameter_name()
                        parameters[parameter_name] = label
                        where.append(
                            [
                                prefix,
                                sql.SQL('.'),
                                sql.Identifier('labels'),
                                sql.SQL(' = ANY('),
                                sql.Placeholder(parameter_name),
                                sql.SQL(')'),
                            ]
                        )
                    value.append(sql.SQL(' FROM '))
                    value.append(
                        self._table_alias(
                            self._nodes_table, node.variable or 'node'
                        )
                    )
                    if where:
                        value.append(sql.SQL(' WHERE '))
                        temp = [sql.Composed(expr) for expr in where]
                        value.append(sql.SQL(' AND ').join(temp))
        return sql.Composed(value).as_string(), parameters

    def _parameter_name(self) -> str:
        name = f'p{len(self._parameters)}'
        self._parameters.add(name)
        return name

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

    def enterStatement(self, ctx: Cypher25Parser.StatementContext) -> None:
        print('enterStatement', parsers.parse_statement(ctx))

    def enterRegularQuery(
        self, ctx: Cypher25Parser.RegularQueryContext
    ) -> None:
        print('enterRegularQuery', parsers.parse_regular_query(ctx))

    def enterUnion(self, ctx: Cypher25Parser.UnionContext) -> None:
        print('enterUnion', parsers.parse_union(ctx))

    def enterWhen(self, ctx: Cypher25Parser.WhenContext) -> None:
        value = parsers.parse_when(ctx)
        print('enterWhen', value)

    def enterWhenBranch(self, ctx: Cypher25Parser.WhenBranchContext) -> None:
        print('enterWhenBranch', ctx)

    def enterElseBranch(self, ctx: Cypher25Parser.ElseBranchContext) -> None:
        print('enterElseBranch', ctx)

    def enterSingleQuery(self, ctx: Cypher25Parser.SingleQueryContext) -> None:
        print('enterSingleQuery', parsers.parse_single_query(ctx))

    def enterClause(self, ctx: Cypher25Parser.ClauseContext) -> None:
        print('enterClause', parsers.parse_clause(ctx))

    def enterUseClause(self, ctx: Cypher25Parser.UseClauseContext) -> None:
        print('enterUseClause', parsers.parse_use_clause(ctx))

    def enterGraphReference(
        self, ctx: Cypher25Parser.GraphReferenceContext
    ) -> None:
        print('enterGraphReference', ctx)

    def enterFinishClause(
        self, ctx: Cypher25Parser.FinishClauseContext
    ) -> None:
        print('enterFinishClause', ctx)

    def enterReturnClause(
        self, ctx: Cypher25Parser.ReturnClauseContext
    ) -> None:
        print('enterReturnClause', parsers.parse_return_clause(ctx))

    def enterReturnBody(self, ctx: Cypher25Parser.ReturnBodyContext) -> None:
        print('enterReturnBody', parsers.parse_return_body(ctx))

    def enterReturnItem(self, ctx: Cypher25Parser.ReturnItemContext) -> None:
        print('enterReturnItem', parsers.parse_return_item(ctx))

    def enterReturnItems(self, ctx: Cypher25Parser.ReturnItemsContext) -> None:
        print('enterReturnItems', parsers.parse_return_items(ctx))

    def enterOrderItem(self, ctx: Cypher25Parser.OrderItemContext) -> None:
        print('enterOrderItem', parsers.parse_order_item(ctx))

    def enterAscToken(self, ctx: Cypher25Parser.AscTokenContext) -> None:
        print('enterAscToken', ctx)

    def enterDescToken(self, ctx: Cypher25Parser.DescTokenContext) -> None:
        print('enterDescToken', parsers.parse_desc_token(ctx))

    def enterOrderBy(self, ctx: Cypher25Parser.OrderByContext) -> None:
        print('enterOrderBy', parsers.parse_order_by(ctx))

    def enterSkip(self, ctx: Cypher25Parser.SkipContext) -> None:
        print('enterSkip', parsers.parse_skip(ctx))

    def enterLimit(self, ctx: Cypher25Parser.LimitContext) -> None:
        print('enterLimit', parsers.parse_limit(ctx))

    def enterWhereClause(self, ctx: Cypher25Parser.WhereClauseContext) -> None:
        print('enterWhereClause', parsers.parse_where_clause(ctx))

    def enterWithClause(self, ctx: Cypher25Parser.WithClauseContext) -> None:
        print('enterWithClause', parsers.parse_with_clause(ctx))

    def enterMatchClause(self, ctx: Cypher25Parser.MatchClauseContext) -> None:
        match_clause = parsers.parse_match_clause(ctx)
        print('enterMatchClause', match_clause)
        self._matches += match_clause.patterns

    def enterMatchMode(self, ctx: Cypher25Parser.MatchModeContext) -> None:
        print('enterMatchMode', ctx)

    def enterHint(self, ctx: Cypher25Parser.HintContext) -> None:
        print('enterHint', ctx)

    def enterFilterClause(
        self, ctx: Cypher25Parser.FilterClauseContext
    ) -> None:
        print('enterFilterClause', parsers.parse_filter_clause(ctx))

    def enterUnwindClause(
        self, ctx: Cypher25Parser.UnwindClauseContext
    ) -> None:
        print('enterUnwindClause', parsers.parse_unwind_clause(ctx))

    def enterLetClause(self, ctx: Cypher25Parser.LetClauseContext) -> None:
        print('enterLetClause', ctx)

    def enterLetItem(self, ctx: Cypher25Parser.LetItemContext) -> None:
        print('enterLetItem', ctx)

    def enterCallClause(self, ctx: Cypher25Parser.CallClauseContext) -> None:
        print('enterCallClause', parsers.parse_call_clause(ctx))

    def enterProcedureName(
        self, ctx: Cypher25Parser.ProcedureNameContext
    ) -> None:
        print('enterProcedureName', ctx)

    def enterProcedureArgument(
        self, ctx: Cypher25Parser.ProcedureArgumentContext
    ) -> None:
        print('enterProcedureArgument', ctx)

    def enterProcedureResultItem(
        self, ctx: Cypher25Parser.ProcedureResultItemContext
    ) -> None:
        print('enterProcedureResultItem', ctx)

    def enterLoadCSVClause(
        self, ctx: Cypher25Parser.LoadCSVClauseContext
    ) -> None:
        print('enterLoadCSVClause', ctx)

    def enterForeachClause(
        self, ctx: Cypher25Parser.ForeachClauseContext
    ) -> None:
        print('enterForeachClause', ctx)

    def enterSubqueryClause(
        self, ctx: Cypher25Parser.SubqueryClauseContext
    ) -> None:
        print('enterSubqueryClause', ctx)

    def enterSubqueryScope(
        self, ctx: Cypher25Parser.SubqueryScopeContext
    ) -> None:
        print('enterSubqueryScope', ctx)

    def enterSubqueryInTransactionsParameters(
        self, ctx: Cypher25Parser.SubqueryInTransactionsParametersContext
    ) -> None:
        print('enterSubqueryInTransactionsParameters', ctx)

    def enterSubqueryInTransactionsBatchParameters(
        self, ctx: Cypher25Parser.SubqueryInTransactionsBatchParametersContext
    ) -> None:
        print('enterSubqueryInTransactionsBatchParameters', ctx)

    def enterSubqueryInTransactionsErrorParameters(
        self, ctx: Cypher25Parser.SubqueryInTransactionsErrorParametersContext
    ) -> None:
        print('enterSubqueryInTransactionsErrorParameters', ctx)

    def enterSubqueryInTransactionsRetryParameters(
        self, ctx: Cypher25Parser.SubqueryInTransactionsRetryParametersContext
    ) -> None:
        print('enterSubqueryInTransactionsRetryParameters', ctx)

    def enterOrderBySkipLimitClause(
        self, ctx: Cypher25Parser.OrderBySkipLimitClauseContext
    ) -> None:
        print('enterOrderBySkipLimitClause', ctx)

    def enterPatternList(self, ctx: Cypher25Parser.PatternListContext) -> None:
        print('enterPatternList', parsers.parse_pattern_list(ctx))

    def enterPattern(self, ctx: Cypher25Parser.PatternContext) -> None:
        print('enterPattern', parsers.parse_pattern(ctx))

    def enterQuantifier(self, ctx: Cypher25Parser.QuantifierContext) -> None:
        print('enterQuantifier', parsers.parse_quantifier(ctx))

    def enterAnonymousPattern(
        self, ctx: Cypher25Parser.AnonymousPatternContext
    ) -> None:
        # print('enterAnonymousPattern', parsers.parse_anonymous_pattern(ctx))
        ...

    def enterShortestPathPattern(
        self, ctx: Cypher25Parser.ShortestPathPatternContext
    ) -> None:
        print('enterShortestPathPattern', ctx)

    def enterPatternElement(
        self, ctx: Cypher25Parser.PatternElementContext
    ) -> None:
        print('enterPatternElement', parsers.parse_pattern_element(ctx))

    def enterAllShortestPath(
        self, ctx: Cypher25Parser.AllShortestPathContext
    ) -> None:
        print('enterAllShortestPath', ctx)

    def enterAnyPath(self, ctx: Cypher25Parser.AnyPathContext) -> None:
        print('enterAnyPath', ctx)

    def enterShortestGroup(
        self, ctx: Cypher25Parser.ShortestGroupContext
    ) -> None:
        print('enterShortestGroup', ctx)

    def enterAnyShortestPath(
        self, ctx: Cypher25Parser.AnyShortestPathContext
    ) -> None:
        print('enterAnyShortestPath', ctx)

    def enterAllPath(self, ctx: Cypher25Parser.AllPathContext) -> None:
        print('enterAllPath', ctx)

    def enterNonNegativeIntegerSpecification(
        self, ctx: Cypher25Parser.NonNegativeIntegerSpecificationContext
    ) -> None:
        print('enterNonNegativeIntegerSpecification', ctx)

    def enterGroupToken(self, ctx: Cypher25Parser.GroupTokenContext) -> None:
        print('enterGroupToken', ctx)

    def enterPathToken(self, ctx: Cypher25Parser.PathTokenContext) -> None:
        print('enterPathToken', ctx)

    def enterPathPatternNonEmpty(
        self, ctx: Cypher25Parser.PathPatternNonEmptyContext
    ) -> None:
        print('enterPathPatternNonEmpty', ctx)

    def enterNodePattern(self, ctx: Cypher25Parser.NodePatternContext) -> None:
        print('enterNodePattern', parsers.parse_node_pattern(ctx))

    def enterParenthesizedPath(
        self, ctx: Cypher25Parser.ParenthesizedPathContext
    ) -> None:
        print('enterParenthesizedPath', parsers.parse_parenthesized_path(ctx))

    def enterNodeLabels(self, ctx: Cypher25Parser.NodeLabelsContext) -> None:
        print('enterNodeLabels', ctx)

    def enterNodeLabelsIs(
        self, ctx: Cypher25Parser.NodeLabelsIsContext
    ) -> None:
        print('enterNodeLabelsIs', ctx)

    def enterDynamicExpression(
        self, ctx: Cypher25Parser.DynamicExpressionContext
    ) -> None:
        print('enterDynamicExpression', ctx)

    def enterDynamicAnyAllExpression(
        self, ctx: Cypher25Parser.DynamicAnyAllExpressionContext
    ) -> None:
        print('enterDynamicAnyAllExpression', ctx)

    def enterDynamicLabelType(
        self, ctx: Cypher25Parser.DynamicLabelTypeContext
    ) -> None:
        print('enterDynamicLabelType', ctx)

    def enterLabelType(self, ctx: Cypher25Parser.LabelTypeContext) -> None:
        print('enterLabelType', ctx)

    def enterRelType(self, ctx: Cypher25Parser.RelTypeContext) -> None:
        print('enterRelType', ctx)

    def enterLabelOrRelType(
        self, ctx: Cypher25Parser.LabelOrRelTypeContext
    ) -> None:
        print('enterLabelOrRelType', ctx)

    def enterProperties(self, ctx: Cypher25Parser.PropertiesContext) -> None:
        print('enterProperties', parsers.parse_properties(ctx))

    def enterRelationshipPattern(
        self, ctx: Cypher25Parser.RelationshipPatternContext
    ) -> None:
        print(
            'enterRelationshipPattern', parsers.parse_relationship_pattern(ctx)
        )

    def enterLeftArrow(self, ctx: Cypher25Parser.LeftArrowContext) -> None:
        print('enterLeftArrow', ctx)

    def enterArrowLine(self, ctx: Cypher25Parser.ArrowLineContext) -> None:
        print('enterArrowLine', parsers.parse_arrow_line(ctx))

    def enterRightArrow(self, ctx: Cypher25Parser.RightArrowContext) -> None:
        print('enterRightArrow', parsers.parse_right_arrow(ctx))

    def enterPathLength(self, ctx: Cypher25Parser.PathLengthContext) -> None:
        print('enterPathLength', parsers.parse_path_length(ctx))

    def enterLabelExpression(
        self, ctx: Cypher25Parser.LabelExpressionContext
    ) -> None:
        print('enterLabelExpression', parsers.parse_label_expression(ctx))

    def enterAnyLabel(self, ctx: Cypher25Parser.AnyLabelContext) -> None:
        print('enterAnyLabel', ctx)

    def enterDynamicLabel(
        self, ctx: Cypher25Parser.DynamicLabelContext
    ) -> None:
        print('enterDynamicLabel', ctx)

    def enterLabelName(self, ctx: Cypher25Parser.LabelNameContext) -> None:
        print('enterLabelName', parsers.parse_label_name(ctx))

    def enterParenthesizedLabelExpression(
        self, ctx: Cypher25Parser.ParenthesizedLabelExpressionContext
    ) -> None:
        print('enterParenthesizedLabelExpression', ctx)

    def enterExpression(self, ctx: Cypher25Parser.ExpressionContext) -> None:
        print('enterExpression', parsers.parse_expression(ctx))

    def enterTypeComparison(
        self, ctx: Cypher25Parser.TypeComparisonContext
    ) -> None:
        print('enterTypeComparison', ctx)

    def enterStringAndListComparison(
        self, ctx: Cypher25Parser.StringAndListComparisonContext
    ) -> None:
        print('enterStringAndListComparison', ctx)

    def enterNormalFormComparison(
        self, ctx: Cypher25Parser.NormalFormComparisonContext
    ) -> None:
        print('enterNormalFormComparison', ctx)

    def enterLabelComparison(
        self, ctx: Cypher25Parser.LabelComparisonContext
    ) -> None:
        print('enterLabelComparison', ctx)

    def enterNullComparison(
        self, ctx: Cypher25Parser.NullComparisonContext
    ) -> None:
        print('enterNullComparison', ctx)

    def enterNormalForm(self, ctx: Cypher25Parser.NormalFormContext) -> None:
        print('enterNormalForm', ctx)

    def enterIndexPostfix(
        self, ctx: Cypher25Parser.IndexPostfixContext
    ) -> None:
        print('enterIndexPostfix', ctx)

    def enterPropertyPostfix(
        self, ctx: Cypher25Parser.PropertyPostfixContext
    ) -> None:
        print('enterPropertyPostfix', parsers.parse_property_postfix(ctx))

    def enterRangePostfix(
        self, ctx: Cypher25Parser.RangePostfixContext
    ) -> None:
        print('enterRangePostfix', ctx)

    def enterProperty(self, ctx: Cypher25Parser.PropertyContext) -> None:
        print('enterProperty', parsers.parse_property(ctx))

    def enterDynamicProperty(
        self, ctx: Cypher25Parser.DynamicPropertyContext
    ) -> None:
        print('enterDynamicProperty', ctx)

    def enterPropertyExpression(
        self, ctx: Cypher25Parser.PropertyExpressionContext
    ) -> None:
        print('enterPropertyExpression', ctx)

    def enterDynamicPropertyExpression(
        self, ctx: Cypher25Parser.DynamicPropertyExpressionContext
    ) -> None:
        print('enterDynamicPropertyExpression', ctx)

    def enterNummericLiteral(
        self, ctx: Cypher25Parser.NummericLiteralContext
    ) -> None:
        print('enterNummericLiteral', parsers.parse_nummeric_literal(ctx))

    def enterBooleanLiteral(
        self, ctx: Cypher25Parser.BooleanLiteralContext
    ) -> None:
        print('enterBooleanLiteral', ctx)

    def enterKeywordLiteral(
        self, ctx: Cypher25Parser.KeywordLiteralContext
    ) -> None:
        print('enterKeywordLiteral', ctx)

    def enterOtherLiteral(
        self, ctx: Cypher25Parser.OtherLiteralContext
    ) -> None:
        print('enterOtherLiteral', ctx)

    def enterStringsLiteral(
        self, ctx: Cypher25Parser.StringsLiteralContext
    ) -> None:
        print('enterStringsLiteral', parsers.parse_strings_literal(ctx))

    def enterCaseExpression(
        self, ctx: Cypher25Parser.CaseExpressionContext
    ) -> None:
        print('enterCaseExpression', ctx)

    def enterCaseAlternative(
        self, ctx: Cypher25Parser.CaseAlternativeContext
    ) -> None:
        print('enterCaseAlternative', ctx)

    def enterExtendedCaseExpression(
        self, ctx: Cypher25Parser.ExtendedCaseExpressionContext
    ) -> None:
        print('enterExtendedCaseExpression', ctx)

    def enterExtendedCaseAlternative(
        self, ctx: Cypher25Parser.ExtendedCaseAlternativeContext
    ) -> None:
        print('enterExtendedCaseAlternative', ctx)

    def enterWhenSimpleComparison(
        self, ctx: Cypher25Parser.WhenSimpleComparisonContext
    ) -> None:
        print('enterWhenSimpleComparison', ctx)

    def enterWhenEquals(self, ctx: Cypher25Parser.WhenEqualsContext) -> None:
        print('enterWhenEquals', ctx)

    def enterWhenAdvancedComparison(
        self, ctx: Cypher25Parser.WhenAdvancedComparisonContext
    ) -> None:
        print('enterWhenAdvancedComparison', ctx)

    def enterListComprehension(
        self, ctx: Cypher25Parser.ListComprehensionContext
    ) -> None:
        print('enterListComprehension', ctx)

    def enterPatternComprehension(
        self, ctx: Cypher25Parser.PatternComprehensionContext
    ) -> None:
        print('enterPatternComprehension', ctx)

    def enterReduceExpression(
        self, ctx: Cypher25Parser.ReduceExpressionContext
    ) -> None:
        print('enterReduceExpression', ctx)

    def enterListItemsPredicate(
        self, ctx: Cypher25Parser.ListItemsPredicateContext
    ) -> None:
        print('enterListItemsPredicate', ctx)

    def enterNormalizeFunction(
        self, ctx: Cypher25Parser.NormalizeFunctionContext
    ) -> None:
        print('enterNormalizeFunction', ctx)

    def enterVectorFunction(
        self, ctx: Cypher25Parser.VectorFunctionContext
    ) -> None:
        print('enterVectorFunction', ctx)

    def enterTrimFunction(
        self, ctx: Cypher25Parser.TrimFunctionContext
    ) -> None:
        print('enterTrimFunction', ctx)

    def enterPatternExpression(
        self, ctx: Cypher25Parser.PatternExpressionContext
    ) -> None:
        print('enterPatternExpression', ctx)

    def enterShortestPathExpression(
        self, ctx: Cypher25Parser.ShortestPathExpressionContext
    ) -> None:
        print('enterShortestPathExpression', ctx)

    def enterParenthesizedExpression(
        self, ctx: Cypher25Parser.ParenthesizedExpressionContext
    ) -> None:
        print('enterParenthesizedExpression', ctx)

    def enterMapProjection(
        self, ctx: Cypher25Parser.MapProjectionContext
    ) -> None:
        print('enterMapProjection', ctx)

    def enterMapProjectionElement(
        self, ctx: Cypher25Parser.MapProjectionElementContext
    ) -> None:
        print('enterMapProjectionElement', ctx)

    def enterCountStar(self, ctx: Cypher25Parser.CountStarContext) -> None:
        print('enterCountStar', ctx)

    def enterExistsExpression(
        self, ctx: Cypher25Parser.ExistsExpressionContext
    ) -> None:
        print('enterExistsExpression', parsers.parse_exists_expression(ctx))

    def enterCountExpression(
        self, ctx: Cypher25Parser.CountExpressionContext
    ) -> None:
        print('enterCountExpression', ctx)

    def enterCollectExpression(
        self, ctx: Cypher25Parser.CollectExpressionContext
    ) -> None:
        print('enterCollectExpression', ctx)

    def enterNumberLiteral(
        self, ctx: Cypher25Parser.NumberLiteralContext
    ) -> None:
        print('enterNumberLiteral', parsers.parse_number_literal(ctx))

    def enterSignedIntegerLiteral(
        self, ctx: Cypher25Parser.SignedIntegerLiteralContext
    ) -> None:
        print('enterSignedIntegerLiteral', ctx)

    def enterListLiteral(self, ctx: Cypher25Parser.ListLiteralContext) -> None:
        print('enterListLiteral', ctx)

    def enterPropertyKeyName(
        self, ctx: Cypher25Parser.PropertyKeyNameContext
    ) -> None:
        print('enterPropertyKeyName', parsers.parse_property_key_name(ctx))

    def enterParameter(self, ctx: Cypher25Parser.ParameterContext) -> None:
        print('enterParameter', ctx)

    def enterParameterName(
        self, ctx: Cypher25Parser.ParameterNameContext
    ) -> None:
        print('enterParameterName', ctx)

    def enterFunctionInvocation(
        self, ctx: Cypher25Parser.FunctionInvocationContext
    ) -> None:
        print('enterFunctionInvocation', ctx)

    def enterFunctionArgument(
        self, ctx: Cypher25Parser.FunctionArgumentContext
    ) -> None:
        print('enterFunctionArgument', ctx)

    def enterFunctionName(
        self, ctx: Cypher25Parser.FunctionNameContext
    ) -> None:
        print('enterFunctionName', ctx)

    def enterNamespace(self, ctx: Cypher25Parser.NamespaceContext) -> None:
        print('enterNamespace', ctx)

    def enterVariable(self, ctx: Cypher25Parser.VariableContext) -> None:
        print('enterVariable', parsers.parse_variable(ctx))

    def enterNonEmptyNameList(
        self, ctx: Cypher25Parser.NonEmptyNameListContext
    ) -> None:
        print('enterNonEmptyNameList', ctx)

    def enterType(self, ctx: Cypher25Parser.TypeContext) -> None:
        print('enterType', ctx)

    def enterTypePart(self, ctx: Cypher25Parser.TypePartContext) -> None:
        print('enterTypePart', ctx)

    def enterTypeName(self, ctx: Cypher25Parser.TypeNameContext) -> None:
        print('enterTypeName', ctx)

    def enterTypeNullability(
        self, ctx: Cypher25Parser.TypeNullabilityContext
    ) -> None:
        print('enterTypeNullability', ctx)

    def enterTypeListSuffix(
        self, ctx: Cypher25Parser.TypeListSuffixContext
    ) -> None:
        print('enterTypeListSuffix', ctx)

    def enterVectorCoordinateType(
        self, ctx: Cypher25Parser.VectorCoordinateTypeContext
    ) -> None:
        print('enterVectorCoordinateType', ctx)

    def enterCommand(self, ctx: Cypher25Parser.CommandContext) -> None:
        print('enterCommand', ctx)

    def enterCreateCommand(
        self, ctx: Cypher25Parser.CreateCommandContext
    ) -> None:
        print('enterCreateCommand', ctx)

    def enterDropCommand(self, ctx: Cypher25Parser.DropCommandContext) -> None:
        print('enterDropCommand', ctx)

    def enterShowCommand(self, ctx: Cypher25Parser.ShowCommandContext) -> None:
        print('enterShowCommand', ctx)

    def enterShowCommandYield(
        self, ctx: Cypher25Parser.ShowCommandYieldContext
    ) -> None:
        print('enterShowCommandYield', ctx)

    def enterYieldItem(self, ctx: Cypher25Parser.YieldItemContext) -> None:
        print('enterYieldItem', ctx)

    def enterYieldSkip(self, ctx: Cypher25Parser.YieldSkipContext) -> None:
        print('enterYieldSkip', ctx)

    def enterYieldLimit(self, ctx: Cypher25Parser.YieldLimitContext) -> None:
        print('enterYieldLimit', ctx)

    def enterYieldClause(self, ctx: Cypher25Parser.YieldClauseContext) -> None:
        print('enterYieldClause', ctx)

    def enterCommandOptions(
        self, ctx: Cypher25Parser.CommandOptionsContext
    ) -> None:
        print('enterCommandOptions', ctx)

    def enterTerminateCommand(
        self, ctx: Cypher25Parser.TerminateCommandContext
    ) -> None:
        print('enterTerminateCommand', ctx)

    def enterComposableCommandClauses(
        self, ctx: Cypher25Parser.ComposableCommandClausesContext
    ) -> None:
        print('enterComposableCommandClauses', ctx)

    def enterComposableShowCommandClauses(
        self, ctx: Cypher25Parser.ComposableShowCommandClausesContext
    ) -> None:
        print('enterComposableShowCommandClauses', ctx)

    def enterShowIndexCommand(
        self, ctx: Cypher25Parser.ShowIndexCommandContext
    ) -> None:
        print('enterShowIndexCommand', ctx)

    def enterShowIndexType(
        self, ctx: Cypher25Parser.ShowIndexTypeContext
    ) -> None:
        print('enterShowIndexType', ctx)

    def enterShowIndexesEnd(
        self, ctx: Cypher25Parser.ShowIndexesEndContext
    ) -> None:
        print('enterShowIndexesEnd', ctx)

    def enterShowConstraintUnique(
        self, ctx: Cypher25Parser.ShowConstraintUniqueContext
    ) -> None:
        print('enterShowConstraintUnique', ctx)

    def enterShowConstraintExist(
        self, ctx: Cypher25Parser.ShowConstraintExistContext
    ) -> None:
        print('enterShowConstraintExist', ctx)

    def enterShowConstraintAll(
        self, ctx: Cypher25Parser.ShowConstraintAllContext
    ) -> None:
        print('enterShowConstraintAll', ctx)

    def enterShowConstraintKey(
        self, ctx: Cypher25Parser.ShowConstraintKeyContext
    ) -> None:
        print('enterShowConstraintKey', ctx)

    def enterShowConstraintPropType(
        self, ctx: Cypher25Parser.ShowConstraintPropTypeContext
    ) -> None:
        print('enterShowConstraintPropType', ctx)

    def enterNodeEntity(self, ctx: Cypher25Parser.NodeEntityContext) -> None:
        print('enterNodeEntity', ctx)

    def enterRelEntity(self, ctx: Cypher25Parser.RelEntityContext) -> None:
        print('enterRelEntity', ctx)

    def enterConstraintExistType(
        self, ctx: Cypher25Parser.ConstraintExistTypeContext
    ) -> None:
        print('enterConstraintExistType', ctx)

    def enterShowConstraintsEnd(
        self, ctx: Cypher25Parser.ShowConstraintsEndContext
    ) -> None:
        print('enterShowConstraintsEnd', ctx)

    def enterShowProcedures(
        self, ctx: Cypher25Parser.ShowProceduresContext
    ) -> None:
        print('enterShowProcedures', ctx)

    def enterShowFunctions(
        self, ctx: Cypher25Parser.ShowFunctionsContext
    ) -> None:
        print('enterShowFunctions', ctx)

    def enterFunctionToken(
        self, ctx: Cypher25Parser.FunctionTokenContext
    ) -> None:
        print('enterFunctionToken', ctx)

    def enterExecutableBy(
        self, ctx: Cypher25Parser.ExecutableByContext
    ) -> None:
        print('enterExecutableBy', ctx)

    def enterShowFunctionsType(
        self, ctx: Cypher25Parser.ShowFunctionsTypeContext
    ) -> None:
        print('enterShowFunctionsType', ctx)

    def enterShowTransactions(
        self, ctx: Cypher25Parser.ShowTransactionsContext
    ) -> None:
        print('enterShowTransactions', ctx)

    def enterTerminateTransactions(
        self, ctx: Cypher25Parser.TerminateTransactionsContext
    ) -> None:
        print('enterTerminateTransactions', ctx)

    def enterShowSettings(
        self, ctx: Cypher25Parser.ShowSettingsContext
    ) -> None:
        print('enterShowSettings', ctx)

    def enterSettingToken(
        self, ctx: Cypher25Parser.SettingTokenContext
    ) -> None:
        print('enterSettingToken', ctx)

    def enterNamesAndClauses(
        self, ctx: Cypher25Parser.NamesAndClausesContext
    ) -> None:
        print('enterNamesAndClauses', ctx)

    def enterStringsOrExpression(
        self, ctx: Cypher25Parser.StringsOrExpressionContext
    ) -> None:
        print('enterStringsOrExpression', ctx)

    def enterCommandNodePattern(
        self, ctx: Cypher25Parser.CommandNodePatternContext
    ) -> None:
        print('enterCommandNodePattern', ctx)

    def enterCommandRelPattern(
        self, ctx: Cypher25Parser.CommandRelPatternContext
    ) -> None:
        print('enterCommandRelPattern', ctx)

    def enterCreateConstraint(
        self, ctx: Cypher25Parser.CreateConstraintContext
    ) -> None:
        print('enterCreateConstraint', ctx)

    def enterConstraintTyped(
        self, ctx: Cypher25Parser.ConstraintTypedContext
    ) -> None:
        print('enterConstraintTyped', ctx)

    def enterConstraintKey(
        self, ctx: Cypher25Parser.ConstraintKeyContext
    ) -> None:
        print('enterConstraintKey', ctx)

    def enterConstraintIsNotNull(
        self, ctx: Cypher25Parser.ConstraintIsNotNullContext
    ) -> None:
        print('enterConstraintIsNotNull', ctx)

    def enterConstraintIsUnique(
        self, ctx: Cypher25Parser.ConstraintIsUniqueContext
    ) -> None:
        print('enterConstraintIsUnique', ctx)

    def enterDropConstraint(
        self, ctx: Cypher25Parser.DropConstraintContext
    ) -> None:
        print('enterDropConstraint', ctx)

    def enterCreateIndex(self, ctx: Cypher25Parser.CreateIndexContext) -> None:
        print('enterCreateIndex', ctx)

    def enterCreateIndex_(
        self, ctx: Cypher25Parser.CreateIndex_Context
    ) -> None:
        print('enterCreateIndex_', ctx)

    def enterCreateFulltextIndex(
        self, ctx: Cypher25Parser.CreateFulltextIndexContext
    ) -> None:
        print('enterCreateFulltextIndex', ctx)

    def enterFulltextNodePattern(
        self, ctx: Cypher25Parser.FulltextNodePatternContext
    ) -> None:
        print('enterFulltextNodePattern', ctx)

    def enterFulltextRelPattern(
        self, ctx: Cypher25Parser.FulltextRelPatternContext
    ) -> None:
        print('enterFulltextRelPattern', ctx)

    def enterCreateLookupIndex(
        self, ctx: Cypher25Parser.CreateLookupIndexContext
    ) -> None:
        print('enterCreateLookupIndex', ctx)

    def enterLookupIndexNodePattern(
        self, ctx: Cypher25Parser.LookupIndexNodePatternContext
    ) -> None:
        print('enterLookupIndexNodePattern', ctx)

    def enterLookupIndexRelPattern(
        self, ctx: Cypher25Parser.LookupIndexRelPatternContext
    ) -> None:
        print('enterLookupIndexRelPattern', ctx)

    def enterDropIndex(self, ctx: Cypher25Parser.DropIndexContext) -> None:
        print('enterDropIndex', ctx)

    def enterPropertyList(
        self, ctx: Cypher25Parser.PropertyListContext
    ) -> None:
        print('enterPropertyList', ctx)

    def enterEnclosedPropertyList(
        self, ctx: Cypher25Parser.EnclosedPropertyListContext
    ) -> None:
        print('enterEnclosedPropertyList', ctx)

    def enterAlterCommand(
        self, ctx: Cypher25Parser.AlterCommandContext
    ) -> None:
        print('enterAlterCommand', ctx)

    def enterRenameCommand(
        self, ctx: Cypher25Parser.RenameCommandContext
    ) -> None:
        print('enterRenameCommand', ctx)

    def enterGrantCommand(
        self, ctx: Cypher25Parser.GrantCommandContext
    ) -> None:
        print('enterGrantCommand', ctx)

    def enterDenyCommand(self, ctx: Cypher25Parser.DenyCommandContext) -> None:
        print('enterDenyCommand', ctx)

    def enterRevokeCommand(
        self, ctx: Cypher25Parser.RevokeCommandContext
    ) -> None:
        print('enterRevokeCommand', ctx)

    def enterUserNames(self, ctx: Cypher25Parser.UserNamesContext) -> None:
        print('enterUserNames', ctx)

    def enterRoleNames(self, ctx: Cypher25Parser.RoleNamesContext) -> None:
        print('enterRoleNames', ctx)

    def enterRoleToken(self, ctx: Cypher25Parser.RoleTokenContext) -> None:
        print('enterRoleToken', ctx)

    def enterEnableServerCommand(
        self, ctx: Cypher25Parser.EnableServerCommandContext
    ) -> None:
        print('enterEnableServerCommand', ctx)

    def enterAlterServer(self, ctx: Cypher25Parser.AlterServerContext) -> None:
        print('enterAlterServer', ctx)

    def enterRenameServer(
        self, ctx: Cypher25Parser.RenameServerContext
    ) -> None:
        print('enterRenameServer', ctx)

    def enterDropServer(self, ctx: Cypher25Parser.DropServerContext) -> None:
        print('enterDropServer', ctx)

    def enterShowServers(self, ctx: Cypher25Parser.ShowServersContext) -> None:
        print('enterShowServers', ctx)

    def enterAllocationCommand(
        self, ctx: Cypher25Parser.AllocationCommandContext
    ) -> None:
        print('enterAllocationCommand', ctx)

    def enterDeallocateDatabaseFromServers(
        self, ctx: Cypher25Parser.DeallocateDatabaseFromServersContext
    ) -> None:
        print('enterDeallocateDatabaseFromServers', ctx)

    def enterReallocateDatabases(
        self, ctx: Cypher25Parser.ReallocateDatabasesContext
    ) -> None:
        print('enterReallocateDatabases', ctx)

    def enterCreateRole(self, ctx: Cypher25Parser.CreateRoleContext) -> None:
        print('enterCreateRole', ctx)

    def enterDropRole(self, ctx: Cypher25Parser.DropRoleContext) -> None:
        print('enterDropRole', ctx)

    def enterRenameRole(self, ctx: Cypher25Parser.RenameRoleContext) -> None:
        print('enterRenameRole', ctx)

    def enterShowRoles(self, ctx: Cypher25Parser.ShowRolesContext) -> None:
        print('enterShowRoles', ctx)

    def enterGrantRole(self, ctx: Cypher25Parser.GrantRoleContext) -> None:
        print('enterGrantRole', ctx)

    def enterRevokeRole(self, ctx: Cypher25Parser.RevokeRoleContext) -> None:
        print('enterRevokeRole', ctx)

    def enterCreateUser(self, ctx: Cypher25Parser.CreateUserContext) -> None:
        print('enterCreateUser', ctx)

    def enterDropUser(self, ctx: Cypher25Parser.DropUserContext) -> None:
        print('enterDropUser', ctx)

    def enterRenameUser(self, ctx: Cypher25Parser.RenameUserContext) -> None:
        print('enterRenameUser', ctx)

    def enterAlterCurrentUser(
        self, ctx: Cypher25Parser.AlterCurrentUserContext
    ) -> None:
        print('enterAlterCurrentUser', ctx)

    def enterAlterUser(self, ctx: Cypher25Parser.AlterUserContext) -> None:
        print('enterAlterUser', ctx)

    def enterRemoveNamedProvider(
        self, ctx: Cypher25Parser.RemoveNamedProviderContext
    ) -> None:
        print('enterRemoveNamedProvider', ctx)

    def enterPassword(self, ctx: Cypher25Parser.PasswordContext) -> None:
        print('enterPassword', ctx)

    def enterPasswordOnly(
        self, ctx: Cypher25Parser.PasswordOnlyContext
    ) -> None:
        print('enterPasswordOnly', ctx)

    def enterPasswordExpression(
        self, ctx: Cypher25Parser.PasswordExpressionContext
    ) -> None:
        print('enterPasswordExpression', ctx)

    def enterPasswordChangeRequired(
        self, ctx: Cypher25Parser.PasswordChangeRequiredContext
    ) -> None:
        print('enterPasswordChangeRequired', ctx)

    def enterUserStatus(self, ctx: Cypher25Parser.UserStatusContext) -> None:
        print('enterUserStatus', ctx)

    def enterHomeDatabase(
        self, ctx: Cypher25Parser.HomeDatabaseContext
    ) -> None:
        print('enterHomeDatabase', ctx)

    def enterSetAuthClause(
        self, ctx: Cypher25Parser.SetAuthClauseContext
    ) -> None:
        print('enterSetAuthClause', ctx)

    def enterUserAuthAttribute(
        self, ctx: Cypher25Parser.UserAuthAttributeContext
    ) -> None:
        print('enterUserAuthAttribute', ctx)

    def enterShowUsers(self, ctx: Cypher25Parser.ShowUsersContext) -> None:
        print('enterShowUsers', ctx)

    def enterShowCurrentUser(
        self, ctx: Cypher25Parser.ShowCurrentUserContext
    ) -> None:
        print('enterShowCurrentUser', ctx)

    def enterShowSupportedPrivileges(
        self, ctx: Cypher25Parser.ShowSupportedPrivilegesContext
    ) -> None:
        print('enterShowSupportedPrivileges', ctx)

    def enterShowPrivileges(
        self, ctx: Cypher25Parser.ShowPrivilegesContext
    ) -> None:
        print('enterShowPrivileges', ctx)

    def enterShowRolePrivileges(
        self, ctx: Cypher25Parser.ShowRolePrivilegesContext
    ) -> None:
        print('enterShowRolePrivileges', ctx)

    def enterShowUserPrivileges(
        self, ctx: Cypher25Parser.ShowUserPrivilegesContext
    ) -> None:
        print('enterShowUserPrivileges', ctx)

    def enterPrivilegeAsCommand(
        self, ctx: Cypher25Parser.PrivilegeAsCommandContext
    ) -> None:
        print('enterPrivilegeAsCommand', ctx)

    def enterPrivilegeToken(
        self, ctx: Cypher25Parser.PrivilegeTokenContext
    ) -> None:
        print('enterPrivilegeToken', ctx)

    def enterPrivilege(self, ctx: Cypher25Parser.PrivilegeContext) -> None:
        print('enterPrivilege', ctx)

    def enterAllPrivilege(
        self, ctx: Cypher25Parser.AllPrivilegeContext
    ) -> None:
        print('enterAllPrivilege', ctx)

    def enterAllPrivilegeType(
        self, ctx: Cypher25Parser.AllPrivilegeTypeContext
    ) -> None:
        print('enterAllPrivilegeType', ctx)

    def enterDefaultTarget(
        self, ctx: Cypher25Parser.DefaultTargetContext
    ) -> None:
        print('enterDefaultTarget', ctx)

    def enterDatabaseVariableTarget(
        self, ctx: Cypher25Parser.DatabaseVariableTargetContext
    ) -> None:
        print('enterDatabaseVariableTarget', ctx)

    def enterGraphVariableTarget(
        self, ctx: Cypher25Parser.GraphVariableTargetContext
    ) -> None:
        print('enterGraphVariableTarget', ctx)

    def enterDBMSTarget(self, ctx: Cypher25Parser.DBMSTargetContext) -> None:
        print('enterDBMSTarget', ctx)

    def enterCreatePrivilege(
        self, ctx: Cypher25Parser.CreatePrivilegeContext
    ) -> None:
        print('enterCreatePrivilege', ctx)

    def enterCreatePrivilegeForDatabase(
        self, ctx: Cypher25Parser.CreatePrivilegeForDatabaseContext
    ) -> None:
        print('enterCreatePrivilegeForDatabase', ctx)

    def enterCreateNodePrivilegeToken(
        self, ctx: Cypher25Parser.CreateNodePrivilegeTokenContext
    ) -> None:
        print('enterCreateNodePrivilegeToken', ctx)

    def enterCreateRelPrivilegeToken(
        self, ctx: Cypher25Parser.CreateRelPrivilegeTokenContext
    ) -> None:
        print('enterCreateRelPrivilegeToken', ctx)

    def enterCreatePropertyPrivilegeToken(
        self, ctx: Cypher25Parser.CreatePropertyPrivilegeTokenContext
    ) -> None:
        print('enterCreatePropertyPrivilegeToken', ctx)

    def enterActionForDBMS(
        self, ctx: Cypher25Parser.ActionForDBMSContext
    ) -> None:
        print('enterActionForDBMS', ctx)

    def enterDropPrivilege(
        self, ctx: Cypher25Parser.DropPrivilegeContext
    ) -> None:
        print('enterDropPrivilege', ctx)

    def enterLoadPrivilege(
        self, ctx: Cypher25Parser.LoadPrivilegeContext
    ) -> None:
        print('enterLoadPrivilege', ctx)

    def enterShowPrivilege(
        self, ctx: Cypher25Parser.ShowPrivilegeContext
    ) -> None:
        print('enterShowPrivilege', ctx)

    def enterSetPrivilege(
        self, ctx: Cypher25Parser.SetPrivilegeContext
    ) -> None:
        print('enterSetPrivilege', ctx)

    def enterPasswordToken(
        self, ctx: Cypher25Parser.PasswordTokenContext
    ) -> None:
        print('enterPasswordToken', ctx)

    def enterRemovePrivilege(
        self, ctx: Cypher25Parser.RemovePrivilegeContext
    ) -> None:
        print('enterRemovePrivilege', ctx)

    def enterWritePrivilege(
        self, ctx: Cypher25Parser.WritePrivilegeContext
    ) -> None:
        print('enterWritePrivilege', ctx)

    def enterDatabasePrivilege(
        self, ctx: Cypher25Parser.DatabasePrivilegeContext
    ) -> None:
        print('enterDatabasePrivilege', ctx)

    def enterDbmsPrivilege(
        self, ctx: Cypher25Parser.DbmsPrivilegeContext
    ) -> None:
        print('enterDbmsPrivilege', ctx)

    def enterDbmsPrivilegeExecute(
        self, ctx: Cypher25Parser.DbmsPrivilegeExecuteContext
    ) -> None:
        print('enterDbmsPrivilegeExecute', ctx)

    def enterAdminToken(self, ctx: Cypher25Parser.AdminTokenContext) -> None:
        print('enterAdminToken', ctx)

    def enterProcedureToken(
        self, ctx: Cypher25Parser.ProcedureTokenContext
    ) -> None:
        print('enterProcedureToken', ctx)

    def enterIndexToken(self, ctx: Cypher25Parser.IndexTokenContext) -> None:
        print('enterIndexToken', ctx)

    def enterConstraintToken(
        self, ctx: Cypher25Parser.ConstraintTokenContext
    ) -> None:
        print('enterConstraintToken', ctx)

    def enterTransactionToken(
        self, ctx: Cypher25Parser.TransactionTokenContext
    ) -> None:
        print('enterTransactionToken', ctx)

    def enterUserQualifier(
        self, ctx: Cypher25Parser.UserQualifierContext
    ) -> None:
        print('enterUserQualifier', ctx)

    def enterExecuteFunctionQualifier(
        self, ctx: Cypher25Parser.ExecuteFunctionQualifierContext
    ) -> None:
        print('enterExecuteFunctionQualifier', ctx)

    def enterExecuteProcedureQualifier(
        self, ctx: Cypher25Parser.ExecuteProcedureQualifierContext
    ) -> None:
        print('enterExecuteProcedureQualifier', ctx)

    def enterSettingQualifier(
        self, ctx: Cypher25Parser.SettingQualifierContext
    ) -> None:
        print('enterSettingQualifier', ctx)

    def enterGlobs(self, ctx: Cypher25Parser.GlobsContext) -> None:
        print('enterGlobs', ctx)

    def enterGlob(self, ctx: Cypher25Parser.GlobContext) -> None:
        print('enterGlob', ctx)

    def enterGlobRecursive(
        self, ctx: Cypher25Parser.GlobRecursiveContext
    ) -> None:
        print('enterGlobRecursive', ctx)

    def enterGlobPart(self, ctx: Cypher25Parser.GlobPartContext) -> None:
        print('enterGlobPart', ctx)

    def enterQualifiedGraphPrivileges(
        self, ctx: Cypher25Parser.QualifiedGraphPrivilegesContext
    ) -> None:
        print('enterQualifiedGraphPrivileges', ctx)

    def enterLabelsResource(
        self, ctx: Cypher25Parser.LabelsResourceContext
    ) -> None:
        print('enterLabelsResource', ctx)

    def enterPropertiesResource(
        self, ctx: Cypher25Parser.PropertiesResourceContext
    ) -> None:
        print('enterPropertiesResource', ctx)

    def enterNonEmptyStringList(
        self, ctx: Cypher25Parser.NonEmptyStringListContext
    ) -> None:
        print('enterNonEmptyStringList', ctx)

    def enterGraphQualifier(
        self, ctx: Cypher25Parser.GraphQualifierContext
    ) -> None:
        print('enterGraphQualifier', ctx)

    def enterGraphQualifierToken(
        self, ctx: Cypher25Parser.GraphQualifierTokenContext
    ) -> None:
        print('enterGraphQualifierToken', ctx)

    def enterRelToken(self, ctx: Cypher25Parser.RelTokenContext) -> None:
        print('enterRelToken', ctx)

    def enterElementToken(
        self, ctx: Cypher25Parser.ElementTokenContext
    ) -> None:
        print('enterElementToken', ctx)

    def enterNodeToken(self, ctx: Cypher25Parser.NodeTokenContext) -> None:
        print('enterNodeToken', ctx)

    def enterDatabaseScope(
        self, ctx: Cypher25Parser.DatabaseScopeContext
    ) -> None:
        print('enterDatabaseScope', ctx)

    def enterGraphScope(self, ctx: Cypher25Parser.GraphScopeContext) -> None:
        print('enterGraphScope', ctx)

    def enterCreateCompositeDatabase(
        self, ctx: Cypher25Parser.CreateCompositeDatabaseContext
    ) -> None:
        print('enterCreateCompositeDatabase', ctx)

    def enterCreateDatabase(
        self, ctx: Cypher25Parser.CreateDatabaseContext
    ) -> None:
        print('enterCreateDatabase', ctx)

    def enterShards(self, ctx: Cypher25Parser.ShardsContext) -> None:
        print('enterShards', ctx)

    def enterGraphShard(self, ctx: Cypher25Parser.GraphShardContext) -> None:
        print('enterGraphShard', ctx)

    def enterPropertyShard(
        self, ctx: Cypher25Parser.PropertyShardContext
    ) -> None:
        print('enterPropertyShard', ctx)

    def enterTopology(self, ctx: Cypher25Parser.TopologyContext) -> None:
        print('enterTopology', ctx)

    def enterPrimaryTopology(
        self, ctx: Cypher25Parser.PrimaryTopologyContext
    ) -> None:
        print('enterPrimaryTopology', ctx)

    def enterPrimaryToken(
        self, ctx: Cypher25Parser.PrimaryTokenContext
    ) -> None:
        print('enterPrimaryToken', ctx)

    def enterSecondaryTopology(
        self, ctx: Cypher25Parser.SecondaryTopologyContext
    ) -> None:
        print('enterSecondaryTopology', ctx)

    def enterSecondaryToken(
        self, ctx: Cypher25Parser.SecondaryTokenContext
    ) -> None:
        print('enterSecondaryToken', ctx)

    def enterDefaultLanguageSpecification(
        self, ctx: Cypher25Parser.DefaultLanguageSpecificationContext
    ) -> None:
        print('enterDefaultLanguageSpecification', ctx)

    def enterDropDatabase(
        self, ctx: Cypher25Parser.DropDatabaseContext
    ) -> None:
        print('enterDropDatabase', ctx)

    def enterAliasAction(self, ctx: Cypher25Parser.AliasActionContext) -> None:
        print('enterAliasAction', ctx)

    def enterAlterDatabase(
        self, ctx: Cypher25Parser.AlterDatabaseContext
    ) -> None:
        print('enterAlterDatabase', ctx)

    def enterAlterDatabaseAccess(
        self, ctx: Cypher25Parser.AlterDatabaseAccessContext
    ) -> None:
        print('enterAlterDatabaseAccess', ctx)

    def enterAlterDatabaseTopology(
        self, ctx: Cypher25Parser.AlterDatabaseTopologyContext
    ) -> None:
        print('enterAlterDatabaseTopology', ctx)

    def enterAlterDatabaseOption(
        self, ctx: Cypher25Parser.AlterDatabaseOptionContext
    ) -> None:
        print('enterAlterDatabaseOption', ctx)

    def enterStartDatabase(
        self, ctx: Cypher25Parser.StartDatabaseContext
    ) -> None:
        print('enterStartDatabase', ctx)

    def enterStopDatabase(
        self, ctx: Cypher25Parser.StopDatabaseContext
    ) -> None:
        print('enterStopDatabase', ctx)

    def enterWaitClause(self, ctx: Cypher25Parser.WaitClauseContext) -> None:
        print('enterWaitClause', ctx)

    def enterSecondsToken(
        self, ctx: Cypher25Parser.SecondsTokenContext
    ) -> None:
        print('enterSecondsToken', ctx)

    def enterShowDatabase(
        self, ctx: Cypher25Parser.ShowDatabaseContext
    ) -> None:
        print('enterShowDatabase', ctx)

    def enterAliasName(self, ctx: Cypher25Parser.AliasNameContext) -> None:
        print('enterAliasName', ctx)

    def enterAliasTargetName(
        self, ctx: Cypher25Parser.AliasTargetNameContext
    ) -> None:
        print('enterAliasTargetName', ctx)

    def enterDatabaseName(
        self, ctx: Cypher25Parser.DatabaseNameContext
    ) -> None:
        print('enterDatabaseName', ctx)

    def enterCreateAlias(self, ctx: Cypher25Parser.CreateAliasContext) -> None:
        print('enterCreateAlias', ctx)

    def enterDropAlias(self, ctx: Cypher25Parser.DropAliasContext) -> None:
        print('enterDropAlias', ctx)

    def enterAlterAlias(self, ctx: Cypher25Parser.AlterAliasContext) -> None:
        print('enterAlterAlias', ctx)

    def enterAlterAliasTarget(
        self, ctx: Cypher25Parser.AlterAliasTargetContext
    ) -> None:
        print('enterAlterAliasTarget', ctx)

    def enterAlterAliasUser(
        self, ctx: Cypher25Parser.AlterAliasUserContext
    ) -> None:
        print('enterAlterAliasUser', ctx)

    def enterAlterAliasPassword(
        self, ctx: Cypher25Parser.AlterAliasPasswordContext
    ) -> None:
        print('enterAlterAliasPassword', ctx)

    def enterAlterAliasDriver(
        self, ctx: Cypher25Parser.AlterAliasDriverContext
    ) -> None:
        print('enterAlterAliasDriver', ctx)

    def enterAlterAliasProperties(
        self, ctx: Cypher25Parser.AlterAliasPropertiesContext
    ) -> None:
        print('enterAlterAliasProperties', ctx)

    def enterShowAliases(self, ctx: Cypher25Parser.ShowAliasesContext) -> None:
        print('enterShowAliases', ctx)

    def enterSymbolicNameOrStringParameter(
        self, ctx: Cypher25Parser.SymbolicNameOrStringParameterContext
    ) -> None:
        print('enterSymbolicNameOrStringParameter', ctx)

    def enterCommandNameExpression(
        self, ctx: Cypher25Parser.CommandNameExpressionContext
    ) -> None:
        print('enterCommandNameExpression', ctx)

    def enterSymbolicNameOrStringParameterList(
        self, ctx: Cypher25Parser.SymbolicNameOrStringParameterListContext
    ) -> None:
        print('enterSymbolicNameOrStringParameterList', ctx)

    def enterSymbolicAliasNameList(
        self, ctx: Cypher25Parser.SymbolicAliasNameListContext
    ) -> None:
        print('enterSymbolicAliasNameList', ctx)

    def enterSymbolicAliasNameOrParameter(
        self, ctx: Cypher25Parser.SymbolicAliasNameOrParameterContext
    ) -> None:
        print('enterSymbolicAliasNameOrParameter', ctx)

    def enterSymbolicAliasName(
        self, ctx: Cypher25Parser.SymbolicAliasNameContext
    ) -> None:
        print('enterSymbolicAliasName', ctx)

    def enterStringListLiteral(
        self, ctx: Cypher25Parser.StringListLiteralContext
    ) -> None:
        print('enterStringListLiteral', ctx)

    def enterStringList(self, ctx: Cypher25Parser.StringListContext) -> None:
        print('enterStringList', ctx)

    def enterStringLiteral(
        self, ctx: Cypher25Parser.StringLiteralContext
    ) -> None:
        print('enterStringLiteral', parsers.parse_string_literal(ctx))

    def enterStringOrParameterExpression(
        self, ctx: Cypher25Parser.StringOrParameterExpressionContext
    ) -> None:
        print('enterStringOrParameterExpression', ctx)

    def enterStringOrParameter(
        self, ctx: Cypher25Parser.StringOrParameterContext
    ) -> None:
        print('enterStringOrParameter', ctx)

    def enterUIntOrIntParameter(
        self, ctx: Cypher25Parser.UIntOrIntParameterContext
    ) -> None:
        print('enterUIntOrIntParameter', ctx)

    def enterMapOrParameter(
        self, ctx: Cypher25Parser.MapOrParameterContext
    ) -> None:
        print('enterMapOrParameter', ctx)

    def enterMap(self, ctx: Cypher25Parser.MapContext) -> None:
        print('enterMap', parsers.parse_map(ctx))

    def enterSymbolicVariableNameString(
        self, ctx: Cypher25Parser.SymbolicVariableNameStringContext
    ) -> None:
        print(
            'enterSymbolicVariableNameString',
            parsers.parse_symbolic_variable_name_string(ctx),
        )

    def enterEscapedSymbolicVariableNameString(
        self, ctx: Cypher25Parser.EscapedSymbolicVariableNameStringContext
    ) -> None:
        print('enterEscapedSymbolicVariableNameString', ctx)

    def enterUnescapedSymbolicVariableNameString(
        self, ctx: Cypher25Parser.UnescapedSymbolicVariableNameStringContext
    ) -> None:
        print(
            'enterUnescapedSymbolicVariableNameString',
            parsers.parse_unescaped_symbolic_variable_name_string(ctx),
        )

    def enterSymbolicNameString(
        self, ctx: Cypher25Parser.SymbolicNameStringContext
    ) -> None:
        print(
            'enterSymbolicNameString', parsers.parse_symbolic_name_string(ctx)
        )

    def enterEscapedSymbolicNameString(
        self, ctx: Cypher25Parser.EscapedSymbolicNameStringContext
    ) -> None:
        print('enterEscapedSymbolicNameString', ctx)

    def enterUnescapedSymbolicNameString(
        self, ctx: Cypher25Parser.UnescapedSymbolicNameStringContext
    ) -> None:
        print(
            'enterUnescapedSymbolicNameString',
            parsers.parse_unescaped_symbolic_name_string(ctx),
        )

    def enterEndOfFile(self, ctx: Cypher25Parser.EndOfFileContext) -> None:
        print('enterEndOfFile', ctx)
