"""数据库基础模块，定义基础类和适配器接口。"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

# type: ignore[attr-defined]
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session

# 定义类型变量
ModelType = TypeVar("ModelType")


@as_declarative()
class Base:
    """SQLAlchemy 声明式基类"""

    # 生成表名
    @declared_attr
    # pylint: disable=no-self-argument,no-member
    def __tablename__(cls) -> str:
        """生成表名，将类名转换为小写作为表名"""
        return cls.__name__.lower()

    # 通用属性和方法
    id: Any
    metadata: MetaData


class DatabaseAdapter(Generic[ModelType]):
    """数据库适配器抽象基类

    这个类定义了数据库操作的通用接口，可以被不同的数据库实现类继承。
    """

    def __init__(self, db_session: Session):
        """初始化数据库适配器

        Args:
            db_session: 数据库会话对象
        """
        self.database_session = db_session

    def get(self, model: Type[ModelType], object_id: Union[UUID, str, int]) -> Optional[ModelType]:
        """通过ID获取单个对象

        Args:
            model: 模型类
            object_id: 对象ID

        Returns:
            找到的对象，如果不存在则返回None
        """
        return self.database_session.query(model).filter(model.id == object_id).first()

    def get_multi(
            self,
            model: Type[ModelType],
            *,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """获取多个对象

        Args:
            model: 模型类
            skip: 跳过的记录数
            limit: 返回的最大记录数
            filters: 过滤条件字典

        Returns:
            对象列表
        """
        query = self.database_session.query(model)

        # 应用过滤条件
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        return query.offset(skip).limit(limit).all()

    def create(self, model: Type[ModelType], obj_in: Dict[str, Any]) -> ModelType:
        """创建新对象

        Args:
            model: 模型类
            obj_in: 包含对象数据的字典

        Returns:
            创建的对象
        """
        db_obj = model(**obj_in)
        self.database_session.add(db_obj)
        self.database_session.commit()
        self.database_session.refresh(db_obj)
        return db_obj

    def update(
            self,
            db_obj: ModelType,
            obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """更新对象

        Args:
            db_obj: 数据库中的对象
            obj_in: 更新数据，可以是字典或对象

        Returns:
            更新后的对象
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.__dict__

        for field in update_data:
            if field in update_data and hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        self.database_session.add(db_obj)
        self.database_session.commit()
        self.database_session.refresh(db_obj)
        return db_obj

    def delete(
            self,
            model: Type[ModelType],
            object_id: Union[UUID, str, int]
    ) -> Optional[ModelType]:
        """删除对象

        Args:
            model: 模型类
            object_id: 对象ID

        Returns:
            被删除的对象，如果不存在则返回None
        """
        obj = self.database_session.query(model).get(object_id)
        if obj:
            self.database_session.delete(obj)
            self.database_session.commit()
        return obj


# 数据库适配器工厂
def get_db_adapter(db_type: str, db_session: Session) -> DatabaseAdapter:
    """根据数据库类型获取适配器实例

    Args:
        db_type: 数据库类型
        db_session: 数据库会话

    Returns:
        数据库适配器实例
    """
    # 导入放在函数内部，避免循环导入
    from app.db.postgresql import PostgreSQLAdapter  # pylint: disable=import-outside-toplevel

    adapters = {
        "postgresql": PostgreSQLAdapter,
        # 可以添加其他数据库类型
        # "mysql": MySQLAdapter,
        # "sqlite": SQLiteAdapter,
    }

    adapter_class = adapters.get(db_type.lower())
    if not adapter_class:
        raise ValueError(f"不支持的数据库类型: {db_type}")

    return adapter_class(db_session)
