from app.models.optimization_models import CrisisZone, DeliveryPoint, OptimizationResult, RoadNetwork, Vehicle
"""
Генетический алгоритм для решения Vehicle Routing Problem (VRP)
"""
import random
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set
import time
from copy import deepcopy

from app.models.optimization_models import (
    Vehicle, DeliveryPoint, RoadNetwork,
    CrisisZone, OptimizationResult
)
from .base_optimizer import BaseOptimizer

class GeneticAlgorithmOptimizer(BaseOptimizer):
    """Генетический алгоритм для оптимизации маршрутов"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "GeneticAlgorithm"
        self.population_size = config.get("population_size", 50)
        self.generations = config.get("generations", 100)
        self.mutation_rate = config.get("mutation_rate", 0.1)
        self.crossover_rate = config.get("crossover_rate", 0.8)
        self.elite_size = config.get("elite_size", 5)
        self.tournament_size = config.get("tournament_size", 3)
        self.weights = {
            "distance": config.get("distance_weight", 1.0),
            "time_penalty": config.get("time_penalty_weight", 10.0),
            "capacity_violation": config.get("capacity_weight", 1000.0),
            "unserved_penalty": config.get("unserved_weight", 5000.0),
            "priority_weight": config.get("priority_weight", 100.0)
        }
    def optimize(
            self,
            vehicles: List[Vehicle],
            delivery_points: List[DeliveryPoint],
            road_network: RoadNetwork,
            crisis_zones: List[CrisisZone],
            depot_location: tuple
    ) -> OptimizationResult:
        """
        Оптимизация с помощью генетического алгоритма
        """
        start_time = time.time()
        self.validate_input(vehicles, delivery_points, road_network)
        road_network.apply_crisis_impact(crisis_zones, road_network)
        distance_matrix = self.calculate_distance_matrix(
            delivery_points, road_network, depot_location
        )
        population = self._initialize_population(vehicles, delivery_points)
        best_solution = None
        best_fitness = -float('inf')
        fitness_history = []
        for generation in range(self.generations):
            fitness_scores = []
            for individual in population:
                fitness = self._calculate_fitness(
                    individual, vehicles, delivery_points, distance_matrix
                )
                fitness_scores.append(fitness)
            elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
            elite = [population[i] for i in elite_indices]
            current_best_idx = elite_indices[-1]
            current_best_fitness = fitness_scores[current_best_idx]
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_solution = deepcopy(population[current_best_idx])
            new_population = elite.copy()
            while len(new_population) < self.population_size:
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                if random.random() < self.crossover_rate:
                    child = self._crossover(parent1, parent2)
                else:
                    child = random.choice([parent1, parent2])
                child = self._mutate(child)
                new_population.append(child)
            population = new_population
            avg_fitness = np.mean(fitness_scores)
            fitness_history.append({
                "generation": generation,
                "best_fitness": best_fitness,
                "avg_fitness": avg_fitness
            })
            if generation % 20 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness:.4f}, "
                      f"Avg = {avg_fitness:.4f}")
        routes = self._format_solution(
            best_solution, vehicles, delivery_points, distance_matrix, depot_location
        )
        all_served_points = set()
        for route in routes:
            for point in route["route_points"]:
                if point["type"] == "delivery":
                    all_served_points.add(point["id"])
        all_point_ids = set(point.id for point in delivery_points)
        unserved_points = list(all_point_ids - all_served_points)
        result = self.create_optimization_result(routes, unserved_points, start_time)
        result.optimization_history = fitness_history
        return result
    def _initialize_population(
            self,
            vehicles: List[Vehicle],
            points: List[DeliveryPoint]
    ) -> List[List[List[int]]]:
        """Инициализация популяции"""
        population = []
        for _ in range(self.population_size):
            individual = []
            point_indices = list(range(1, len(points) + 1))
            random.shuffle(point_indices)
            start_idx = 0
            for vehicle in vehicles:
                max_points_for_vehicle = self._estimate_max_points(
                    vehicle, points, point_indices, start_idx
                )
                if max_points_for_vehicle <= 0:
                    route = [0, 0]
                else:
                    end_idx = start_idx + max_points_for_vehicle
                    route_points = point_indices[start_idx:end_idx]
                    random.shuffle(route_points)
                    route = [0] + route_points + [0]
                individual.append(route)
                start_idx += max_points_for_vehicle
            population.append(individual)
        return population
    def _estimate_max_points(
            self,
            vehicle: Vehicle,
            points: List[DeliveryPoint],
            point_indices: List[int],
            start_idx: int
    ) -> int:
        """Оценить максимальное количество точек для транспортного средства"""
        max_points = min(len(point_indices) - start_idx, len(points))
        avg_demand = np.mean([points[idx - 1].demand for idx in point_indices[start_idx:]])
        if avg_demand > 0:
            capacity_based = int(vehicle.capacity / avg_demand)
            max_points = min(max_points, capacity_based)
        return max(1, max_points) if max_points > 0 else 0
    def _calculate_fitness(
            self,
            individual: List[List[int]],
            vehicles: List[Vehicle],
            points: List[DeliveryPoint],
            distance_matrix: np.ndarray
    ) -> float:
        """Рассчитать приспособленность индивида"""
        total_cost = 0
        total_penalty = 0
        served_points = set()
        for vehicle_idx, route in enumerate(individual):
            if len(route) <= 2:
                continue
            vehicle = vehicles[vehicle_idx]
            route_cost, route_penalty, route_points = self._evaluate_route(
                route, vehicle, points, distance_matrix
            )
            total_cost += route_cost
            total_penalty += route_penalty
            served_points.update(route_points)
        unserved_points = set(range(1, len(points) + 1)) - served_points
        unserved_penalty = 0
        for point_idx in unserved_points:
            point = points[point_idx - 1]
            priority_multiplier = 6 - point.priority
            unserved_penalty += priority_multiplier * self.weights["unserved_penalty"]
        total = total_cost + total_penalty + unserved_penalty
        return 1.0 / (total + 1)
    def _evaluate_route(
            self,
            route: List[int],
            vehicle: Vehicle,
            points: List[DeliveryPoint],
            distance_matrix: np.ndarray
    ) -> Tuple[float, float, Set[int]]:
        """Оценить один маршрут"""
        route_cost = 0
        route_penalty = 0
        route_points = set()
        current_time = 0
        total_demand = 0
        for i in range(len(route) - 1):
            from_idx = route[i]
            to_idx = route[i + 1]
            distance = distance_matrix[from_idx][to_idx]
            route_cost += distance * self.weights["distance"]
            travel_time = distance / vehicle.effective_speed()
            current_time += travel_time
            if to_idx != 0:
                point = points[to_idx - 1]
                route_points.add(to_idx)
                total_demand += point.demand
                penalty = point.time_window_penalty(current_time)
                route_penalty += penalty * self.weights["time_penalty"]
                current_time += point.unloading_time
        if total_demand > vehicle.capacity:
            excess = total_demand - vehicle.capacity
            route_penalty += excess * self.weights["capacity_violation"]
        return route_cost, route_penalty, route_points
    def _tournament_selection(
            self,
            population: List,
            fitness_scores: List[float]
    ) -> List:
        """Турнирный отбор"""
        tournament_indices = random.sample(range(len(population)), self.tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return deepcopy(population[winner_idx])
    def _crossover(self, parent1: List, parent2: List) -> List:
        """Скрещивание двух родителей"""
        child = []
        for v_idx in range(len(parent1)):
            if random.random() < 0.5:
                child.append(parent1[v_idx].copy())
            else:
                child.append(parent2[v_idx].copy())
        return child
    def _mutate(self, individual: List) -> List:
        """Мутация индивида"""
        mutated = []
        for route in individual:
            if len(route) <= 3 or random.random() > self.mutation_rate:
                mutated.append(route.copy())
                continue
            new_route = route.copy()
            mutation_type = random.choice(['swap', 'reverse', 'insert', 'scramble'])
            if mutation_type == 'swap' and len(new_route) > 3:
                i, j = random.sample(range(1, len(new_route) - 1), 2)
                new_route[i], new_route[j] = new_route[j], new_route[i]
            elif mutation_type == 'reverse' and len(new_route) > 3:
                i, j = sorted(random.sample(range(1, len(new_route) - 1), 2))
                new_route[i:j] = reversed(new_route[i:j])
            elif mutation_type == 'insert' and len(new_route) > 3:
                i = random.randint(1, len(new_route) - 2)
                point = new_route.pop(i)
                j = random.randint(1, len(new_route) - 1)
                new_route.insert(j, point)
            mutated.append(new_route)
        return mutated
    def _format_solution(
            self,
            solution: List[List[int]],
            vehicles: List[Vehicle],
            points: List[DeliveryPoint],
            distance_matrix: np.ndarray,
            depot_location: tuple
    ) -> List[Dict[str, Any]]:
        """Форматирование решения для вывода"""
        routes = []
        for vehicle_idx, route_indices in enumerate(solution):
            if len(route_indices) <= 2:
                continue
            vehicle = vehicles[vehicle_idx]
            route_result = self.format_route_result(
                vehicle, route_indices, points, distance_matrix, depot_location
            )
            routes.append(route_result)
        return routes
