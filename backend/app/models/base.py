"""基础模型定义"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr

from app.db import Base


class BaseModel(Base):
    """所有模型的基类，包含共同字段和方法"""

    __abstract__ = True

    # pylint: disable=no-self-argument,no-member
    @declared_attr
    def __tablename__(cls) -> str:
        """生成表名，将类名转换为小写作为表名"""
        return cls.__name__.lower()

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False,
                        comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                        nullable=False, comment="更新时间")

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, UUID):
                value = str(value)
            result[column.name] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """从字典创建模型实例"""
        return cls(**data)

    def update(self, data: Dict[str, Any]) -> None:
        """使用字典更新模型实例"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
