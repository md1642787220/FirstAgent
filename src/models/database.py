"""
数据库引擎初始化与Session工厂
基于 SQLAlchemy + SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings
from src.models.tables import Base

# 创建 SQLite 引擎（check_same_thread=False 允许多线程访问，echo=False 关闭SQL日志）
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """获取数据库 Session（用于 FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """获取数据库 Session（用于非依赖注入场景）"""
    return SessionLocal()
