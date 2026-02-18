"""
Муравьиный алгоритм для решения задачи маршрутизации транспорта (ACO-VRP)
Основан на поведении муравьев при поиске кратчайших путей к источнику пищи
"""
import random
import numpy as np
from typing import List, Dict, Tuple, Any
from copy import deepcopy
class AntColonyOptimizer:
    """
    Муравьиный алгоритм для оптимизации маршрутов
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация параметров муравьиного алгоритма
        Args:
            config: Словарь с параметрами
                - ants: количество муравьев
                - evaporation: коэффициент испарения феромона
                - alpha: влияние феромона
                - beta: влияние эвристики
                - iterations: количество итераций
                - q: константа для откладывания феромона
        """
        if config is None:
            config = {}
        self.name = "AntColony"
        self.ants = config.get("ants", 50)
        self.evaporation = config.get("evaporation", 0.1)
        self.alpha = config.get("alpha", 1.0)
        self.beta = config.get("beta", 2.0)
        self.iterations = config.get("iterations", 100)
        self.q = config.get("q", 100)
    def optimize(self, distance_matrix: np.ndarray, n_vehicles: int, capacity: float, demands: List[float]):
        print(f"🐜 Запуск муравьиного алгоритма...")
        print(f"   Муравьев: {self.ants}, Итераций: {self.iterations}")
        n_customers = len(demands)
        n_nodes = n_customers + 1
        pheromone = np.ones((n_nodes, n_nodes)) * 0.1
        heuristic = 1.0 / (distance_matrix + 0.001)
        np.fill_diagonal(heuristic, 0)
        best_route = None
        best_cost = float('inf')
        best_fitness_history = []
        for iteration in range(self.iterations):
            all_routes = []
            all_costs = []
            for ant in range(self.ants):
                routes, cost = self._construct_solution(
                    n_customers, n_vehicles, capacity, demands,
                    pheromone, heuristic, distance_matrix
                )
                all_routes.append(routes)
                all_costs.append(cost)
                if cost < best_cost:
                    best_cost = cost
                    best_route = deepcopy(routes)
            pheromone *= (1 - self.evaporation)
            for routes, cost in zip(all_routes, all_costs):
                deposit = self.q / (cost + 1)
                for route in routes:
                    for i in range(len(route) - 1):
                        pheromone[route[i]][route[i + 1]] += deposit
            best_fitness_history.append(best_cost)
            if iteration % 20 == 0:
                print(f"   Итерация {iteration}: лучшая стоимость = {best_cost:.2f}")
        result = {
            "algorithm": "ant_colony",
            "total_cost": best_cost,
            "routes": best_route,
            "iterations": self.iterations,
            "ants": self.ants,
            "evaporation": self.evaporation,
            "alpha": self.alpha,
            "beta": self.beta,
            "best_fitness_history": best_fitness_history[-10:]
        }
        return result
    def _construct_solution(self, n_customers, n_vehicles, capacity, demands,
                            pheromone, heuristic, distance_matrix):
        """Построение маршрута одним муравьем"""
        unvisited = set(range(1, n_customers + 1))
        routes = []
        total_cost = 0
        vehicle_load = 0
        for vehicle in range(n_vehicles):
            if not unvisited:
                break
            route = [0]
            current = 0
            vehicle_load = 0
            while unvisited:
                probabilities = []
                candidates = []
                for next_node in unvisited:
                    if vehicle_load + demands[next_node - 1] <= capacity:
                        prob = (pheromone[current][next_node] ** self.alpha) * \
                               (heuristic[current][next_node] ** self.beta)
                        probabilities.append(prob)
                        candidates.append(next_node)
                if not candidates:
                    break
                probabilities = np.array(probabilities)
                probabilities = probabilities / probabilities.sum()
                next_node = np.random.choice(candidates, p=probabilities)
                route.append(next_node)
                total_cost += distance_matrix[current][next_node]
                vehicle_load += demands[next_node - 1]
                unvisited.remove(next_node)
                current = next_node
            route.append(0)
            total_cost += distance_matrix[current][0]
            routes.append(route)
        return routes, total_cost