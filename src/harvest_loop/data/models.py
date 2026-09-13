"""Typed data entities for the synthetic farm world.

These are plain data containers (Pydantic models), not database tables —
Phase 01b will map them onto Postgres. Using Pydantic here (rather than
dataclasses) is deliberate: it's the same validation pattern the agents
will use for structured LLM output from Phase 02 onward, so this is also
a first, low-stakes look at that pattern.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field as PydanticField


class CropType(str, Enum):
    WHEAT = "wheat"
    BARLEY = "barley"
    APPLE = "apple"
    GRAPE = "grape"


class Farm(BaseModel):
    farm_id: str
    name: str
    region: str
    latitude: float
    longitude: float
    established_year: int


class Field(BaseModel):
    field_id: str
    farm_id: str
    crop: CropType
    area_hectares: float
    planted_on: date


class SensorReading(BaseModel):
    field_id: str
    timestamp: datetime
    soil_moisture_pct: float
    soil_temperature_c: float
    leaf_wetness_hours: float
    is_anomalous: bool = False


class HarvestRecord(BaseModel):
    field_id: str
    season_year: int
    yield_tonnes_per_hectare: float
    quality_score: float = PydanticField(ge=0, le=100)
    notes: str = ""


class AgronomyRule(BaseModel):
    rule_id: str
    crop: CropType
    title: str
    condition: str
    recommendation: str
    source: str
