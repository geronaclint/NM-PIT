# Richardson Extrapolation — Numerical Methods Online Calculator

A Flask-based web application for computing numerical derivatives using **Richardson Extrapolation**. Built as a final project for a Numerical Methods PIT requirement.

---

## Features

| Feature | Description |
|---|---|
| **Theory Page** | Complete mathematical discussion with LaTeX formulas (MathJax) |
| **Worked Examples** | Two fully solved problems (1st & 2nd derivative) with Richardson tables |
| **Interactive Calculator** | Enter any function → get step-by-step solution, table, & graphs |
| **Graph Visualization** | Function plot, approximation comparison, and error convergence |
| **Mobile Responsive** | Works on desktop, tablet, and mobile devices |
| **Safe Input Parsing** | SymPy-based parser with restricted symbol set to prevent code injection |

---

## Project Structure

```
NM CALC/
├── app.py                  # Flask entry point & routes
├── utils/
│   ├── __init__.py
│   ├── richardson.py       # Core algorithm (manual implementation)
│   ├── parser.py           # Safe expression parsing via SymPy
│   └── plotting.py         # Matplotlib graph generation
├── templates/
│   ├── base.html           # Shared layout (navbar, footer, MathJax)
│   ├── home.html           # Landing page
│   ├── theory.html         # Mathematical discussion
│   ├── examples.html       # Two worked examples
│   └── calculator.html     # Interactive calculator
├── static/
│   ├── css/style.css       # All styles
│   └── js/calculator.js    # Calculator UI logic
├── requirements.txt
├── vercel.json
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone or download the project
cd "NM CALC"

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Deployment to Vercel

1. Install the [Vercel CLI](https://vercel.com/docs/cli):
   ```bash
   npm i -g vercel
   ```

2. From the project root:
   ```bash
   vercel
   ```

3. Follow the prompts. The `vercel.json` is pre-configured.

> **Note:** Matplotlib requires system-level libraries. On Vercel's serverless environment, plot generation may need the `Agg` backend (already configured) and may have cold-start latency.

---

## Architecture Overview

### Backend

- **`app.py`** — Flask application with five page routes and two JSON API endpoints (`/api/calculate`, `/api/plot`).
- **`utils/parser.py`** — Uses `sympy.sympify` with a whitelist of allowed names (`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `pi`, `e`, `x`) to safely parse user input. Converts to a NumPy-backed callable via `lambdify`. Also computes symbolic derivatives for error comparison.
- **`utils/richardson.py`** — Manually implements central-difference formulas and builds the Richardson Extrapolation table column-by-column. No built-in differentiation functions are used. Returns structured data including every computation step.
- **`utils/plotting.py`** — Generates three Matplotlib figures (function plot, bar chart, error convergence), returns them as base64-encoded PNGs.

### Frontend

- **`templates/`** — Jinja2 templates extending `base.html`. MathJax renders all LaTeX. The calculator page uses AJAX (Fetch API) for a smooth single-page experience.
- **`static/css/style.css`** — Custom CSS with CSS variables, responsive grid layout, and a professional engineering-style palette.
- **`static/js/calculator.js`** — Client-side validation, API calls, dynamic DOM rendering for results, table, steps, and graphs.

### Safe Input Handling

User expressions are parsed by SymPy with a restricted `locals` dictionary — only mathematical functions and the variable `x` are allowed. This prevents arbitrary code execution. Additional validation includes:

- Empty field checks
- Numeric type validation
- Division-by-zero prevention (finite-value check)
- Friendly error messages for all failure modes

---

## Supported Functions

| Input | Meaning |
|---|---|
| `sin(x)` | Sine |
| `cos(x)` | Cosine |
| `tan(x)` | Tangent |
| `exp(x)` | Exponential (eˣ) |
| `log(x)` / `ln(x)` | Natural logarithm |
| `sqrt(x)` | Square root |
| `x**2` or `x^2` | Power |
| `pi`, `e` | Constants π, e |

Expressions can be combined: `sin(x)**2 + cos(x)`, `exp(-x^2)`, `x**3 - 2*x + 1`.

---

## Technologies

- **Python 3.8+** / Flask
- **SymPy** — symbolic math & expression parsing
- **NumPy** — numerical evaluation
- **Matplotlib** — plot generation
- **MathJax 3** — LaTeX rendering in the browser
- **Vanilla JS & CSS** — no frontend framework dependencies

---

## License

This project is created for academic purposes as a Numerical Methods PIT requirement.
