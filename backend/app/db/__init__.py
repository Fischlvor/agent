"""数据库模块，提供数据库适配器和会话管理功能。"""

from app.db.base import Base, DatabaseAdapter, get_db_adapter
from app.db.mysql import MySQLAdapter
from app.db.postgresql import PostgreSQLAdapter
from app.db.session import (DBSessionManager, SESSION_LOCAL, ENGINE,
                            get_adapter, get_db,
                            get_db_adapter_instance)

__all__ = [
    # 从base.py导出
    "Base",
    "DatabaseAdapter",
    "get_db_adapter",
    # 从mysql.py导出
    "MySQLAdapter",
    # 从postgresql.py导出
    "PostgreSQLAdapter",
    # 从session.py导出
    "DBSessionManager",
    "SESSION_LOCAL",
    "ENGINE",
    "get_adapter",
    "get_db",
    "get_db_adapter_instance",
]
