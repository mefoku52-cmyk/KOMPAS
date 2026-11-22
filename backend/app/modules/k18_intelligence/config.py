import os

SETTINGS = {
    "INTELLIGENCE_ENABLED": os.environ.get("INTELLIGENCE_ENABLED", "true").lower() == "true",
    "RETENTION_DAYS_DEFAULT": int(os.environ.get("IL_RETENTION_DAYS", "365")),
    "RETENTION_APPROVED": os.environ.get("IL_RETENTION_APPROVED", "false").lower() == "true",
    "EXTERNAL_AI_ALLOWED": False,
    "HUMAN_APPROVAL_REQUIRED_FOR_SENSITIVE": True,
    "MAX_NOTIFICATIONS_PER_ENTITY_PER_DAY": int(os.environ.get("IL_MAX_NOTIFICATIONS_PER_DAY", "3")),
}
