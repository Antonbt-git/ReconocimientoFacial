from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    INSIGHTFACE_MODEL_PACK: str = "buffalo_sc"

    # Lista de orígenes separados por coma permitidos por CORS, ej:
    # ALLOWED_ORIGINS=https://mi-frontend.vercel.app,http://localhost:5174
    ALLOWED_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origen.strip()
            for origen in self.ALLOWED_ORIGINS.split(",")
            if origen.strip()
        ]


settings = Settings()