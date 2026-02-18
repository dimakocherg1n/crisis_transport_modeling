from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ScenarioType(str, Enum):
    NATURAL = "natural"
    TECHNOLOGICAL = "technological"
    SOCIAL = "social"
    INFRASTRUCTURE = "infrastructure"


class ScenarioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scenario_type: ScenarioType
    severity: int = Field(..., ge=1, le=5)
    description: Optional[str] = None
    affected_area: float = Field(100.0, ge=0.0)
    transport_modes: str = Field("road,rail", max_length=200)
    parameters: Optional[Dict[str, Any]] = None


class ScenarioCreate(ScenarioBase):
    pass


class Scenario(ScenarioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SimulationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scenario_id: int
    duration_hours: int = Field(..., ge=1, le=720)
    num_vehicles: int = Field(..., ge=1, le=1000)
    num_hubs: int = Field(5, ge=1, le=50)
    crisis_intensity: float = Field(..., ge=0.0, le=1.0)
    additional_params: Optional[Dict[str, Any]] = None


class SimulationCreate(SimulationBase):
    pass


class Simulation(SimulationBase):
    id: int
    total_deliveries: int
    avg_travel_time: float
    efficiency: float
    vehicle_utilization: float
    fuel_consumption: float
    co2_emissions: float
    metrics: Optional[Dict[str, Any]]
    simulation_data: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SimulationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    total_deliveries: Optional[int] = None
    avg_travel_time: Optional[float] = None
    efficiency: Optional[float] = None
    vehicle_utilization: Optional[float] = None
    fuel_consumption: Optional[float] = None
    co2_emissions: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    simulation_data: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)