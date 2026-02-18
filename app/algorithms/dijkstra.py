from app.models.optimization_models import Vehicle
import heapq
import time
from typing import List, Dict, Optional, Tuple, Any

from .base_optimizer import BaseOptimizer
class DijkstraOptimizer(BaseOptimizer):
    """Оптимизатор на основе алгоритма Дейкстры"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "Dijkstra Optimizer"
    def find_shortest_path(self, graph: Dict[str, Dict[str, float]], 
                          start: str, end: str) -> Tuple[List[str], float]:
        """
        Находит кратчайший путь между двумя узлами
        """
        if start not in graph or end not in graph:
            return [], float('inf')
        distances = {node: float('inf') for node in graph}
        previous = {node: None for node in graph}
        distances[start] = 0
        pq = [(0, start)]
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            if current_distance > distances[current_node]:
                continue
            if current_node == end:
                break
            for neighbor, weight in graph.get(current_node, {}).items():
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path, distances[end] if end in distances else float('inf')
    def optimize_routes(self, network, requests, **kwargs) -> Dict[str, Any]:
        """
        Оптимизирует маршруты для всех запросов
        """
        start_time = time.time()
        graph = {}
        for edge_id, edge in network.edges.items():
            if edge.source not in graph:
                graph[edge.source] = {}
            if edge.target not in graph:
                graph[edge.target] = {}
            travel_time = edge.travel_time * (1 + edge.damage_level)
            if edge.is_blocked:
                travel_time = float('inf')
            graph[edge.source][edge.target] = travel_time
            graph[edge.target][edge.source] = travel_time  # для неориентированного графа
        results = {
            "routes": [],
            "unassigned_requests": [],
            "total_distance": 0,
            "total_time": 0,
            "optimization_time": 0
        }
        for request in requests:
            best_route = None
            best_vehicle = None
            best_time = float('inf')
            for vehicle_id, vehicle in network.vehicles.items():
                if (vehicle.type == request.required_vehicle_type and 
                    vehicle.capacity >= request.required_capacity and
                    vehicle.status == "available"):
                    path, travel_time = self.find_shortest_path(
                        graph, vehicle.current_location, request.location
                    )
                    if travel_time < best_time and path:
                        best_time = travel_time
                        best_route = path
                        best_vehicle = vehicle_id
            if best_route:
                route = {
                    "request_id": request.id,
                    "vehicle_id": best_vehicle,
                    "path": best_route,
                    "travel_time": best_time,
                    "distance": best_time * 50
                }
                results["routes"].append(route)
                results["total_time"] += best_time
                results["total_distance"] += route["distance"]
            else:
                results["unassigned_requests"].append(request.id)
        results["optimization_time"] = time.time() - start_time
        return results
