"""
Утилиты для расчета расстояний и геопространственных операций
"""

import math
from typing import Tuple, List
import numpy as np


class DistanceCalculator:
    """Калькулятор расстояний и геопространственных операций"""
    @staticmethod
    def haversine_distance(
            coord1: Tuple[float, float],
            coord2: Tuple[float, float]
    ) -> float:
        """
        Рассчитать расстояние между двумя точками на сфере (Земле)
        с использованием формулы гаверсинуса.

        Args:
            coord1: (широта, долгота) в градусах
            coord2: (широта, долгота) в градусах

        Returns:
            Расстояние в километрах
        """
        R = 6371.0
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    @staticmethod
    def euclidean_distance(
            point1: Tuple[float, float],
            point2: Tuple[float, float]
    ) -> float:
        """
        Рассчитать евклидово расстояние между двумя точками.

        Args:
            point1: (x, y) координаты
            point2: (x, y) координаты

        Returns:
            Евклидово расстояние
        """
        return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
    @staticmethod
    def manhattan_distance(
            point1: Tuple[float, float],
            point2: Tuple[float, float]
    ) -> float:
        """
        Рассчитать манхэттенское расстояние между двумя точками.

        Args:
            point1: (x, y) координаты
            point2: (x, y) координаты

        Returns:
            Манхэттенское расстояние
        """
        return abs(point2[0] - point1[0]) + abs(point2[1] - point1[1])
    @staticmethod
    def calculate_bearing(
            point1: Tuple[float, float],
            point2: Tuple[float, float]
    ) -> float:
        """
        Рассчитать азимут (направление) от point1 к point2.

        Args:
            point1: Начальная точка (широта, долгота)
            point2: Конечная точка (широта, долгота)

        Returns:
            Азимут в градусах (0-360)
        """
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        return bearing
    @staticmethod
    def is_point_in_polygon(
            point: Tuple[float, float],
            polygon: List[Tuple[float, float]]
    ) -> bool:
        """
        Проверить, находится ли точка внутри многоугольника.

        Args:
            point: Проверяемая точка (x, y)
            polygon: Список вершин многоугольника

        Returns:
            True если точка внутри многоугольника
        """
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    @staticmethod
    def calculate_centroid(points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Рассчитать центроид (центр масс) набора точек.

        Args:
            points: Список точек (x, y)

        Returns:
            Координаты центроида
        """
        x_sum = sum(p[0] for p in points)
        y_sum = sum(p[1] for p in points)
        n = len(points)
        return (x_sum / n, y_sum / n)
    @staticmethod
    def calculate_bounding_box(
            points: List[Tuple[float, float]]
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Рассчитать ограничивающий прямоугольник для набора точек.

        Args:
            points: Список точек (x, y)

        Returns:
            ((min_x, min_y), (max_x, max_y))
        """
        if not points:
            return ((0, 0), (0, 0))
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        return ((min_x, min_y), (max_x, max_y))
    @staticmethod
    def calculate_travel_time(
            distance_km: float,
            speed_kph: float,
            traffic_factor: float = 1.0
    ) -> float:
        """
        Рассчитать время в пути.

        Args:
            distance_km: Расстояние в километрах
            speed_kph: Скорость в км/ч
            traffic_factor: Коэффициент трафика (1.0 = норма, <1.0 = пробки)

        Returns:
            Время в часах
        """
        if speed_kph <= 0:
            return float('inf')
        effective_speed = speed_kph * traffic_factor
        return distance_km / effective_speed

    @staticmethod
    def interpolate_point(
            point1: Tuple[float, float],
            point2: Tuple[float, float],
            fraction: float
    ) -> Tuple[float, float]:
        """
        Интерполировать точку между двумя точками.

        Args:
            point1: Первая точка
            point2: Вторая точка
            fraction: Доля расстояния от point1 к point2 (0-1)

        Returns:
            Интерполированная точка
        """
        x = point1[0] + fraction * (point2[0] - point1[0])
        y = point1[1] + fraction * (point2[1] - point1[1])
        return (x, y)