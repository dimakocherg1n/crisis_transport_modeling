"""
API endpoints для оптимизации маршрутов
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from app.services.optimization_service import OptimizationService
from app.models.optimization_models import (
    Vehicle, DeliveryPoint, CrisisZone, VehicleType, CrisisType
)

router = APIRouter(prefix="/optimization", tags=["optimization"])

optimization_service = OptimizationService()
class VehicleRequest(BaseModel):
    id: int
    capacity: float = Field(..., gt=0, description="Грузоподъемность в тоннах")
    current_location: tuple = Field(..., description="Текущие координаты (x, y)")
    speed: float = Field(..., gt=0, description="Средняя скорость в км/ч")
    vehicle_type: VehicleType
    fuel_level: float = Field(0.0, ge=0, le=1, description="Уровень топлива (0-1)")
    can_use_damaged_roads: bool = False
    operating_cost_per_km: float = Field(10.0, gt=0)
    driver_available: bool = True
    special_equipment: List[str] = []
class DeliveryPointRequest(BaseModel):
    id: int
    location: tuple = Field(..., description="Координаты точки (x, y)")
    demand: float = Field(..., gt=0, description="Требуемый объем поставки в тоннах")
    priority: int = Field(..., ge=1, le=5, description="Приоритет (1-высокий, 5-низкий)")
    time_window_start: float = Field(..., ge=0, description="Начало временного окна в часах")
    time_window_end: float = Field(..., gt=0, description="Конец временного окна в часах")
    crisis_affected: bool = False
    required_equipment: List[str] = []
    unloading_time: float = Field(0.5, gt=0)
    contact_person: str = ""
    phone_number: str = ""
class CrisisZoneRequest(BaseModel):
    id: int
    center: tuple = Field(..., description="Центр зоны (x, y)")
    radius: float = Field(..., gt=0, description="Радиус зоны в км")
    intensity: float = Field(..., ge=0, le=1, description="Интенсивность кризиса (0-1)")
    crisis_type: CrisisType
    affected_roads: List[int] = []
    start_time: datetime
    expected_end_time: datetime
    description: str = ""
    evacuation_required: bool = False
class OptimizationRequest(BaseModel):
    vehicles: List[VehicleRequest]
    delivery_points: List[DeliveryPointRequest]
    crisis_zones: List[CrisisZoneRequest] = []
    depot_location: tuple = Field(..., description="Местоположение депо (x, y)")
    algorithm: str = Field("hybrid", description="Алгоритм оптимизации")
    time_limit: float = Field(30.0, gt=0, description="Лимит времени в секундах")
class OptimizationResponse(BaseModel):
    success: bool
    optimization_id: str
    message: str
    status_url: Optional[str] = None
class OptimizationStatusResponse(BaseModel):
    optimization_id: str
    status: str
    progress: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
class AlgorithmComparisonResponse(BaseModel):
    comparison_id: str
    algorithms: Dict[str, Dict[str, Any]]
    best_algorithm: str
    best_score: float
    timestamp: datetime
@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_routes(
        request: OptimizationRequest,
        background_tasks: BackgroundTasks
):
    try:
        vehicles = [
            Vehicle(**vehicle.dict())
            for vehicle in request.vehicles
        ]
        delivery_points = [
            DeliveryPoint(**point.dict())
            for point in request.delivery_points
        ]
        crisis_zones = [
            CrisisZone(**zone.dict())
            for zone in request.crisis_zones
        ]
        from app.models.road_network import RoadNetwork
        road_network = RoadNetwork()
        result = await optimization_service.optimize_async(
            vehicles=vehicles,
            delivery_points=delivery_points,
            road_network=road_network,
            crisis_zones=crisis_zones,
            depot_location=request.depot_location,
            algorithm=request.algorithm,
            time_limit=request.time_limit
        )
        return OptimizationResponse(
            success=True,
            optimization_id=result.optimization_id,
            message="Оптимизация запущена успешно",
            status_url=f"/optimization/status/{result.optimization_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске оптимизации: {str(e)}"
        )
@router.get("/status/{optimization_id}", response_model=OptimizationStatusResponse)
async def get_optimization_status(optimization_id: str):
    status = optimization_service.get_optimization_status(optimization_id)
    if status.get("status") == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"Оптимизация с ID {optimization_id} не найдена"
        )
    return OptimizationStatusResponse(
        optimization_id=optimization_id,
        status=status.get("status", "unknown"),
        progress=status.get("progress", 0),
        start_time=status.get("start_time"),
        end_time=status.get("end_time"),
        result=status.get("result"),
        error=status.get("error")
    )
@router.post("/compare-algorithms", response_model=AlgorithmComparisonResponse)
async def compare_algorithms(request: OptimizationRequest):
    try:
        vehicles = [
            Vehicle(**vehicle.dict())
            for vehicle in request.vehicles
        ]
        delivery_points = [
            DeliveryPoint(**point.dict())
            for point in request.delivery_points
        ]
        crisis_zones = [
            CrisisZone(**zone.dict())
            for zone in request.crisis_zones
        ]
        from app.models.road_network import RoadNetwork
        road_network = RoadNetwork()

        comparison = optimization_service.compare_algorithms(
            vehicles=vehicles,
            delivery_points=delivery_points,
            road_network=road_network,
            crisis_zones=crisis_zones,
            depot_location=request.depot_location
        )
        comparison_id = f"comparison_{int(datetime.now().timestamp())}"
        return AlgorithmComparisonResponse(
            comparison_id=comparison_id,
            algorithms=comparison,
            best_algorithm=comparison.get("best_algorithm", ""),
            best_score=comparison.get("best_score", 0),
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сравнении алгоритмов: {str(e)}"
        )
@router.get("/sample-data")
async def get_sample_data():
    sample_data = optimization_service.create_sample_data()
    def convert_to_json(obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, (list, tuple)):
            return [convert_to_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_to_json(value) for key, value in obj.items()}
        elif hasattr(obj, '__dict__'):
            return {key: convert_to_json(value) for key, value in obj.__dict__.items()
                    if not key.startswith('_')}
        else:
            return obj
    return convert_to_json(sample_data)
@router.get("/algorithms")
async def get_available_algorithms():
    algorithms = {
        "dijkstra": {
            "name": "Алгоритм Дейкстры",
            "description": "Поиск кратчайших путей на графе",
            "best_for": "Быстрая начальная оптимизация, небольшие задачи",
            "time_complexity": "O(V²) или O(E + V log V) с кучей",
            "parameters": {
                "consider_traffic": {
                    "type": "bool",
                    "default": True,
                    "description": "Учитывать трафик на дорогах"
                },
                "consider_damage": {
                    "type": "bool",
                    "default": True,
                    "description": "Учитывать повреждения дорог"
                }
            }
        },
        "genetic": {
            "name": "Генетический алгоритм",
            "description": "Эволюционный алгоритм поиска оптимальных маршрутов",
            "best_for": "Сложные задачи с множеством ограничений",
            "time_complexity": "O(population_size × generations)",
            "parameters": {
                "population_size": {
                    "type": "int",
                    "default": 50,
                    "description": "Размер популяции"
                },
                "generations": {
                    "type": "int",
                    "default": 100,
                    "description": "Количество поколений"
                },
                "mutation_rate": {
                    "type": "float",
                    "default": 0.1,
                    "description": "Вероятность мутации"
                },
                "crossover_rate": {
                    "type": "float",
                    "default": 0.8,
                    "description": "Вероятность скрещивания"
                }
            }
        },
        "annealing": {
            "name": "Имитация отжига",
            "description": "Вероятностный алгоритм для глобальной оптимизации",
            "best_for": "Локальная оптимизация уже существующих решений",
            "time_complexity": "O(iterations)",
            "parameters": {
                "initial_temperature": {
                    "type": "float",
                    "default": 1000.0,
                    "description": "Начальная температура"
                },
                "cooling_rate": {
                    "type": "float",
                    "default": 0.995,
                    "description": "Скорость охлаждения"
                },
                "max_iterations": {
                    "type": "int",
                    "default": 1000,
                    "description": "Максимальное количество итераций"
                }
            }
        },
        "clustering": {
            "name": "Кластеризация",
            "description": "Разделение точек на группы и оптимизация внутри групп",
            "best_for": "Большие задачи с множеством точек доставки",
            "time_complexity": "O(n²) для K-means",
            "parameters": {
                "clustering_method": {
                    "type": "string",
                    "default": "kmeans",
                    "options": ["kmeans", "dbscan", "priority_based", "balanced"],
                    "description": "Метод кластеризации"
                },
                "use_priority": {
                    "type": "bool",
                    "default": True,
                    "description": "Учитывать приоритет точек"
                },
                "use_demand": {
                    "type": "bool",
                    "default": True,
                    "description": "Учитывать спрос точек"
                }
            }
        },
        "hybrid": {
            "name": "Гибридный алгоритм",
            "description": "Комбинация нескольких алгоритмов для лучшего результата",
            "best_for": "Производственные задачи с требованием к качеству",
            "time_complexity": "Зависит от комбинации",
            "parameters": {
                "time_limit": {
                    "type": "float",
                    "default": 30.0,
                    "description": "Лимит времени выполнения"
                }
            }
        }
    }
    return {
        "algorithms": algorithms,
        "default_algorithm": "hybrid",
        "recommendations": {
            "small_problems": ["dijkstra", "clustering"],
            "medium_problems": ["genetic", "annealing"],
            "large_problems": ["clustering", "hybrid"],
            "real_time": ["dijkstra"],
            "offline_optimization": ["genetic", "hybrid"]
        }
    }
@router.post("/quick-optimize")
async def quick_optimize():
    try:
        sample_data = optimization_service.create_sample_data()
        result = await optimization_service.optimize_async(
            vehicles=sample_data["vehicles"],
            delivery_points=sample_data["delivery_points"],
            road_network=sample_data["road_network"],
            crisis_zones=sample_data["crisis_zones"],
            depot_location=sample_data["depot_location"],
            algorithm="hybrid",
            time_limit=10.0
        )
        return {
            "success": True,
            "optimization_id": result.optimization_id,
            "message": "Быстрая оптимизация завершена",
            "result": result.to_dict(),
            "status_url": f"/optimization/status/{result.optimization_id}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при быстрой оптимизации: {str(e)}"
        )