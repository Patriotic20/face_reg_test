from pydantic import BaseModel, PostgresDsn
from pydantic_settings import SettingsConfigDict, BaseSettings
from dotenv import load_dotenv


load_dotenv()

class ServerConfig(BaseModel):
    app_path: str
    host: str 
    port: int
    
    
class JwtConfig(BaseModel):
    access_token_secret: str
    refresh_token_secret: str
    access_token_expires_minutes: int
    refresh_token_expires_days: int
    algorithm: str

class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

class AdminConfig(BaseModel):
    username: str
    password: str
    name: str

class FileUrl(BaseModel):
    http: str
    upload_dir: str

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        extra="ignore"
    )

    server: ServerConfig
    database: DatabaseConfig
    jwt: JwtConfig
    admin: AdminConfig
    file_url: FileUrl



settings = AppConfig()