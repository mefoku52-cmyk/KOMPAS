# PRODUKCIA_AUDIT

## 8.2 Inventár súborov

Inventár: backend/app, backend/tests, frontend/src, scripts, db, docs. Python analyzovaný cez `ast`, TypeScript/TSX cez čítanie/grep heuristiky. Stav: hotový/čiastočný/stub (orientačne; placeholdery detailne v 8.7).

| Súbor | Riadky | Účel | Stav |
|---|---:|---|---|
| `backend/app/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/audit/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/audit/logger.py` | 118 | logger.py | hotový |
| `backend/app/core/config/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/config/settings.py` | 66 | settings.py | hotový |
| `backend/app/core/database/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/database/session.py` | 33 | session.py | hotový |
| `backend/app/core/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/events/bus.py` | 81 | bus.py | hotový |
| `backend/app/core/permissions/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/permissions/policy.py` | 149 | policy.py | hotový |
| `backend/app/core/security/__init__.py` | 0 | prázdny | stub |
| `backend/app/core/security/auth.py` | 71 | auth.py | hotový |
| `backend/app/core/security/routes.py` | 45 | routes.py | hotový |
| `backend/app/main.py` | 47 | main.py | hotový |
| `backend/app/modules/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k01_learning_profile/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k01_learning_profile/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/domain/models.py` | 27 | models.py | hotový |
| `backend/app/modules/k01_learning_profile/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k01_learning_profile/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/repository/repository.py` | 63 | repository.py | hotový |
| `backend/app/modules/k01_learning_profile/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/services/service.py` | 160 | service.py | hotový |
| `backend/app/modules/k01_learning_profile/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k01_learning_profile/tests/test_service.py` | 97 | test_service.py | hotový |
| `backend/app/modules/k02_subject_workspace/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k02_subject_workspace/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k02_subject_workspace/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/domain/models.py` | 34 | models.py | hotový |
| `backend/app/modules/k02_subject_workspace/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k02_subject_workspace/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/repository/repository.py` | 78 | repository.py | hotový |
| `backend/app/modules/k02_subject_workspace/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/services/service.py` | 125 | service.py | hotový |
| `backend/app/modules/k02_subject_workspace/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k02_subject_workspace/tests/test_service.py` | 64 | test_service.py | hotový |
| `backend/app/modules/k03_adaptive_learning/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k03_adaptive_learning/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k03_adaptive_learning/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/domain/models.py` | 18 | models.py | hotový |
| `backend/app/modules/k03_adaptive_learning/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k03_adaptive_learning/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/repository/repository.py` | 26 | repository.py | hotový |
| `backend/app/modules/k03_adaptive_learning/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/services/service.py` | 89 | service.py | hotový |
| `backend/app/modules/k03_adaptive_learning/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k03_adaptive_learning/tests/test_service.py` | 95 | test_service.py | hotový |
| `backend/app/modules/k04_missions/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k04_missions/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k04_missions/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/domain/models.py` | 49 | models.py | hotový |
| `backend/app/modules/k04_missions/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k04_missions/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/repository/repository.py` | 41 | repository.py | hotový |
| `backend/app/modules/k04_missions/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/services/service.py` | 91 | service.py | hotový |
| `backend/app/modules/k04_missions/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k04_missions/tests/test_service.py` | 74 | test_service.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/domain/models.py` | 34 | models.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/events/handlers.py` | 57 | handlers.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/repository/repository.py` | 51 | repository.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/services/service.py` | 103 | service.py | hotový |
| `backend/app/modules/k05_knowledge_continuity/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k05_knowledge_continuity/tests/test_service.py` | 126 | test_service.py | hotový |
| `backend/app/modules/k06_virtual_lab/__init__.py` | 8 | __init__.py | hotový |
| `backend/app/modules/k06_virtual_lab/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/api/router.py` | 3 | router.py | hotový |
| `backend/app/modules/k06_virtual_lab/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/domain/models.py` | 32 | models.py | hotový |
| `backend/app/modules/k06_virtual_lab/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/events/handlers.py` | 5 | handlers.py | hotový |
| `backend/app/modules/k06_virtual_lab/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/repository/repository.py` | 46 | repository.py | hotový |
| `backend/app/modules/k06_virtual_lab/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/services/service.py` | 91 | service.py | hotový |
| `backend/app/modules/k06_virtual_lab/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k06_virtual_lab/tests/test_service.py` | 44 | test_service.py | hotový |
| `backend/app/modules/k07_professional_library/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k07_professional_library/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k07_professional_library/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/domain/models.py` | 44 | models.py | hotový |
| `backend/app/modules/k07_professional_library/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k07_professional_library/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/repository/repository.py` | 53 | repository.py | hotový |
| `backend/app/modules/k07_professional_library/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/services/service.py` | 95 | service.py | hotový |
| `backend/app/modules/k07_professional_library/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k07_professional_library/tests/test_service.py` | 52 | test_service.py | hotový |
| `backend/app/modules/k08_work_assistant/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k08_work_assistant/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k08_work_assistant/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/domain/models.py` | 28 | models.py | hotový |
| `backend/app/modules/k08_work_assistant/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k08_work_assistant/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/repository/repository.py` | 31 | repository.py | hotový |
| `backend/app/modules/k08_work_assistant/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/services/service.py` | 103 | service.py | hotový |
| `backend/app/modules/k08_work_assistant/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k08_work_assistant/tests/test_service.py` | 60 | test_service.py | hotový |
| `backend/app/modules/k09_class_overview/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k09_class_overview/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k09_class_overview/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/domain/models.py` | 20 | models.py | hotový |
| `backend/app/modules/k09_class_overview/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k09_class_overview/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/repository/repository.py` | 75 | repository.py | hotový |
| `backend/app/modules/k09_class_overview/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/services/service.py` | 73 | service.py | hotový |
| `backend/app/modules/k09_class_overview/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k09_class_overview/tests/test_service.py` | 74 | test_service.py | hotový |
| `backend/app/modules/k10_organization_center/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k10_organization_center/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k10_organization_center/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/domain/models.py` | 38 | models.py | hotový |
| `backend/app/modules/k10_organization_center/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k10_organization_center/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/repository/repository.py` | 43 | repository.py | hotový |
| `backend/app/modules/k10_organization_center/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/services/service.py` | 62 | service.py | hotový |
| `backend/app/modules/k10_organization_center/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k10_organization_center/tests/test_service.py` | 45 | test_service.py | hotový |
| `backend/app/modules/k11_operations_center/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k11_operations_center/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k11_operations_center/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/domain/models.py` | 30 | models.py | hotový |
| `backend/app/modules/k11_operations_center/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/events/handlers.py` | 8 | handlers.py | hotový |
| `backend/app/modules/k11_operations_center/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/repository/repository.py` | 26 | repository.py | hotový |
| `backend/app/modules/k11_operations_center/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/services/service.py` | 73 | service.py | hotový |
| `backend/app/modules/k11_operations_center/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k11_operations_center/tests/test_service.py` | 50 | test_service.py | hotový |
| `backend/app/modules/k12_analytics_center/__init__.py` | 5 | __init__.py | hotový |
| `backend/app/modules/k12_analytics_center/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/api/router.py` | 3 | router.py | hotový |
| `backend/app/modules/k12_analytics_center/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/domain/models.py` | 20 | models.py | hotový |
| `backend/app/modules/k12_analytics_center/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/events/handlers.py` | 3 | handlers.py | hotový |
| `backend/app/modules/k12_analytics_center/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/repository/repository.py` | 73 | repository.py | hotový |
| `backend/app/modules/k12_analytics_center/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/services/service.py` | 94 | service.py | hotový |
| `backend/app/modules/k12_analytics_center/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k12_analytics_center/tests/test_service.py` | 91 | test_service.py | hotový |
| `backend/app/modules/k13_parent_center/__init__.py` | 8 | __init__.py | hotový |
| `backend/app/modules/k13_parent_center/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/api/router.py` | 3 | router.py | hotový |
| `backend/app/modules/k13_parent_center/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/domain/models.py` | 6 | K-13 Rodičovské centrum - doménové modely. | hotový |
| `backend/app/modules/k13_parent_center/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/events/handlers.py` | 7 | handlers.py | hotový |
| `backend/app/modules/k13_parent_center/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/repository/repository.py` | 59 | repository.py | hotový |
| `backend/app/modules/k13_parent_center/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/services/service.py` | 55 | service.py | hotový |
| `backend/app/modules/k13_parent_center/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k13_parent_center/tests/test_service.py` | 50 | test_service.py | hotový |
| `backend/app/modules/k14_communication_center/__init__.py` | 8 | __init__.py | hotový |
| `backend/app/modules/k14_communication_center/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/api/router.py` | 3 | router.py | hotový |
| `backend/app/modules/k14_communication_center/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/domain/models.py` | 39 | models.py | hotový |
| `backend/app/modules/k14_communication_center/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/events/handlers.py` | 5 | handlers.py | hotový |
| `backend/app/modules/k14_communication_center/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/repository/repository.py` | 51 | repository.py | hotový |
| `backend/app/modules/k14_communication_center/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/services/service.py` | 70 | service.py | hotový |
| `backend/app/modules/k14_communication_center/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k14_communication_center/tests/test_service.py` | 51 | test_service.py | hotový |
| `backend/app/modules/k15_collaboration_projects/__init__.py` | 8 | __init__.py | hotový |
| `backend/app/modules/k15_collaboration_projects/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/api/router.py` | 3 | router.py | hotový |
| `backend/app/modules/k15_collaboration_projects/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/domain/models.py` | 54 | models.py | hotový |
| `backend/app/modules/k15_collaboration_projects/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/events/handlers.py` | 5 | handlers.py | hotový |
| `backend/app/modules/k15_collaboration_projects/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/repository/repository.py` | 53 | repository.py | hotový |
| `backend/app/modules/k15_collaboration_projects/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/services/service.py` | 90 | service.py | hotový |
| `backend/app/modules/k15_collaboration_projects/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k15_collaboration_projects/tests/test_service.py` | 48 | test_service.py | hotový |
| `backend/app/modules/k16_intelligent_core/__init__.py` | 10 | __init__.py | hotový |
| `backend/app/modules/k16_intelligent_core/analytics_engine/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/analytics_engine/service.py` | 23 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/api/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/api/router.py` | 8 | router.py | hotový |
| `backend/app/modules/k16_intelligent_core/audit_engine/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/audit_engine/service.py` | 35 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/context_memory/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/context_memory/service.py` | 36 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/domain/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/domain/models.py` | 27 | models.py | hotový |
| `backend/app/modules/k16_intelligent_core/events/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/events/handlers.py` | 9 | handlers.py | hotový |
| `backend/app/modules/k16_intelligent_core/knowledge_system/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/knowledge_system/service.py` | 63 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/orchestrator/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/orchestrator/service.py` | 60 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/repository/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/repository/repository.py` | 70 | repository.py | hotový |
| `backend/app/modules/k16_intelligent_core/rule_system/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/rule_system/service.py` | 61 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/services/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/services/service.py` | 21 | service.py | hotový |
| `backend/app/modules/k16_intelligent_core/tests/__init__.py` | 0 | prázdny | stub |
| `backend/app/modules/k16_intelligent_core/tests/test_service.py` | 87 | test_service.py | hotový |
| `backend/app/shared/__init__.py` | 0 | prázdny | stub |
| `backend/app/shared/curriculum.py` | 34 | curriculum.py | hotový |
| `backend/app/shared/identity.py` | 44 | identity.py | hotový |
| `backend/app/shared/school.py` | 50 | school.py | hotový |
| `backend/app/shared/storage.py` | 35 | storage.py | čiastočný |
| `backend/app/shared/types.py` | 48 | types.py | hotový |
| `backend/tests/test_core_phase1.py` | 126 | test_core_phase1.py | hotový |
| `backend/tests/test_integration_main_flow.py` | 129 | test_integration_main_flow.py | hotový |
| `backend/tests/test_k01_repository.py` | 28 | test_k01_repository.py | hotový |
| `backend/tests/test_k02_repository.py` | 26 | test_k02_repository.py | hotový |
| `backend/tests/test_permissions_matrix.py` | 82 | test_permissions_matrix.py | hotový |
| `backend/tests/test_phase2_migrations.py` | 20 | test_phase2_migrations.py | hotový |
| `backend/tests/test_phase2_schema.py` | 99 | test_phase2_schema.py | hotový |
| `frontend/src/app/globals.css` | 17 | globals.css | hotový |
| `frontend/src/app/layout.tsx` | 16 | layout.tsx | hotový |
| `frontend/src/app/leadership/page.tsx` | 43 | page.tsx | hotový |
| `frontend/src/app/page.tsx` | 74 | page.tsx | hotový |
| `frontend/src/app/parent/page.tsx` | 39 | page.tsx | hotový |
| `frontend/src/app/student/page.tsx` | 51 | page.tsx | hotový |
| `frontend/src/app/teacher/page.tsx` | 50 | page.tsx | hotový |
| `frontend/src/components/.gitkeep` | 0 | .gitkeep | stub |
| `frontend/src/lib/api.ts` | 90 | api.ts | hotový |
| `frontend/src/lib/i18n.ts` | 11 | i18n.ts | hotový |
| `frontend/src/locales/.gitkeep` | 0 | .gitkeep | stub |
| `frontend/src/locales/en/common.json` | 9 | common.json | hotový |
| `frontend/src/locales/sk/common.json` | 9 | common.json | hotový |
| `scripts/build_tree.sh` | 102 | build_tree.sh | hotový |
| `scripts/check_phase.sh` | 170 | check_phase.sh | hotový |
| `scripts/check_prod.sh` | 225 | check_prod.sh | čiastočný |
| `scripts/export_schema.py` | 112 | export_schema.py | hotový |
| `scripts/generate_docs.py` | 75 | Generate docs for phase 7: API contracts (OpenAPI), events catalog, permissions matrix copy, data model. | hotový |
| `scripts/install_deps.sh` | 24 | install_deps.sh | hotový |
| `scripts/make_env.sh` | 40 | make_env.sh | hotový |
| `scripts/run_dev.sh` | 18 | run_dev.sh | hotový |
| `scripts/seed_demo.py` | 127 | Demonštračné dáta pre KOMPAS (ilustračné, nie skutočné osobné údaje). | hotový |
| `scripts/sync_locales.sh` | 9 | sync_locales.sh | hotový |
| `db/migrations/.gitkeep` | 0 | .gitkeep | stub |
| `db/migrations/env.py` | 87 | env.py | hotový |
| `db/migrations/script.py.mako` | 25 | script.py.mako | hotový |
| `db/migrations/versions/075c5fee0acb_k04_learning_missions_tables.py` | 91 | k04 learning missions tables | hotový |
| `db/migrations/versions/0efd5c3fea8a_k10_organization_center_tables.py` | 81 | k10 organization center tables | hotový |
| `db/migrations/versions/10190dd26821_k14_communication_tables.py` | 90 | k14 communication tables | hotový |
| `db/migrations/versions/1772fc0f95d2_k08_work_assistant_draft_table.py` | 49 | k08 work assistant draft table | hotový |
| `db/migrations/versions/2082a58f3cf8_k02_subject_workspace_tables.py` | 77 | k02 subject workspace tables | hotový |
| `db/migrations/versions/3f22949ff3ef_k09_class_teacher_assignment.py` | 49 | k09 class teacher assignment | hotový |
| `db/migrations/versions/42c945b3f8ef_k03_adaptive_recommendation_table.py` | 50 | k03 adaptive recommendation table | hotový |
| `db/migrations/versions/4b3ffc9c996d_k11_operations_center_request_table.py` | 48 | k11 operations center request table | hotový |
| `db/migrations/versions/663424a2243d_k15_collaboration_project_tables.py` | 117 | k15 collaboration project tables | hotový |
| `db/migrations/versions/66e26d8f3c95_k06_virtual_lab_tables.py` | 70 | k06 virtual lab tables | hotový |
| `db/migrations/versions/759ba5ad5f06_k05_progress_topic_state.py` | 52 | k05 progress topic state | hotový |
| `db/migrations/versions/822ee05ee37a_core_and_shared_tables.py` | 229 | core and shared tables | hotový |
| `db/migrations/versions/8fc7fb274460_k01_progress_student_profile.py` | 51 | k01 progress student profile | hotový |
| `db/migrations/versions/a356d488b6eb_k16_ai_knowledge_tables.py` | 56 | k16 ai knowledge tables | hotový |
| `db/migrations/versions/c0094984f2f2_k07_teacher_workspace_library_tables.py` | 88 | k07 teacher workspace library tables | hotový |
| `db/migrations/versions/c33529dc7080_k12_analytics_snapshot_table.py` | 45 | k12 analytics snapshot table | hotový |
| `db/schema/ai_knowledge.sql` | 29 | ai_knowledge.sql | hotový |
| `db/schema/audit.sql` | 33 | audit.sql | hotový |
| `db/schema/communication.sql` | 62 | communication.sql | hotový |
| `db/schema/curriculum.sql` | 89 | curriculum.sql | hotový |
| `db/schema/identity.sql` | 55 | identity.sql | hotový |
| `db/schema/learning.sql` | 106 | learning.sql | hotový |
| `db/schema/organization.sql` | 164 | organization.sql | hotový |
| `db/schema/progress.sql` | 89 | progress.sql | hotový |
| `db/schema/school.sql` | 93 | school.sql | hotový |
| `db/schema/teacher_workspace.sql` | 82 | teacher_workspace.sql | hotový |
| `db/seeds/.gitkeep` | 0 | .gitkeep | stub |
| `docs/BASELINE.md` | 104 | BASELINE.md | hotový |
| `docs/OPENCODE_PROMPT.md` | 220 | OPENCODE_PROMPT.md | hotový |
| `docs/OPENCODE_PROMPT_PRODUKCIA.md` | 203 | OPENCODE_PROMPT_PRODUKCIA.md | čiastočný |
| `docs/PROGRES.md` | 12 | PROGRES.md | hotový |
| `docs/REPORT_FAZA_7.md` | 193 | REPORT_FAZA_7.md | hotový |
| `docs/adr/0001-identity-partner.md` | 0 | 0001-identity-partner.md | stub |
| `docs/adr/0002-technology-and-storage.md` | 17 | 0002-technology-and-storage.md | hotový |
| `docs/adr/0003-migrations-and-schema-export.md` | 15 | 0003-migrations-and-schema-export.md | hotový |
| `docs/adr/0004-table-naming-convention.md` | 16 | 0004-table-naming-convention.md | hotový |
| `docs/adr/0005-cache-queue-and-knowledge-index.md` | 16 | 0005-cache-queue-and-knowledge-index.md | hotový |
| `docs/adr/0006-authentication-and-secrets.md` | 18 | 0006-authentication-and-secrets.md | hotový |
| `docs/adr/0007-file-storage.md` | 14 | 0007-file-storage.md | hotový |
| `docs/adr/0008-frontend-locales.md` | 15 | 0008-frontend-locales.md | hotový |
| `docs/adr/0009-local-env-bootstrap.md` | 17 | 0009-local-env-bootstrap.md | hotový |
| `docs/api-contracts/README.md` | 19 | README.md | hotový |
| `docs/api-contracts/openapi.json` | 380 | openapi.json | hotový |
| `docs/architecture/system_architecture.md` | 0 | system_architecture.md | stub |
| `docs/data-model/README.md` | 63 | README.md | hotový |
| `docs/events/README.md` | 9 | README.md | hotový |
| `docs/metrics/README.md` | 0 | README.md | stub |
| `docs/modules/K-01.md` | 25 | K-01.md | hotový |
| `docs/modules/K-02.md` | 25 | K-02.md | hotový |
| `docs/modules/K-03.md` | 23 | K-03.md | hotový |
| `docs/modules/K-04.md` | 28 | K-04.md | hotový |
| `docs/modules/K-05.md` | 23 | K-05.md | hotový |
| `docs/modules/K-06.md` | 22 | K-06.md | hotový |
| `docs/modules/K-07.md` | 24 | K-07.md | hotový |
| `docs/modules/K-08.md` | 23 | K-08.md | hotový |
| `docs/modules/K-09.md` | 24 | K-09.md | hotový |
| `docs/modules/K-10.md` | 21 | K-10.md | hotový |
| `docs/modules/K-11.md` | 25 | K-11.md | hotový |
| `docs/modules/K-12.md` | 21 | K-12.md | hotový |
| `docs/modules/K-13.md` | 20 | K-13.md | hotový |
| `docs/modules/K-14.md` | 21 | K-14.md | hotový |
| `docs/modules/K-15.md` | 22 | K-15.md | hotový |
| `docs/modules/K-16.md` | 36 | K-16.md | hotový |
| `docs/permissions/README.md` | 36 | README.md | hotový |
| `docs/research/README.md` | 0 | README.md | stub |

## 8.3 Porovnanie modulov K-01 až K-16

Porovnanie so sekciou 7 `docs/OPENCODE_PROMPT.md` a `docs/modules/K-XX.md`. Stav vychádza z prítomnosti vrstiev, service logiky, testov a reálne vystavených API endpointov (OpenAPI).

### K-16 - Inteligentné jadro
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | orchestrator ModelProvider/NullProvider, výber podľa úlohy, volanie cez rule_system+audit<br>knowledge_system register schválených zdrojov, vyhľadávanie iba nad schválenými (KnowledgeIndex)<br>context_memory s odkazom na zdrojový štruktúrovaný záznam a platnosťou, nie zdroj pravdy<br>rule_system povolené polia, zakázané akcie (pedagogické rozhodnutia, hodnotenie osobnosti), povolenie/zamietnutie<br>analytics_engine spracovanie udalostí na agregáty<br>audit_engine iba čítanie/dotazy nad auditom |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>testy: test_service.py<br>podsystémy: analytics_engine, audit_engine, context_memory, knowledge_system, orchestrator, rule_system<br>požiadavka pokrytá v kóde/docs: orchestrator ModelProvider/NullProvider, výber podľa úlohy, volanie cez rule_system+audit<br>požiadavka pokrytá v kóde/docs: knowledge_system register schválených zdrojov, vyhľadávanie iba nad schválenými (KnowledgeIndex)<br>požiadavka pokrytá v kóde/docs: context_memory s odkazom na zdrojový štruktúrovaný záznam a platnosťou, nie zdroj pravdy<br>požiadavka pokrytá v kóde/docs: rule_system povolené polia, zakázané akcie (pedagogické rozhodnutia, hodnotenie osobnosti), povolenie/zamietnutie<br>požiadavka pokrytá v kóde/docs: analytics_engine spracovanie udalostí na agregáty<br>požiadavka pokrytá v kóde/docs: audit_engine iba čítanie/dotazy nad auditom |
| Chýbajúce / medzery | bez UI integrácie (frontend dlaždice) okrem status endpointu; externí poskytovatelia zámerne nie (P6) |
| Endpointy (OpenAPI) | `GET /k16/status` |
| Testy | `backend/app/modules/k16_intelligent_core/tests/test_service.py` |

### K-01 - Osobný vzdelávací profil
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | profil žiaka na školský rok a ročník<br>história sa nikdy neprepisuje (nový záznam na nový rok)<br>prehľad histórie |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k01/status` |
| Testy | `backend/app/modules/k01_learning_profile/tests/test_service.py` |

### K-02 - Predmetové prostredie
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | predmet a konfigurovateľný strom učiva učiteľa (poradie,vnorenie)<br>podľa existujúceho plánu, bez núteného meniaceho sa rozvrhu |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k02/status` |
| Testy | `backend/app/modules/k02_subject_workspace/tests/test_service.py` |

### K-05 - Znalostná kontinuita
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | záznam stavu témy: druhy prebraté/precvičené/overené; stavy prebiehajúce precvičovanie, čiastočne zvládnuté, overené zvládnutie<br>každá zmena má dôkaz (odkaz na pokus) a platnosť<br>overené zvládnutie iba z overovacieho pokusu, nikdy z precvičovania<br>odoberá udalosť vyhodnotenia odpovede |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>odber AnswerEvaluated v event handleri<br>rozlíšenie druhov/stavov a dôkaz v doméne/service (podľa docs/testov) |
| Chýbajúce / medzery | API pre čítanie/zápis stavov nie je vystavené (len status) |
| Endpointy (OpenAPI) | `GET /k05/status` |
| Testy | `backend/app/modules/k05_knowledge_continuity/tests/test_service.py` |

### K-04 - Vzdelávacie misie
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | misia, úlohy (výber, číselná odpoveď, text so zhodou) s deterministickým vyhodnotením<br>pokus žiaka<br>publikovanie udalosti AnswerEvaluated |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>publikovanie udalosti AnswerEvaluated<br>deterministické vyhodnotenie typov úloh v service vrstve |
| Chýbajúce / medzery | verejné API pokrýva najmä status; chýbajú CRUD/submit endpointy pre UI tok |
| Endpointy (OpenAPI) | `GET /k04/status` |
| Testy | `backend/app/modules/k04_missions/tests/test_service.py` |

### K-03 - Adaptívne učenie
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | odporúčanie ďalšieho precvičovania z K-05<br>deterministické a vysvetliteľné (dôvod)<br>bez odvodzovania vlastností osobnosti<br>odporúčanie je návrh, učiteľ môže zmeniť |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>deterministické vysvetliteľné odporúčania s dôvodom |
| Chýbajúce / medzery | API endpoint na získanie odporúčaní pre UI chýba (len status) |
| Endpointy (OpenAPI) | `GET /k03/status` |
| Testy | `backend/app/modules/k03_adaptive_learning/tests/test_service.py` |

### K-09 - Triedny prehľad
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | rozdelenie stavov učiva v triede<br>iba pre triedy daného učiteľa |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>triedny prehľad v service vrstve (agregácia stavov) |
| Chýbajúce / medzery | API endpoint prehľadu triedy pre učiteľa chýba (len status) |
| Endpointy (OpenAPI) | `GET /k09/status` |
| Testy | `backend/app/modules/k09_class_overview/tests/test_service.py` |

### K-07 - Profesionálna knižnica
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | položky vlastnené učiteľom, verzie, štítky<br>archív prežívajúci zmenu školského roka<br>súbory cez FileStorage |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k07/status` |
| Testy | `backend/app/modules/k07_professional_library/tests/test_service.py` |

### K-08 - Pracovný asistent
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | návrh pracovného listu/testu z knižnice a učiva cez orchestrátor<br>výstup je koncept vyžadujúci schválenie učiteľom<br>funguje aj bez AI (šablónový režim) |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k08/status` |
| Testy | `backend/app/modules/k08_work_assistant/tests/test_service.py` |

### K-10 - Organizačné centrum
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | úlohy, termíny, plán školy, priradenia |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k10/status` |
| Testy | `backend/app/modules/k10_organization_center/tests/test_service.py` |

### K-11 - Prevádzkové centrum
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | požiadavky na priestory a vybavenie so stavovým tokom |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>základná funkcionalita podľa docs/modules a service vrstvy |
| Chýbajúce / medzery | API pokrýva najmä status; chýbajú doménové endpointy pre UI |
| Endpointy (OpenAPI) | `GET /k11/status` |
| Testy | `backend/app/modules/k11_operations_center/tests/test_service.py` |

### K-12 - Analytické centrum
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | agregované prehľady školy<br>skupiny menšie než prah (predvolene 5) sa potláčajú<br>individuálne údaje iba s uvedeným účelom (audit) |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>agregácie, prah potlačenia a účel pri individuálnych údajoch v service vrstve |
| Chýbajúce / medzery | žiadny endpoint v OpenAPI (router bez ciest) |
| Endpointy (OpenAPI) | žiadne (okrem prípadného neexportovaného) |
| Testy | `backend/app/modules/k12_analytics_center/tests/test_service.py` |

### K-13 - Rodičovské centrum
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | väzba rodič-dieťa<br>prehľad schválených informácií o vlastnom dieťati<br>rodič nikdy nevidí súkromné poznámky učiteľa |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>väzba rodič-dieťa a filtrovanie schválených informácií v service vrstve |
| Chýbajúce / medzery | žiadny endpoint v OpenAPI (router bez ciest) |
| Endpointy (OpenAPI) | žiadne (okrem prípadného neexportovaného) |
| Testy | `backend/app/modules/k13_parent_center/tests/test_service.py` |

### K-14 - Komunikačné centrum
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | vlákna a správy medzi povolenými účastníkmi<br>súkromné vlákna viditeľné iba účastníkom<br>prístup k obsahu sa audituje |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>vlákna/správy/účastníci a kontrola prístupu v service/doméne |
| Chýbajúce / medzery | žiadny endpoint v OpenAPI (router bez ciest) |
| Endpointy (OpenAPI) | žiadne (okrem prípadného neexportovaného) |
| Testy | `backend/app/modules/k14_communication_center/tests/test_service.py` |

### K-15 - Spolupráca a projekty
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | projekt, členovia (aj medziročníkoví), úlohy, odovzdania |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>projekty/členovia/úlohy/odovzdania v service/doméne |
| Chýbajúce / medzery | žiadny endpoint v OpenAPI (router bez ciest) |
| Endpointy (OpenAPI) | žiadne (okrem prípadného neexportovaného) |
| Testy | `backend/app/modules/k15_collaboration_projects/tests/test_service.py` |

### K-06 - Virtuálne laboratórium
| Oblasť | Obsah |
|---|---|
| Požadované funkcie (sekcia 7) | dátovo riadený rámec simulácií (parametre a deterministická funkcia v registri)<br>jedna ukážková simulácia |
| Hotové (kód/testy/docs) | štruktúra a-g (domain/repo/service/events/api/tests)<br>autorizácia/audit v service vrstve (podľa implementácie)<br>testy: test_service.py<br>rámec simulácií a ukážková simulácia v service/doméne |
| Chýbajúce / medzery | žiadny endpoint v OpenAPI (router bez ciest) |
| Endpointy (OpenAPI) | žiadne (okrem prípadného neexportovaného) |
| Testy | `backend/app/modules/k06_virtual_lab/tests/test_service.py` |

