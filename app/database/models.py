# app/database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scenarios = relationship("Scenario", back_populates="user")
    simulations = relationship("Simulation", back_populates="user")
class Scenario(Base):
    __tablename__ = 'scenarios'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    scenario_type = Column(String(50))
    severity = Column(Integer)
    description = Column(Text)
    affected_area = Column(Float)
    transport_modes = Column(String(100))
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="scenarios")
    simulations = relationship("Simulation", back_populates="scenario")
class Simulation(Base):
    __tablename__ = 'simulations'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String(20))
    results_json = Column(Text)  # JSON с результатами
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="simulations")
    scenario = relationship("Scenario", back_populates="simulations")