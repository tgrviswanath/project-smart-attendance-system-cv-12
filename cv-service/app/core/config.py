from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "Smart Attendance CV Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    RECOGNITION_TOLERANCE: float = 0.5   # lower = stricter match
    MAX_IMAGE_SIZE: int = 1280

    class Config:
        env_file = ".env"


settings = Settings()
