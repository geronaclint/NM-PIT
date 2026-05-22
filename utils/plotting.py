"""
plotting.py — Graph generation for Richardson Extrapolation Calculator

Generates base64-encoded PNG images for:
  1. Function plot around the evaluation point
  2. Approximation comparison (bar chart)
  3. Error convergence (log-scale)
"""

import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt


# Consistent styling
COLORS = {
    'primary': '#e2e8f0',   # light text
    'accent': '#38bdf8',    # sky blue
    'success': '#10b981',   # emerald
    'warning': '#f59e0b',   # amber
    'grid': '#334155',      # subtle border
    'bg': '#1e293b',        # surface background (matches cards)
    'line': '#0ea5e9',      # function plot line
}


def _fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['bg'], edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def plot_function(f, x_val: float, h: float, expr_str: str) -> str:
    """
    Plot the function over a region around x_val.
    Returns base64-encoded PNG.
    """
    margin = max(abs(h) * 8, 2.0)
    x_min, x_max = x_val - margin, x_val + margin
    xs = np.linspace(x_min, x_max, 400)

    # Evaluate safely
    with np.errstate(all='ignore'):
        ys = np.array([f(xi) for xi in xs], dtype=float)
    mask = np.isfinite(ys)

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    ax.plot(xs[mask], ys[mask], color=COLORS['line'], linewidth=2,
            label=f'f(x) = {expr_str}')
    ax.axvline(x_val, color=COLORS['warning'], linestyle='--', linewidth=1.2,
               label=f'x = {x_val:.4f}')
    # Mark the point
    try:
        y_point = f(x_val)
        if np.isfinite(y_point):
            ax.plot(x_val, y_point, 'o', color=COLORS['warning'],
                    markersize=8, zorder=5)
    except Exception:
        pass

    ax.set_xlabel('x', fontsize=11)
    ax.set_ylabel('f(x)', fontsize=11)
    ax.set_title('Function Plot', fontsize=13, fontweight='bold',
                 color=COLORS['primary'])
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3, color=COLORS['grid'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return _fig_to_base64(fig)


def plot_approximations(table, exact_val, step_sizes) -> str:
    """
    Bar chart comparing column-0 (base) approximations and the best
    Richardson value against the exact derivative.
    """
    levels = len(step_sizes)
    labels = [f'h={step_sizes[i]:.4f}' for i in range(levels)]
    base_vals = [table[i][0] for i in range(levels)]
    best_val = table[-1][-1]

    labels.append('Richardson\nBest')
    base_vals.append(best_val)

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    bar_colors = [COLORS['accent']] * levels + [COLORS['success']]
    bars = ax.bar(labels, base_vals, color=bar_colors, edgecolor='white',
                  linewidth=0.5)

    if exact_val is not None:
        ax.axhline(exact_val, color=COLORS['warning'], linestyle='--',
                   linewidth=1.5, label=f'Exact = {exact_val:.4f}')
        ax.legend(fontsize=9)

    ax.set_ylabel('Approximation Value', fontsize=11)
    ax.set_title('Approximation Comparison', fontsize=13, fontweight='bold',
                 color=COLORS['primary'])
    ax.grid(axis='y', alpha=0.3, color=COLORS['grid'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(fontsize=9, rotation=15)

    return _fig_to_base64(fig)


def plot_error_convergence(table, exact_val, step_sizes) -> str:
    """
    Log-scale plot of absolute error for each Richardson column.
    """
    if exact_val is None:
        # Cannot compute errors without exact value; return a placeholder message
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor(COLORS['bg'])
        ax.set_facecolor(COLORS['bg'])
        ax.text(0.5, 0.5, 'Exact derivative unavailable\nfor error analysis',
                ha='center', va='center', fontsize=13, color='#888',
                transform=ax.transAxes)
        ax.set_title('Error Convergence', fontsize=13, fontweight='bold',
                     color=COLORS['primary'])
        ax.axis('off')
        return _fig_to_base64(fig)

    levels = len(step_sizes)
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])

    # For each column j, plot errors for rows i >= j
    max_cols = min(levels, 4)
    col_colors = [COLORS['primary'], COLORS['accent'], COLORS['success'], COLORS['warning']]

    for j in range(max_cols):
        errors = []
        hs = []
        for i in range(j, levels):
            if table[i][j] is not None:
                err = abs(table[i][j] - exact_val)
                if err > 0:
                    errors.append(err)
                    hs.append(step_sizes[i])
        if errors:
            ax.semilogy(range(len(errors)), errors, 'o-',
                        color=col_colors[j % len(col_colors)],
                        linewidth=1.5, markersize=6,
                        label=f'Column {j}')

    ax.set_xlabel('Row index', fontsize=11)
    ax.set_ylabel('|Error|  (log scale)', fontsize=11)
    ax.set_title('Error Convergence', fontsize=13, fontweight='bold',
                 color=COLORS['primary'])
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, color=COLORS['grid'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return _fig_to_base64(fig)
