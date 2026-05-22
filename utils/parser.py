"""
parser.py — Safe mathematical expression parsing
Uses SymPy to parse user-supplied expressions into callable Python functions.
Only allows a restricted set of symbols and functions to prevent code injection.
"""


from tokenize import TokenError
import sympy as sp
import numpy as np
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# The single independent variable
x = sp.Symbol('x')

# Allowed names for sympify — math functions + constants only
ALLOWED_FUNCTIONS = {
    'sin': sp.sin,
    'cos': sp.cos,
    'tan': sp.tan,
    'exp': sp.exp,
    'log': sp.log,       # natural log
    'ln': sp.log,
    'sqrt': sp.sqrt,
    'abs': sp.Abs,
    'pi': sp.pi,
    'e': sp.E,
    'x': x,
}

# Allowed names for numeric-only expressions (x and h fields)
ALLOWED_CONSTANTS = {
    'pi': sp.pi,
    'e': sp.E,
    'sin': sp.sin,
    'cos': sp.cos,
    'tan': sp.tan,
    'sqrt': sp.sqrt,
    'log': sp.log,
    'ln': sp.log,
}

# Transformations for the expression parser
TRANSFORMATIONS = (
    standard_transformations
    + (implicit_multiplication_application, convert_xor)
)


import re

def parse_expression(expr_string: str):
    """
    Parse a user-supplied math expression string into a SymPy expression.

    Parameters
    ----------
    expr_string : str
        e.g. "sin(x)", "x**3 + 2*x", "exp(-x**2)"

    Returns
    -------
    sympy.Expr
        The parsed symbolic expression.

    Raises
    ------
    ValueError
        If the expression contains disallowed names or is otherwise invalid.
    """
    if not expr_string or not expr_string.strip():
        raise ValueError("Expression cannot be empty.")

    # Normalise common notations
    cleaned = expr_string.strip()
    cleaned = cleaned.replace('**', '^')
    # Wrap naked exponents in parentheses for correct implicit multiplication precedence
    cleaned = re.sub(r'\^([a-zA-Z0-9_.]+)', r'^(\1)', cleaned)
    cleaned = cleaned.replace('^', '**')  # convert back for parser

    try:
        expr = parse_expr(
            cleaned,
            local_dict=ALLOWED_FUNCTIONS,
            transformations=TRANSFORMATIONS,
        )
    except (sp.SympifyError, SyntaxError, TypeError, TokenError) as exc:
        raise ValueError(
            f"Could not parse the expression '{expr_string}'. "
            "Make sure you use valid syntax, e.g. sin(x), x**2 + 1, exp(-x)."
        ) from exc

    # Ensure the expression only involves the symbol x (and numeric constants)
    free = expr.free_symbols
    if free and free != {x}:
        extra = ', '.join(str(s) for s in free - {x})
        raise ValueError(
            f"Expression contains unknown variable(s): {extra}. "
            "Only 'x' is allowed as a variable."
        )

    return expr


def make_callable(expr):
    """Convert a SymPy expression to a fast NumPy-backed callable f(x)."""
    return sp.lambdify(x, expr, modules=['numpy'])


def symbolic_derivative(expr, order: int = 1):
    """Return the symbolic derivative of 'expr' with respect to x."""
    return sp.diff(expr, x, order)


def evaluate_exact(expr, x_val: float, order: int = 1) -> float | None:
    """
    Compute the exact (symbolic) derivative value for error comparison.
    Returns None if evaluation fails.
    """
    try:
        deriv = symbolic_derivative(expr, order)
        val = float(deriv.subs(x, x_val))
        if not np.isfinite(val):
            return None
        return val
    except Exception:
        return None


def parse_numeric_expression(value_string: str) -> float:
    """
    Parse a numeric expression that may contain math constants and functions.

    Supports inputs like: 3.14, pi/4, 2*pi, sqrt(2), pi/6, e, etc.

    Parameters
    ----------
    value_string : str
        The string to evaluate as a number.

    Returns
    -------
    float
        The evaluated numeric result.

    Raises
    ------
    ValueError
        If the string cannot be evaluated to a finite number.
    """
    if not value_string or not value_string.strip():
        raise ValueError("Value cannot be empty.")

    cleaned = value_string.strip()
    cleaned = cleaned.replace('^', '**')

    try:
        expr = parse_expr(
            cleaned,
            local_dict=ALLOWED_CONSTANTS,
            transformations=TRANSFORMATIONS,
        )
    except Exception as exc:
        raise ValueError(
            f"Could not parse '{value_string}' as a numeric value. "
            "Use numbers or math constants like pi, e, pi/4, sqrt(2)."
        ) from exc

    # Must not contain any free symbols (must be a pure number)
    if expr.free_symbols:
        raise ValueError(
            f"'{value_string}' contains variables. "
            "Only numbers and constants (pi, e) are allowed here."
        )

    try:
        result = float(expr.evalf())
    except Exception as exc:
        raise ValueError(
            f"Could not evaluate '{value_string}' to a number."
        ) from exc

    if not np.isfinite(result):
        raise ValueError(f"'{value_string}' evaluates to a non-finite value.")

    return result
