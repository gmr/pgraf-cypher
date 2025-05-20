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
    from_expr: Expression | None = pydantic.Field(alias='from', default=None)
    to_expr: Expression | None = pydantic.Field(alias='to', default=None)


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


Expression.model_rebuild()
Pattern.model_rebuild()
PatternElement.model_rebuild()
RangeAccessExpression.model_rebuild()
