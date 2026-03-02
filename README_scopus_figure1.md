# Figure 1 from Scopus API — Energy Forecasting Publications

This folder contains a script that **reproduces and updates Figure 1** from:

> Hong et al., "Energy Forecasting: A Review and Outlook,"  
> IEEE Open Access Journal of Power and Energy, 2020.

The figure shows the **number of publications** in load, price, wind, and solar forecasting returned by the respective Scopus search, by year (2010–2025).

## Method (aligned with the paper)

- **Searches:** One phrase per subdomain, in title/abstract/keywords:
  - **Load:** `TITLE-ABS-KEY("load forecasting")`
  - **Price:** `TITLE-ABS-KEY("electricity price forecasting")`
  - **Wind:** `TITLE-ABS-KEY("wind forecasting")`
  - **Solar:** `TITLE-ABS-KEY("solar forecasting")`
- **No journal filter** — Figure 1 uses all Scopus results (top-10 journals are used only in Figure 2 in the paper).
- **Counts:** One query per domain per year (`AND PUBYEAR = YYYY`). Counts are **independent** per domain (a paper can be counted in more than one category if it matches multiple phrases).
- **2025:** Included as a partial year; the figure caption notes that 2025 data are as of the extraction date.

## Setup

1. **Scopus API key**  
   Get a key at: https://dev.elsevier.com/myapikey.html  

2. **Configure the key** (one of the following):
   - **Option A:** Run the script once; pybliometrics will prompt for the key and save it in `~/.config/pybliometrics.cfg`.
   - **Option B:** Set the environment variable:  
     `SCOPUS_API_KEY=your_key`

3. **Install Python dependencies**
   ```bash
   pip install -r requirements_scopus_figure1.txt
   ```
   or:
   ```bash
   pip install pybliometrics pandas matplotlib
   ```

## Usage

- **Fetch from Scopus and plot:**  
  ```bash
  python scopus_figure1_from_api.py
  ```
  This runs **4 queries** (one per domain) with a year-range filter and uses **facets (pubyear)** to extract year-by-year counts (2010–2025). It does not download full records; it writes the CSV and figure.
  You can switch query sets via `--query-option 1` (replication phrases), `--query-option 2` (expanded queries + `DOCTYPE(ar OR re)`), `--query-option 3` (same as option 2 but without `predict*`), `--query-option 4` (same as option 2 but without `irradiance` and `speed`), `--query-option 5` (like option 4 but with `W/3` and `(forecast* OR predict*)`), `--query-option 6` (electricity/power context + `W/3` + `DOCTYPE(ar OR re)`), or `--query-option 7` (adds short-term/day-ahead terms + `DOCTYPE(ar OR re)`).

- **Re-plot from existing counts (no API):**  
  ```bash
  python scopus_figure1_from_api.py --plot-only
  ```
  Uses `scopus_figure1_counts.csv` if it exists and only regenerates the figure.
  You can also use `--no-api` (alias) and `--counts-csv path\to\counts.csv`.

## Outputs

| File | Description |
|------|-------------|
| `scopus_figure1_counts.csv` | Year × domain counts (columns: Year, Load, Price, Wind, Solar) |
| `scopus_figure1_optN.tif`   | Vertical stacked bar chart (publications vs. year), where `N` is the query option |

## Reproducibility

For a methods or appendix note you can state:

- Search field: **TITLE-ABS-KEY**
- Exact query phrases as above; one query per (domain, year) with `AND PUBYEAR = YYYY`
- Document types: **all** (no LIMIT-TO(DOCTYPE,…) applied)
- Extraction date: *[date you ran the script]*
- Source: Scopus via pybliometrics (Scopus Search API)

If you need to match the original paper’s numbers exactly, note that Scopus content and indexing change over time; the script replicates the **method**, not necessarily the same integers as in the 2020 paper.
