"""数据库会话管理模块，提供数据库连接和会话管理功能。"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import SETTINGS
from app.db.base import DatabaseAdapter, get_db_adapter

# 创建数据库引擎（配置连接池）
ENGINE = create_engine(
    str(SETTINGS.database_uri),
    pool_size=20,              # 连接池大小（根据并发量调整）
    max_overflow=10,           # 超出 pool_size 后最多创建10个临时连接
    pool_timeout=30,           # 获取连接的超时时间（秒）
    pool_recycle=3600,         # 1小时后回收连接（防止连接过期）
    pool_pre_ping=True,        # 使用前检查连接是否有效
    echo=False,                # 不打印SQL语句（生产环境）
    echo_pool=False            # 不打印连接池日志
)

# 创建会话工厂
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)


def get_db() -> Generator:
    """获取数据库会话

    用于依赖注入，提供数据库会话对象

    Yields:
        数据库会话对象
    """
    database_session = SESSION_LOCAL()
    try:
        yield database_session
    finally:
        database_session.close()


def get_db_adapter_instance() -> Generator:
    """获取数据库适配器实例

    用于依赖注入，提供数据库适配器对象

    Yields:
        数据库适配器对象
    """
    database_session = SESSION_LOCAL()
    try:
        adapter = get_db_adapter(SETTINGS.database_type, database_session)
        yield adapter
    finally:
        database_session.close()


class DBSessionManager:
    """数据库会话管理器

    提供上下文管理器接口，用于管理数据库会话的生命周期
    """

    def __init__(self):
        self.database_session = None
        self.adapter = None

    def __enter__(self):
        """进入上下文时创建数据库会话和适配器

        Returns:
            数据库适配器实例
        """
        self.database_session = SESSION_LOCAL()
        self.adapter = get_db_adapter(SETTINGS.database_type, self.database_session)
        return self.adapter

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭数据库会话

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        if self.database_session:
            if exc_type:
                # 发生异常时回滚
                self.database_session.rollback()
            self.database_session.close()


# 导出便捷函数，用于获取数据库适配器
def get_adapter() -> DatabaseAdapter:
    """获取数据库适配器

    用于在非依赖注入场景下获取数据库适配器

    Returns:
        数据库适配器实例
    """
    database_session = SESSION_LOCAL()
    return get_db_adapter(SETTINGS.database_type, database_session)
