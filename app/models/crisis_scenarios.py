from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class CrisisType(str, Enum):
    NATURAL = "natural"
    TECHNOLOGICAL = "technological"
    SOCIAL = "social"
    INFRASTRUCTURE = "infrastructure"
    CLIMATIC = "climatic"
class TransportMode(str, Enum):
    ROAD = "road"
    RAIL = "rail"
    AIR = "air"
    MARITIME = "maritime"
    PIPELINE = "pipeline"
class CrisisScenario(BaseModel):
    name: str
    type: CrisisType
    severity: int
    description: str
    affected_area: Dict[str, Any]
    epicenter: Dict[str, float]
    start_time: datetime
    duration_hours: float
    development_curve: List[float]
    affected_transport_modes: List[TransportMode]
    road_blockage_percentage: float = 0.0
    rail_disruption_level: float = 0.0
    airport_closure_probability: float = 0.0
    port_operational_capacity: float = 1.0
    weather_conditions: Dict[str, Any]
    time_of_day: str
    day_of_week: str
    economic_impact_per_hour: float
    emergency_funds_available: float
    class Config:
        from_attributes = True
class NaturalDisaster(CrisisScenario):
    disaster_type: str
    magnitude: float
    aftershock_probability: float
    warning_time_hours: float
class TechnologicalAccident(CrisisScenario):
    accident_type: str
    hazardous_material: Optional[str]
    contamination_radius_km: float
    evacuation_zone_km: float
class SocialCrisis(CrisisScenario):
    crisis_type: str
    participants_count: int
    expected_duration_days: int
    negotiation_possible: bool