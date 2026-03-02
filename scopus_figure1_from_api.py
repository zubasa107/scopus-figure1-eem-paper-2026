"""
Reproduce and update Figure 1 from:
  Hong et al., "Energy Forecasting: A Review and Outlook,"
  IEEE Open Access Journal of Power and Energy, 2020.

Figure 1: Number of publications in load, price, wind and solar forecasting
returned by respective Scopus search (TITLE-ABS-KEY phrase searches).
Data are fetched via the Scopus API (pybliometrics) and plotted as
a vertical stacked bar chart (2010–2025).

Usage:
  1. Get a Scopus API key: https://dev.elsevier.com/myapikey.html
  2. Either:
     - Put ELSEVIER_API_KEY=your_key in a .env file in this folder, or
     - Set environment variable: SCOPUS_API_KEY=your_key or ELSEVIER_API_KEY=your_key
  3. Install: pip install -r requirements_scopus_figure1.txt  (or: pybliometrics pandas matplotlib)
  4. Run: python scopus_figure1_from_api.py
  5. To re-plot without re-querying Scopus: python scopus_figure1_from_api.py --plot-only

Outputs:
  - scopus_figure1_counts_optN.csv  (year-by-year counts per domain; N = query option)
  - scopus_figure1_optN.tif         (stacked bar chart; N = query option)
"""

from __future__ import annotations

import os
import sys
import time
import argparse
from pathlib import Path

# Load .env from script folder (e.g. ELSEVIER_API_KEY=...)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

_PYB_CACHE: tuple[object, dict, object] | None = None


def _require_pybliometrics():
    global _PYB_CACHE
    if _PYB_CACHE is not None:
        return _PYB_CACHE
    try:
        import pybliometrics
        from pybliometrics.utils import URLS, get_content
    except ImportError as e:
        raise SystemExit("Install pybliometrics: pip install pybliometrics") from e
    _PYB_CACHE = (pybliometrics, URLS, get_content)
    return _PYB_CACHE

import pandas as pd
import matplotlib.pyplot as plt

# Matplotlib defaults for journal-style figure
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 8,
})

# -----------------------------------------------------------------------------
# Search logic (replicated from paper methodology)
# Paper: "returned by respective Scopus search" — phrase-only, no journal filter.
# Figure 1 uses ALL Scopus results (top-10 journals apply only to Figure 2).
# -----------------------------------------------------------------------------

DOMAINS = {
    "Load": 'TITLE-ABS-KEY("load forecasting")',
    "Price": 'TITLE-ABS-KEY("electricity price forecasting")',
    "Wind": 'TITLE-ABS-KEY("wind forecasting")',
    "Solar": 'TITLE-ABS-KEY("solar forecasting")',
}

YEAR_MIN = 2010
YEAR_MAX = 2025  # include partial 2025; annotate in figure


def build_domain_queries(query_option: int, year_min: int, year_max: int) -> dict[str, str]:
    year_filter = f"PUBYEAR > {year_min - 1} AND PUBYEAR < {year_max + 1}"

    if query_option == 1:
        return {k: f"{v} AND {year_filter}" for k, v in DOMAINS.items()}

    if query_option in (2, 3, 4):
        # Expanded/high-recall queries + document type restriction.
        # Option 3 removes "OR predict*" (forecasting-only).
        # Option 4 removes "irradiance" and "speed" terms.
        forecast_pred = "(forecast* OR predict*)" if query_option in (2, 4) else "forecast*"
        doctype_filter = "DOCTYPE(ar OR re)"
        wind_terms = '("power" OR "generation")' if query_option == 4 else '("power" OR "speed" OR "generation")'
        solar_terms = '("power" OR "generation")' if query_option == 4 else '("power" OR "irradiance" OR "generation")'
        domains2 = {
            "Load": f'TITLE-ABS-KEY((("load" OR "electricity demand" OR "power demand") W/2 {forecast_pred}))',
            "Price": f'TITLE-ABS-KEY(((("electricity" OR "power") W/2 "price") AND {forecast_pred}))',
            "Wind": f'TITLE-ABS-KEY((("wind" W/2 {wind_terms}) AND {forecast_pred}))',
            "Solar": f'TITLE-ABS-KEY(((("solar" OR "photovoltaic" OR "PV") W/2 {solar_terms}) AND {forecast_pred}))',
        }
        return {k: f"{v} AND {year_filter} AND {doctype_filter}" for k, v in domains2.items()}

    if query_option == 5:
        doctype_filter = "DOCTYPE(ar OR re)"
        domains5 = {
            "Load": 'TITLE-ABS-KEY((("load" OR "electricity demand" OR "power demand") W/3 (forecast* OR predict*)))',
            "Price": 'TITLE-ABS-KEY(((("electricity" OR "power") W/3 "price") AND (forecast* OR predict*)))',
            "Wind": 'TITLE-ABS-KEY((("wind" W/3 ("power" OR "generation")) AND (forecast* OR predict*)))',
            "Solar": 'TITLE-ABS-KEY(((("solar" OR "photovoltaic" OR "PV") W/3 ("power" OR "generation")) AND (forecast* OR predict*)))',
        }
        return {k: f"{v} AND {year_filter} AND {doctype_filter}" for k, v in domains5.items()}

    if query_option == 6:
        doctype_filter = "DOCTYPE(ar OR re)"
        domains6 = {
            "Load": 'TITLE-ABS-KEY((("electricity" OR "power") W/3 ("load" OR "demand")) W/3 (forecast* OR predict*))',
            "Price": 'TITLE-ABS-KEY((("electricity" OR "power") W/3 "price") W/3 (forecast* OR predict*))',
            "Wind": 'TITLE-ABS-KEY((("wind" W/3 ("power" OR "generation")) W/3 (forecast* OR predict*)))',
            "Solar": 'TITLE-ABS-KEY(((("solar" OR "photovoltaic" OR "PV") W/3 ("power" OR "generation")) W/3 (forecast* OR predict*)))',
        }
        return {k: f"{v} AND {year_filter} AND {doctype_filter}" for k, v in domains6.items()}

    if query_option == 7:
        doctype_filter = "DOCTYPE(ar OR re)"
        domains7 = {
            "Load": 'TITLE-ABS-KEY((("electricity" OR "electric" OR "power") W/3 ("load" OR "demand")) W/3 (forecast* OR predict* OR "short-term forecast*" OR "day-ahead forecast*"))',
            "Price": 'TITLE-ABS-KEY((("electricity" OR "power" OR "energy") W/3 ("price" OR "spot price" OR "market price")) W/3 (forecast* OR predict* OR "day-ahead forecast*"))',
            "Wind": 'TITLE-ABS-KEY((("wind" W/3 ("power" OR "generation" OR "output")) W/3 (forecast* OR predict* OR "day-ahead forecast*")))',
            "Solar": 'TITLE-ABS-KEY(((("solar" OR "photovoltaic" OR "PV") W/3 ("power" OR "generation" OR "output")) W/3 (forecast* OR predict* OR "day-ahead forecast*")))',
        }
        return {k: f"{v} AND {year_filter} AND {doctype_filter}" for k, v in domains7.items()}

    raise ValueError(f"Unsupported query option: {query_option}")


def init_pybliometrics() -> None:
    """Ensure pybliometrics is configured (API key)."""
    pybliometrics, _, _ = _require_pybliometrics()
    # Prefer env / .env: ELSEVIER_API_KEY or SCOPUS_API_KEY
    api_key = (
        os.environ.get("ELSEVIER_API_KEY", "").strip()
        or os.environ.get("SCOPUS_API_KEY", "").strip()
    )
    if api_key:
        try:
            pybliometrics.init(keys=[api_key])
        except Exception as e:
            print(f"Warning: init with SCOPUS_API_KEY failed: {e}. Trying default config.")
            pybliometrics.init()
    else:
        pybliometrics.init()


def get_count_for_query(query: str, download: bool = False, subscriber: bool = False) -> int:
    """
    Run a single Scopus query and return total result count.
    Uses get_results_size() so we don't need to download records (saves quota/time).
    """
    try:
        from pybliometrics.scopus import ScopusSearch
    except ImportError as e:
        raise SystemExit("Install pybliometrics: pip install pybliometrics") from e
    try:
        s = ScopusSearch(
            query,
            download=download,
            subscriber=subscriber,
            verbose=False,
        )
        return s.get_results_size()
    except Exception as e:
        print(f"  Query failed: {query[:60]}... -> {e}", file=sys.stderr)
        return -1


def get_total_results(query: str) -> int:
    """Return the total results count for a Scopus query without downloading entries."""
    _, URLS, get_content = _require_pybliometrics()
    params = {
        "query": query,
        "view": "STANDARD",
        "count": 0,
        "start": 0,
    }
    resp = get_content(URLS["ScopusSearch"], "ScopusSearch", params=params)
    js = resp.json()
    n = js.get("search-results", {}).get("opensearch:totalResults", 0) or 0
    return int(n)


def fetch_all_counts(
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
    delay_seconds: float = 0.5,
    out_csv: str | Path | None = None,
    query_option: int = 1,
) -> pd.DataFrame:
    """
    For each domain, run a single query with a year range filter and use the
    Scopus Search API facets to get publication counts by year. Optionally save
    to CSV.
    """
    years = list(range(year_min, year_max + 1))
    wide = pd.DataFrame({"Year": years})

    facets = f"pubyear(count={len(years)},sort=na)"
    _, URLS, get_content = _require_pybliometrics()

    domain_queries = build_domain_queries(query_option=query_option, year_min=year_min, year_max=year_max)
    print(f"Scopus search strings used (option {query_option}):")
    for domain_name in ["Load", "Price", "Wind", "Solar"]:
        full_query = domain_queries.get(domain_name)
        if not full_query:
            continue
        print(f"  {domain_name}: {full_query}")

        params = {
            "query": full_query,
            "view": "STANDARD",
            "count": 1,
            "start": 0,
            "facets": facets,
        }
        resp = get_content(URLS["ScopusSearch"], "ScopusSearch", params=params)
        js = resp.json()

        facet = js.get("search-results", {}).get("facet")
        if isinstance(facet, list):
            # Some endpoints return a list of facets; select pubyear if present.
            facet = next((f for f in facet if f.get("name") == "pubyear"), facet[0] if facet else None)
        categories = facet.get("category", []) if isinstance(facet, dict) else []

        by_year: dict[int, int] = {}
        for c in categories:
            try:
                y = int(c.get("value") or c.get("name"))
                by_year[y] = int(c.get("hitCount", 0) or 0)
            except Exception:
                continue

        wide[domain_name] = [by_year.get(y, 0) for y in years]
        time.sleep(delay_seconds)

    # Ensure column order: Year, Load, Price, Wind, Solar
    for col in ["Load", "Price", "Wind", "Solar"]:
        if col not in wide.columns:
            wide[col] = 0
    wide = wide[["Year", "Load", "Price", "Wind", "Solar"]]

    if out_csv is not None:
        out_csv = Path(out_csv)
        wide.to_csv(out_csv, index=False)
        print(f"Saved counts to {out_csv}")

    return wide


def plot_figure1(
    df: pd.DataFrame,
    out_path: str | Path = "scopus_figure1.tif",
    year_max: int = YEAR_MAX,
) -> None:
    """
    Vertical stacked bar chart: year on x-axis, number of publications on y-axis,
    stacked by domain (Load, Price, Wind, Solar).
    """
    # Stack order: bottom to top = Load, Price, Solar, Wind
    domains = ["Load", "Price", "Solar", "Wind"]
    colors = {
        "Load": "#FBE3D6",
        "Price": "#C2F1C8",
        "Wind": "#83CBEB",
        "Solar": "#FFFFCC",
    }

    fig_width_in = 8.9 / 2.54
    fig_height_in = 7.0 / 2.54
    fig, ax = plt.subplots(figsize=(fig_width_in, fig_height_in))
    years = df["Year"].astype(int)
    bottom = None
    for d in domains:
        if d not in df.columns:
            continue
        vals = df[d].fillna(0).astype(int)
        if bottom is None:
            ax.bar(years, vals, label=d, color=colors.get(d, "gray"), width=0.7)
            bottom = vals.values.copy()
        else:
            ax.bar(years, vals, bottom=bottom, label=d, color=colors.get(d, "gray"), width=0.7)
            bottom = bottom + vals.values

    ax.set_xlabel("Year")
    ax.set_ylabel("Number of forecast publications")
    tick_years = years[::2]
    ax.set_xticks(tick_years)
    ax.set_xticklabels(tick_years, rotation=45, ha="right")
    handles, labels = ax.get_legend_handles_labels()
    ordered = {label: handle for handle, label in zip(handles, labels)}
    legend_order = ["Wind", "Solar", "Price", "Load"]
    ax.legend([ordered[d] for d in legend_order if d in ordered], legend_order, loc="upper left")
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure to {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reproduce Figure 1 from Scopus API counts.")
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="Skip API calls and plot from an existing counts CSV.",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Alias for --plot-only.",
    )
    parser.add_argument(
        "--counts-csv",
        type=str,
        default=None,
        help="Path to an existing counts CSV (used with --plot-only/--no-api).",
    )
    parser.add_argument(
        "--query-option",
        type=int,
        default=6,
        choices=[1, 2, 3, 4, 5, 6, 7],
        help="Query set to use for Scopus fetching (1=replication phrases; 2=expanded + DOCTYPE(ar OR re); 3=expanded minus predict* + DOCTYPE(ar OR re); 4=expanded minus irradiance/speed + DOCTYPE(ar OR re); 5=option-4 style with W/3 and (forecast* OR predict*); 6=expanded with electricity/power context + W/3 + DOCTYPE(ar OR re); 7=expanded with short-term/day-ahead terms + DOCTYPE(ar OR re)).",
    )
    return parser.parse_args()


def main() -> None:

    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    if args.counts_csv:
        csv_path = Path(args.counts_csv)
        if not csv_path.is_absolute():
            csv_path = script_dir / csv_path
    else:
        csv_path = script_dir / f"scopus_figure1_counts_opt{args.query_option}.csv"
        legacy_csv_path = script_dir / "scopus_figure1_counts.csv"
    tif_path = script_dir / f"scopus_figure1_opt{args.query_option}.tif"

    # Optional: plot from existing CSV only (no API calls)
    plot_only = (
        args.plot_only
        or args.no_api
        or os.environ.get("SCOPUS_FIGURE1_PLOT_ONLY", "")
    )
    if plot_only and csv_path.exists():
        print(f"Using existing counts from {csv_path} (no API calls).")
        df = pd.read_csv(csv_path)
        plot_figure1(df, out_path=tif_path, year_max=df["Year"].max())
        print("Done.")
        return
    if plot_only and not csv_path.exists():
        if not args.counts_csv and legacy_csv_path.exists():
            print(f"Using legacy counts file {legacy_csv_path} (no API calls).")
            df = pd.read_csv(legacy_csv_path)
            plot_figure1(df, out_path=tif_path, year_max=df["Year"].max())
            print("Done.")
            return
        raise SystemExit(f"Counts CSV not found: {csv_path}")

    print("Initializing Scopus API (pybliometrics)...")
    init_pybliometrics()

    print("Fetching publication counts from Scopus (one query per domain; facets by year)...")
    df = fetch_all_counts(
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
        delay_seconds=0.5,
        out_csv=csv_path,
        query_option=args.query_option,
    )

    print("Plotting Figure 1...")
    plot_figure1(df, out_path=tif_path, year_max=YEAR_MAX)

    cred_year = YEAR_MAX
    cred_queries = build_domain_queries(query_option=args.query_option, year_min=cred_year, year_max=cred_year)
    credibility_query = "(" + " OR ".join(f"({q})" for q in cred_queries.values()) + ")"
    print(f"Credibility check query (PUBYEAR={cred_year}):")
    print(f"  {credibility_query}")
    try:
        n_cred = get_total_results(credibility_query)
        print(f"  Total publications: {n_cred}")
    except Exception as e:
        print(f"  Query failed: {e}", file=sys.stderr)

    print("Done.")


if __name__ == "__main__":
    main()
