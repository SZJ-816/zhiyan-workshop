"""应用配置"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "智研工坊 - 科技创新研发效能平台"
    APP_VERSION: str = "3.0.0"
    
    # 数据库
    DB_HOST: str = os.getenv("DB_HOST", "mysql")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "zentao")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "zentao123")
    DB_NAME: str = os.getenv("DB_NAME", "zentao")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "zentao-secret-key-change-in-production-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # 文件上传
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    # 分页
    PAGE_SIZE: int = 20

settings = Settings()
