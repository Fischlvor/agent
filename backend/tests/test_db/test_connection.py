"""测试数据库连接"""

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db import get_db


def test_database_connection():
    """测试数据库连接是否成功"""
    # 获取数据库会话
    db = next(get_db())

    try:
        # 执行简单查询
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
        print("数据库连接成功!")

        # 查询数据库版本
        version = db.execute(text("SELECT version()")).scalar()
        print(f"PostgreSQL版本: {version}")

        # 查询表信息
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        tables = [row[0] for row in db.execute(text(tables_query))]
        print(f"数据库表: {tables}")

        # 查询users表结构
        if "users" in tables:
            columns_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            """
            columns = [(row[0], row[1]) for row in db.execute(text(columns_query))]
            print("Users表结构:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")

    finally:
        db.close()


if __name__ == "__main__":
    # 显示数据库连接信息
    print(f"尝试连接到数据库: {settings.DATABASE_URI}")

    # 运行测试
    test_database_connection()
