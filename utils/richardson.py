"""
richardson.py — Manual Richardson Extrapolation for Numerical Differentiation

Implements central-difference approximations and Richardson Extrapolation
for first and second derivatives WITHOUT using any built-in differentiation.
"""

import numpy as np

DECIMALS = 4


def _fmt(value: float) -> str:
    """Format a numeric value for display (fixed 4 decimal places)."""
    return f"{value:.{DECIMALS}f}"


def central_diff_first(f, x: float, h: float) -> float:
    """
    First derivative via central difference:
        f'(x) ≈ [f(x+h) − f(x−h)] / (2h)
    """
    return (f(x + h) - f(x - h)) / (2.0 * h)


def forward_diff_first(f, x: float, h: float) -> float:
    """
    First derivative via forward difference:
        f'(x) ≈ [f(x+h) − f(x)] / h
    """
    return (f(x + h) - f(x)) / h


def backward_diff_first(f, x: float, h: float) -> float:
    """
    First derivative via backward difference:
        f'(x) ≈ [f(x) − f(x−h)] / h
    """
    return (f(x) - f(x - h)) / h


def central_diff_second(f, x: float, h: float) -> float:
    """
    Second derivative via central difference:
        f''(x) ≈ [f(x+h) − 2f(x) + f(x−h)] / h²
    """
    return (f(x + h) - 2.0 * f(x) + f(x - h)) / (h ** 2)


def richardson_extrapolation(f, x_val: float, h: float,
                              order: int = 1, levels: int = 4,
                              method: str = 'central'):
    """
    Build the Richardson Extrapolation table.

    Parameters
    ----------
    f : callable
        The function to differentiate.
    x_val : float
        The point at which to approximate the derivative.
    h : float
        Initial step size.
    order : int
        Derivative order (1 or 2).
    levels : int
        Number of Richardson levels (rows in the table).
    method : str
        Difference method ('central', 'forward', 'backward').

    Returns
    -------
    dict with keys:
        'table'       — 2-D list (Richardson triangle), table[i][j]
        'step_sizes'  — list of step sizes used per level
        'final_value' — best approximation (bottom-right of triangle)
        'steps'       — list of dicts describing each computation step
    """
    if order not in (1, 2):
        raise ValueError("Only first (1) and second (2) derivatives are supported.")
    if h <= 0:
        raise ValueError("Step size h must be positive.")
    if levels < 1:
        raise ValueError("Number of levels must be at least 1.")

    method = method.lower()
    if method not in ('central', 'forward', 'backward'):
        raise ValueError("Method must be 'central', 'forward', or 'backward'.")

    # Second derivative only supports central in this implementation
    if order == 2 and method != 'central':
        method = 'central'

    # Determine p value (base error O(h^p))
    if order == 1:
        if method == 'central':
            p = 2
            diff_func = central_diff_first
        elif method == 'forward':
            p = 1
            diff_func = forward_diff_first
        elif method == 'backward':
            p = 1
            diff_func = backward_diff_first
    else:  # order == 2
        p = 2
        diff_func = central_diff_second

    # ------------------------------------------------------------------
    # Column 0: base finite-difference approximations at h, h/2, h/4, …
    # ------------------------------------------------------------------
    step_sizes = [h / (2 ** i) for i in range(levels)]
    table = [[None] * levels for _ in range(levels)]
    steps = []

    for i in range(levels):
        hi = step_sizes[i]
        val = diff_func(f, x_val, hi)
        table[i][0] = val

        if order == 1:
            if method == 'central':
                fx_plus = f(x_val + hi)
                fx_minus = f(x_val - hi)
                steps.append({
                    'level': i,
                    'column': 0,
                    'h': hi,
                    'description': (
                        f"D[{i},0] = (f(x+h) - f(x-h)) / (2h)\n"
                        f"     = ({_fmt(fx_plus)} - ({_fmt(fx_minus)})) / (2 x {_fmt(hi)})\n"
                        f"     = {_fmt(val)}"
                    ),
                    'value': val,
                })
            elif method == 'forward':
                fx_plus = f(x_val + hi)
                fx_0 = f(x_val)
                steps.append({
                    'level': i,
                    'column': 0,
                    'h': hi,
                    'description': (
                        f"D[{i},0] = (f(x+h) - f(x)) / h\n"
                        f"     = ({_fmt(fx_plus)} - ({_fmt(fx_0)})) / {_fmt(hi)}\n"
                        f"     = {_fmt(val)}"
                    ),
                    'value': val,
                })
            elif method == 'backward':
                fx_0 = f(x_val)
                fx_minus = f(x_val - hi)
                steps.append({
                    'level': i,
                    'column': 0,
                    'h': hi,
                    'description': (
                        f"D[{i},0] = (f(x) - f(x-h)) / h\n"
                        f"     = ({_fmt(fx_0)} - ({_fmt(fx_minus)})) / {_fmt(hi)}\n"
                        f"     = {_fmt(val)}"
                    ),
                    'value': val,
                })
        else:
            fx_plus = f(x_val + hi)
            fx_0 = f(x_val)
            fx_minus = f(x_val - hi)
            steps.append({
                'level': i,
                'column': 0,
                'h': hi,
                'description': (
                    f"D[{i},0] = (f(x+h) - 2*f(x) + f(x-h)) / h^2\n"
                    f"     = ({_fmt(fx_plus)} - 2*{_fmt(fx_0)} + ({_fmt(fx_minus)})) / ({_fmt(hi)})^2\n"
                    f"     = {_fmt(val)}"
                ),
                'value': val,
            })

    # ------------------------------------------------------------------
    # Columns 1, 2, … : Richardson combination
    # D[i][j] = (2^(p*j) · D[i][j-1] − D[i-1][j-1]) / (2^(p*j) − 1)
    # ------------------------------------------------------------------
    for j in range(1, levels):
        power = 2 ** (p * j)
        for i in range(j, levels):
            prev_curr = table[i][j - 1]
            prev_above = table[i - 1][j - 1]
            val = (power * prev_curr - prev_above) / (power - 1)
            table[i][j] = val

            steps.append({
                'level': i,
                'column': j,
                'h': step_sizes[i],
                'description': (
                    f"D[{i},{j}] = (2^({p}*{j}) * D[{i},{j-1}] - D[{i-1},{j-1}]) / (2^({p}*{j}) - 1)\n"
                    f"     = ({power} * {_fmt(prev_curr)} - {_fmt(prev_above)}) / ({power - 1})\n"
                    f"     = {_fmt(val)}"
                ),
                'value': val,
            })

    final_value = table[levels - 1][levels - 1]

    return {
        'table': table,
        'step_sizes': step_sizes,
        'final_value': final_value,
        'steps': steps,
        'method_used': method,
        'p': p
    }
