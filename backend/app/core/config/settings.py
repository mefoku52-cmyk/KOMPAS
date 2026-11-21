from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="KOMPAS", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")
    # Swagger/OpenAPI. Defaultne zapnuté v development, v produkcii len ak sa povolí.
    app_docs_enabled: bool = Field(default=False, alias="APP_DOCS_ENABLED")

    # Technicka predvolena hodnota, docasna - kym pouzivatel nerozhodne.
    grade_min: int = Field(default=1, alias="GRADE_MIN")
    grade_max: int = Field(default=9, alias="GRADE_MAX")

    # Analyticke centrum: potlacenie skupin mensich nez prah (predvolene 5)
    analytics_min_group_size: int = Field(default=5, alias="ANALYTICS_MIN_GROUP_SIZE")

    # K-17: interval spracovania počas nečinnosti (sekundy)
    k17_processing_interval_seconds: int = Field(default=300, alias="K17_PROCESSING_INTERVAL_SECONDS")

    database_url: str = Field(..., alias="DATABASE_URL")

    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_timeout_seconds: int = Field(default=30, alias="DB_POOL_TIMEOUT_SECONDS")
    db_pool_recycle_seconds: int = Field(default=1800, alias="DB_POOL_RECYCLE_SECONDS")
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")
    db_statement_timeout_ms: int = Field(default=30000, alias="DB_STATEMENT_TIMEOUT_MS")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_issuer: str = Field(default="kompas", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="kompas-api", alias="JWT_AUDIENCE")

    rate_limit_login_attempts: int = Field(default=5, alias="RATE_LIMIT_LOGIN_ATTEMPTS")
    rate_limit_login_window_seconds: int = Field(default=300, alias="RATE_LIMIT_LOGIN_WINDOW_SECONDS")
    rate_limit_default_per_minute: int = Field(default=120, alias="RATE_LIMIT_DEFAULT_PER_MINUTE")
    login_max_failures: int = Field(default=5, alias="LOGIN_MAX_FAILURES")
    login_lockout_minutes: int = Field(default=15, alias="LOGIN_LOCKOUT_MINUTES")

    # P6: externí poskytovatelia AI sa v tejto etape neimplementujú.
    ai_provider: str = Field(default="null", alias="AI_PROVIDER")
    ai_external_enabled: bool = Field(default=False, alias="AI_EXTERNAL_ENABLED")

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256 (D5).")
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("JWT_SECRET_KEY must be set (no default secret).")
        return value

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        if value != "null":
            raise ValueError("only the null AI provider is implemented (P6).")
        return value

    @field_validator("ai_external_enabled")
    @classmethod
    def validate_ai_external_enabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("external AI providers are not implemented (P6).")
        return value

    @field_validator("grade_min", "grade_max")
    @classmethod
    def validate_grade_bounds(cls, value: int) -> int:
        if value < 1:
            raise ValueError("grade bounds must be >= 1")
        return value

    @field_validator("grade_max")
    @classmethod
    def validate_grade_range(cls, value: int, info) -> int:
        grade_min = info.data.get("grade_min", 1)
        if value < grade_min:
            raise ValueError("GRADE_MAX must be >= GRADE_MIN")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
