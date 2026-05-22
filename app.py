"""
app.py — Flask application for Richardson Extrapolation Calculator

Routes:
  GET  /             → Home page
  GET  /theory       → Theory / discussion page
  GET  /examples     → Worked examples page
  GET  /calculator   → Interactive calculator page
  POST /api/calculate → JSON API — run Richardson algorithm
  POST /api/plot      → JSON API — generate graphs
"""

import os

from flask import Flask, render_template, request, jsonify, send_from_directory
import numpy as np

from utils.parser import parse_expression, make_callable, evaluate_exact, parse_numeric_expression
from utils.richardson import richardson_extrapolation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'public', 'static')

app = Flask(__name__)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve CSS/JS on Vercel when requests hit Flask (fallback if CDN route misses)."""
    return send_from_directory(STATIC_DIR, filename)


# ── Page Routes ──────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/theory')
def theory():
    return render_template('theory.html')


@app.route('/examples')
def examples():
    return render_template('examples.html')


@app.route('/calculator')
def calculator():
    return render_template('calculator.html')


# ── API Routes ───────────────────────────────────────────────────────

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """
    Expects JSON:
      { "expression": "sin(x)", "x": 0.7854, "h": 0.1, "order": 1 }
    Returns JSON with step-by-step solution, Richardson table, final value,
    exact value, and error.
    """
    try:
        data = request.get_json(force=True)

        # ── Validate inputs ──────────────────────────────────────────
        expr_str = data.get('expression', '').strip()
        if not expr_str:
            return jsonify({'error': 'Please enter a mathematical expression.'}), 400

        try:
            x_raw = str(data.get('x', '')).strip()
            x_val = parse_numeric_expression(x_raw)
        except (TypeError, ValueError) as ve:
            return jsonify({'error': f'Invalid x value: {ve}'}), 400

        try:
            h_raw = str(data.get('h', '')).strip()
            h_val = parse_numeric_expression(h_raw)
        except (TypeError, ValueError) as ve:
            return jsonify({'error': f'Invalid step size h: {ve}'}), 400

        if h_val <= 0:
            return jsonify({'error': 'Step size h must be a positive number.'}), 400

        try:
            order = int(data.get('order', 1))
        except (TypeError, ValueError):
            order = 1
        if order not in (1, 2):
            return jsonify({'error': 'Derivative order must be 1 or 2.'}), 400

        method = data.get('method', 'central').strip()

        # ── Parse expression ─────────────────────────────────────────
        try:
            expr = parse_expression(expr_str)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        f = make_callable(expr)

        # Quick sanity check — can we evaluate f(x)?
        try:
            test_val = f(x_val)
            if not np.isfinite(test_val):
                return jsonify({
                    'error': f'f({x_val}) is not finite. Check your function and x value.'
                }), 400
        except Exception:
            return jsonify({
                'error': f'Cannot evaluate the function at x = {x_val}.'
            }), 400

        # ── Run Richardson Extrapolation ─────────────────────────────
        levels = 4
        result = richardson_extrapolation(f, x_val, h_val,
                                          order=order, levels=levels, method=method)

        # ── Exact value for comparison ───────────────────────────────
        exact = evaluate_exact(expr, x_val, order)

        # ── Generate Plot Data ───────────────────────────────────────
        xs_plot = np.linspace(x_val - 3, x_val + 3, 200)
        ys_plot = []
        for x_p in xs_plot:
            try:
                y_p = float(f(x_p))
                ys_plot.append(round(y_p, 4) if np.isfinite(y_p) else None)
            except Exception:
                ys_plot.append(None)

        # ── Build response ───────────────────────────────────────────
        # Convert table to serializable format
        table_data = []
        for i, row in enumerate(result['table']):
            table_row = []
            for j, val in enumerate(row):
                table_row.append(round(val, 4) if val is not None else None)
            table_data.append(table_row)

        response = {
            'expression': expr_str,
            'x': round(x_val, 4),
            'h': round(h_val, 4),
            'order': order,
            'method': result['method_used'],
            'p': result['p'],
            'levels': levels,
            'step_sizes': [round(s, 4) for s in result['step_sizes']],
            'table': table_data,
            'final_value': round(result['final_value'], 4),
            'steps': result['steps'],
            'exact_value': round(exact, 4) if exact is not None else None,
            'absolute_error': (
                round(abs(result['final_value'] - exact), 4)
                if exact is not None else None
            ),
            'plot_data': {
                'xs': [round(x, 4) for x in xs_plot],
                'ys': ys_plot,
            }
        }
        return jsonify(response)

    except Exception as exc:
        return jsonify({
            'error': f'An unexpected error occurred: {str(exc)}'
        }), 500


# ── Entry point ──────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
