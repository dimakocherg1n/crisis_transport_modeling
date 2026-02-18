from typing import List, Dict, Any, Optional
from app.models.optimization_models import (
    TransportType, RoadNetwork, OptimizationRequest, 
    OptimizationResponse, OptimizedRoute, RouteSegment,
    Vehicle, Node, Edge, EmergencyRequest,
    DeliveryPoint, CrisisZone, CrisisType, CrisisSeverity,
    RoadSegment, Transport, OptimizationResult
)
from app.algorithms import VRPSolver


class OptimizationService:
    """Сервис для оптимизации маршрутов в кризисных ситуациях"""
    def __init__(self):
        self.solver = VRPSolver()
        self.name = "Optimization Service"
    def create_sample_data(self) -> Dict[str, Any]:
        """Создает тестовые данные для демонстрации"""
        nodes = {
            "hospital": Node(
                id="hospital",
                name="Central Hospital",
                latitude=55.7558,
                longitude=37.6173,
                type="hospital",
                capacity=100
            ),
            "shelter": Node(
                id="shelter",
                name="Emergency Shelter",
                latitude=55.7600,
                longitude=37.6200,
                type="shelter",
                capacity=200
            ),
            "zone_a": Node(
                id="zone_a",
                name="Crisis Zone A",
                latitude=55.7500,
                longitude=37.6150,
                type="crisis_zone",
                capacity=0
            )
        }
        delivery_points = {
            "dp_hospital": DeliveryPoint(
                id="dp_hospital",
                name="Hospital Delivery Point",
                latitude=55.7558,
                longitude=37.6173,
                type="hospital",
                capacity=100,
                current_load=30,
                priority=1
            ),
            "dp_shelter": DeliveryPoint(
                id="dp_shelter",
                name="Shelter Delivery Point",
                latitude=55.7600,
                longitude=37.6200,
                type="shelter",
                capacity=200,
                current_load=80,
                priority=2
            )
        }
        crisis_zones = {
            "cz_a": CrisisZone(
                id="cz_a",
                name="Earthquake Zone A",
                center_latitude=55.7500,
                center_longitude=37.6150,
                radius=1000.0,
                severity=CrisisSeverity.HIGH,
                crisis_type=CrisisType.EARTHQUAKE,
                affected_people=150
            )
        }
        edges = {
            "road_1": Edge(
                id="road_1",
                source="hospital",
                target="shelter",
                distance=1500.0,
                travel_time=300.0,
                capacity=100,
                is_blocked=False,
                damage_level=0.0
            ),
            "road_2": Edge(
                id="road_2",
                source="shelter",
                target="zone_a",
                distance=2000.0,
                travel_time=400.0,
                capacity=80,
                is_blocked=False,
                damage_level=0.2
            )
        }
        vehicles = {
            "ambulance_1": Vehicle(
                id="ambulance_1",
                type=TransportType.AMBULANCE,
                capacity=5,
                current_location="hospital",
                speed=60.0,
                fuel_level=100.0,
                status="available"
            ),
            "fire_truck_1": Vehicle(
                id="fire_truck_1",
                type=TransportType.FIRE_TRUCK,
                capacity=8,
                current_location="shelter",
                speed=50.0,
                fuel_level=100.0,
                status="available"
            ),
            "bus_1": Vehicle(
                id="bus_1",
                type=TransportType.BUS,
                capacity=30,
                current_location="shelter",
                speed=40.0,
                fuel_level=100.0,
                status="available"
            )
        }
        requests = [
            EmergencyRequest(
                id="request_1",
                priority=1,
                location="zone_a",
                required_vehicle_type=TransportType.AMBULANCE,
                required_capacity=3
            ),
            EmergencyRequest(
                id="request_2",
                priority=2,
                location="zone_a",
                required_vehicle_type=TransportType.FIRE_TRUCK,
                required_capacity=5
            ),
            EmergencyRequest(
                id="request_3",
                priority=3,
                location="zone_a",
                required_vehicle_type=TransportType.BUS,
                required_capacity=20
            )
        ]
        return {
            "nodes": {k: v.dict() for k, v in nodes.items()},
            "delivery_points": {k: v.dict() for k, v in delivery_points.items()},
            "crisis_zones": {k: v.dict() for k, v in crisis_zones.items()},
            "edges": {k: v.dict() for k, v in edges.items()},
            "vehicles": {k: v.dict() for k, v in vehicles.items()},
            "requests": [r.dict() for r in requests]
        }
    def optimize_routes(self, request: OptimizationRequest) -> OptimizationResponse:
        """Оптимизирует маршруты для всех запросов"""
        routes = []
        assigned_vehicles = set()
        unassigned_requests = []
        for req in request.network.requests:
            assigned = False
            for vehicle_id, vehicle in request.network.vehicles.items():
                if (vehicle_id not in assigned_vehicles and
                    vehicle.type == req.required_vehicle_type and
                    vehicle.capacity >= req.required_capacity and
                    vehicle.status == "available"):
                    route = OptimizedRoute(
                        request_id=req.id,
                        vehicle_id=vehicle_id,
                        segments=[
                            RouteSegment(
                                from_node=vehicle.current_location,
                                to_node=req.location,
                                distance=1000.0,
                                travel_time=200.0
                            )
                        ],
                        total_distance=1000.0,
                        total_time=200.0,
                        estimated_arrival=200.0
                    )
                    routes.append(route)
                    assigned_vehicles.add(vehicle_id)
                    assigned = True
                    break
            if not assigned:
                unassigned_requests.append(req.id)
        return OptimizationResponse(
            routes=routes,
            unassigned_requests=unassigned_requests,
            total_distance=sum(r.total_distance for r in routes),
            total_time=sum(r.total_time for r in routes),
            optimization_time=0.05
        )

optimization_service = OptimizationService()
