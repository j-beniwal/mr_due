from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str
    database_name: str
    google_client_id: str
    google_client_secret: str
    secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()