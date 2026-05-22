/**
 * calculator.js — Interactive Richardson Extrapolation Calculator
 *
 * Handles form submission, API calls, and dynamic result rendering.
 */

const DECIMALS = 4;

function fmt4(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(DECIMALS) : String(value);
}

document.addEventListener('DOMContentLoaded', () => {
    const form      = document.getElementById('calc-form');
    const btnText   = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');
    const errorBox  = document.getElementById('error-box');
    const resultsPanel = document.getElementById('results-panel');
    const orderSelect = document.getElementById('order');
    const methodSelect = document.getElementById('method');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    let currentChart = null;
    let lastCalcData = null;

    // Disable Forward/Backward if Second Derivative is chosen
    orderSelect.addEventListener('change', (e) => {
        const isSecondOrder = e.target.value === '2';
        const options = methodSelect.querySelectorAll('option[data-first-only="true"]');
        options.forEach(opt => {
            opt.disabled = isSecondOrder;
        });
        if (isSecondOrder && methodSelect.value !== 'central') {
            methodSelect.value = 'central';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();
        showLoading(true);
        resultsPanel.style.display = 'none';

        // Gather inputs
        const expression = document.getElementById('expression').value.trim();
        const xVal       = document.getElementById('x-value').value.trim();
        const hVal       = document.getElementById('h-value').value.trim();
        const order      = document.getElementById('order').value;
        const method     = document.getElementById('method').value;

        // Client-side validation (basic — server does full parsing)
        if (!expression) { showError('Please enter a mathematical expression.'); showLoading(false); return; }
        if (!xVal) { showError('Please enter a value for x.'); showLoading(false); return; }
        if (!hVal) { showError('Please enter a value for step size h.'); showLoading(false); return; }

        // Send raw strings — the server parses expressions like pi/4, sqrt(2)
        const payload = {
            expression,
            x: xVal,
            h: hVal,
            order: parseInt(order),
            method: method,
        };

        try {
            // ── Calculation request ──────────────────────────────
            const calcRes = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const calcData = await calcRes.json();

            if (calcData.error) {
                showError(calcData.error);
                showLoading(false);
                return;
            }

            // Show results panel
            lastCalcData = calcData;
            resultsPanel.style.display = 'block';
            renderSummary(calcData);
            renderTable(calcData);
            renderSteps(calcData);
            renderChart(calcData);

        } catch (err) {
            showError('Network error — could not reach the server. Is it running?');
        } finally {
            showLoading(false);
        }
    });

    // ── Export to PDF ───────────────────────────────────────────
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', () => exportResultsToPdf());
    }

    /* ── Render Functions ──────────────────────────────────────── */

    function renderSummary(data) {
        const container = document.getElementById('summary-content');
        const orderLabel = data.order === 1 ? "f'(x)" : "f''(x)";
        
        let methodName = "Central";
        if (data.method === "forward") methodName = "Forward";
        if (data.method === "backward") methodName = "Backward";

        let items = [
            { label: 'Function', value: `f(x) = ${data.expression}` },
            { label: 'Point', value: `x = ${fmt4(data.x)}` },
            { label: 'Step size', value: `h = ${fmt4(data.h)}` },
            { label: 'Derivative', value: orderLabel },
            { label: 'Method / Base Error', value: `${methodName} / O(h^${data.p})` },
            { label: 'Best Approximation', value: fmt4(data.final_value), highlight: true },
        ];

        if (data.exact_value !== null) {
            items.push({ label: 'Exact Value', value: fmt4(data.exact_value) });
            items.push({ label: 'Absolute Error', value: fmt4(data.absolute_error) });
        }

        container.innerHTML = items.map(item => `
            <div class="summary-item${item.highlight ? ' summary-item--highlight' : ''}">
                <div class="summary-label">${item.label}</div>
                <div class="summary-value${item.highlight ? ' highlight' : ''}">${escapeHtml(String(item.value))}</div>
            </div>
        `).join('');
    }


    function renderTable(data) {
        const container = document.getElementById('richardson-table-container');
        const levels = data.levels;

        let headerCells = '<th>h</th>';
        for (let j = 0; j < levels; j++) {
            headerCells += `<th>O(h^${2 * (j + 1)})</th>`;
        }

        let rows = '';
        for (let i = 0; i < levels; i++) {
            let cells = `<td>${fmt4(data.step_sizes[i])}</td>`;
            for (let j = 0; j < levels; j++) {
                const val = data.table[i][j];
                cells += `<td>${val !== null ? fmt4(val) : ''}</td>`;
            }
            rows += `<tr>${cells}</tr>`;
        }

        container.innerHTML = `
            <table class="richardson-table">
                <thead><tr>${headerCells}</tr></thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }


    function renderSteps(data) {
        const container = document.getElementById('steps-container');
        
        const baseSteps = data.steps.filter(s => s.column === 0);
        const extraSteps = data.steps.filter(s => s.column > 0);

        let html = '';

        if (baseSteps.length > 0) {
            html += `<h3 class="step-phase-heading">Phase 1: Base Finite-Difference Estimates</h3>`;
            html += `<div class="steps-list">`;
            html += baseSteps.map(step => `
                <div class="step-item">
                    <div class="text-step">${escapeHtml(step.description)}</div>
                </div>
            `).join('');
            html += `</div>`;
        }

        if (extraSteps.length > 0) {
            html += `<h3 class="step-phase-heading">Phase 2: Richardson Extrapolation Levels</h3>`;
            html += `<div class="steps-list">`;
            html += extraSteps.map(step => `
                <div class="step-item">
                    <div class="text-step">${escapeHtml(step.description)}</div>
                </div>
            `).join('');
            html += `</div>`;
        }

        container.innerHTML = html;
    }


    function renderChart(data) {
        const ctx = document.getElementById('mainChart').getContext('2d');
        if (currentChart) {
            currentChart.destroy();
        }

        const xs = data.plot_data.xs;
        const ys = data.plot_data.ys;
        const targetX = data.x;
        const targetY = data.final_value;

        // Base line series
        const linePoints = xs.map((val, idx) => ({ x: val, y: ys[idx] }));

        currentChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: `f(x) = ${data.expression}`,
                        data: linePoints,
                        showLine: true,
                        borderColor: '#0ea5e9',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1
                    },
                    {
                        label: `Evaluation Point x = ${fmt4(targetX)}`,
                        data: [{ x: targetX, y: targetY }],
                        backgroundColor: '#ef4444',
                        borderColor: '#fff',
                        borderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#e2e8f0' } },
                    tooltip: {
                        callbacks: {
                            label(ctx) {
                                const x = fmt4(ctx.parsed.x);
                                const y = fmt4(ctx.parsed.y);
                                return `${ctx.dataset.label}: (${x}, ${y})`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => fmt4(v),
                        },
                    },
                    y: {
                        grid: { color: '#334155' },
                        ticks: {
                            color: '#94a3b8',
                            callback: (v) => fmt4(v),
                        },
                    },
                },
            }
        });
    }


    /* ── PDF export (dedicated clean report document) ─────────── */

    function getSummaryItems(data) {
        const orderLabel = data.order === 1 ? "f'(x)" : "f''(x)";
        let methodName = 'Central';
        if (data.method === 'forward') methodName = 'Forward';
        if (data.method === 'backward') methodName = 'Backward';

        const items = [
            { label: 'Function', value: `f(x) = ${data.expression}` },
            { label: 'Point', value: `x = ${fmt4(data.x)}` },
            { label: 'Step size', value: `h = ${fmt4(data.h)}` },
            { label: 'Derivative', value: orderLabel },
            { label: 'Method / Base Error', value: `${methodName} / O(h^${data.p})` },
            { label: 'Best Approximation', value: fmt4(data.final_value), highlight: true },
        ];

        if (data.exact_value !== null) {
            items.push({ label: 'Exact Value', value: fmt4(data.exact_value) });
            items.push({ label: 'Absolute Error', value: fmt4(data.absolute_error) });
        }

        return items;
    }

    function buildPdfTableHtml(data) {
        const levels = data.levels;
        let headers = '<th>h</th>';
        for (let j = 0; j < levels; j++) {
            headers += `<th>O(h^${2 * (j + 1)})</th>`;
        }

        let rows = '';
        for (let i = 0; i < levels; i++) {
            let cells = `<td>${fmt4(data.step_sizes[i])}</td>`;
            for (let j = 0; j < levels; j++) {
                const val = data.table[i][j];
                cells += `<td>${val !== null ? fmt4(val) : ''}</td>`;
            }
            rows += `<tr>${cells}</tr>`;
        }

        return `<table class="pdf-table"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    }

    function buildPdfStepsHtml(data) {
        const baseSteps = data.steps.filter((s) => s.column === 0);
        const extraSteps = data.steps.filter((s) => s.column > 0);
        let html = '';

        if (baseSteps.length > 0) {
            html += '<h3 class="pdf-step-phase">Phase 1: Base Finite-Difference Estimates</h3>';
            html += baseSteps.map((step) => `
                <div class="pdf-step-box"><pre class="pdf-step-text">${escapeHtml(step.description)}</pre></div>
            `).join('');
        }

        if (extraSteps.length > 0) {
            html += '<h3 class="pdf-step-phase">Phase 2: Richardson Extrapolation Levels</h3>';
            html += extraSteps.map((step) => `
                <div class="pdf-step-box"><pre class="pdf-step-text">${escapeHtml(step.description)}</pre></div>
            `).join('');
        }

        return html;
    }

    function buildPdfReportElement(data) {
        const summaryHtml = getSummaryItems(data).map((item) => `
            <div class="pdf-summary-card${item.highlight ? ' pdf-summary-card--highlight' : ''}">
                <div class="pdf-summary-label">${escapeHtml(item.label)}</div>
                <div class="pdf-summary-value">${escapeHtml(String(item.value))}</div>
            </div>
        `).join('');

        const chartSrc = currentChart ? currentChart.toBase64Image('image/png', 1) : '';
        const chartHtml = chartSrc
            ? `<img class="pdf-chart-img" src="${chartSrc}" alt="Function graph" />`
            : '<p class="pdf-muted">Graph not available.</p>';

        const wrapper = document.createElement('div');
        wrapper.className = 'pdf-export-root';
        wrapper.setAttribute('aria-hidden', 'true');
        wrapper.innerHTML = `
            <div class="pdf-report-document">
                <header class="pdf-report-header">
                    <h1>Richardson Extrapolation Report</h1>
                    <p>Generated ${escapeHtml(new Date().toLocaleString())}</p>
                </header>

                <section class="pdf-section">
                    <h2>Result Summary</h2>
                    <div class="pdf-summary-grid">${summaryHtml}</div>
                </section>

                <section class="pdf-section">
                    <h2>Richardson Extrapolation Table</h2>
                    ${buildPdfTableHtml(data)}
                </section>

                <section class="pdf-section pdf-section-graph">
                    <h2>Function Graph</h2>
                    ${chartHtml}
                </section>

                <div class="pdf-break-before"></div>

                <section class="pdf-section">
                    <h2>Step-by-Step Solution</h2>
                    ${buildPdfStepsHtml(data)}
                </section>
            </div>
        `;

        document.body.appendChild(wrapper);
        return wrapper.querySelector('.pdf-report-document');
    }

    function removePdfExportRoot(root) {
        if (root && root.parentNode) {
            root.parentNode.removeChild(root);
        }
    }

    function waitForImages(container) {
        const images = Array.from(container.querySelectorAll('img'));
        if (images.length === 0) return Promise.resolve();

        return Promise.all(images.map((img) => new Promise((resolve) => {
            if (img.complete) {
                resolve();
                return;
            }
            img.onload = () => resolve();
            img.onerror = () => resolve();
        })));
    }

    async function exportResultsToPdf() {
        if (!lastCalcData) {
            showError('Run a calculation first, then export the report.');
            return;
        }

        if (typeof html2pdf !== 'function') {
            showError('PDF library failed to load. Refresh the page and try again.');
            return;
        }

        const oldBtnText = exportPdfBtn.textContent;
        exportPdfBtn.disabled = true;
        exportPdfBtn.textContent = 'Exporting…';

        let exportWrapper = null;

        try {
            const reportEl = buildPdfReportElement(lastCalcData);
            exportWrapper = reportEl.parentElement;

            await waitForImages(reportEl);
            await new Promise((resolve) => setTimeout(resolve, 200));

            const opt = {
                margin: [12, 12, 14, 12],
                filename: 'Richardson_Extrapolation_Report.pdf',
                image: { type: 'jpeg', quality: 0.95 },
                html2canvas: {
                    scale: 2,
                    backgroundColor: '#ffffff',
                    useCORS: true,
                    logging: false,
                },
                pagebreak: {
                    mode: ['css', 'legacy'],
                    before: '.pdf-break-before',
                    avoid: '.pdf-section-graph',
                },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
            };

            await html2pdf().set(opt).from(reportEl).save();
        } catch (err) {
            console.error(err);
            showError('PDF export failed. Please try again.');
        } finally {
            exportPdfBtn.disabled = false;
            exportPdfBtn.textContent = oldBtnText;
            removePdfExportRoot(exportWrapper);
        }
    }

    /* ── Helpers ───────────────────────────────────────────────── */

    function showError(msg) {
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
    }

    function hideError() {
        errorBox.style.display = 'none';
        errorBox.textContent = '';
    }

    function showLoading(loading) {
        btnText.style.display   = loading ? 'none' : '';
        btnLoader.style.display = loading ? '' : 'none';
        document.getElementById('calc-btn').disabled = loading;
    }

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
});
