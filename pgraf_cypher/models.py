import enum
import typing

import pydantic


class ExpressionType(str, enum.Enum):
    EMPTY = 'empty'
    LITERAL = 'literal'
    VARIABLE = 'variable'
    PARAMETER = 'parameter'
    OPERATOR = 'operator'
    UNARY_OPERATOR = 'unary_operator'
    COMPARISON = 'comparison'
    NULL_COMPARISON = 'null_comparison'
    STRING_COMPARISON = 'string_comparison'
    TYPE_COMPARISON = 'type_comparison'
    ARITHMETIC = 'arithmetic'
    LOGICAL = 'logical'
    RELATIONSHIP = 'relationship'
    FUNCTION = 'function'
    INDEX_ACCESS = 'index_access'
    PROPERTY_ACCESS = 'property_access'
    RANGE_ACCESS = 'range_access'
    MAP = 'map'
    LIST = 'list'
    PATTERN = 'pattern'
    CASE = 'case'
    EXISTS = 'exists'
    UNKNOWN = 'unknown'


class Expression(pydantic.BaseModel):
    type: ExpressionType


class ArithmeticExpression(Expression):
    type: ExpressionType = ExpressionType.ARITHMETIC
    operators: list[str]
    operands: list[Expression] = pydantic.Field(default_factory=list)


class ComparisonExpression(Expression):
    type: ExpressionType = ExpressionType.COMPARISON
    operator: str | list[str]
    operands: list[Expression] = pydantic.Field(default_factory=list)
    left: Expression | None = None
    right: Expression | None = None


class FunctionExpression(Expression):
    type: ExpressionType = ExpressionType.FUNCTION
    name: str
    arguments: list[Expression] = pydantic.Field(default_factory=list)


class IndexAccessExpression(Expression):
    type: ExpressionType = ExpressionType.INDEX_ACCESS
    object: Expression
    index: Expression


class NullComparisonExpression(ComparisonExpression):
    type: ExpressionType = ExpressionType.NULL_COMPARISON
    operator: str
    operand: Expression


class OperatorExpression(Expression):
    type: ExpressionType = ExpressionType.OPERATOR
    operator: str
    operands: list[Expression] = pydantic.Field(default_factory=list)


class ParameterExpression(Expression):
    type: ExpressionType = ExpressionType.PARAMETER
    name: str


class PropertyAccessExpression(Expression):
    type: ExpressionType = ExpressionType.PROPERTY_ACCESS
    object: Expression
    property: str


class RangeAccessExpression(Expression):
    type: ExpressionType = ExpressionType.RANGE_ACCESS
    object: Expression
    from_: Expression | None = pydantic.Field(alias='from', default=None)
    to: Expression | None = pydantic.Field(default=None)


class TypeComparisonExpression(ComparisonExpression):
    type: ExpressionType = ExpressionType.TYPE_COMPARISON
    operator: str
    operand: Expression
    expected_type: str


class UnaryOperatorExpression(Expression):
    type: ExpressionType = ExpressionType.UNARY_OPERATOR
    operator: str
    operand: Expression


class VariableExpression(Expression):
    type: ExpressionType = ExpressionType.VARIABLE
    name: str


class LiteralExpression(Expression):
    type: ExpressionType = ExpressionType.LITERAL
    value: typing.Optional['LiteralValue'] = None


class ListAccess(pydantic.BaseModel):
    expression: Expression
    index: Expression


class LiteralValue(pydantic.BaseModel):
    type: typing.Literal[
        'string',
        'integer',
        'float',
        'boolean',
        'null',
        'map',
        'keyword',
        'unknown_literal',
    ]
    value: str | int | float | bool | None | dict


class NodePattern(pydantic.BaseModel):
    variable: str | None = None
    labels: list[str] = pydantic.Field(default_factory=list)
    properties: dict[str, object] = pydantic.Field(default_factory=dict)
    where_expression: Expression | None = None


class Pattern(pydantic.BaseModel):
    variable: str | None = None
    elements: list['PatternElement']
    selector: str | None = None


class PatternElement(pydantic.BaseModel):
    nodes: list[NodePattern]
    relationships: list['RelationshipPattern'] = pydantic.Field(
        default_factory=list
    )


class PropertyAccess(pydantic.BaseModel):
    expression: Expression
    property_name: str


class RelationshipPattern(pydantic.BaseModel):
    variable: str | None = None
    labels: list[str] = pydantic.Field(default_factory=list)
    properties: dict[str, object] = pydantic.Field(default_factory=dict)
    direction: typing.Literal['outgoing', 'incoming', 'both'] = 'outgoing'
    path_length: dict[str, int | None] | None = None
    where_expression: str | None = None


class RegularQuery(pydantic.BaseModel):
    union: typing.Optional['Union'] = None
    when: typing.Optional['When'] = None


class Statement(pydantic.BaseModel):
    command: str | None = None
    regular_query: RegularQuery | None = None


class SingleQuery(pydantic.BaseModel):
    clauses: list['Clause'] = pydantic.Field(default_factory=list)
    use_clause: typing.Optional['UseClause'] = None
    regular_query: typing.Optional['RegularQuery'] = None


class Union(pydantic.BaseModel):
    single_queries: list[SingleQuery] = pydantic.Field(default_factory=list)
    union_type: typing.Literal['ALL', 'DISTINCT', None] = None


class WhenBranch(pydantic.BaseModel):
    condition: Expression
    query: SingleQuery


class ElseBranch(pydantic.BaseModel):
    query: SingleQuery


class When(pydantic.BaseModel):
    when_branches: list[WhenBranch] = pydantic.Field(default_factory=list)
    else_branch: ElseBranch | None = None


class Clause(pydantic.BaseModel):
    type: str
    content: str | None = None


class UseClause(pydantic.BaseModel):
    graph_reference: str | None = None


class OrderItem(pydantic.BaseModel):
    expression: Expression
    direction: typing.Literal['ASC', 'DESC', None] = None


class OrderBy(pydantic.BaseModel):
    items: list[OrderItem] = pydantic.Field(default_factory=list)


class Skip(pydantic.BaseModel):
    expression: Expression


class Limit(pydantic.BaseModel):
    expression: Expression


class ReturnItem(pydantic.BaseModel):
    expression: Expression
    alias: str | None = None


class ReturnBody(pydantic.BaseModel):
    distinct: bool = False
    items: list[ReturnItem] = pydantic.Field(default_factory=list)
    order_by: OrderBy | None = None
    skip: Skip | None = None
    limit: Limit | None = None


class WithClause(pydantic.BaseModel):
    return_body: ReturnBody
    where_expression: Expression | None = None


class MergeAction(pydantic.BaseModel):
    action_type: typing.Literal['MATCH', 'CREATE']
    set_clause: typing.Optional['SetClause'] = None


class MergeClause(pydantic.BaseModel):
    pattern: Pattern
    actions: list[MergeAction] = pydantic.Field(default_factory=list)


class FilterClause(pydantic.BaseModel):
    expression: Expression


class SetItem(pydantic.BaseModel):
    type: typing.Literal[
        'SET_PROP', 'SET_DYNAMIC_PROP', 'SET_PROPS', 'ADD_PROP', 'SET_LABELS'
    ]
    target: str | Expression
    value: Expression | None = None


class SetClause(pydantic.BaseModel):
    items: list[SetItem] = pydantic.Field(default_factory=list)


class MatchMode(pydantic.BaseModel):
    type: typing.Literal['REPEATABLE', 'DIFFERENT']
    target: typing.Literal[
        'ELEMENT', 'ELEMENTS', 'RELATIONSHIP', 'RELATIONSHIPS'
    ]
    bindings: bool = False


class Hint(pydantic.BaseModel):
    type: typing.Literal[
        'INDEX', 'TEXT_INDEX', 'RANGE_INDEX', 'POINT_INDEX', 'JOIN', 'SCAN'
    ]
    variable: str | None = None
    label_or_rel_type: str | None = None
    properties: list[str] = pydantic.Field(default_factory=list)
    seek: bool = False


class MatchClause(pydantic.BaseModel):
    optional: bool = False
    match_mode: MatchMode | None = None
    patterns: list[Pattern] = pydantic.Field(default_factory=list)
    hints: list[Hint] = pydantic.Field(default_factory=list)
    where_expression: Expression | None = None


class ReturnClause(pydantic.BaseModel):
    return_body: ReturnBody


class WhereClause(pydantic.BaseModel):
    expression: Expression


class UnwindClause(pydantic.BaseModel):
    expression: Expression
    variable: str


class ProcedureArgument(pydantic.BaseModel):
    expression: Expression


class ProcedureResultItem(pydantic.BaseModel):
    name: str
    alias: str | None = None


class CallClause(pydantic.BaseModel):
    optional: bool = False
    procedure_name: str
    arguments: list[ProcedureArgument] = pydantic.Field(default_factory=list)
    yield_items: list[ProcedureResultItem] = pydantic.Field(
        default_factory=list
    )
    yield_all: bool = False
    where_expression: Expression | None = None


RegularQuery.model_rebuild()
SingleQuery.model_rebuild()
Expression.model_rebuild()
Pattern.model_rebuild()
PatternElement.model_rebuild()
RangeAccessExpression.model_rebuild()
MergeAction.model_rebuild()
SetClause.model_rebuild()
MatchClause.model_rebuild()
CallClause.model_rebuild()
