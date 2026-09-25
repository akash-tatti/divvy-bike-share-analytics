#!/usr/bin/env python3
"""Run the SQL analysis (sql/analysis.sql) against Divvy trip data and save results."""
import duckdb, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect()
con.execute(f"""CREATE OR REPLACE VIEW trips AS
SELECT * FROM read_csv('{BASE}/data/2026*-divvy-tripdata/*.csv', header=true)
WHERE started_at >= '2026-06-01' AND started_at < '2026-09-01'""")

def q(name, sql):
    df = con.execute(sql).fetchdf()
    df.to_csv(f"{BASE}/results/{name}.csv", index=False)
    print(f"--- {name} ({len(df)} rows) ---")
    print(df.to_string(index=False))
    print()
    return df

os.makedirs(f"{BASE}/results", exist_ok=True)

q("data_quality", "SELECT COUNT(*) AS total_trips FROM trips")
q("q1_rider_mix", """
SELECT member_casual, COUNT(*) AS trips,
 ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct,
 ROUND(AVG(date_diff('second',started_at,ended_at))/60,1) AS avg_min,
 ROUND(QUANTILE_CONT(date_diff('second',started_at,ended_at),0.5)/60,1) AS med_min
FROM trips WHERE ended_at>started_at GROUP BY 1 ORDER BY 2 DESC""")
q("q2_hourly", """
SELECT EXTRACT(HOUR FROM started_at)::INT AS hr, member_casual, COUNT(*) AS trips
FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 1,2""")
q("q3_dow", """
SELECT EXTRACT(ISODOW FROM started_at)::INT AS dow, member_casual, COUNT(*) AS trips
FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 1,2""")
q("q4_monthly", """
SELECT DATE_TRUNC('month',started_at)::DATE AS month, COUNT(*) AS trips,
 ROUND(AVG(date_diff('second',started_at,ended_at))/60,1) AS avg_min
FROM trips WHERE ended_at>started_at GROUP BY 1 ORDER BY 1""")
q("q5_rideable", """
SELECT rideable_type, member_casual, COUNT(*) AS trips,
 ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY member_casual),1) AS pct
FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 2,3 DESC""")
q("q6_rebalance", """
WITH f AS (
 SELECT start_station_name AS s, COUNT(*) AS a, 0 AS b FROM trips
 WHERE start_station_name IS NOT NULL GROUP BY 1
 UNION ALL
 SELECT end_station_name AS s, 0 AS a, COUNT(*) AS b FROM trips
 WHERE end_station_name IS NOT NULL GROUP BY 1)
SELECT s AS station, SUM(a) AS starts, SUM(b) AS ends,
 SUM(a)-SUM(b) AS net, ABS(SUM(a)-SUM(b)) AS imb
FROM f GROUP BY 1 HAVING SUM(a)+SUM(b)>=1000 ORDER BY imb DESC LIMIT 15""")
q("q7_top_stations", """
SELECT start_station_name AS station, COUNT(*) AS trips
FROM trips WHERE start_station_name IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC LIMIT 10""")
q("q8_rush", """
SELECT CASE WHEN EXTRACT(HOUR FROM started_at) BETWEEN 7 AND 9 THEN 'AM rush'
            WHEN EXTRACT(HOUR FROM started_at) BETWEEN 17 AND 19 THEN 'PM rush'
            ELSE 'Off-peak' END AS period,
 member_casual, COUNT(*) AS trips,
 ROUND(QUANTILE_CONT(date_diff('second',started_at,ended_at),0.5)/60,1) AS med_min
FROM trips WHERE ended_at>started_at GROUP BY 1,2 ORDER BY 1,2""")
print("saved to results/")
