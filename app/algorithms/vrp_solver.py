from app.models.optimization_models import CrisisZone, DeliveryPoint, OptimizationResult, RoadNetwork, Vehicle
"""
Основной решатель Vehicle Routing Problem (VRP)
Интегрирует различные алгоритмы оптимизации
"""
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

from app.models.optimization_models import (
    Vehicle, DeliveryPoint, RoadNetwork,
    CrisisZone, OptimizationResult
)
from app.algorithms import (
    DijkstraOptimizer, GeneticAlgorithmOptimizer,
    SimulatedAnnealingOptimizer, ClusteringOptimizer
)
from .base_optimizer import BaseOptimizer
class VRPSolver(BaseOptimizer):
    """Основной решатель VRP, интегрирующий разные алгоритмы"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "VRPSolver"
        self.algorithms = {
            "dijkstra": DijkstraOptimizer,
            "genetic": GeneticAlgorithmOptimizer,
            "annealing": SimulatedAnnealingOptimizer,
            "clustering": ClusteringOptimizer,
            "hybrid": None
        }
        self.algorithm_configs = {
            "dijkstra": {"consider_traffic": True, "consider_damage": True},
            "genetic": {
                "population_size": 50,
                "generations": 100,
                "mutation_rate": 0.1,
                "crossover_rate": 0.8
            },
            "annealing": {
                "initial_temperature": 1000.0,
                "cooling_rate": 0.995,
                "max_iterations": 1000
            },
            "clustering": {
                "clustering_method": "kmeans",
                "use_priority": True,
                "use_demand": True
            }
        }
    def optimize(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
            road_network: RoadNetwork,
            crisis_zones: List[CrisisZone],
            depot_location: tuple,
            algorithm: str = "hybrid",
            time_limit: float = 30.0
    ) -> OptimizationResult:
        start_time = time.time()
        self.validate_input(vehicles, delivery_points, road_network)
        road_network.apply_crisis_impact(crisis_zones, road_network)
        if algorithm == "hybrid":
            result = self._hybrid_optimization(
                vehicles, delivery_points, road_network,
                crisis_zones, depot_location, time_limit
            )
        elif algorithm in self.algorithms:
            optimizer_class = self.algorithms[algorithm]
            if optimizer_class:
                config = self.algorithm_configs.get(algorithm, {})
                optimizer = optimizer_class(config)
                result = optimizer.optimize(
                    vehicles, delivery_points, road_network,
                    crisis_zones, depot_location
                )
            else:
                result = self._hybrid_optimization(
                    vehicles, delivery_points, road_network,
                    crisis_zones, depot_location, time_limit
                )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        result.algorithm_used = algorithm
        result.execution_time = time.time() - start_time
        return result
    def _hybrid_optimization(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
            road_network: RoadNetwork,
            crisis_zones: List[CrisisZone],
            depot_location: tuple,
            time_limit: float
    ) -> OptimizationResult:
        """Гибридная оптимизация (комбинация алгоритмов)"""
        start_time = time.time()

        clustering_config = self.algorithm_configs["clustering"]
        clustering_optimizer = ClusteringOptimizer(clustering_config)
        clustering_result = clustering_optimizer.optimize(
            vehicles, delivery_points, road_network,
            crisis_zones, depot_location
        )

        elapsed_time = time.time() - start_time
        if elapsed_time > time_limit * 0.3:
            clustering_result.algorithm_used = "clustering (time limited)"
            return clustering_result
        annealing_config = self.algorithm_configs["annealing"]
        annealing_optimizer = SimulatedAnnealingOptimizer(annealing_config)
        initial_solution = self._result_to_solution(
            clustering_result, vehicles, delivery_points
        )
        annealing_result = annealing_optimizer.optimize(
            vehicles, delivery_points, road_network,
            crisis_zones, depot_location
        )

        if annealing_result.efficiency_score > clustering_result.efficiency_score:
            best_result = annealing_result
            best_result.algorithm_used = "hybrid (clustering + annealing)"
        else:
            best_result = clustering_result
            best_result.algorithm_used = "hybrid (clustering only)"
        best_result.hybrid_stages = {
            "clustering_time": clustering_result.execution_time,
            "annealing_time": annealing_result.execution_time,
            "total_time": time.time() - start_time,
            "clustering_score": clustering_result.efficiency_score,
            "annealing_score": annealing_result.efficiency_score,
            "improvement": annealing_result.efficiency_score - clustering_result.efficiency_score
        }
        return best_result
    def _result_to_solution(
            self,
            result: OptimizationResult,
            vehicles: List[Vehicle],
            points: List[DeliveryPoint]
    ) -> List[List[int]]:
        """Конвертировать результат оптимизации в формат решения"""
        solution = []
        point_id_to_idx = {point.id: i + 1 for i, point in enumerate(points)}
        for vehicle_idx, vehicle in enumerate(vehicles):
            vehicle_route = None
            for route in result.routes:
                if route.get("vehicle_id") == vehicle.id:
                    vehicle_route = route
                    break
            if vehicle_route:
                route_indices = [0]  # Начинаем с депо
                for route_point in vehicle_route.get("route_points", []):
                    if route_point["type"] == "delivery":
                        point_idx = point_id_to_idx.get(route_point["id"])
                        if point_idx:
                            route_indices.append(point_idx)
                route_indices.append(0)
            else:
                route_indices = [0, 0]
            solution.append(route_indices)
        return solution
    def compare_algorithms(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
            road_network: RoadNetwork,
            crisis_zones: List[CrisisZone],
            depot_location: tuple
    ) -> Dict[str, Any]:
        """Сравнение разных алгоритмов оптимизации"""
        comparison_results = {}
        for algo_name in ["dijkstra", "clustering", "genetic", "annealing"]:
            try:
                print(f"\n🔍 Тестирование алгоритма: {algo_name}")
                start_time = time.time()
                optimizer_class = self.algorithms[algo_name]
                config = self.algorithm_configs.get(algo_name, {})
                optimizer = optimizer_class(config)
                result = optimizer.optimize(
                    vehicles, delivery_points, road_network,
                    crisis_zones, depot_location
                )
                execution_time = time.time() - start_time
                comparison_results[algo_name] = {
                    "success": True,
                    "execution_time": execution_time,
                    "total_distance": result.total_distance,
                    "total_cost": result.total_cost,
                    "total_delivered": result.total_delivered,
                    "efficiency_score": result.efficiency_score,
                    "unserved_points": len(result.unserved_points),
                    "routes_count": len(result.routes),
                    "summary": result.get_summary()
                }
                print(f"   Время: {execution_time:.2f} сек")
                print(f"   Дистанция: {result.total_distance:.2f} км")
                print(f"   Доставлено: {result.total_delivered:.2f} т")
                print(f"   Эффективность: {result.efficiency_score:.4f}")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                comparison_results[algo_name] = {
                    "success": False,
                    "error": str(e)
                }
        best_algo = None
        best_score = -1
        for algo_name, result in comparison_results.items():
            if result.get("success") and result.get("efficiency_score", 0) > best_score:
                best_score = result["efficiency_score"]
                best_algo = algo_name
        comparison_results["best_algorithm"] = best_algo
        comparison_results["best_score"] = best_score
        return comparison_results
