from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    oracle_dsn: str = ''
    oracle_user: str = ''
    oracle_password: str = ''
    oracle_client_dir: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = ''
    data_dir: Path = Path('data')
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / '.env', extra='ignore')

    @field_validator('data_dir', mode='after')
    @classmethod
    def resolve_data_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else BACKEND_DIR / value


settings = Settings()
