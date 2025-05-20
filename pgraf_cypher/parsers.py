from pgraf_cypher import antlr, models
from pgraf_cypher.antlr import Cypher25Parser


class Expression:
    def parse(
        self, ctx: Cypher25Parser.ExpressionContext
    ) -> models.Expression:
        """Parse the top-level expression (contains OR operations)."""
        if not ctx:
            return models.Expression(type=models.ExpressionType.EMPTY)

        # If multiple expressions with OR, create an OR operation
        if len(ctx.expression11()) > 1:
            return models.OperatorExpression(
                operator='OR',
                operands=[self._expr11(expr) for expr in ctx.expression11()],
            )
        return self._expr11(ctx.expression11(0))

    def _expr11(
        self, ctx: Cypher25Parser.Expression11Context
    ) -> models.Expression:
        """Parse expression11 (contains XOR operations)."""
        if len(ctx.expression10()) > 1:
            return models.OperatorExpression(
                operator='XOR',
                operands=[self._expr10(expr) for expr in ctx.expression10()],
            )
        return self._expr10(ctx.expression10(0))

    def _expr10(
        self, ctx: Cypher25Parser.Expression10Context
    ) -> models.Expression:
        """Parse expression10 (contains AND operations)."""
        if len(ctx.expression9()) > 1:
            return models.OperatorExpression(
                operator='AND',
                operands=[self._expr9(expr) for expr in ctx.expression9()],
            )
        return self._expr9(ctx.expression9(0))

    def _expr9(
        self, ctx: Cypher25Parser.Expression9Context
    ) -> models.Expression:
        """Parse expression9 (contains NOT operations)."""
        expr = self._expr8(ctx.expression8())
        return (
            models.OperatorExpression(operator='NOT', operands=[expr])
            if ctx.NOT()
            else expr
        )

    def _expr8(
        self, ctx: Cypher25Parser.Expression8Context
    ) -> models.Expression:
        """Parse expression8 (contains comparison operations)."""
        if len(ctx.expression7()) > 1:
            operands = [self._expr7(expr) for expr in ctx.expression7()]
            operators = []
            for i in range(len(ctx.children)):
                if ctx.children[i].getText() in [
                    '=',
                    '<>',
                    '!=',
                    '<=',
                    '>=',
                    '<',
                    '>',
                ]:
                    operators.append(ctx.children[i].getText())
            return models.ComparisonExpression(
                operator=operators, operands=operands
            )
        return self._expr7(ctx.expression7(0))

    def _expr7(
        self, ctx: Cypher25Parser.Expression7Context
    ) -> models.Expression:
        """Parse expression7 (contains string/list comparisons)."""
        expr = self._expr6(ctx.expression6())
        if ctx.comparisonExpression6():
            comp_expr = ctx.comparisonExpression6()
            if comp_expr.StringAndListComparison():
                op = None
                if comp_expr.REGEQ():
                    op = '=~'
                elif comp_expr.STARTS():
                    op = 'STARTS WITH'
                elif comp_expr.ENDS():
                    op = 'ENDS WITH'
                elif comp_expr.CONTAINS():
                    op = 'CONTAINS'
                elif comp_expr.IN():
                    op = 'IN'
                return models.ComparisonExpression(
                    operator=op,
                    left=expr,
                    right=self._expr6(comp_expr.expression6()),
                )
            elif comp_expr.NullComparison():
                return models.NullComparisonExpression(
                    operator='IS NULL'
                    if not comp_expr.NOT()
                    else 'IS NOT NULL',
                    operand=expr,
                )
            elif comp_expr.TypeComparison():
                models.TypeComparisonExpression(
                    operator='IS' if not comp_expr.NOT() else 'IS NOT',
                    operand=expr,
                    expected_type=comp_expr.type().getText(),
                )
        return expr

    def _expr6(
        self, ctx: Cypher25Parser.Expression6Context
    ) -> models.Expression:
        """Parse expression6 (contains addition/subtraction)."""
        if len(ctx.expression5()) > 1:
            operands = [self._expr5(expr) for expr in ctx.expression5()]
            operators = []
            for i in range(len(ctx.children)):
                if ctx.children[i].getText() in ['+', '-', '||']:
                    operators.append(ctx.children[i].getText())
            return models.ArithmeticExpression(
                operators=operators, operands=operands
            )
        return self._expr5(ctx.expression5(0))

    def _expr5(
        self, ctx: Cypher25Parser.Expression5Context
    ) -> models.Expression:
        """Parse expression5 (contains multiplication/division/modulo)."""
        if len(ctx.expression4()) > 1:
            operands = [self._expr4(expr) for expr in ctx.expression4()]
            operators = []
            for i in range(len(ctx.children)):
                if ctx.children[i].getText() in ['*', '/', '%']:
                    operators.append(ctx.children[i].getText())
            return models.ArithmeticExpression(
                operators=operators, operands=operands
            )
        return self._expr4(ctx.expression4(0))

    def _expr4(
        self, ctx: Cypher25Parser.Expression4Context
    ) -> models.Expression:
        """Parse expression4 (contains power operations)."""
        if len(ctx.expression3()) > 1:
            operands = [self._expr3(expr) for expr in ctx.expression3()]
            return models.ArithmeticExpression(
                operators=['^'] * (len(operands) - 1), operands=operands
            )
        return self._expr3(ctx.expression3(0))

    def _expr3(
        self, ctx: Cypher25Parser.Expression3Context
    ) -> models.Expression:
        """Parse expression3 (unary plus/minus)."""
        expr = self._expr2(ctx.expression2())
        if ctx.PLUS():
            return models.UnaryOperatorExpression(operator='+', operand=expr)
        elif ctx.MINUS():
            return models.UnaryOperatorExpression(operator='-', operand=expr)
        return expr

    def _expr2(
        self, ctx: Cypher25Parser.Expression2Context
    ) -> models.Expression:
        """Parse expression2 (property access and indexing)."""
        expr = self._expr1(ctx.expression1())
        if ctx.postFix():
            for postfix in ctx.postFix():
                if isinstance(postfix, Cypher25Parser.PropertyPostfixContext):
                    property_name = (
                        postfix.property_().propertyKeyName().getText()
                    )
                    expr = models.PropertyAccessExpression(
                        object=expr, property=property_name
                    )
                elif isinstance(postfix, Cypher25Parser.IndexPostfixContext):
                    index_expr = self.parse(
                        postfix.IndexPostfix().expression()
                    )
                    expr = models.IndexAccessExpression(
                        object=expr, index=index_expr
                    )
                elif isinstance(postfix, Cypher25Parser.RangePostfixContext):
                    from_expr = None
                    to_expr = None
                    if postfix.RangePostfix().fromExp:
                        from_expr = self.parse(postfix.RangePostfix().fromExp)
                    if postfix.RangePostfix().toExp:
                        to_expr = self.parse(postfix.RangePostfix().toExp)
                    expr = models.RangeAccessExpression(
                        object=expr, from_expr=from_expr, to_expr=to_expr
                    )
        return expr

    def _expr1(
        self, ctx: Cypher25Parser.Expression1Context
    ) -> models.Expression | models.LiteralValue:
        """Parse expression1 (atomic expressions)."""
        if ctx.literal():
            return self._literal(ctx.literal())
        elif ctx.variable():
            return models.VariableExpression(name=ctx.variable().getText())
        elif ctx.parameter():
            return models.ParameterExpression(
                name=ctx.parameter().parameterName().getText()
            )
        elif ctx.functionInvocation():
            func_ctx = ctx.functionInvocation()
            return models.FunctionExpression(
                name=func_ctx.functionName().getText(),
                arguments=[
                    self.parse(arg) for arg in func_ctx.functionArgument()
                ],
            )
        elif ctx.parenthesizedExpression():
            return self.parse(ctx.parenthesizedExpression().expression())
        return models.Expression(type=models.ExpressionType.UNKNOWN)

    @staticmethod
    def _literal(ctx: Cypher25Parser.LiteralContext) -> models.LiteralValue:
        """Parse literal values."""
        if isinstance(ctx, Cypher25Parser.NummericLiteralContext):
            value = ctx.getText()
            literal_type = 'float' if '.' in value else 'integer'
            return models.LiteralValue(type=literal_type, value=ctx.getText())  # type: ignore
        elif isinstance(ctx, Cypher25Parser.StringLiteralContext):
            return models.LiteralValue(type='string', value=ctx.getText())
        elif isinstance(ctx, Cypher25Parser.BooleanLiteralContext):
            return models.LiteralValue(
                type='boolean', value=ctx.getText().lower() == 'true'
            )
        elif isinstance(ctx, Cypher25Parser.OtherLiteralContext):
            return models.LiteralValue(type='map', value=ctx.getText())
        elif isinstance(ctx, Cypher25Parser.KeywordLiteralContext):
            return models.LiteralValue(type='keyword', value=ctx.getText())
        return models.LiteralValue(type='unknown_literal', value=None)


class LabelExpession:
    def parse(self, ctx: Cypher25Parser.LabelExpressionContext) -> list[str]:
        """Parse a label expression recursively into a list of label strings."""
        return self._label_expr4(ctx.labelExpression4()) if ctx else []

    def _label_expr4(
        self, ctx: Cypher25Parser.LabelExpression4Context
    ) -> list[str]:
        """Parse a level 4 label expression (contains OR operations)."""
        result = []
        if ctx:
            for expr3 in ctx.labelExpression3():
                result.extend(self._label_expr3(expr3))
        return result

    def _label_expr3(
        self, ctx: Cypher25Parser.LabelExpression3Context
    ) -> list[str]:
        """Parse a level 3 label expression (contains AND operations)."""
        if not ctx:
            return []
        result = []
        for expr2 in ctx.labelExpression2():
            result.extend(self._label_expr2(expr2))
        return result

    def _label_expr2(
        self, ctx: Cypher25Parser.LabelExpression2Context
    ) -> list[str]:
        """Parse a level 2 label expression (contains NOT operations)."""
        labels = []
        if ctx:
            labels += self._label_expr1(ctx.labelExpression1())
            if ctx.EXCLAMATION_MARK():
                return [f'NOT {label}' for label in labels]
        return labels

    def _label_expr1(
        self, ctx: Cypher25Parser.LabelExpression1Context
    ) -> list[str]:
        """Parse a level 1 label expression (atomic or parenthesized)."""
        labels = []
        if ctx:
            if isinstance(ctx, Cypher25Parser.LabelNameContext):
                labels.append(ctx.symbolicNameString().getText())
            elif isinstance(ctx, Cypher25Parser.AnyLabelContext):
                return ['ANY_LABEL']
            elif isinstance(ctx, Cypher25Parser.DynamicLabelContext):
                return ['DYNAMIC_LABEL']
            elif isinstance(
                ctx, Cypher25Parser.ParenthesizedLabelExpressionContext
            ):
                return self._label_expr4(ctx.labelExpression4())
        return labels


def node_properties(ctx: Cypher25Parser.PropertiesContext) -> dict[str, str]:
    properties: dict[str, str] = {}
    if ctx and ctx.map():
        props_map = ctx.map()
        for i in range(len(props_map.propertyKeyName())):
            key = props_map.propertyKeyName(i).getText()
            value = props_map.expression(i).getText().strip('"')
            properties[key] = value
    return properties


def node_pattern(ctx: Cypher25Parser.NodePatternContext) -> models.NodePattern:
    node = models.NodePattern()
    if ctx.variable():
        node.variable = ctx.variable().getText()
    if ctx.labelExpression():
        node.labels = LabelExpession().parse(ctx.labelExpression())
    if ctx.properties():
        node.properties = node_properties(ctx.properties())
    if ctx.expression():
        node.where_expression = Expression().parse(ctx.expression())
    return node


def pattern(ctx: antlr.Cypher25Parser.PatternContext) -> models.Pattern:
    """Convert a parsed antlr pattern to a model."""
    elements, variable = [], None
    if ctx.variable():
        variable = ctx.variable().getText()
    anon_pattern = ctx.anonymousPattern()
    if anon_pattern.patternElement():
        element = models.PatternElement(nodes=[])
        for node in anon_pattern.patternElement().nodePattern():
            element.nodes.append(node_pattern(node))
        elements.append(element)
    return models.Pattern(
        variable=variable,
        elements=elements,
        selector=None,  # Would need to extract from selector context
    )
