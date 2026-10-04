from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    oracle_dsn: str = ''
    oracle_user: str = ''
    oracle_password: str = ''
    oracle_client_dir: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = ''
    data_dir: Path = Path('data')
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
