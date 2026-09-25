-- ============================================================================
-- Divvy Bike-Share Analytics — SQL analysis
-- Dataset: Divvy (Chicago bike-share) trip data, Jun–Aug 2026 (~2M trips)
-- Source : https://divvybikes.com/system-data
--
-- How to run (DuckDB):
--   CREATE OR REPLACE VIEW trips AS
--   SELECT * FROM read_csv('data/2026*-divvy-tripdata/*.csv', header=true,
--                          columns={'ride_id':'VARCHAR','rideable_type':'VARCHAR',
--                                   'started_at':'TIMESTAMP','ended_at':'TIMESTAMP',
--                                   'start_station_name':'VARCHAR','start_station_id':'VARCHAR',
--                                   'end_station_name':'VARCHAR','end_station_id':'VARCHAR',
--                                   'member_casual':'VARCHAR'});
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0. Data-quality check: volume, nulls, bad durations
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*)                                            AS total_trips,
    COUNT(*) FILTER (WHERE ride_id IS NULL)             AS null_ride_id,
    COUNT(*) FILTER (WHERE started_at IS NULL
                          OR ended_at IS NULL)          AS null_timestamps,
    COUNT(*) FILTER (WHERE ended_at <= started_at)      AS non_positive_duration,
    COUNT(*) FILTER (WHERE date_diff('minute', started_at, ended_at) > 1440)
                                                        AS trips_over_24h
FROM trips;

-- ----------------------------------------------------------------------------
-- Q1. Who rides? Member vs casual — volume and trip duration
-- Business: members are subscribers; casuals pay per ride. The mix drives
-- pricing and marketing strategy.
-- ----------------------------------------------------------------------------
SELECT
    member_casual,
    COUNT(*)                                            AS trips,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_trips,
    ROUND(AVG(date_diff('second', started_at, ended_at)) / 60, 1)
                                                        AS avg_minutes,
    ROUND(QUANTILE_CONT(date_diff('second', started_at, ended_at), 0.5) / 60, 1)
                                                        AS median_minutes
FROM trips
WHERE ended_at > started_at
GROUP BY member_casual
ORDER BY trips DESC;

-- ----------------------------------------------------------------------------
-- Q2. When is demand highest? Trips by hour of day and rider type
-- Business: informs station rebalancing crews and staffing.
-- ----------------------------------------------------------------------------
SELECT
    EXTRACT(HOUR FROM started_at)                        AS hour_of_day,
    member_casual,
    COUNT(*)                                            AS trips,
    ROUND(AVG(date_diff('second', started_at, ended_at)) / 60, 1)
                                                        AS avg_minutes
FROM trips
WHERE ended_at > started_at
GROUP BY hour_of_day, member_casual
ORDER BY hour_of_day, member_casual;

-- ----------------------------------------------------------------------------
-- Q3. Day-of-week patterns: commuters vs leisure
-- Business: weekday peaks suggest commuting; weekend peaks suggest leisure.
-- ----------------------------------------------------------------------------
SELECT
    DAYNAME(started_at)                                 AS day_of_week,
    EXTRACT(ISODOW FROM started_at)                     AS dow_num,
    member_casual,
    COUNT(*)                                            AS trips
FROM trips
WHERE ended_at > started_at
GROUP BY day_of_week, dow_num, member_casual
ORDER BY dow_num, member_casual;

-- ----------------------------------------------------------------------------
-- Q4. Monthly trend over the summer quarter
-- ----------------------------------------------------------------------------
SELECT
    DATE_TRUNC('month', started_at)::DATE               AS month,
    COUNT(*)                                            AS trips,
    ROUND(AVG(date_diff('second', started_at, ended_at)) / 60, 1)
                                                        AS avg_minutes
FROM trips
WHERE ended_at > started_at
GROUP BY month
ORDER BY month;

-- ----------------------------------------------------------------------------
-- Q5. Rideable mix: electric vs classic vs docked, by rider type
-- Business: e-bikes cost more to operate (charging); who uses them?
-- ----------------------------------------------------------------------------
SELECT
    rideable_type,
    member_casual,
    COUNT(*)                                            AS trips,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY member_casual), 1)
                                                        AS pct_of_rider_type
FROM trips
WHERE ended_at > started_at
GROUP BY rideable_type, member_casual
ORDER BY member_casual, trips DESC;

-- ----------------------------------------------------------------------------
-- Q6. Rebalancing: stations with the biggest start/end imbalance
-- Business: stations where bikes pile up (or run out) need rebalancing runs.
-- ----------------------------------------------------------------------------
WITH station_flow AS (
    SELECT start_station_name AS station, COUNT(*) AS starts, 0 AS ends
    FROM trips WHERE start_station_name IS NOT NULL GROUP BY 1
    UNION ALL
    SELECT end_station_name   AS station, 0 AS starts, COUNT(*) AS ends
    FROM trips WHERE end_station_name IS NOT NULL GROUP BY 1
)
SELECT
    station,
    SUM(starts)                                         AS total_starts,
    SUM(ends)                                           AS total_ends,
    SUM(starts) - SUM(ends)                             AS net_outflow,
    ABS(SUM(starts) - SUM(ends))                        AS abs_imbalance
FROM station_flow
GROUP BY station
HAVING SUM(starts) + SUM(ends) >= 1000   -- busy stations only
ORDER BY abs_imbalance DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- Q7. Top 10 start stations overall
-- ----------------------------------------------------------------------------
SELECT
    start_station_name                                  AS station,
    COUNT(*)                                            AS trips_started
FROM trips
WHERE start_station_name IS NOT NULL
GROUP BY station
ORDER BY trips_started DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- Q8. Rush-hour check: are morning/evening trips shorter (commutes)?
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN EXTRACT(HOUR FROM started_at) BETWEEN 7 AND 9  THEN 'AM rush (7-9)'
        WHEN EXTRACT(HOUR FROM started_at) BETWEEN 17 AND 19 THEN 'PM rush (17-19)'
        ELSE 'Off-peak'
    END                                                 AS period,
    member_casual,
    COUNT(*)                                            AS trips,
    ROUND(QUANTILE_CONT(date_diff('second', started_at, ended_at), 0.5) / 60, 1)
                                                        AS median_minutes
FROM trips
WHERE ended_at > started_at
GROUP BY period, member_casual
ORDER BY period, member_casual;
