import enum
import typing
from typing import Literal

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

    model_config = pydantic.ConfigDict(
        # Ensure all fields are included in serialization
        use_enum_values=True,
        # Enable polymorphic serialization
        discriminator='type',
    )


class ExistsExpression(Expression):
    type: Literal[ExpressionType.EXISTS] = ExpressionType.EXISTS
    pattern: 'Pattern | None' = None
    match_clause: 'MatchClause | None' = None


class CountExpression(Expression):
    type: Literal[ExpressionType.FUNCTION] = ExpressionType.FUNCTION
    name: str = 'COUNT'
    distinct: bool = False
    argument: Expression | None = None


class AggregateExpression(Expression):
    type: Literal[ExpressionType.FUNCTION] = ExpressionType.FUNCTION
    name: str  # SUM, AVG, MIN, MAX, COLLECT, etc.
    distinct: bool = False
    argument: Expression


class ArithmeticExpression(Expression):
    type: Literal[ExpressionType.ARITHMETIC] = ExpressionType.ARITHMETIC
    operators: list[str]
    operands: list['ExpressionUnion'] = pydantic.Field(default_factory=list)


class ComparisonExpression(Expression):
    type: Literal[ExpressionType.COMPARISON] = ExpressionType.COMPARISON
    operator: str | list[str]
    operands: list['ExpressionUnion'] = pydantic.Field(default_factory=list)
    left: 'ExpressionUnion | None' = None
    right: 'ExpressionUnion | None' = None


class FunctionExpression(Expression):
    type: Literal[ExpressionType.FUNCTION] = ExpressionType.FUNCTION
    name: str
    arguments: list['ExpressionUnion'] = pydantic.Field(default_factory=list)


class IndexAccessExpression(Expression):
    type: Literal[ExpressionType.INDEX_ACCESS] = ExpressionType.INDEX_ACCESS
    object: 'ExpressionUnion'
    index: 'ExpressionUnion'


class NullComparisonExpression(ComparisonExpression):
    type: Literal[ExpressionType.NULL_COMPARISON] = (
        ExpressionType.NULL_COMPARISON
    )
    operator: str
    operand: 'ExpressionUnion'


class OperatorExpression(Expression):
    type: Literal[ExpressionType.OPERATOR] = ExpressionType.OPERATOR
    operator: str
    operands: list['ExpressionUnion'] = pydantic.Field(default_factory=list)


class ParameterExpression(Expression):
    type: Literal[ExpressionType.PARAMETER] = ExpressionType.PARAMETER
    name: str


class PropertyAccessExpression(Expression):
    type: Literal[ExpressionType.PROPERTY_ACCESS] = (
        ExpressionType.PROPERTY_ACCESS
    )
    object: 'ExpressionUnion'
    property: str


class RangeAccessExpression(Expression):
    type: Literal[ExpressionType.RANGE_ACCESS] = ExpressionType.RANGE_ACCESS
    object: 'ExpressionUnion'
    from_: 'ExpressionUnion | None' = pydantic.Field(
        alias='from', default=None
    )
    to: 'ExpressionUnion | None' = pydantic.Field(default=None)


class TypeComparisonExpression(ComparisonExpression):
    type: Literal[ExpressionType.TYPE_COMPARISON] = (
        ExpressionType.TYPE_COMPARISON
    )
    operator: str
    operand: 'ExpressionUnion'
    expected_type: str


class UnaryOperatorExpression(Expression):
    type: Literal[ExpressionType.UNARY_OPERATOR] = (
        ExpressionType.UNARY_OPERATOR
    )
    operator: str
    operand: 'ExpressionUnion'


class VariableExpression(Expression):
    type: Literal[ExpressionType.VARIABLE] = ExpressionType.VARIABLE
    name: str


class LiteralExpression(Expression):
    type: Literal[ExpressionType.LITERAL] = ExpressionType.LITERAL
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


class PathLength(pydantic.BaseModel):
    min_value: int | None = pydantic.Field(alias='min', default=None)
    max_value: int | None = pydantic.Field(alias='max', default=None)


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


class Quantifier(pydantic.BaseModel):
    from_value: int | None = pydantic.Field(alias='from', default=None)
    to_value: int | None = pydantic.Field(alias='to', default=None)


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


# Use a simple union without discriminator for now
ExpressionUnion = (
    ExistsExpression
    | CountExpression
    | AggregateExpression
    | ArithmeticExpression
    | ComparisonExpression
    | FunctionExpression
    | IndexAccessExpression
    | NullComparisonExpression
    | OperatorExpression
    | ParameterExpression
    | PropertyAccessExpression
    | RangeAccessExpression
    | TypeComparisonExpression
    | UnaryOperatorExpression
    | VariableExpression
    | LiteralExpression
    | Expression  # Base Expression as fallback
)

RegularQuery.model_rebuild()
SingleQuery.model_rebuild()
Expression.model_rebuild()
ExistsExpression.model_rebuild()
CountExpression.model_rebuild()
AggregateExpression.model_rebuild()
ArithmeticExpression.model_rebuild()
ComparisonExpression.model_rebuild()
PropertyAccessExpression.model_rebuild()
LiteralExpression.model_rebuild()
VariableExpression.model_rebuild()
FunctionExpression.model_rebuild()
IndexAccessExpression.model_rebuild()
NullComparisonExpression.model_rebuild()
OperatorExpression.model_rebuild()
ParameterExpression.model_rebuild()
RangeAccessExpression.model_rebuild()
TypeComparisonExpression.model_rebuild()
UnaryOperatorExpression.model_rebuild()
Pattern.model_rebuild()
PatternElement.model_rebuild()
MergeAction.model_rebuild()
SetClause.model_rebuild()
MatchClause.model_rebuild()
CallClause.model_rebuild()
