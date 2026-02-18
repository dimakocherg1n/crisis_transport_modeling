from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime



class TransportType(str, Enum):
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"
    BUS = "bus"
    TRUCK = "truck"
class CrisisSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
class CrisisType(str, Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    FIRE = "fire"
    TERRORIST_ATTACK = "terrorist_attack"
    INDUSTRIAL_ACCIDENT = "industrial_accident"
    EPIDEMIC = "epidemic"
    OTHER = "other"
class Node(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    type: Optional[str] = None
    capacity: Optional[int] = 0
class Edge(BaseModel):
    id: str
    source: str
    target: str
    distance: float
    travel_time: float
    capacity: Optional[int] = None
    is_blocked: bool = False
    damage_level: float = 0.0
class Vehicle(BaseModel):
    id: int
    type: TransportType = Field(alias="vehicle_type")
    capacity: int
    current_location: List[float]
    speed: float
    fuel_level: float = Field(1.0, ge=0.0, le=1.0)
    status: str = "available"
    can_use_damaged_roads: bool = False
    driver_available: bool = True
    special_equipment: List[str] = []
    class Config:
        allow_population_by_field_name = True
class DeliveryPoint(BaseModel):
    id: int
    location: List[float]  # [latitude, longitude]
    demand: float
    priority: int
    time_window_start: float
    time_window_end: float
    name: Optional[str] = None
    crisis_affected: bool = False
    required_equipment: List[str] = []
    unloading_time: float = 0.5
class CrisisZone(BaseModel):
    id: str
    name: str
    center_latitude: float
    center_longitude: float
    radius: float
    severity: CrisisSeverity = CrisisSeverity.MEDIUM
    crisis_type: CrisisType = CrisisType.OTHER
    affected_people: int = 0
class EmergencyRequest(BaseModel):
    id: str
    priority: int
    location: str
    required_vehicle_type: TransportType
    required_capacity: int
    deadline: Optional[float] = None
class RoadNetwork(BaseModel):
    nodes: Dict[str, Node]
    edges: Dict[str, Edge]
    vehicles: Dict[str, Vehicle]
    requests: List[EmergencyRequest]
    crisis_zones: Dict[str, CrisisZone] = {}
class OptimizationRequest(BaseModel):
    vehicles: List[Vehicle]
    delivery_points: List[DeliveryPoint]
    depot_location: List[float]
    crisis_zones: Optional[List[CrisisZone]] = None
    algorithm: Optional[str] = "genetic"
    time_limit: Optional[float] = 60.0
class RouteSegment(BaseModel):
    from_node: str
    to_node: str
    distance: float
    travel_time: float
    vehicle_id: str
class OptimizedRoute(BaseModel):
    request_id: str
    vehicle_id: str
    segments: List[RouteSegment]
    total_distance: float
    total_time: float
    estimated_arrival: float
class OptimizationResponse(BaseModel):
    routes: List[OptimizedRoute]
    unassigned_requests: List[str]
    total_distance: float
    total_time: float
    optimization_time: float = 0.0
class OptimizationResult(BaseModel):
    id: str
    scenario_id: Optional[str] = None
    timestamp: datetime = datetime.now()
    response: OptimizationResponse
    parameters: Dict[str, Any] = {}
    performance_metrics: Dict[str, float] = {}
RoadSegment = Edge
VehicleType = TransportType
NetworkNode = Node
NetworkEdge = Edge
__all__ = [
    'TransportType', 'VehicleType', 'CrisisSeverity', 'CrisisType',
    'Node', 'NetworkNode', 'Edge', 'NetworkEdge', 'RoadSegment',
    'Vehicle', 'DeliveryPoint', 'CrisisZone', 'EmergencyRequest',
    'RoadNetwork', 'OptimizationRequest', 'RouteSegment',
    'OptimizedRoute', 'OptimizationResponse', 'OptimizationResult'
]

Transport = Vehicle
RoadSegment = Edge
VehicleType = TransportType
NetworkNode = Node
NetworkEdge = Edge
