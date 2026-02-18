from app.models.optimization_models import CrisisZone, DeliveryPoint, OptimizationResult, RoadNetwork, Vehicle
"""
Базовый класс для всех алгоритмов оптимизации
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time
from datetime import datetime
import numpy as np

from app.models.optimization_models import (
    Vehicle, DeliveryPoint, RoadNetwork,
    CrisisZone, OptimizationResult
)
class BaseOptimizer(ABC):
    """Абстрактный базовый класс для оптимизаторов"""
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.execution_time = 0
        self.iteration_count = 0
    @abstractmethod
    def optimize(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
            road_network: RoadNetwork,
            crisis_zones: List[CrisisZone],
            depot_location: tuple
    ) -> OptimizationResult:
        pass
    def validate_input(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
    ) -> bool:
        """Валидация входных данных"""
        if not vehicles:
            raise ValueError("No vehicles provided")
        if not delivery_points:
            raise ValueError("No delivery points provided")
        for vehicle in vehicles:
            if vehicle.capacity <= 0:
                raise ValueError(f"Vehicle {vehicle.id} has invalid capacity")
            if vehicle.speed <= 0:
                raise ValueError(f"Vehicle {vehicle.id} has invalid speed")
            if not 0 <= vehicle.fuel_level <= 1:
                raise ValueError(f"Vehicle {vehicle.id} has invalid fuel level")
        for point in delivery_points:
            if point.demand <= 0:
                raise ValueError(f"Delivery point {point.id} has invalid demand")
            if not 1 <= point.priority <= 5:
                raise ValueError(f"Delivery point {point.id} has invalid priority")
            if point.time_window_start >= point.time_window_end:
                raise ValueError(f"Delivery point {point.id} has invalid time window")
        return True
    def calculate_distance_matrix(
            self,
            points: List[DeliveryPoint],
            road_network: RoadNetwork,
            depot_location: tuple,
            vehicle: Optional[Vehicle] = None
    ) -> np.ndarray:
        """Рассчитать матрицу расстояний между всеми точками"""
        n_points = len(points)
        matrix = np.zeros((n_points + 1, n_points + 1))
        all_locations = [depot_location] + [p.location for p in points]
        for i in range(len(all_locations)):
            for j in range(len(all_locations)):
                if i == j:
                    matrix[i][j] = 0
                else:
                    path, distance, _ = road_network.find_path(
                        all_locations[i], all_locations[j], vehicle
                    )
                    matrix[i][j] = distance if distance != float('inf') else 1e9
        return matrix
    def format_route_result(
            self,
            vehicle: Vehicle,
            route_indices: List[int],
            delivery_points: List[DeliveryPoint],
            distance_matrix: np.ndarray,
            depot_location: tuple
    ) -> Dict[str, Any]:
        """Форматирование результата для одного маршрута"""
        route_points = []
        total_distance = 0
        total_demand = 0
        total_time = 0
        current_time = 0
        time_penalty = 0
        current_location_idx = 0
        for i in range(len(route_indices)):
            point_idx = route_indices[i]
            if point_idx == 0 and i not in [0, len(route_indices) - 1]:
                continue
            distance = distance_matrix[current_location_idx][point_idx]
            total_distance += distance
            travel_time = distance / vehicle.effective_speed()
            current_time += travel_time
            if point_idx == 0:
                point_info = {
                    "type": "depot",
                    "location": depot_location,
                    "arrival_time": round(current_time, 2),
                    "distance_from_previous": round(distance, 2)
                }
            else:
                point = delivery_points[point_idx - 1]
                total_demand += point.demand
                penalty = point.time_window_penalty(current_time)
                time_penalty += penalty
                current_time += point.unloading_time
                point_info = {
                    "type": "delivery",
                    "id": point.id,
                    "location": point.location,
                    "demand": point.demand,
                    "priority": point.priority,
                    "arrival_time": round(current_time, 2),
                    "time_window": [point.time_window_start, point.time_window_end],
                    "in_window": point.is_in_time_window(current_time - point.unloading_time),
                    "distance_from_previous": round(distance, 2),
                    "penalty": round(penalty, 2)
                }
            route_points.append(point_info)
            current_location_idx = point_idx
        capacity_violation = 1 if total_demand > vehicle.capacity else 0
        fuel_violation = 1 if total_distance > vehicle.max_travel_distance() else 0
        return {
            "vehicle_id": vehicle.id,
            "vehicle_type": vehicle.vehicle_type.value,
            "route_points": route_points,
            "total_distance": round(total_distance, 2),
            "total_demand": round(total_demand, 2),
            "total_time": round(current_time, 2),
            "time_penalty": round(time_penalty, 2),
            "capacity_utilization": round(total_demand / vehicle.capacity * 100, 1),
            "fuel_required": round(total_distance / 500, 2),  # Пример: 500 км на бак
            "constraint_violations": {
                "capacity": capacity_violation,
                "fuel": fuel_violation,
                "time_windows": 1 if time_penalty > 0 else 0
            }
        }
    def create_optimization_result(
            self,
            routes: List[Dict[str, Any]],
            unserved_points: List[int],
            start_time: float
    ) -> OptimizationResult:
        """Создание объекта результата оптимизации"""
        total_distance = sum(route.get("total_distance", 0) for route in routes)
        total_delivered = sum(route.get("total_demand", 0) for route in routes)
        total_cost = total_distance * 10
        efficiency = total_delivered / (total_distance + 1) if total_distance > 0 else 0
        execution_time = time.time() - start_time
        return OptimizationResult(
            optimization_id=f"{self.name}_{int(time.time())}",
            algorithm_used=self.name,
            execution_time=execution_time,
            total_distance=total_distance,
            total_cost=total_cost,
            total_delivered=total_delivered,
            routes=routes,
            unserved_points=unserved_points,
            efficiency_score=efficiency,
            timestamp=datetime.now()
        )
