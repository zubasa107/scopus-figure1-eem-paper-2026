# Figure 1 (EEM paper 2026) — Scopus query counts

This repository contains the code used to **fetch Scopus publication counts** and generate the **Figure 1** stacked bar chart (publications per year, split by domain: load, price, wind, solar).

In the paper, **Search String Option 6** is used.

## What the script does

- Uses the Scopus Search API (via `pybliometrics`) to run **one query per domain** with a year-range filter (2010–2025)
- Extracts **year-by-year counts via Scopus facets (`pubyear`)** (no full record download)
- Writes:
  - a CSV with counts
  - a `.tif` figure (stacked bars)

## Setup

1. Get a Scopus API key: `https://dev.elsevier.com/myapikey.html`
2. Provide the key (one of the following):
   - Create a local `.env` file (see `.env.example`) with `ELSEVIER_API_KEY=...`, or
   - Set an environment variable: `ELSEVIER_API_KEY=...` (or `SCOPUS_API_KEY=...`)
3. Install dependencies:

```bash
pip install -r requirements_scopus_figure1.txt
```

## Usage

- Fetch from Scopus and plot (paper default = option 6):

```bash
python scopus_figure1_from_api.py
```

- Explicitly select the search string option:

```bash
python scopus_figure1_from_api.py --query-option 6
```

- Re-plot from an existing counts CSV (no API calls):

```bash
python scopus_figure1_from_api.py --plot-only
```

## Outputs

| File | Description |
|------|-------------|
| `scopus_figure1_counts_optN.csv` | Year × domain counts (columns: Year, Load, Price, Wind, Solar) |
| `scopus_figure1_optN.tif`        | Vertical stacked bar chart, where `N` is the query option |

## Credibility check (example)

The script prints a final “credibility check” query that OR-combines the 4 domain queries for the last year (currently 2025).

Recorded run (local time): **2026-03-02**

```text
Credibility check query (PUBYEAR=2025):
  ((TITLE-ABS-KEY((("electricity" OR "power") W/3 ("load" OR "demand")) W/3 (forecast* OR predict*)) AND PUBYEAR > 2024 AND PUBYEAR < 2026 AND DOCTYPE(ar OR re)) OR (TITLE-ABS-KEY((("electricity" OR "power") W/3 "price") W/3 (forecast* OR predict*)) AND PUBYEAR > 2024 AND PUBYEAR < 2026 AND DOCTYPE(ar OR re)) OR (TITLE-ABS-KEY((("wind" W/3 ("power" OR "generation")) W/3 (forecast* OR predict*))) AND PUBYEAR > 2024 AND PUBYEAR < 2026 AND DOCTYPE(ar OR re)) OR (TITLE-ABS-KEY(((("solar" OR "photovoltaic" OR "PV") W/3 ("power" OR "generation")) W/3 (forecast* OR predict*))) AND PUBYEAR > 2024 AND PUBYEAR < 2026 AND DOCTYPE(ar OR re)))
  Total publications: 2441
Done.
```

