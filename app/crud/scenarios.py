from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.database_models import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate


class CRUDScenario(CRUDBase[Scenario, ScenarioCreate, ScenarioUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Scenario]:
        return db.query(Scenario).filter(Scenario.name == name).first()
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Scenario]:
        return db.query(Scenario).filter(Scenario.is_active == True).offset(skip).limit(limit).all()
    def search_by_crisis_type(
            self, db: Session, *, crisis_type: str, skip: int = 0, limit: int = 100
    ) -> List[Scenario]:
        return (
            db.query(Scenario)
            .filter(Scenario.crisis_type.ilike(f"%{crisis_type}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )
scenario = CRUDScenario(Scenario)