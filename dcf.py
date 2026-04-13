"""
DCF Valuation Tool — C25 Index Stocks
======================================
Fetches real financial data via yfinance and builds a Discounted Cash Flow
model to estimate intrinsic value vs current market price.
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
import os

warnings.filterwarnings("ignore")

# ─── C25 constituents (ticker : display name) ────────────────────────────────
C25_STOCKS = {
    "NOVO-B.CO":    "Novo Nordisk",
    "FLS.CO":       "FLSmidth",
    "MAERSK-B.CO":  "A.P. Møller-Mærsk B",
    "ORSTED.CO":    "Ørsted",
    "CARL-B.CO":    "Carlsberg",
    "NSIS-B.CO":    "Novonesis",
    "DSV.CO":       "DSV",
    "DEMANT.CO":    "Demant",
    "GN.CO":        "GN Store Nord",
    "COLO-B.CO":    "Coloplast",
    "AMBU-B.CO":    "Ambu",
    "TRYG.CO":      "Tryg",
    "RBREW.CO":     "Royal Unibrew",
    "ROCK-B.CO":    "Rockwool",
    "PNDORA.CO":    "Pandora",
    "DANSKE.CO":    "Danske Bank",
    "GMAB.CO":      "Genmab",
    "VWS.CO":       "Vestas Wind Systems",
    "ZEAL.CO":      "Zealand Pharma",
    "ISS.CO":       "ISS",
    "NKT.CO":       "NKT",
    "NDA-DK.CO":    "Nordea Bank",
    "JYSK.CO":      "Jyske Bank",
    "ALSYDB.CO":    "AL Sydbank",
    "BAVA.CO":      "Bavarian Nordic",
}

# ─── DCF parameters ───────────────────────────────────────────────────────────
PROJECTION_YEARS  = 5      # years to project free cash flow
DISCOUNT_RATE     = 0.10   # WACC / required rate of return (10%)
TERMINAL_GROWTH   = 0.025  # long-term growth rate (2.5%)
FCF_GROWTH_RATE   = 0.07   # assumed annual FCF growth rate (7%)


def fetch_stock_data(ticker: str) -> dict | None:
    """Download key financials for a single ticker."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        cf    = stock.cashflow

        # Free Cash Flow = Operating Cash Flow - Capital Expenditures
        if cf is None or cf.empty:
            return None

        # yfinance labels vary; try common keys
        op_cf_key  = next((k for k in cf.index if "Operating" in k and "Cash" in k), None)
        capex_key  = next((k for k in cf.index if "Capital" in k and "Expenditure" in k), None)

        if op_cf_key is None:
            return None

        operating_cf = cf.loc[op_cf_key].iloc[0]
        capex        = cf.loc[capex_key].iloc[0] if capex_key else 0
        fcf          = operating_cf - abs(capex)

        shares       = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        currency     = info.get("currency", "DKK")

        if not shares or not current_price or fcf <= 0:
            return None

        return {
            "ticker":        ticker,
            "name":          info.get("longName", ticker),
            "current_price": current_price,
            "shares":        shares,
            "fcf":           fcf,
            "currency":      currency,
        }

    except Exception:
        return None


def run_dcf(fcf: float, shares: float) -> float:
    """
    Classic 2-stage DCF:
      Stage 1 — project FCF over PROJECTION_YEARS at FCF_GROWTH_RATE
      Stage 2 — terminal value using Gordon Growth Model
    Returns intrinsic value per share.
    """
    projected_fcfs = []
    for year in range(1, PROJECTION_YEARS + 1):
        projected_fcf = fcf * (1 + FCF_GROWTH_RATE) ** year
        pv            = projected_fcf / (1 + DISCOUNT_RATE) ** year
        projected_fcfs.append(pv)

    terminal_fcf   = fcf * (1 + FCF_GROWTH_RATE) ** PROJECTION_YEARS
    terminal_value = terminal_fcf * (1 + TERMINAL_GROWTH) / (DISCOUNT_RATE - TERMINAL_GROWTH)
    pv_terminal    = terminal_value / (1 + DISCOUNT_RATE) ** PROJECTION_YEARS

    intrinsic_value = (sum(projected_fcfs) + pv_terminal) / shares
    return intrinsic_value


def analyse_all() -> pd.DataFrame:
    """Run DCF on all C25 stocks and return a results DataFrame."""
    results = []
    print(f"\n{'─'*55}")
    print(f"  DCF Valuation — C25 Index   (WACC={DISCOUNT_RATE:.0%}, g={TERMINAL_GROWTH:.1%})")
    print(f"{'─'*55}")

    for ticker, display_name in C25_STOCKS.items():
        print(f"  Fetching {display_name:<22} ({ticker}) ...", end=" ", flush=True)
        data = fetch_stock_data(ticker)

        if data is None:
            print("skipped (missing data)")
            continue

        intrinsic = run_dcf(data["fcf"], data["shares"])
        margin    = (intrinsic - data["current_price"]) / data["current_price"] * 100
        verdict   = "🟢 Undervalued" if margin > 10 else ("🔴 Overvalued" if margin < -10 else "🟡 Fairly Valued")

        print(f"{verdict}")
        results.append({
            "Ticker":          ticker,
            "Company":         display_name,
            "Currency":        data["currency"],
            "Current Price":   round(data["current_price"], 2),
            "Intrinsic Value": round(intrinsic, 2),
            "Margin of Safety": round(margin, 1),
            "Verdict":         verdict,
        })

    print(f"{'─'*55}\n")
    return pd.DataFrame(results)


def plot_results(df: pd.DataFrame):
    """Bar chart comparing intrinsic value vs current price for all stocks."""
    if df.empty:
        print("No data to plot.")
        return

    df_sorted = df.sort_values("Margin of Safety", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    colors = []
    for m in df_sorted["Margin of Safety"]:
        if m > 10:
            colors.append("#00c49a")   # undervalued — green
        elif m < -10:
            colors.append("#ff4d6d")   # overvalued  — red
        else:
            colors.append("#ffd166")   # fair value  — yellow

    bars = ax.barh(df_sorted["Company"], df_sorted["Margin of Safety"],
                   color=colors, edgecolor="none", height=0.6)

    ax.axvline(0, color="#ffffff", linewidth=0.8, linestyle="--", alpha=0.5)

    # Annotate bars
    for bar, val in zip(bars, df_sorted["Margin of Safety"]):
        x = bar.get_width()
        ax.text(x + (1 if x >= 0 else -1), bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%", va="center", ha="left" if x >= 0 else "right",
                color="white", fontsize=8.5)

    ax.set_xlabel("Margin of Safety (%)", color="#aaaaaa", labelpad=8)
    ax.set_title("DCF Valuation — C25 Index\nMargin of Safety vs Current Price",
                 color="white", fontsize=14, pad=16, fontweight="bold")
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.label.set_color("#aaaaaa")

    legend_items = [
        mpatches.Patch(color="#00c49a", label="Undervalued (>+10%)"),
        mpatches.Patch(color="#ffd166", label="Fairly Valued (±10%)"),
        mpatches.Patch(color="#ff4d6d", label="Overvalued (<-10%)"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              framealpha=0.15, labelcolor="white", fontsize=9)

    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    out_path = "output/dcf_c25.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  Chart saved → {out_path}")
    plt.show()


def main():
    df = analyse_all()
    if df.empty:
        print("No results — check your internet connection or ticker symbols.")
        return

    # Save CSV
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/dcf_results.csv", index=False)
    print(f"  Results saved → output/dcf_results.csv\n")

    print(df[["Company", "Current Price", "Intrinsic Value", "Margin of Safety", "Verdict"]]
          .to_string(index=False))
    print()

    plot_results(df)


if __name__ == "__main__":
    main()
