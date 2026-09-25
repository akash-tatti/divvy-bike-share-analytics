#!/usr/bin/env python3
"""Build dashboard/index.html — KPI cards + Plotly charts (self-contained, CDN plotly.js)."""
import os
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect()
con.execute(f"""CREATE OR REPLACE VIEW trips AS
SELECT * FROM read_csv('{BASE}/data/2026*-divvy-tripdata/*.csv', header=true)
WHERE started_at >= '2026-06-01' AND started_at < '2026-09-01'""")

def run(sql):
    return con.execute(sql).fetchdf()

total = run("SELECT COUNT(*) n FROM trips")["n"][0]
mix = run("""SELECT member_casual, COUNT(*) t,
 ROUND(AVG(date_diff('second',started_at,ended_at))/60,1) a
 FROM trips WHERE ended_at>started_at GROUP BY 1""")
mem_pct = round(100 * mix.loc[mix.member_casual == "member", "t"].iloc[0] / total, 1)
cas_avg = mix.loc[mix.member_casual == "casual", "a"].iloc[0]
peak_hr = run("""SELECT EXTRACT(HOUR FROM started_at)::INT h, COUNT(*) t
 FROM trips GROUP BY 1 ORDER BY 2 DESC LIMIT 1""").iloc[0]
ebike = run("""SELECT ROUND(100.0*COUNT(*) FILTER (WHERE rideable_type='electric_bike')/COUNT(*),1) p
 FROM trips""")["p"][0]

hourly = run("""SELECT EXTRACT(HOUR FROM started_at)::INT hr, member_casual, COUNT(*) trips
 FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 1""")
fig_h = px.line(hourly, x="hr", y="trips", color="member_casual", markers=True,
                title="Trips by hour of day", labels={"hr": "Hour", "member_casual": "Rider"})
dow = run("""SELECT EXTRACT(ISODOW FROM started_at)::INT d, member_casual, COUNT(*) trips
 FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 1""")
dow["day"] = dow["d"].map({1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat",7:"Sun"})
fig_d = px.bar(dow, x="day", y="trips", color="member_casual", barmode="group",
               category_orders={"day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]},
               title="Trips by day of week", labels={"day": ""})
rb = run("""WITH f AS (
 SELECT start_station_name s, COUNT(*) a, 0 b FROM trips WHERE start_station_name IS NOT NULL GROUP BY 1
 UNION ALL
 SELECT end_station_name s, 0 a, COUNT(*) b FROM trips WHERE end_station_name IS NOT NULL GROUP BY 1)
 SELECT s station, SUM(a)-SUM(b) net FROM f GROUP BY 1
 HAVING SUM(a)+SUM(b)>=1000 ORDER BY ABS(SUM(a)-SUM(b)) DESC LIMIT 12""").sort_values("net")
fig_r = px.bar(rb, x="net", y="station", orientation="h", color="net",
               color_continuous_scale="RdBu", title="Station imbalance (net outflow)",
               labels={"net": "Bikes (starts − ends)", "station": ""})
top = run("""SELECT start_station_name s, COUNT(*) t FROM trips
 WHERE start_station_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10""").sort_values("t")
fig_t = px.bar(top, x="t", y="s", orientation="h", title="Top 10 start stations",
               labels={"t": "Trips", "s": ""}, text_auto=True)

def div(fig):
    return plot(fig, include_plotlyjs=False, output_type="div")

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Divvy Bike-Share Analytics — Summer 2026</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0;background:#f4f6f8;color:#1c1e21}}
.wrap{{max-width:1100px;margin:0 auto;padding:28px 20px 60px}}
h1{{margin:0 0 4px}} .sub{{color:#5b616b;margin-bottom:22px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:22px}}
.kpi{{background:#fff;border-radius:10px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.kpi .v{{font-size:26px;font-weight:700}} .kpi .l{{color:#5b616b;font-size:13px;margin-top:4px}}
.card{{background:#fff;border-radius:10px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:18px}}
.insight{{background:#eef4ff;border-left:4px solid #2f6fed;border-radius:6px;padding:12px 16px;margin-bottom:18px;font-size:14.5px}}
footer{{color:#8a8f98;font-size:12.5px;margin-top:26px}}
</style></head><body><div class="wrap">
<h1>Divvy Bike-Share Analytics</h1>
<div class="sub">Chicago · June – August 2026 · 2.5M trips · SQL (DuckDB) + Plotly</div>
<div class="kpis">
<div class="kpi"><div class="v">{total:,}</div><div class="l">Total trips</div></div>
<div class="kpi"><div class="v">{mem_pct}%</div><div class="l">Trips by members</div></div>
<div class="kpi"><div class="v">{cas_avg} min</div><div class="l">Avg casual trip duration</div></div>
<div class="kpi"><div class="v">{int(peak_hr['h'])}:00</div><div class="l">Peak hour ({int(peak_hr['t']):,} trips)</div></div>
<div class="kpi"><div class="v">{ebike}%</div><div class="l">Trips on e-bikes</div></div>
</div>
<div class="insight"><b>Headline:</b> two segments — <b>members commute</b> (AM/PM rush peaks, 8.5-min median AM trips)
and <b>casual riders play</b> (64% longer trips, dominate weekends). E-bikes are 70%+ of all rides.
Top rebalancing targets: Franklin St &amp; Monroe St (+1,380 surplus) and Field Museum (−1,020 deficit).</div>
<div class="card">{div(fig_h)}</div>
<div class="card">{div(fig_d)}</div>
<div class="card">{div(fig_t)}</div>
<div class="card">{div(fig_r)}</div>
<footer>Data: Divvy / City of Chicago open trip data (divvybikes.com/system-data).
Built with SQL + Python. See <a href="../notebooks/divvy_analysis.ipynb">notebook</a> and
<a href="../sql/analysis.sql">SQL</a> for the full analysis.</footer>
</div></body></html>"""

out = os.path.join(BASE, "dashboard", "index.html")
open(out, "w").write(html)
print("wrote", out, f"({len(html)//1024} KB)")
