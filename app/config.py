from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    path: str = "data/datasets.db"


class DataConfig(BaseSettings):
    path: str = "data/images"


class AppConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class AIConfig(BaseSettings):
    base_url: str = "https://api.minimaxi.com/anthropic/v1"
    api_key: str = "your_api_key_here"
    model: str = "MiniMax-M2.7"


class Settings(BaseSettings):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    ai: AIConfig = Field(default_factory=AIConfig)

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                yaml_data: dict[str, Any] = yaml.safe_load(f) or {}
            return cls(**yaml_data)
        return cls()


settings = Settings.from_yaml()
