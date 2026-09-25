# Divvy Bike-Share Analytics — Chicago, Summer 2026

SQL + Python analysis of **2.5 million** Divvy (Chicago bike-share) trips from June–August 2026,
answering business questions about rider segments, demand patterns, and station rebalancing —
with an interactive dashboard.

## Business questions → answers

| # | Question | Finding |
|---|----------|---------|
| 1 | Who rides — members or casual riders? | Members take **59.5%** of trips, but casual trips run **~64% longer** on average (21.0 vs 12.8 min) — commute vs leisure behavior |
| 2 | When does demand peak? | Member spikes at **8 AM and 5 PM** (commutes); casual demand builds all afternoon, also peaking at 5 PM |
| 3 | Weekday vs weekend? | Members dominate Mon–Fri; on **Saturdays casual riders overtake members** — the weekend leisure crowd |
| 4 | Summer trend? | Demand jumps **~14% from June to July** (763K → 869K trips), holding steady through August |
| 5 | E-bike vs classic? | **E-bikes dominate**: 75.7% of casual trips, 70.3% of member trips |
| 6 | Which stations need rebalancing? | **Franklin St & Monroe St** accumulates ~1,380 surplus bikes; **Field Museum** drains ~1,020 — top rebalancing targets |
| 7 | Where do rides start? | **Navy Pier** leads (33.9K starts) — tourist/leisure demand |

**Recommendations:** market commuter passes to members and leisure bundles to casuals;
plan charging capacity around an e-bike-majority fleet; schedule rebalancing runs for the 4–7 PM peak,
prioritizing Franklin St & Monroe St and Field Museum.

## What's here

```
├── dashboard/index.html        # interactive dashboard (open in a browser)
├── notebooks/divvy_analysis.ipynb  # full narrative analysis (renders on GitHub)
├── sql/analysis.sql            # all analysis queries (DuckDB SQL)
├── scripts/
│   ├── download_data.py        # fetches the raw trip data
│   ├── analyze.py              # runs the SQL, saves results/*.csv
│   ├── build_notebook.py       # regenerates the notebook
│   └── build_dashboard.py      # regenerates the dashboard
├── results/                    # query outputs (CSV)
└── data/                       # raw trip data (downloaded, git-ignored)
```

## Reproduce

```bash
pip install -r requirements.txt
python scripts/download_data.py   # ~90 MB, Chicago open data
python scripts/analyze.py         # runs sql/analysis.sql
python scripts/build_dashboard.py # rebuilds dashboard/index.html
```

Then open `dashboard/index.html`, or read `notebooks/divvy_analysis.ipynb`.

## Data

Divvy trip data, City of Chicago open data portal — https://divvybikes.com/system-data
(Jun–Aug 2026). Trips under 60 seconds and staff/service trips are already excluded by the publisher.

## Tech

SQL (DuckDB) · Python (pandas) · Plotly
