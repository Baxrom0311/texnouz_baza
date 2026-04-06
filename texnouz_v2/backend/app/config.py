from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local PostgreSQL
    LOCAL_DB_HOST: str = "127.0.0.1"
    LOCAL_DB_PORT: int = 5432
    LOCAL_DB_NAME: str = "texnouz"
    LOCAL_DB_USER: str = "postgres"
    LOCAL_DB_PASSWORD: str = "postgres"

    # Remote PostgreSQL (sync target)
    REMOTE_DB_HOST: str = "3.122.18.70"
    REMOTE_DB_PORT: int = 5432
    REMOTE_DB_NAME: str = "mms_localhost"
    REMOTE_DB_USER: str = "postgres"
    REMOTE_DB_PASSWORD: str = "postgres"

    # AZS (gas station) identity
    AZS_ID: int = 1
    AZS_NAME: str = "AZS #1"

    # Hardware COM ports
    TRK_PORT: str = "COM1"
    TRK_BAUD: int = 9600
    PRINTER_PORT: str = "COM2"
    PRINTER_BAUD: int = 9600
    SIMULATE_HARDWARE: bool = True  # False — real hardware

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "texnouz-v2-secret-change-in-prod"
    TOKEN_EXPIRE_MINUTES: int = 480  # 8 soat

    # Receipt header
    RECEIPT_HEADER: str = "Товарный чек"

    @property
    def local_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}"
            f"@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_NAME}"
        )

    @property
    def local_dsn_sync(self) -> str:
        return (
            f"postgresql://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}"
            f"@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_NAME}"
        )


settings = Settings()
