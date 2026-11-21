# Architektonické alternatívy pre integráciu K-17 (Wellbeing) s K-14 (Communication)

Tento dokument obsahuje tri overené prístupy, ako môže modul K-17 iniciovať komunikáciu so žiakom, zoradené od najrýchlejšieho po najčistejší architektonický štandard.

---

## PRÍSTUP 1: Priamy zápis do DB (The "Direct DB" Hack)
**Koncept:** Úplné obídenie service vrstvy K-14. K-17 priamo manipuluje s modelom `Message`.
**Vhodné pre:** Rýchle prototypovanie, keď neexistuje active thread.
**Nevýhody:** Obchádza validácie vlastníctva threadu, business logiku a eventy K-14.

### Kód pre implementáciu (v `k17_wellbeing_companion/services/service.py`):
```python
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
# Predpokladáme, že tieto modely existujú v K-14
from app.modules.k14_communication_center.domain.models import Message, CommunicationThread

def force_send_ai_intervention(db: Session, student_id: str, thread_id: uuid.UUID, text: str) -> None:
    """
    Priamo vytvorí záznam správy bez volania K-14 service.
    """
    new_message = Message(
        id=uuid.uuid4(),
        thread_id=thread_id,
        sender_id="system_ai_companion", # Fiktívny, ale konzistentný identifikátor
        body=text,
        created_at=datetime.now(timezone.utc),
        is_demo=False # Alebo dynamicky podľa kontextu
    )
    db.add(new_message)
    # Voláme flush, nie commit, aby sme rešpektovali transakciu volajúceho (Event Bus)
    db.flush()
```

---

## PRÍSTUP 2: Interný API kľúč / System Principal (The Clean Bypass)
**Koncept:** Rozšírenie autorizačnej vrstvy tak, aby akceptovala dôveryhodný systémový token a vracala syntetický objekt `Principal`.
**Vhodné pre:** Produkčné prostredie, kde chceme zachovať centralizovanú service vrstvu K-14, ale potrebujeme systémové akcie.

### Krok 2.1: Úprava závislosti (napr. `app/core/security/dependencies.py` alebo kde je `get_current_principal`):
```python
from fastapi import Request, HTTPException, Depends
from app.core.config.settings import settings
# ... ostatné importy pre Principal ...

async def get_current_principal_or_system(
    request: Request,
    db: Session = Depends(get_db)
) -> Principal:
    # 1. Štandardná kontrola JWT tokenu
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        # return await resolve_user_from_jwt(token, db) # Tvoj existujúci kód
    
    # 2. FALLBACK: Kontrola interného systémového kľúča
    internal_key = request.headers.get("X-CMEP-Internal-Key")
    if internal_key and internal_key == settings.CMEP_INTERNAL_API_KEY:
        # Vráť syntetického, ale platného Principal pre AI
        return Principal(
            user_id="ai_companion", 
            role="SYSTEM", 
            school_id=None,
            is_system=True # Custom flag pre bypass kontrol v K-14
        )
        
    raise HTTPException(status_code=401, detail="Unauthorized")
```

### Krok 2.2: Volanie z K-17 (cez HTTP client alebo priame volanie service s mock principalom):
```python
# V K-17 service
from app.core.config.settings import settings
from app.modules.k14_communication_center.services.service import CommunicationService

async def trigger_k14_message(db: Session, student_id: str, text: str):
    # Vytvoríme syntetického principal
    system_principal = Principal(user_id="ai_companion", role="SYSTEM", school_id=None, is_system=True)
    
    # Nájdeme alebo vytvoríme thread pre študenta (zjednodušené)
    # thread = ... 
    
    comm_service = CommunicationService(db)
    # K-14 service musí byť upravená, aby akceptovala role="SYSTEM" bez kontroly participant User ID
    comm_service.post_message(principal=system_principal, thread_id=thread.id, body=text)
```

---

## PRÍSTUP 3: Event-Driven Decoupling (The Architectural Way)
**Koncept:** K-17 nikdy nevolá K-14 priamo. Vydá udalosť. K-14 túto udalosť počúva a spracuje ju vo svojej vlastnej doméne.
**Vhodné pre:** Najvyššiu úroveň škálovateľnosti, čistotu kódu a dodržanie Single Responsibility Principle.

### Krok 3.1: Vydanie udalosti z K-17 (`k17_wellbeing_companion/events/handlers.py`):
```python
from app.core.events.bus import DomainEvent, bus, current_session

# ... v rámci on_AnswerEvaluated, ak alert_level >= 2 ...
intervention_event = DomainEvent(
    event_type="wellbeing.intervention_requested",
    school_id=event.school_id,
    payload={
        "student_id": str(student_id),
        "message": intervention_text,
        "reason": obs.inferred_state.value
    }
)
# Publikujeme s rovnakou DB session, aby sme zachovali konzistenciu transakcie
bus.publish(intervention_event, db=current_session())
```

### Krok 3.2: Vytvorenie handlera v K-14 (`k14_communication_center/events/handlers.py`):
```python
import uuid
from app.core.events.bus import DomainEvent, current_session
from app.modules.k14_communication_center.services.service import CommunicationService
from app.core.security.dependencies import Principal # alebo vytvorenie syntetického

def on_wellbeing_intervention_requested(event: DomainEvent) -> None:
    if event.event_type != "wellbeing.intervention_requested":
        return
        
    db = current_session()
    if not db:
        return # Alebo vytvoriť novú SessionLocal()

    student_id = event.payload.get("student_id")
    message_text = event.payload.get("message")
    
    # Tu K-14 použije svoju vlastnú logiku na nájdenie/vytvorenie threadu
    # a odošle správu. Môže použiť interný bypass pre "SYSTEM" rolu.
    # comm_service = CommunicationService(db)
    # comm_service.send_system_message_to_student(student_id, message_text)
```

### Krok 3.3: Registrácia v `app/core/events/bus.py`:
```python
# Na koniec súboru bus.py
try:
    from app.modules.k14_communication_center.events.handlers import on_wellbeing_intervention_requested
    bus.subscribe("wellbeing.intervention_requested", on_wellbeing_intervention_requested)
except ImportError:
    pass # Handler zatiaľ neexistuje
```
