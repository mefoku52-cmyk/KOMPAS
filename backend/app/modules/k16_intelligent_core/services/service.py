from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.k16_intelligent_core.analytics_engine.service import AnalyticsEngineService
from app.modules.k16_intelligent_core.audit_engine.service import AuditEngineService
from app.modules.k16_intelligent_core.context_memory.service import ContextMemoryService
from app.modules.k16_intelligent_core.knowledge_system.service import KnowledgeIndex, KnowledgeSystemService
from app.modules.k16_intelligent_core.orchestrator.service import ModelProvider, NullProvider, OrchestratorService
from app.modules.k16_intelligent_core.rule_system.service import FORBIDDEN_AI_ACTIONS, RuleDecision, RuleSystemService


class K16ServiceFacade:
    def __init__(self, db: Session):
        self.db = db
        self.rule_system = RuleSystemService()
        self.orchestrator = OrchestratorService(db, rule_system=self.rule_system)
        self.knowledge = KnowledgeSystemService(db, index=KnowledgeIndex())
        self.context_memory = ContextMemoryService(db)
        self.analytics = AnalyticsEngineService(db)
        self.audit_engine = AuditEngineService(db)
