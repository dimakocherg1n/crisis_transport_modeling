from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
from datetime import datetime


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
class UUIDMixin:
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
class UserRole(str, enum.Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class User(Base, TimestampMixin, UUIDMixin):
    """Модель пользователя"""
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    scenarios = relationship("Scenario", back_populates="owner", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="created_by")
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
class Scenario(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "scenarios"
    name = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    region_data = Column(JSON, default=dict)
    crisis_type = Column(String(100))
    max_vehicles = Column(Integer, default=5)
    time_horizon = Column(Float, default=24.0)
    budget = Column(Float, nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("User", back_populates="scenarios")
    vehicles = relationship("Vehicle", back_populates="scenario", cascade="all, delete-orphan")
    requests = relationship("TransportRequest", back_populates="scenario", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="scenario", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Scenario(id={self.id}, name={self.name})>"
class Vehicle(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "vehicles"
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    capacity = Column(Float, nullable=False)
    speed = Column(Float, default=60.0)
    cost_per_km = Column(Float, default=50.0)
    fuel_consumption = Column(Float)
    start_location = Column(JSON, nullable=False)
    current_location = Column(JSON)
    is_available = Column(Boolean, default=True)
    scenario = relationship("Scenario", back_populates="vehicles")
    def __repr__(self):
        return f"<Vehicle(id={self.id}, type={self.vehicle_type})>"
class TransportRequest(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "transport_requests"
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    pickup_location = Column(JSON, nullable=False)
    delivery_location = Column(JSON, nullable=False)
    weight = Column(Float, nullable=False)
    volume = Column(Float)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    scenario = relationship("Scenario", back_populates="requests")
    def __repr__(self):
        return f"<TransportRequest(id={self.id}, weight={self.weight})>"
class Simulation(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "simulations"
    scenario_id = Column(String, ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")
    parameters = Column(JSON, default=dict)
    random_seed = Column(Integer)
    results = Column(JSON)
    routes = Column(JSON)
    metrics = Column(JSON)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float)
    created_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = relationship("User", back_populates="simulations")
    error_message = Column(Text)
    error_traceback = Column(Text)
    scenario = relationship("Scenario", back_populates="simulations")
    def __repr__(self):
        return f"<Simulation(id={self.id}, name={self.name}, status={self.status})>"
class OptimizationResult(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "optimization_results"
    simulation_id = Column(String, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    algorithm_name = Column(String(100), nullable=False)
    algorithm_params = Column(JSON, default=dict)
    routes = Column(JSON)
    total_distance = Column(Float)
    total_cost = Column(Float)
    total_time = Column(Float)
    status = Column(String(50), default="completed")
    execution_time = Column(Float)
    simulation = relationship("Simulation")
    def __repr__(self):
        return f"<OptimizationResult(id={self.id}, algorithm={self.algorithm_name})>"
__all__ = [
    'Base', 'User', 'Scenario', 'Vehicle',
    'TransportRequest', 'Simulation', 'OptimizationResult',
    'UserRole'
]