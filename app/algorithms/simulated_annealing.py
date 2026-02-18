from app.models.optimization_models import CrisisZone, DeliveryPoint, OptimizationResult, RoadNetwork, Vehicle
"""
Алгоритм имитации отжига для локальной оптимизации
"""
import random
import math
import numpy as np
from typing import Dict, List, Tuple, Any
import time
from copy import deepcopy

from app.models.optimization_models import (
    Vehicle, DeliveryPoint, RoadNetwork,
    CrisisZone, OptimizationResult
)
from .base_optimizer import BaseOptimizer
class SimulatedAnnealingOptimizer(BaseOptimizer):
    """Алгоритм имитации отжига для оптимизации"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "SimulatedAnnealing"
        # Параметры алгоритма
        self.initial_temperature = config.get("initial_temperature", 1000.0)
        self.cooling_rate = config.get("cooling_rate", 0.995)
        self.min_temperature = config.get("min_temperature", 0.01)
        self.max_iterations = config.get("max_iterations", 1000)
        self.iterations_per_temp = config.get("iterations_per_temp", 10)
        # Веса для функции стоимости
        self.weights = {
            "distance": config.get("distance_weight", 1.0),
            "time_penalty": config.get("time_penalty_weight", 10.0),
            "capacity": config.get("capacity_weight", 1000.0),
            "unserved": config.get("unserved_weight", 5000.0)
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
        Оптимизация с помощью алгоритма имитации отжига
        """
        start_time = time.time()
        # Валидация
        self.validate_input(vehicles, delivery_points, road_network)
        # Применяем эффекты кризиса
        road_network.apply_crisis_impact(crisis_zones, road_network)
        # Матрица расстояний
        distance_matrix = self.calculate_distance_matrix(
            delivery_points, road_network, depot_location
        )
        # Начальное решение (жадный алгоритм)
        current_solution = self._initial_solution(
            vehicles, delivery_points, distance_matrix
        )
        current_cost = self._calculate_cost(
            current_solution, vehicles, delivery_points, distance_matrix
        )
        best_solution = deepcopy(current_solution)
        best_cost = current_cost
        temperature = self.initial_temperature
        iteration = 0
        cost_history = []
        # Основной цикл алгоритма
        while temperature > self.min_temperature and iteration < self.max_iterations:
            for _ in range(self.iterations_per_temp):
                # Генерация соседнего решения
                neighbor = self._generate_neighbor(current_solution)
                neighbor_cost = self._calculate_cost(
                    neighbor, vehicles, delivery_points, distance_matrix
                )
                # Разница в стоимости
                delta_cost = neighbor_cost - current_cost
                # Принятие решения
                if delta_cost < 0 or random.random() < math.exp(-delta_cost / temperature):
                    current_solution = neighbor
                    current_cost = neighbor_cost
                    if current_cost < best_cost:
                        best_solution = deepcopy(current_solution)
                        best_cost = current_cost
                iteration += 1
            # Охлаждение
            temperature *= self.cooling_rate
            # Логирование
            if iteration % 100 == 0:
                cost_history.append({
                    "iteration": iteration,
                    "temperature": temperature,
                    "current_cost": current_cost,
                    "best_cost": best_cost
                })
                print(f"Iteration {iteration}: Temp = {temperature:.2f}, "
                      f"Cost = {current_cost:.2f}, Best = {best_cost:.2f}")
        # Форматирование результата
        routes = self._format_solution(
            best_solution, vehicles, delivery_points, distance_matrix, depot_location
        )
        # Определяем необслуженные точки
        all_served_points = set()
        for route in routes:
            for point in route["route_points"]:
                if point["type"] == "delivery":
                    all_served_points.add(point["id"])
        all_point_ids = set(point.id for point in delivery_points)
        unserved_points = list(all_point_ids - all_served_points)
        # Создаем результат
        result = self.create_optimization_result(routes, unserved_points, start_time)
        result.optimization_history = cost_history
        return result
    def _initial_solution(
            self,
            vehicles: List[Vehicle],
            points: List[DeliveryPoint],
            distance_matrix: np.ndarray
    ) -> List[List[int]]:
        """Создание начального решения (жадный алгоритм)"""
        solution = []
        # Копируем точки для работы
        remaining_points = list(range(1, len(points) + 1))
        random.shuffle(remaining_points)
        # Распределяем точки по транспортным средствам
        for vehicle in vehicles:
            route = [0]  # Начинаем с депо
            current_load = 0
            # Добавляем точки, пока есть место
            i = 0
            while i < len(remaining_points):
                point_idx = remaining_points[i]
                point = points[point_idx - 1]
                if current_load + point.demand <= vehicle.capacity:
                    route.append(point_idx)
                    current_load += point.demand
                    remaining_points.pop(i)
                else:
                    i += 1
            route.append(0)  # Возвращаемся в депо
            solution.append(route)
        # Если остались точки, добавляем их в первый маршрут (с нарушением ограничений)
        if remaining_points:
            for point_idx in remaining_points:
                solution[0].insert(-1, point_idx)
        return solution
    def _calculate_cost(
            self,
            solution: List[List[int]],
            vehicles: List[Vehicle],
            points: List[DeliveryPoint],
            distance_matrix: np.ndarray
    ) -> float:
        """Рассчитать стоимость решения"""
        total_cost = 0
        total_penalty = 0
        served_points = set()
        for vehicle_idx, route in enumerate(solution):
            if len(route) <= 2:
                continue
            vehicle = vehicles[vehicle_idx]
            route_cost = 0
            route_demand = 0
            current_time = 0
            # Оцениваем маршрут
            for i in range(len(route) - 1):
                from_idx = route[i]
                to_idx = route[i + 1]
                # Стоимость переезда
                distance = distance_matrix[from_idx][to_idx]
                route_cost += distance * self.weights["distance"]
                # Время в пути
                travel_time = distance / vehicle.effective_speed()
                current_time += travel_time
                if to_idx != 0:
                    point = points[to_idx - 1]
                    served_points.add(to_idx)
                    route_demand += point.demand
                    # Штраф за временное окно
                    penalty = point.time_window_penalty(current_time)
                    total_penalty += penalty * self.weights["time_penalty"]
                    # Время разгрузки
                    current_time += point.unloading_time
            # Штраф за превышение вместимости
            if route_demand > vehicle.capacity:
                excess = route_demand - vehicle.capacity
                total_penalty += excess * self.weights["capacity"]
            total_cost += route_cost
        # Штраф за необслуженные точки
        unserved_points = set(range(1, len(points) + 1)) - served_points
        unserved_penalty = len(unserved_points) * self.weights["unserved"]
        return total_cost + total_penalty + unserved_penalty
    def _generate_neighbor(self, solution: List[List[int]]) -> List[List[int]]:
        """Сгенерировать соседнее решение"""
        neighbor = deepcopy(solution)
        if not neighbor:
            return neighbor
        # Выбираем случайную операцию
        operation = random.choice([
            'swap_within_route',
            'swap_between_routes',
            'move_point',
            'reverse_segment',
            'split_route',
            'merge_routes'
        ])
        if operation == 'swap_within_route':
            # Обмен точек внутри маршрута
            route_idx = random.randint(0, len(neighbor) - 1)
            route = neighbor[route_idx]
            if len(route) > 4:
                i, j = random.sample(range(1, len(route) - 1), 2)
                route[i], route[j] = route[j], route[i]
        elif operation == 'swap_between_routes' and len(neighbor) >= 2:
            # Обмен точек между маршрутами
            route1_idx, route2_idx = random.sample(range(len(neighbor)), 2)
            route1 = neighbor[route1_idx]
            route2 = neighbor[route2_idx]
            if len(route1) > 2 and len(route2) > 2:
                i = random.randint(1, len(route1) - 2)
                j = random.randint(1, len(route2) - 2)
                route1[i], route2[j] = route2[j], route1[i]
        elif operation == 'move_point' and len(neighbor) >= 2:
            # Перемещение точки из одного маршрута в другой
            route1_idx, route2_idx = random.sample(range(len(neighbor)), 2)
            route1 = neighbor[route1_idx]
            route2 = neighbor[route2_idx]
            if len(route1) > 2:
                i = random.randint(1, len(route1) - 2)
                point = route1.pop(i)
                j = random.randint(1, len(route2) - 1)
                route2.insert(j, point)
        elif operation == 'reverse_segment':
            # Разворот сегмента маршрута
            route_idx = random.randint(0, len(neighbor) - 1)
            route = neighbor[route_idx]
            if len(route) > 4:
                i, j = sorted(random.sample(range(1, len(route) - 1), 2))
                route[i:j] = reversed(route[i:j])
        return neighbor
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
