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


class Settings(BaseSettings):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    app: AppConfig = Field(default_factory=AppConfig)

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                yaml_data: dict[str, Any] = yaml.safe_load(f) or {}
            return cls(**yaml_data)
        return cls()


settings = Settings.from_yaml()
