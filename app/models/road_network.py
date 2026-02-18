"""
Модели и функции для работы с дорожной сетью
"""

from typing import Dict, List, Tuple, Optional, Set
import heapq
from dataclasses import dataclass
from .optimization_models import RoadSegment, Vehicle


@dataclass
class RoadNetwork:
    """Дорожная сеть"""
    segments: Dict[int, RoadSegment]
    nodes: Dict[Tuple, List[int]]
    def __init__(self):
        self.segments = {}
        self.nodes = {}
    def add_segment(self, segment: RoadSegment):
        """Добавить сегмент дороги"""
        self.segments[segment.id] = segment
        if segment.start not in self.nodes:
            self.nodes[segment.start] = []
        if segment.end not in self.nodes:
            self.nodes[segment.end] = []
        self.nodes[segment.start].append(segment.id)
        self.nodes[segment.end].append(segment.id)
    def get_neighbors(self, point: Tuple[float, float]) -> List[Tuple[Tuple, float]]:
        """Получить соседние узлы и расстояния до них"""
        neighbors = []
        if point not in self.nodes:
            return neighbors
        for segment_id in self.nodes[point]:
            segment = self.segments[segment_id]
            other_end = segment.end if segment.start == point else segment.start
            neighbors.append((other_end, segment.length))
        return neighbors
    def build_graph(self, vehicle: Optional[Vehicle] = None) -> Dict[Tuple, List[Tuple[Tuple, float, int]]]:
        """Построить граф для алгоритмов поиска пути"""
        graph = {}
        for node in self.nodes:
            graph[node] = []
            for segment_id in self.nodes[node]:
                segment = self.segments[segment_id]
                if segment.is_blocked:
                    continue
                if vehicle and not vehicle.can_use_damaged_roads and segment.damage_level > 0.5:
                    continue
                other_end = segment.end if segment.start == node else segment.start
                if vehicle:
                    weight = segment.travel_time(vehicle.speed)
                else:
                    weight = segment.length
                graph[node].append((other_end, weight, segment.id))
        return graph
    def find_path(
            self,
            start: Tuple[float, float],
            end: Tuple[float, float],
            vehicle: Optional[Vehicle] = None,
            algorithm: str = "dijkstra"
    ) -> Tuple[List[Tuple], float, List[int]]:
        """Найти путь между двумя точками"""
        if start not in self.nodes or end not in self.nodes:
            return [], float('inf'), []
        graph = self.build_graph(vehicle)
        if algorithm == "dijkstra":
            return self._dijkstra(graph, start, end)
        elif algorithm == "astar":
            return self._astar(graph, start, end)
        else:
            return self._dijkstra(graph, start, end)
    def _dijkstra(
            self,
            graph: Dict[Tuple, List[Tuple[Tuple, float, int]]],
            start: Tuple,
            end: Tuple
    ) -> Tuple[List[Tuple], float, List[int]]:
        """Алгоритм Дейкстры"""
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        previous_segment = {node: None for node in graph}
        priority_queue = [(0, start)]
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            if current_node == end:
                break
            if current_distance > distances[current_node]:
                continue
            for neighbor, weight, segment_id in graph[current_node]:
                new_distance = current_distance + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_node
                    previous_segment[neighbor] = segment_id
                    heapq.heappush(priority_queue, (new_distance, neighbor))
        if distances[end] == float('inf'):
            return [], float('inf'), []
        path = []
        segments = []
        current = end
        while current is not None:
            path.append(current)
            if previous_segment[current] is not None:
                segments.append(previous_segment[current])
            current = previous[current]
        path.reverse()
        segments.reverse()
        unique_segments = []
        seen = set()
        for seg in segments:
            if seg not in seen:
                unique_segments.append(seg)
                seen.add(seg)
        return path, distances[end], unique_segments
    def _astar(
            self,
            graph: Dict[Tuple, List[Tuple[Tuple, float, int]]],
            start: Tuple,
            end: Tuple
    ) -> Tuple[List[Tuple], float, List[int]]:
        """A* алгоритм"""
        def heuristic(a: Tuple, b: Tuple) -> float:
            """Эвристическая функция (евклидово расстояние)"""
            import math
            return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        previous_segment = {node: None for node in graph}
        f_score = {node: float('inf') for node in graph}
        f_score[start] = heuristic(start, end)
        open_set = [(f_score[start], start)]
        while open_set:
            _, current_node = heapq.heappop(open_set)
            if current_node == end:
                break
            for neighbor, weight, segment_id in graph[current_node]:
                tentative_g = distances[current_node] + weight
                if tentative_g < distances[neighbor]:
                    previous[neighbor] = current_node
                    previous_segment[neighbor] = segment_id
                    distances[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        if distances[end] == float('inf'):
            return [], float('inf'), []
        path = []
        segments = []
        current = end
        while current is not None:
            path.append(current)
            if previous_segment[current] is not None:
                segments.append(previous_segment[current])
            current = previous[current]
        path.reverse()
        segments.reverse()
        unique_segments = []
        seen = set()
        for seg in segments:
            if seg not in seen:
                unique_segments.append(seg)
                seen.add(seg)
        return path, distances[end], unique_segments
    def apply_crisis_impact(
            self,
            crisis_zones: List['CrisisZone'],
            road_network: 'RoadNetwork'
    ):
        """Применить воздействие кризисных зон к дорожной сети"""
        for zone in crisis_zones:
            for road_id in zone.affected_roads:
                if road_id in self.segments:
                    road = self.segments[road_id]
                    road.damage_level = min(1.0, road.damage_level + zone.intensity * 0.3)
                    road.current_traffic = min(1.0, road.current_traffic + zone.intensity * 0.4)
                    if zone.crisis_type == "EARTHQUAKE" and zone.intensity > 0.7:
                        if road.damage_level > 0.5:
                            road.is_blocked = True
                    elif road.damage_level > 0.8:
                        road.is_blocked = True