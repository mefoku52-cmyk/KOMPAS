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

    # Technicka predvolena hodnota, docasna - kym pouzivatel nerozhodne.
    grade_min: int = Field(default=1, alias="GRADE_MIN")
    grade_max: int = Field(default=9, alias="GRADE_MAX")

    database_url: str = Field(..., alias="DATABASE_URL")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

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
