# DCF Valuation — C25 Index

A Python tool that builds a **Discounted Cash Flow (DCF) model** for all stocks in the Danish C25 index, using live financial data to estimate intrinsic value and identify potential buying opportunities.

![DCF Chart](output/dcf_c25.png)

---

## What it does

- Fetches real financial data (Free Cash Flow, shares outstanding, current price) via `yfinance`
- Projects future cash flows over 5 years using a two-stage DCF model
- Calculates intrinsic value per share and compares it to the current market price
- Outputs a **margin of safety** for each stock and flags it as undervalued, fairly valued, or overvalued
- Saves results to CSV and generates a visualisation

---

## The DCF Model

The intrinsic value is estimated using a classic two-stage model:

**Stage 1 — Projected FCF (years 1–5)**

$$
PV_t = \frac{FCF_0 \times (1 + g)^t}{(1 + r)^t}
$$

**Stage 2 — Terminal Value (Gordon Growth Model)**

$$
TV = \frac{FCF_5 \times (1 + g_{terminal})}{r - g_{terminal}}
$$

**Intrinsic Value per Share**

$$
\text{IV} = \frac{\sum PV_t + PV_{terminal}}{\text{shares outstanding}}
$$

| Parameter | Value | Description |
|---|---|---|
| Discount rate `r` | 10% | Required rate of return (WACC proxy) |
| FCF growth rate `g` | 7% | Near-term annual FCF growth |
| Terminal growth `g_terminal` | 2.5% | Long-run sustainable growth |
| Projection horizon | 5 years | Forecast window |

---

## Project Structure

```
dcf-c25/
├── dcf.py               # Main script (run from terminal)
├── dcf_notebook.ipynb   # Jupyter notebook with walkthrough & charts
├── requirements.txt     # Python dependencies
├── output/
│   ├── dcf_results.csv  # Full results table
│   └── dcf_c25.png      # Margin of safety chart
└── README.md
```

---

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/dcf-c25.git
cd dcf-c25
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3a. Run the script**
```bash
python dcf.py
```

**3b. Or open the notebook**
```bash
jupyter notebook dcf_notebook.ipynb
```

---

## Example Output

```
─────────────────────────────────────────────────────
  DCF Valuation — C25 Index   (WACC=10%, g=2.5%)
─────────────────────────────────────────────────────
  Fetching Novo Nordisk          (NOVO-B.CO) ... 🟢 Undervalued
  Fetching A.P. Møller-Mærsk     (MAERSK-B.CO) ... 🔴 Overvalued
  Fetching Pandora               (PNDORA.CO) ... 🟢 Undervalued
  ...
```

---

## Limitations & Disclaimer

- Growth assumptions are **uniform across all companies** for simplicity. A full analysis would use company-specific guidance and analyst consensus estimates.
- DCF models are highly sensitive to input assumptions — small changes in discount rate or growth rate produce large swings in intrinsic value.
- Data is sourced from Yahoo Finance and may not reflect the most recent filings.

> ⚠️ **This is not investment advice.** This project is for educational and portfolio demonstration purposes only.

---

## Tech Stack

`Python` · `yfinance` · `pandas` · `matplotlib` · `Jupyter`
