from pgraf_cypher import antlr, models
from pgraf_cypher.antlr import Cypher25Parser


def parse_call_clause(
    ctx: Cypher25Parser.CallClauseContext | None,
) -> models.CallClause:
    """Parse a CALL clause."""
    if not ctx:
        return models.CallClause(procedure_name='')
    optional = bool(ctx.OPTIONAL())
    procedure_name = ''
    arguments = []
    yield_items = []
    yield_all = False
    where_expression = None
    if ctx.procedureName():
        procedure_name = ctx.procedureName().getText()
    for arg_ctx in ctx.procedureArgument():
        arg_expr = parse_expression(arg_ctx.expression())
        arguments.append(models.ProcedureArgument(expression=arg_expr))
    if ctx.YIELD():
        if ctx.TIMES():
            yield_all = True
        else:
            for result_ctx in ctx.procedureResultItem():
                name = result_ctx.getText()
                alias = None
                yield_items.append(
                    models.ProcedureResultItem(name=name, alias=alias)
                )
    if ctx.whereClause():
        where_expression = parse_expression(ctx.whereClause().expression())
    return models.CallClause(
        optional=optional,
        procedure_name=procedure_name,
        arguments=arguments,
        yield_items=yield_items,
        yield_all=yield_all,
        where_expression=where_expression,
    )


def parse_clause(ctx: Cypher25Parser.ClauseContext) -> models.Clause:
    """Parse a clause."""
    clause_type = 'unknown'
    content = ctx.getText() if ctx else ''
    if ctx.useClause():
        clause_type = 'USE'
    elif ctx.finishClause():
        clause_type = 'FINISH'
    elif ctx.returnClause():
        clause_type = 'RETURN'
    elif ctx.createClause():
        clause_type = 'CREATE'
    elif ctx.matchClause():
        clause_type = 'MATCH'
    elif ctx.withClause():
        clause_type = 'WITH'
    elif ctx.mergeClause():
        clause_type = 'MERGE'
    elif ctx.filterClause():
        clause_type = 'FILTER'
    elif ctx.setClause():
        clause_type = 'SET'
    elif ctx.removeClause():
        clause_type = 'REMOVE'
    elif ctx.deleteClause():
        clause_type = 'DELETE'
    elif ctx.unwindClause():
        clause_type = 'UNWIND'
    elif ctx.callClause():
        clause_type = 'CALL'
    return models.Clause(type=clause_type, content=content)


def parse_command(ctx: Cypher25Parser.CommandContext) -> str:
    """Parse a command and return its text representation."""
    return ctx.getText() if ctx else ''


def parse_expression(
    ctx: Cypher25Parser.ExpressionContext | None,
) -> models.Expression:
    """Parse the top-level expression (contains OR operations)."""
    if not ctx:
        return models.Expression(type=models.ExpressionType.EMPTY)
    elif len(ctx.expression11()) > 1:
        return models.OperatorExpression(
            operator='OR',
            operands=[_expr11(expr) for expr in ctx.expression11()],
        )
    return _expr11(ctx.expression11(0))


def _expr11(ctx: Cypher25Parser.Expression11Context) -> models.Expression:
    """Parse expression11 (contains XOR operations)."""
    if len(ctx.expression10()) > 1:
        return models.OperatorExpression(
            operator='XOR',
            operands=[_expr10(expr) for expr in ctx.expression10()],
        )
    return _expr10(ctx.expression10(0))


def _expr10(ctx: Cypher25Parser.Expression10Context) -> models.Expression:
    """Parse expression10 (contains AND operations)."""
    if len(ctx.expression9()) > 1:
        return models.OperatorExpression(
            operator='AND',
            operands=[_expr9(expr) for expr in ctx.expression9()],
        )
    return _expr9(ctx.expression9(0))


def _expr9(ctx: Cypher25Parser.Expression9Context) -> models.Expression:
    """Parse expression9 (contains NOT operations)."""
    expr = _expr8(ctx.expression8())
    return (
        models.OperatorExpression(operator='NOT', operands=[expr])
        if ctx.NOT()
        else expr
    )


def _expr8(ctx: Cypher25Parser.Expression8Context) -> models.Expression:
    """Parse expression8 (contains comparison operations)."""
    if len(ctx.expression7()) > 1:
        operands = [_expr7(expr) for expr in ctx.expression7()]
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
    return _expr7(ctx.expression7(0))


def _expr7(ctx: Cypher25Parser.Expression7Context) -> models.Expression:
    """Parse expression7 (contains string/list comparisons)."""
    expr = _expr6(ctx.expression6())
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
                operator=op or '',
                left=expr,
                right=_expr6(comp_expr.expression6()),
            )
        elif comp_expr.NullComparison():
            return models.NullComparisonExpression(
                operator='IS NULL' if not comp_expr.NOT() else 'IS NOT NULL',
                operand=expr,
            )
        elif comp_expr.TypeComparison():
            models.TypeComparisonExpression(
                operator='IS' if not comp_expr.NOT() else 'IS NOT',
                operand=expr,
                expected_type=comp_expr.type().getText(),
            )
    return expr


def _expr6(ctx: Cypher25Parser.Expression6Context) -> models.Expression:
    """Parse expression6 (contains addition/subtraction)."""
    if len(ctx.expression5()) > 1:
        operands = [_expr5(expr) for expr in ctx.expression5()]
        operators = []
        for i in range(len(ctx.children)):
            if ctx.children[i].getText() in ['+', '-', '||']:
                operators.append(ctx.children[i].getText())
        return models.ArithmeticExpression(
            operators=operators, operands=operands
        )
    return _expr5(ctx.expression5(0))


def _expr5(ctx: Cypher25Parser.Expression5Context) -> models.Expression:
    """Parse expression5 (contains multiplication/division/modulo)."""
    if len(ctx.expression4()) > 1:
        operands = [_expr4(expr) for expr in ctx.expression4()]
        operators = []
        for i in range(len(ctx.children)):
            if ctx.children[i].getText() in ['*', '/', '%']:
                operators.append(ctx.children[i].getText())
        return models.ArithmeticExpression(
            operators=operators, operands=operands
        )
    return _expr4(ctx.expression4(0))


def _expr4(ctx: Cypher25Parser.Expression4Context) -> models.Expression:
    """Parse expression4 (contains power operations)."""
    if len(ctx.expression3()) > 1:
        operands = [_expr3(expr) for expr in ctx.expression3()]
        return models.ArithmeticExpression(
            operators=['^'] * (len(operands) - 1), operands=operands
        )
    return _expr3(ctx.expression3(0))


def _expr3(ctx: Cypher25Parser.Expression3Context) -> models.Expression:
    """Parse expression3 (unary plus/minus)."""
    expr = _expr2(ctx.expression2())
    if ctx.PLUS():
        return models.UnaryOperatorExpression(operator='+', operand=expr)
    elif ctx.MINUS():
        return models.UnaryOperatorExpression(operator='-', operand=expr)
    return expr


def _expr2(ctx: Cypher25Parser.Expression2Context) -> models.Expression:
    """Parse expression2 (property access and indexing)."""
    expr = _expr1(ctx.expression1())
    if ctx.postFix():
        for postfix in ctx.postFix():
            if isinstance(postfix, Cypher25Parser.PropertyPostfixContext):
                property_name = postfix.property_().propertyKeyName().getText()
                expr = models.PropertyAccessExpression(
                    object=expr, property=property_name
                )
            elif isinstance(postfix, Cypher25Parser.IndexPostfixContext):
                index_expr = parse_expression(
                    postfix.IndexPostfix().expression()
                )
                expr = models.IndexAccessExpression(
                    object=expr, index=index_expr
                )
            elif isinstance(postfix, Cypher25Parser.RangePostfixContext):
                from_expr = None
                to_expr = None
                if postfix.RangePostfix().fromExp:
                    from_expr = parse_expression(
                        postfix.RangePostfix().fromExp
                    )
                if postfix.RangePostfix().toExp:
                    to_expr = parse_expression(postfix.RangePostfix().toExp)
                range_expr = models.RangeAccessExpression(
                    object=expr, to=to_expr
                )
                if from_expr is not None:
                    range_expr.from_ = from_expr
                expr = range_expr
    return expr


def _expr1(ctx: Cypher25Parser.Expression1Context) -> models.Expression:
    """Parse expression1 (atomic expressions)."""
    if ctx.literal():
        literal_val = parse_literal(ctx.literal())
        return models.LiteralExpression(value=literal_val)
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
                parse_expression(arg) for arg in func_ctx.functionArgument()
            ],
        )
    elif ctx.parenthesizedExpression():
        return parse_expression(ctx.parenthesizedExpression().expression())
    return models.Expression(type=models.ExpressionType.UNKNOWN)


def parse_filter_clause(
    ctx: Cypher25Parser.FilterClauseContext,
) -> models.FilterClause:
    """Parse a FILTER clause."""
    return models.FilterClause(expression=parse_expression(ctx.expression()))


def parse_hint(ctx: Cypher25Parser.HintContext | None) -> models.Hint:
    """Parse a hint."""
    if not ctx:
        return models.Hint(type='INDEX')
    hint_type = 'INDEX'
    variable = None
    label_or_rel_type = None
    properties = []
    seek = False
    text = ctx.getText()
    if 'INDEX' in text:
        if 'TEXT' in text:
            hint_type = 'TEXT_INDEX'
        elif 'RANGE' in text:
            hint_type = 'RANGE_INDEX'
        elif 'POINT' in text:
            hint_type = 'POINT_INDEX'
        else:
            hint_type = 'INDEX'
        seek = 'SEEK' in text
    elif 'JOIN' in text:
        hint_type = 'JOIN'
    elif 'SCAN' in text:
        hint_type = 'SCAN'
    if ctx.variable():
        variable = ctx.variable().getText()
    if ctx.labelOrRelType():
        label_or_rel_type = ctx.labelOrRelType().getText()
    if ctx.nonEmptyNameList():
        for name in ctx.nonEmptyNameList().symbolicNameString():
            properties.append(name.getText())
    return models.Hint(
        type=hint_type,  # type: ignore
        variable=variable,
        label_or_rel_type=label_or_rel_type,
        properties=properties,
        seek=seek,
    )


def parse_label_expression(
    ctx: Cypher25Parser.LabelExpressionContext,
) -> list[str]:
    """Parse a label expression recursively into a list of strings."""
    return _label_expr4(ctx.labelExpression4()) if ctx else []


def _label_expr4(ctx: Cypher25Parser.LabelExpression4Context) -> list[str]:
    """Parse a level 4 label expression (contains OR operations)."""
    result = []
    for expr3 in ctx.labelExpression3():
        result.extend(_label_expr3(expr3))
    return result


def _label_expr3(ctx: Cypher25Parser.LabelExpression3Context) -> list[str]:
    """Parse a level 3 label expression (contains AND operations)."""
    result = []
    for expr2 in ctx.labelExpression2():
        result.extend(_label_expr2(expr2))
    return result


def _label_expr2(ctx: Cypher25Parser.LabelExpression2Context) -> list[str]:
    """Parse a level 2 label expression (contains NOT operations)."""
    labels = _label_expr1(ctx.labelExpression1())
    if ctx.EXCLAMATION_MARK():
        return [f'NOT {label}' for label in labels]
    return labels


def _label_expr1(ctx: Cypher25Parser.LabelExpression1Context) -> list[str]:
    """Parse a level 1 label expression (atomic or parenthesized)."""
    labels = []
    if isinstance(ctx, Cypher25Parser.LabelNameContext):
        labels.append(ctx.symbolicNameString().getText())
    elif isinstance(ctx, Cypher25Parser.AnyLabelContext):
        return ['ANY_LABEL']
    elif isinstance(ctx, Cypher25Parser.DynamicLabelContext):
        return ['DYNAMIC_LABEL']
    elif isinstance(ctx, Cypher25Parser.ParenthesizedLabelExpressionContext):
        return _label_expr4(ctx.labelExpression4())
    return labels


def parse_limit(ctx: Cypher25Parser.LimitContext | None) -> models.Limit:
    """Parse a LIMIT clause."""
    if not ctx or not ctx.expression():
        return models.Limit(
            expression=models.Expression(type=models.ExpressionType.EMPTY)
        )
    return models.Limit(expression=parse_expression(ctx.expression()))


def parse_literal(ctx: Cypher25Parser.LiteralContext) -> models.LiteralValue:
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


def parse_match_mode(ctx: Cypher25Parser.MatchModeContext) -> models.MatchMode:
    """Parse a match mode."""
    if not ctx:
        return models.MatchMode(type='REPEATABLE', target='ELEMENT')
    mode_type = 'REPEATABLE'
    target = 'ELEMENT'
    bindings = False
    for child in ctx.children:
        if hasattr(child, 'getText'):
            text = child.getText()
            if text == 'REPEATABLE':
                mode_type = 'REPEATABLE'
            elif text == 'DIFFERENT':
                mode_type = 'DIFFERENT'
            elif text == 'ELEMENT':
                target = 'ELEMENT'
            elif text == 'ELEMENTS':
                target = 'ELEMENTS'
            elif text == 'RELATIONSHIP':
                target = 'RELATIONSHIP'
            elif text == 'RELATIONSHIPS':
                target = 'RELATIONSHIPS'
            elif text == 'BINDINGS':
                bindings = True
    return models.MatchMode(
        type=mode_type,  # type: ignore
        target=target,  # type: ignore
        bindings=bindings,
    )


def parse_match_clause(
    ctx: Cypher25Parser.MatchClauseContext,
) -> models.MatchClause:
    """Parse a MATCH clause."""
    if not ctx:
        return models.MatchClause()
    optional = bool(ctx.OPTIONAL())
    match_mode = None
    patterns = []
    hints = []
    where_expression = None
    if ctx.matchMode():
        match_mode = parse_match_mode(ctx.matchMode())
    if ctx.patternList():
        patterns = parse_pattern_list(ctx.patternList())
    for hint_ctx in ctx.hint():
        hint = parse_hint(hint_ctx)
        hints.append(hint)
    if ctx.whereClause():
        where_expression = parse_expression(ctx.whereClause().expression())
    return models.MatchClause(
        optional=optional,
        match_mode=match_mode,
        patterns=patterns,
        hints=hints,
        where_expression=where_expression,
    )


def parse_merge_action(
    ctx: Cypher25Parser.MergeActionContext,
) -> models.MergeAction:
    """Parse a merge action."""
    if not ctx:
        return models.MergeAction(action_type='MATCH')
    action_type = 'MATCH'
    set_clause = None
    for child in ctx.children:
        if hasattr(child, 'getText'):
            text = child.getText()
            if text == 'MATCH':
                action_type = 'MATCH'
            elif text == 'CREATE':
                action_type = 'CREATE'
    if ctx.setClause():
        set_clause = parse_set_clause(ctx.setClause())
    return models.MergeAction(
        action_type=action_type,  # type: ignore
        set_clause=set_clause,
    )


def parse_merge_clause(
    ctx: Cypher25Parser.MergeClauseContext,
) -> models.MergeClause:
    """Parse a MERGE clause."""
    if not ctx:
        return models.MergeClause(pattern=models.Pattern(elements=[]))
    actions = []
    merge_pattern = (
        parse_pattern(ctx.pattern())
        if ctx.pattern()
        else models.Pattern(elements=[])
    )
    for merge_action_ctx in ctx.mergeAction():
        actions.append(parse_merge_action(merge_action_ctx))
    return models.MergeClause(pattern=merge_pattern, actions=actions)


def parse_node_properties(
    ctx: Cypher25Parser.PropertiesContext,
) -> dict[str, object]:
    """Parse node properties"""
    properties: dict[str, object] = {}
    if ctx and ctx.map():
        props_map = ctx.map()
        for i in range(len(props_map.propertyKeyName())):
            key = props_map.propertyKeyName(i).getText()
            value = props_map.expression(i).getText().strip('"')
            properties[key] = value
    return properties


def parse_node_pattern(
    ctx: Cypher25Parser.NodePatternContext,
) -> models.NodePattern:
    """Parse a node pattern"""
    node = models.NodePattern()
    if ctx.variable():
        node.variable = ctx.variable().getText()
    if ctx.labelExpression():
        node.labels = parse_label_expression(ctx.labelExpression())
    if ctx.properties():
        node.properties = parse_node_properties(ctx.properties())
    if ctx.expression():
        node.where_expression = parse_expression(ctx.expression())
    return node


def parse_order_by(ctx: Cypher25Parser.OrderByContext | None) -> models.OrderBy:
    """Parse an ORDER BY clause."""
    if not ctx:
        return models.OrderBy(items=[])
    return models.OrderBy(
        items=[parse_order_item(item) for item in ctx.orderItem()]
    )


def parse_order_item(ctx: Cypher25Parser.OrderItemContext) -> models.OrderItem:
    """Parse an individual order item."""
    direction = None
    if ctx.ascToken():
        direction = 'ASC'
    elif ctx.descToken():
        direction = 'DESC'
    return models.OrderItem(
        expression=parse_expression(ctx.expression()), direction=direction
    )


def parse_pattern(ctx: antlr.Cypher25Parser.PatternContext) -> models.Pattern:
    """Convert a parsed antlr pattern to a model."""
    elements = []
    anon_pattern = ctx.anonymousPattern()
    if anon_pattern.patternElement():
        element = models.PatternElement(nodes=[])
        for node in anon_pattern.patternElement().nodePattern():
            element.nodes.append(parse_node_pattern(node))
        elements.append(element)
    return models.Pattern(
        variable=ctx.variable().getText() if ctx.variable() else None,
        elements=elements,
        selector=None,  # Would need to extract from selector context
    )


def parse_pattern_list(
    ctx: Cypher25Parser.PatternListContext,
) -> list[models.Pattern]:
    """Parse a pattern list."""
    return [parse_pattern(pattern) for pattern in ctx.pattern()]


def parse_regular_query(
    ctx: Cypher25Parser.RegularQueryContext | None,
) -> models.RegularQuery:
    """Parse a regular query."""
    if ctx and ctx.union():
        return models.RegularQuery(union=parse_union(ctx.union()))
    elif ctx and ctx.when():
        return models.RegularQuery(when=parse_when(ctx.when()))
    return models.RegularQuery()


def parse_return_body(
    ctx: Cypher25Parser.ReturnBodyContext | None,
) -> models.ReturnBody:
    """Parse a return body."""
    if not ctx:
        return models.ReturnBody()
    return models.ReturnBody(
        distinct=bool(ctx.DISTINCT()),
        items=parse_return_items(ctx.returnItems()),
        order_by=parse_order_by(ctx.orderBy()),
        skip=parse_skip(ctx.skip()),
        limit=parse_limit(ctx.limit()),
    )


def parse_return_clause(
    ctx: Cypher25Parser.ReturnClauseContext | None,
) -> models.ReturnClause:
    """Parse a RETURN clause."""
    if not ctx or not ctx.returnBody():
        return models.ReturnClause(return_body=models.ReturnBody())
    return models.ReturnClause(return_body=parse_return_body(ctx.returnBody()))


def parse_return_items(
    ctx: Cypher25Parser.ReturnItemsContext | None,
) -> list[models.ReturnItem]:
    """Parse return items."""
    if not ctx:
        return []
    items = []
    for return_item_ctx in ctx.returnItem():
        if return_item_ctx.expression():
            alias = None
            if return_item_ctx.variable():
                alias = return_item_ctx.variable().getText()
            items.append(
                models.ReturnItem(
                    expression=parse_expression(return_item_ctx.expression()),
                    alias=alias,
                )
            )
    return items


def parse_set_clause(ctx: Cypher25Parser.SetClauseContext) -> models.SetClause:
    """Parse a SET clause."""
    return models.SetClause(
        items=[parse_set_item(item) for item in ctx.setItem()]
    )


def parse_set_item(ctx: Cypher25Parser.SetItemContext) -> models.SetItem:
    """Parse a set item."""
    if not ctx:
        return models.SetItem(type='SET_PROP', target='')

    # Determine the type of set item based on context type
    if hasattr(ctx, 'propertyExpression') and ctx.propertyExpression():
        return models.SetItem(
            type='SET_PROP',
            target=ctx.propertyExpression().getText(),
            value=parse_expression(ctx.propertyExpression()),
        )
    elif (
        hasattr(ctx, 'dynamicPropertyExpression')
        and ctx.dynamicPropertyExpression()
    ):
        return models.SetItem(
            type='SET_DYNAMIC_PROP',
            target=ctx.dynamicPropertyExpression().getText(),
            value=parse_expression(ctx.dynamicPropertyExpression()),
        )
    elif hasattr(ctx, 'variable') and ctx.variable():
        var_text = ctx.variable().getText()
        if hasattr(ctx, 'nodeLabels') and ctx.nodeLabels():
            return models.SetItem(type='SET_LABELS', target=var_text)
        else:
            return models.SetItem(
                type='SET_PROPS',
                target=var_text,
                value=parse_expression(ctx.variable()),
            )
    return models.SetItem(type='SET_PROP', target='')


def parse_single_query(
    ctx: Cypher25Parser.SingleQueryContext,
) -> models.SingleQuery:
    """Parse a single query."""
    return models.SingleQuery(
        clauses=[parse_clause(clause) for clause in ctx.clause()],
        use_clause=parse_use_clause(ctx.useClause()),
        regular_query=parse_regular_query(ctx.regularQuery()),
    )


def parse_skip(ctx: Cypher25Parser.SkipContext | None) -> models.Skip:
    """Parse a SKIP clause."""
    if not ctx or not ctx.expression():
        return models.Skip(
            expression=models.Expression(type=models.ExpressionType.EMPTY)
        )
    return models.Skip(expression=parse_expression(ctx.expression()))


def parse_statement(ctx: Cypher25Parser.StatementContext | None) -> models.Statement:
    """Parse a statement."""
    if not ctx:
        return models.Statement()
    if ctx.command():
        return models.Statement(command=parse_command(ctx.command()))
    elif ctx.regularQuery():
        return models.Statement(
            regular_query=parse_regular_query(ctx.regularQuery())
        )
    return models.Statement()


def parse_union(ctx: Cypher25Parser.UnionContext) -> models.Union:
    """Parse a union query with single queries."""
    single_queries = []
    union_type = None
    for single_query_ctx in ctx.singleQuery():
        single_queries.append(parse_single_query(single_query_ctx))
    if len(ctx.children) > 1:
        for child in ctx.children:
            if hasattr(child, 'getText'):
                text = child.getText()
                if text == 'ALL':
                    union_type = 'ALL'
                elif text == 'DISTINCT':
                    union_type = 'DISTINCT'
    return models.Union(single_queries=single_queries, union_type=union_type)


def parse_unwind_clause(
    ctx: Cypher25Parser.UnwindClauseContext,
) -> models.UnwindClause:
    """Parse an UNWIND clause."""
    if not ctx or not ctx.expression() or not ctx.variable():
        return models.UnwindClause(
            expression=models.Expression(type=models.ExpressionType.EMPTY),
            variable='',
        )
    return models.UnwindClause(
        expression=parse_expression(ctx.expression()),
        variable=ctx.variable().getText(),
    )


def parse_use_clause(ctx: Cypher25Parser.UseClauseContext | None) -> models.UseClause:
    """Parse a USE clause."""
    if not ctx or not ctx.graphReference():
        return models.UseClause()
    return models.UseClause(graph_reference=ctx.graphReference().getText())


def parse_when(ctx: Cypher25Parser.WhenContext) -> models.When:
    """Parse a when conditional query."""
    when_branches = []
    else_branch = None
    for when_branch_ctx in ctx.whenBranch():
        if when_branch_ctx.expression() and when_branch_ctx.singleQuery():
            condition = parse_expression(when_branch_ctx.expression())
            query = parse_single_query(when_branch_ctx.singleQuery())
            when_branches.append(
                models.WhenBranch(condition=condition, query=query)
            )
    if ctx.elseBranch():
        else_query = parse_single_query(ctx.elseBranch().singleQuery())
        else_branch = models.ElseBranch(query=else_query)
    return models.When(when_branches=when_branches, else_branch=else_branch)


def parse_where_clause(
    ctx: Cypher25Parser.WhereClauseContext,
) -> models.WhereClause:
    """Parse a WHERE clause."""
    if not ctx or not ctx.expression():
        return models.WhereClause(
            expression=models.Expression(type=models.ExpressionType.EMPTY)
        )
    return models.WhereClause(expression=parse_expression(ctx.expression()))


def parse_with_clause(ctx: Cypher25Parser.WithClauseContext | None) -> models.WithClause:
    """Parse a WITH clause."""
    if not ctx:
        return models.WithClause(
            return_body=models.ReturnBody(),
            where_expression=None,
        )
    where_expression = None
    if ctx.whereClause():
        where_expression = parse_expression(ctx.whereClause().expression())
    return models.WithClause(
        return_body=parse_return_body(ctx.returnBody()),
        where_expression=where_expression,
    )
