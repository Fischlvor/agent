"""PostgreSQL数据库适配器实现模块。"""

from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy.orm import Session

from app.db.base import DatabaseAdapter

# 定义类型变量
ModelType = TypeVar("ModelType")


class PostgreSQLAdapter(DatabaseAdapter[ModelType]):
    """PostgreSQL适配器实现

    继承自DatabaseAdapter，提供PostgreSQL特有的功能
    """

    def __init__(self, db_session: Session):
        """初始化PostgreSQL适配器

        Args:
            db_session: 数据库会话对象
        """
        super().__init__(db_session)

    def execute_raw_query(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行原始SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        result = self.database_session.execute(query, params or {})
        return [dict(row) for row in result]

    def full_text_search(
            self,
            model: type,
            column_name: str,
            search_term: str,
            limit: int = 10
    ) -> List[ModelType]:
        """PostgreSQL全文搜索

        使用PostgreSQL的全文搜索功能

        Args:
            model: 模型类
            column_name: 要搜索的列名
            search_term: 搜索词
            limit: 结果限制

        Returns:
            搜索结果列表
        """
        # 使用to_tsquery和to_tsvector进行全文搜索
        query = f"""
        SELECT * FROM {model.__tablename__}
        WHERE to_tsvector('simple', {column_name}) @@ to_tsquery('simple', :search_term)
        LIMIT :limit
        """

        result = self.database_session.execute(query, {
            "search_term": " & ".join(search_term.split()),
            "limit": limit
        })

        return [model(**dict(row)) for row in result]

    def upsert(
            self,
            model: type,
            data: Dict[str, Any],
            constraint_columns: List[str]
    ) -> ModelType:
        """PostgreSQL特有的UPSERT操作

        使用ON CONFLICT DO UPDATE语法实现插入或更新

        Args:
            model: 模型类
            data: 要插入或更新的数据
            constraint_columns: 约束列名列表

        Returns:
            插入或更新的对象
        """
        table_name = model.__tablename__
        columns = list(data.keys())
        values = list(data.values())

        # 构建列名和值的字符串
        columns_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])

        # 构建更新部分的字符串
        update_parts = [
            f"{col} = EXCLUDED.{col}" for col in columns
            if col not in constraint_columns
        ]
        update_str = ", ".join(update_parts)

        # 构建约束列的字符串
        constraint_str = ", ".join(constraint_columns)

        # 构建完整的UPSERT查询
        query = f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT ({constraint_str})
        DO UPDATE SET {update_str}
        RETURNING *
        """

        # 执行查询
        params = {col: val for col, val in zip(columns, values)}
        result = self.database_session.execute(query, params)
        self.database_session.commit()

        # 返回插入或更新的对象
        row = result.fetchone()
        return model(**dict(row)) if row else None

    def array_operations(
            self,
            model: type,
            id_value: Any,
            array_column: str,
            operation: str,
            values: List[Any],
    ) -> ModelType:
        """PostgreSQL数组操作

        对PostgreSQL数组类型的列执行操作

        Args:
            model: 模型类
            id_value: ID值
            array_column: 数组列名
            operation: 操作类型 ('append', 'remove', 'replace')
            values: 要操作的值列表

        Returns:
            更新后的对象
        """
        table_name = model.__tablename__

        if operation == "append":
            # 使用数组连接操作符 ||
            query = f"""
            UPDATE {table_name}
            SET {array_column} = {array_column} || :values
            WHERE id = :id
            RETURNING *
            """
        elif operation == "remove":
            # 使用数组减法操作符 -
            query = f"""
            UPDATE {table_name}
            SET {array_column} = array_remove({array_column}, :value)
            WHERE id = :id
            RETURNING *
            """
            # 对每个值执行移除操作
            for value in values:
                self.database_session.execute(query, {"id": id_value, "value": value})
            self.database_session.commit()
            result = self.database_session.query(model).filter_by(id=id_value).first()
            return result
        elif operation == "replace":
            # 直接替换数组
            query = f"""
            UPDATE {table_name}
            SET {array_column} = :values
            WHERE id = :id
            RETURNING *
            """
        else:
            raise ValueError(f"不支持的数组操作: {operation}")

        # 执行查询
        if operation != "remove":
            result = self.database_session.execute(query, {"id": id_value, "values": values})
            self.database_session.commit()
            row = result.fetchone()
            return model(**dict(row)) if row else None

        return None

    def jsonb_operations(
            self,
            model: type,
            id_value: Any,
            jsonb_column: str,
            operation: str,
            path: str,
            value: Any = None,
    ) -> ModelType:
        """PostgreSQL JSONB操作

        对PostgreSQL JSONB类型的列执行操作

        Args:
            model: 模型类
            id_value: ID值
            jsonb_column: JSONB列名
            operation: 操作类型 ('get', 'set', 'delete')
            path: JSON路径
            value: 要设置的值（仅在'set'操作时需要）

        Returns:
            更新后的对象或查询结果
        """
        table_name = model.__tablename__

        if operation == "get":
            # 获取JSONB字段中的值
            query = f"""
            SELECT {jsonb_column} #> :path as value
            FROM {table_name}
            WHERE id = :id
            """
            result = self.database_session.execute(query, {
                "id": id_value,
                "path": path.split(".")
            })
            row = result.fetchone()
            return row.value if row else None

        elif operation == "set":
            # 设置JSONB字段中的值
            query = f"""
            UPDATE {table_name}
            SET {jsonb_column} = jsonb_set({jsonb_column}, :path, :value::jsonb)
            WHERE id = :id
            RETURNING *
            """
            result = self.database_session.execute(query, {
                "id": id_value,
                "path": path.split("."),
                "value": value
            })
            self.database_session.commit()
            row = result.fetchone()
            return model(**dict(row)) if row else None

        elif operation == "delete":
            # 删除JSONB字段中的键
            query = f"""
            UPDATE {table_name}
            SET {jsonb_column} = {jsonb_column} #- :path
            WHERE id = :id
            RETURNING *
            """
            result = self.database_session.execute(query, {
                "id": id_value,
                "path": path.split(".")
            })
            self.database_session.commit()
            row = result.fetchone()
            return model(**dict(row)) if row else None

        else:
            raise ValueError(f"不支持的JSONB操作: {operation}")
