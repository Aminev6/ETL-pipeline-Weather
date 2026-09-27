-- Analytics queries for weather_observations.
-- Averages of double-precision values are rounded to 2 decimal places.

-- 1. Observation count by city
SELECT
    city,
    COUNT(*) AS observation_count
FROM weather_observations
GROUP BY city
ORDER BY observation_count DESC, city;

-- 2. Average temperature by city
SELECT
    city,
    ROUND(AVG(temperature_c)::numeric, 2) AS average_temperature_c
FROM weather_observations
GROUP BY city
ORDER BY city;

-- 3. Minimum and maximum temperature by city
SELECT
    city,
    MIN(temperature_c) AS minimum_temperature_c,
    MAX(temperature_c) AS maximum_temperature_c
FROM weather_observations
GROUP BY city
ORDER BY city;

-- 4. Average humidity by city
SELECT
    city,
    ROUND(AVG(humidity), 2) AS average_humidity
FROM weather_observations
GROUP BY city
ORDER BY city;

-- 5. Average wind speed by city
SELECT
    city,
    ROUND(AVG(wind_speed)::numeric, 2) AS average_wind_speed
FROM weather_observations
GROUP BY city
ORDER BY city;

-- 6. Latest observation for each city
SELECT DISTINCT ON (city)
    city,
    temperature_c,
    humidity,
    wind_speed,
    weather_code,
    observed_at
FROM weather_observations
ORDER BY city, observed_at DESC;

-- 7. Overall weather summary
SELECT
    COUNT(*) AS total_observations,
    ROUND(AVG(temperature_c)::numeric, 2) AS average_temperature_c,
    ROUND(AVG(humidity), 2) AS average_humidity,
    ROUND(AVG(wind_speed)::numeric, 2) AS average_wind_speed,
    MIN(observed_at) AS earliest_observation,
    MAX(observed_at) AS latest_observation
FROM weather_observations;

-- 8. Rank each city's observations from newest to oldest
-- observation_rank = 1 is the latest observation for that city.
SELECT
    city,
    temperature_c,
    humidity,
    wind_speed,
    weather_code,
    observed_at,
    ROW_NUMBER() OVER (
        PARTITION BY city
        ORDER BY observed_at DESC
    ) AS observation_rank
FROM weather_observations
ORDER BY city, observation_rank;

-- 9. Average temperature at each observation time
SELECT
    observed_at,
    ROUND(AVG(temperature_c)::numeric, 2) AS average_temperature_c,
    COUNT(*) AS observation_count
FROM weather_observations
GROUP BY observed_at
ORDER BY observed_at;
