"""Real German growing regions used to place synthetic farms.

The farms themselves are fictional, but their locations are jittered
around real agricultural regions' real coordinates — that's what makes
the weather layer in weather.py genuinely real instead of made up too.
Approximate region centers; precision beyond ~10km doesn't matter here.
"""

from __future__ import annotations

from dataclasses import dataclass

from harvest_loop.data.models import CropType


@dataclass(frozen=True)
class Region:
    key: str
    display_name: str
    latitude: float
    longitude: float
    crops: tuple[CropType, ...]


REGIONS: tuple[Region, ...] = (
    Region(
        key="altes_land",
        display_name="Altes Land",
        latitude=53.53,
        longitude=9.60,
        crops=(CropType.APPLE,),
    ),
    Region(
        key="rheinhessen",
        display_name="Rheinhessen",
        latitude=49.83,
        longitude=8.13,
        crops=(CropType.GRAPE,),
    ),
    Region(
        key="magdeburger_boerde",
        display_name="Magdeburger Börde",
        latitude=52.05,
        longitude=11.40,
        crops=(CropType.WHEAT, CropType.BARLEY),
    ),
    Region(
        key="bodensee",
        display_name="Bodensee",
        latitude=47.65,
        longitude=9.30,
        crops=(CropType.APPLE, CropType.GRAPE),
    ),
)
