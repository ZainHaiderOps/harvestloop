"""The synthetic farm/field/sensor/harvest generator.

Everything here is deterministic given a seed — same seed, same world,
every time. That matters for two reasons: reproducible tests, and a
stable dataset to build every later phase against instead of a fresh
random world on every run.

Two things are deliberately NOT just noise: the "care_quality" latent
factor per field (a stand-in for how well-managed that field actually
is) and each season's "weather_modifier" both feed into yield through
`_expected_yield` in a principled way, so the harvest data has real,
learnable signal — a Planning or Checking agent evaluated against pure
noise would look artificially good at "reasoning" about it, which
defeats the point of building an eval harness in Phase 04.

Sensor readings also carry a small, deliberate fraction of injected
anomalies (`is_anomalous=True`), because Phase 01's own plan calls for
data with real problems in it for the Checking agent to eventually catch
— data that's too clean makes every later phase look better than it is.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from harvest_loop.data.models import (
    CropType,
    Farm,
    Field,
    HarvestRecord,
    SensorReading,
)
from harvest_loop.data.regions import REGIONS

FARM_NAME_STEMS = [
    "Rossberg",
    "Talbrook",
    "Lindenhof",
    "Birkenau",
    "Vogelsang",
    "Kesselbach",
    "Hartmoor",
    "Steinfeld",
    "Amselgrund",
    "Falkenried",
    "Wiesenau",
    "Brombach",
    "Eichgrund",
    "Muehlental",
    "Dornfeld",
]

FARM_SUFFIX_BY_CROP: dict[CropType, str] = {
    CropType.GRAPE: "Weingut",
    CropType.APPLE: "Obsthof",
    CropType.WHEAT: "Hof",
    CropType.BARLEY: "Gutshof",
}

# Illustrative figures loosely in the range of real German crop averages —
# not calibrated against any specific dataset, real or otherwise.
BASE_YIELD_TONNES_PER_HECTARE: dict[CropType, float] = {
    CropType.WHEAT: 7.5,
    CropType.BARLEY: 6.5,
    CropType.APPLE: 38.0,
    CropType.GRAPE: 10.0,
}

ANOMALY_PROBABILITY = 0.02


@dataclass
class World:
    farms: list[Farm]
    fields: list[Field]
    sensor_readings: list[SensorReading]
    harvest_records: list[HarvestRecord]


def _expected_yield(base: float, care_quality: float, weather_modifier: float) -> float:
    """Pure and deterministic — no rng here. tests/test_generator.py checks
    this function's monotonicity directly, separately from any randomness
    elsewhere in the generator.
    """
    care_factor = 0.6 + 0.4 * care_quality  # care_quality in [0,1] -> factor in [0.6, 1.0]
    return base * care_factor * weather_modifier


def _seasonal_signal(day_of_year: int, phase: float) -> float:
    """A smooth signal in [-1, 1] that peaks once a year, offset per field
    so every field doesn't peak on exactly the same calendar day.
    """
    return math.sin(2 * math.pi * day_of_year / 365 + phase)


def _make_farm_name(rng: random.Random, crop: CropType) -> str:
    stem = rng.choice(FARM_NAME_STEMS)
    suffix = FARM_SUFFIX_BY_CROP[crop]
    return f"{suffix} {stem}"


def _generate_farms_and_fields(
    rng: random.Random, farms_per_region: int, reference_date: date
) -> tuple[list[Farm], list[Field], dict[str, float]]:
    farms: list[Farm] = []
    fields: list[Field] = []
    care_quality_by_field: dict[str, float] = {}

    for region in REGIONS:
        for i in range(farms_per_region):
            farm_id = f"{region.key[:4].upper()}-{i:03d}"
            crop = rng.choice(region.crops)
            farm = Farm(
                farm_id=farm_id,
                name=_make_farm_name(rng, crop),
                region=region.display_name,
                latitude=round(region.latitude + rng.uniform(-0.15, 0.15), 4),
                longitude=round(region.longitude + rng.uniform(-0.15, 0.15), 4),
                established_year=rng.randint(1978, 2018),
            )
            farms.append(farm)

            n_fields = rng.randint(1, 2)
            for f_idx in range(n_fields):
                field_crop = crop if f_idx == 0 else rng.choice(region.crops)
                field_id = f"{farm_id}-FLD{f_idx + 1}"
                is_perennial = field_crop in (CropType.APPLE, CropType.GRAPE)
                planted_on = (
                    date(rng.randint(2000, 2015), rng.randint(3, 5), rng.randint(1, 28))
                    if is_perennial
                    # Annual crops here are winter wheat/barley — planted
                    # the previous autumn, not this spring.
                    else date(reference_date.year - 1, 10, rng.randint(1, 28))
                )
                fields.append(
                    Field(
                        field_id=field_id,
                        farm_id=farm_id,
                        crop=field_crop,
                        area_hectares=round(rng.uniform(2.0, 25.0), 1),
                        planted_on=planted_on,
                    )
                )
                # Fixed for the field's lifetime: how well-managed it is.
                care_quality_by_field[field_id] = rng.uniform(0.3, 1.0)

    return farms, fields, care_quality_by_field


def _generate_sensor_readings(
    rng: random.Random,
    fields: list[Field],
    care_quality_by_field: dict[str, float],
    sensor_days: int,
    reference_date: date,
) -> list[SensorReading]:
    readings: list[SensorReading] = []

    for f in fields:
        care = care_quality_by_field[f.field_id]
        phase = rng.uniform(0, 2 * math.pi)

        for day_offset in range(sensor_days, 0, -1):
            day = reference_date - timedelta(days=day_offset)
            seasonal = _seasonal_signal(day.timetuple().tm_yday, phase)

            is_rainy = rng.random() < 0.25
            moisture = 35 + 15 * seasonal + (10 if is_rainy else 0) + 5 * (care - 0.5)
            moisture += rng.uniform(-4, 4)
            moisture = max(2.0, min(98.0, moisture))

            temperature = 10 + 12 * seasonal + rng.uniform(-2, 2)
            leaf_wetness = rng.uniform(4, 10) if is_rainy else rng.uniform(0, 2)

            is_anomalous = rng.random() < ANOMALY_PROBABILITY
            if is_anomalous:
                # A sensor glitch, not a real field condition.
                target = rng.choice(["moisture", "temperature", "leaf_wetness"])
                if target == "moisture":
                    moisture = rng.choice([0.0, 99.5])
                elif target == "temperature":
                    temperature = rng.choice([-15.0, 48.0])
                else:
                    leaf_wetness = rng.choice([0.0, 23.5])

            readings.append(
                SensorReading(
                    field_id=f.field_id,
                    timestamp=datetime.combine(day, datetime.min.time()),
                    soil_moisture_pct=round(moisture, 1),
                    soil_temperature_c=round(temperature, 1),
                    leaf_wetness_hours=round(leaf_wetness, 1),
                    is_anomalous=is_anomalous,
                )
            )

    return readings


def _generate_harvest_records(
    rng: random.Random,
    fields: list[Field],
    care_quality_by_field: dict[str, float],
    reference_date: date,
    seasons_back: int = 3,
) -> list[HarvestRecord]:
    records: list[HarvestRecord] = []

    for f in fields:
        care = care_quality_by_field[f.field_id]
        base = BASE_YIELD_TONNES_PER_HECTARE[f.crop]

        for years_ago in range(seasons_back, 0, -1):
            season_year = reference_date.year - years_ago
            weather_modifier = rng.uniform(0.85, 1.15)

            expected = _expected_yield(base, care, weather_modifier)
            actual_yield = max(0.0, expected * (1 + rng.uniform(-0.05, 0.05)))

            quality_score = 50 + 40 * care + 10 * (weather_modifier - 1)
            quality_score += rng.uniform(-3, 3)
            quality_score = max(0.0, min(100.0, quality_score))

            records.append(
                HarvestRecord(
                    field_id=f.field_id,
                    season_year=season_year,
                    yield_tonnes_per_hectare=round(actual_yield, 2),
                    quality_score=round(quality_score, 1),
                )
            )

    return records


def generate_world(
    seed: int = 42,
    farms_per_region: int = 12,
    sensor_days: int = 90,
    reference_date: date | None = None,
) -> World:
    """The single entry point. Same seed -> identical world, every time."""
    rng = random.Random(seed)
    ref_date = reference_date or date.today()

    farms, fields, care_quality_by_field = _generate_farms_and_fields(
        rng, farms_per_region, ref_date
    )
    sensor_readings = _generate_sensor_readings(
        rng, fields, care_quality_by_field, sensor_days, ref_date
    )
    harvest_records = _generate_harvest_records(rng, fields, care_quality_by_field, ref_date)

    return World(
        farms=farms,
        fields=fields,
        sensor_readings=sensor_readings,
        harvest_records=harvest_records,
    )
