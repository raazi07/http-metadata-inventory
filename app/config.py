from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://mongodb:27017/metadata_inventory"
    DB_NAME: str = "metadata_inventory"
    
    model_config = {
        "env_file": ".env"
    }

settings = Settings()
