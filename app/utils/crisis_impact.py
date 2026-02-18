"""
Утилиты для расчета воздействия кризисных ситуаций
"""

from typing import List, Dict, Tuple
import math
from datetime import datetime, timedelta

from app.models.optimization_models import CrisisZone, RoadSegment, DeliveryPoint


class CrisisImpactCalculator:
    """Калькулятор воздействия кризисных ситуаций"""
    @staticmethod
    def calculate_road_damage(
            road: RoadSegment,
            crisis_zone: CrisisZone,
            distance_to_epicenter: float
    ) -> float:
        """
        Рассчитать повреждение дороги от кризиса.

        Args:
            road: Сегмент дороги
            crisis_zone: Кризисная зона
            distance_to_epicenter: Расстояние до эпицентра

        Returns:
            Уровень повреждения (0-1)
        """
        if distance_to_epicenter == 0:
            base_damage = crisis_zone.intensity
        else:
            decay_rate = 0.1
            base_damage = crisis_zone.intensity * math.exp(-decay_rate * distance_to_epicenter)
        if crisis_zone.crisis_type == "EARTHQUAKE":
            damage_multiplier = 1.5
        elif crisis_zone.crisis_type == "FLOOD":
            damage_multiplier = 1.2
        elif crisis_zone.crisis_type == "INDUSTRIAL_ACCIDENT":
            damage_multiplier = 1.3
        else:
            damage_multiplier = 1.0
        if road.road_type == "bridge":
            vulnerability = 1.5
        elif road.road_type == "tunnel":
            vulnerability = 1.3
        elif road.road_type == "dirt_road":
            vulnerability = 1.2
        else:
            vulnerability = 1.0
        total_damage = min(1.0, base_damage * damage_multiplier * vulnerability)
        return total_damage
    @staticmethod
    def calculate_traffic_impact(
            crisis_zone: CrisisZone,
            road: RoadSegment,
            time_since_start: timedelta
    ) -> float:
        """
        Рассчитать влияние кризиса на трафик.

        Args:
            crisis_zone: Кризисная зона
            road: Сегмент дороги
            time_since_start: Время с начала кризиса

        Returns:
            Коэффициент трафика (множитель от нормального трафика)
        """
        if crisis_zone.evacuation_required:
            base_increase = 0.5 + crisis_zone.intensity * 0.5
        else:
            base_increase = crisis_zone.intensity * 0.3
        hours_since_start = time_since_start.total_seconds() / 3600
        if hours_since_start < 1:
            time_factor = 1.5
        elif hours_since_start < 6:
            time_factor = 1.2
        elif hours_since_start < 24:
            time_factor = 1.0
        elif hours_since_start < 72:
            time_factor = 0.8
        else:
            time_factor = 0.5
        if road.road_type == "highway":
            road_factor = 1.3
        elif road.road_type == "main_road":
            road_factor = 1.1
        else:
            road_factor = 1.0
        traffic_increase = base_increase * time_factor * road_factor
        return min(1.0, traffic_increase)

    @staticmethod
    def calculate_point_priority_modifier(
            point: DeliveryPoint,
            crisis_zones: List[CrisisZone]
    ) -> float:
        """
        Рассчитать модификатор приоритета точки на основе кризисного воздействия.

        Args:
            point: Точка доставки
            crisis_zones: Список кризисных зон

        Returns:
            Модификатор приоритета (>1 = повышенный приоритет)
        """
        base_modifier = 1.0

        for zone in crisis_zones:
            if zone.is_point_affected(point.location):
                crisis_modifier = 1.0 + zone.intensity * 0.5
                base_modifier = max(base_modifier, crisis_modifier)
        for zone in crisis_zones:
            if zone.crisis_type == "PANDEMIC" and point.required_equipment:
                if "medical" in [eq.lower() for eq in point.required_equipment]:
                    base_modifier *= 1.3
        return base_modifier

    @staticmethod
    def estimate_recovery_time(
            crisis_zone: CrisisZone,
            damage_level: float,
            resource_availability: float = 0.5
    ) -> timedelta:
        """
        Оценить время восстановления после кризиса.

        Args:
            crisis_zone: Кризисная зона
            damage_level: Уровень повреждений (0-1)
            resource_availability: Доступность ресурсов для восстановления (0-1)

        Returns:
            Оценочное время восстановления
        """
        if crisis_zone.crisis_type == "EARTHQUAKE":
            base_time_hours = 72
        elif crisis_zone.crisis_type == "FLOOD":
            base_time_hours = 48
        elif crisis_zone.crisis_type == "INDUSTRIAL_ACCIDENT":
            base_time_hours = 96
        else:
            base_time_hours = 24
        estimated_hours = base_time_hours * damage_level
        if resource_availability > 0:
            estimated_hours /= resource_availability
        estimated_hours = max(1, min(estimated_hours, 720))
        return timedelta(hours=estimated_hours)
    @staticmethod
    def calculate_risk_score(
            point: DeliveryPoint,
            crisis_zones: List[CrisisZone],
            current_time: datetime
    ) -> float:
        """
        Рассчитать оценку риска для точки доставки.

        Args:
            point: Точка доставки
            crisis_zones: Список кризисных зон
            current_time: Текущее время

        Returns:
            Оценка риска (0-10, где 10 - максимальный риск)
        """
        risk_score = 0
        for zone in crisis_zones:
            if zone.is_point_affected(point.location):
                zone_risk = zone.intensity * 8
                time_since_start = current_time - zone.start_time
                hours_since_start = time_since_start.total_seconds() / 3600
                if hours_since_start < 1:
                    time_factor = 1.5
                elif hours_since_start < 6:
                    time_factor = 1.2
                elif hours_since_start < 24:
                    time_factor = 1.0
                else:
                    time_factor = 0.7
                if zone.crisis_type == "EARTHQUAKE":
                    type_factor = 1.3
                elif zone.crisis_type == "SOCIAL_UNREST":
                    type_factor = 1.4
                elif zone.crisis_type == "PANDEMIC" and point.contact_person:
                    type_factor = 1.2
                else:
                    type_factor = 1.0
                point_risk = zone_risk * time_factor * type_factor
                risk_score = max(risk_score, point_risk)

        return min(10, max(0, risk_score))