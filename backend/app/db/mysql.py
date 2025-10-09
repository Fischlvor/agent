"""MySQL数据库适配器实现模块。"""

from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import DatabaseAdapter

# 定义类型变量
ModelType = TypeVar("ModelType")


class MySQLAdapter(DatabaseAdapter[ModelType]):
    """MySQL适配器实现

    继承自DatabaseAdapter，提供MySQL特有的功能
    """

    def __init__(self, db_session: Session):
        """初始化MySQL适配器

        Args:
            db_session: 数据库会话对象
        """
        super().__init__(db_session)

    def execute_raw_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行原生SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        result = self.database_session.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]

    def full_text_search(
            self,
            model: type,
            column_name: str,
            search_term: str,
            limit: int = 10
    ) -> List[ModelType]:
        """MySQL全文搜索

        使用MySQL的MATCH AGAINST进行全文搜索
        注意：需要在相应列上创建FULLTEXT索引

        Args:
            model: 模型类
            column_name: 要搜索的列名
            search_term: 搜索词
            limit: 结果限制

        Returns:
            搜索结果列表
        """
        # 使用MATCH AGAINST进行全文搜索
        query = text(f"""
        SELECT * FROM {model.__tablename__}
        WHERE MATCH({column_name}) AGAINST(:search_term IN NATURAL LANGUAGE MODE)
        LIMIT :limit
        """)

        result = self.database_session.execute(query, {
            "search_term": search_term,
            "limit": limit
        })

        return [model(**dict(row._mapping)) for row in result]

    def upsert(
            self,
            model: type,
            data: Dict[str, Any],
            constraint_columns: List[str]
    ) -> ModelType:
        """MySQL的UPSERT操作

        使用ON DUPLICATE KEY UPDATE语法实现插入或更新

        Args:
            model: 模型类
            data: 要插入或更新的数据
            constraint_columns: 约束列名列表（用于判断重复）

        Returns:
            插入或更新的对象
        """
        table_name = model.__tablename__
        columns = list(data.keys())

        # 构建列名和值的字符串
        columns_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])

        # 构建更新部分的字符串（排除约束列）
        update_parts = [
            f"{col} = VALUES({col})" for col in columns
            if col not in constraint_columns
        ]
        update_str = ", ".join(update_parts)

        # 构建完整的UPSERT查询
        query = text(f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_str}
        """)

        # 执行查询
        self.database_session.execute(query, data)
        self.database_session.commit()

        # 查询并返回结果
        # MySQL的ON DUPLICATE KEY UPDATE不支持RETURNING，需要额外查询
        where_conditions = " AND ".join([f"{col} = :{col}" for col in constraint_columns])
        select_query = text(f"SELECT * FROM {table_name} WHERE {where_conditions}")
        result = self.database_session.execute(select_query,
                                               {col: data[col] for col in constraint_columns})
        row = result.fetchone()
        return model(**dict(row._mapping)) if row else None

    def json_extract(
            self,
            model: type,
            id_value: Any,
            json_column: str,
            path: str
    ) -> Any:
        """MySQL JSON提取操作

        使用JSON_EXTRACT函数提取JSON字段中的值

        Args:
            model: 模型类
            id_value: ID值
            json_column: JSON列名
            path: JSON路径（MySQL格式，如 '$.key.subkey'）

        Returns:
            提取的值
        """
        table_name = model.__tablename__
        query = text(f"""
        SELECT JSON_EXTRACT({json_column}, :path) as value
        FROM {table_name}
        WHERE id = :id
        """)

        result = self.database_session.execute(query, {
            "id": id_value,
            "path": path if path.startswith('$') else f'$.{path}'
        })
        row = result.fetchone()
        return row[0] if row else None

    def json_set(
            self,
            model: type,
            id_value: Any,
            json_column: str,
            path: str,
            value: Any
    ) -> ModelType:
        """MySQL JSON设置操作

        使用JSON_SET函数设置JSON字段中的值

        Args:
            model: 模型类
            id_value: ID值
            json_column: JSON列名
            path: JSON路径（MySQL格式，如 '$.key.subkey'）
            value: 要设置的值

        Returns:
            更新后的对象
        """
        table_name = model.__tablename__

        # MySQL的JSON_SET需要字符串格式的值
        import json
        json_value = json.dumps(value) if not isinstance(value, str) else value

        query = text(f"""
        UPDATE {table_name}
        SET {json_column} = JSON_SET({json_column}, :path, CAST(:value AS JSON))
        WHERE id = :id
        """)

        self.database_session.execute(query, {
            "id": id_value,
            "path": path if path.startswith('$') else f'$.{path}',
            "value": json_value
        })
        self.database_session.commit()

        # 查询并返回更新后的对象
        result = self.database_session.query(model).filter_by(id=id_value).first()
        return result

