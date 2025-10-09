"""应用配置模块，定义配置类和设置。"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类，从YAML文件读取配置"""

    # 配置文件路径
    CONFIG_FILE: str = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config",
        "config.yaml",
    )

    # 配置数据
    _config_data: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_config()

    def _load_config(self) -> None:
        """从YAML文件加载配置"""
        config_file = Path(self.CONFIG_FILE)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.CONFIG_FILE}")

        with open(config_file, "r", encoding="utf-8") as config_file_handle:
            self._config_data = yaml.safe_load(config_file_handle)

    # API配置
    @property
    def api_v1_str(self) -> str:
        """API v1路径前缀。"""
        return self._config_data.get("api", {}).get("v1_str", "/api/v1")

    # 项目配置
    @property
    def project_name(self) -> str:
        """项目名称。"""
        return self._config_data.get("project", {}).get("name", "Agent")

    @property
    def project_description(self) -> str:
        """项目描述。"""
        return self._config_data.get("project", {}).get("description", "")

    # 数据库配置
    @property
    def database_type(self) -> str:
        """数据库类型。"""
        return self._config_data.get("database", {}).get("type", "mysql")

    # MySQL配置
    @property
    def mysql_host(self) -> str:
        """MySQL服务器地址。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("host", "localhost"))

    @property
    def mysql_port(self) -> int:
        """MySQL端口。"""
        return int(
            self._config_data.get("database", {})
            .get("mysql", {}).get("port", 3306))

    @property
    def mysql_username(self) -> str:
        """MySQL用户名。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("username", "root"))

    @property
    def mysql_password(self) -> str:
        """MySQL密码。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("password", ""))

    @property
    def mysql_db_name(self) -> str:
        """MySQL数据库名。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("db_name", "agent"))

    @property
    def mysql_charset(self) -> str:
        """MySQL字符集。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("charset", "utf8mb4"))

    @property
    def mysql_max_idle_conns(self) -> int:
        """MySQL最大空闲连接数。"""
        return int(
            self._config_data.get("database", {})
            .get("mysql", {}).get("max_idle_conns", 10))

    @property
    def mysql_max_open_conns(self) -> int:
        """MySQL最大打开连接数。"""
        return int(
            self._config_data.get("database", {})
            .get("mysql", {}).get("max_open_conns", 100))

    @property
    def mysql_log_mode(self) -> str:
        """MySQL日志模式。"""
        return (self._config_data.get("database", {})
                .get("mysql", {}).get("log_mode", "info"))

    @property
    def database_uri(self) -> Optional[str]:
        """构建数据库URI。"""
        if self.database_type == "mysql":
            return (f"mysql+pymysql://{self.mysql_username}:{self.mysql_password}"
                    f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db_name}"
                    f"?charset={self.mysql_charset}")
        elif self.database_type == "postgresql":
            # 保留 PostgreSQL 支持（如需要）
            postgres_config = self._config_data.get("database", {}).get("postgres", {})
            if postgres_config:
                return (f"postgresql://{postgres_config.get('user', 'postgres')}:"
                        f"{postgres_config.get('password', 'postgres')}"
                        f"@{postgres_config.get('server', 'localhost')}:"
                        f"{postgres_config.get('port', 5432)}/{postgres_config.get('db', 'agent_db')}")
        # 可以在这里添加其他数据库类型的支持
        return None

    # JWT配置
    @property
    def access_token_secret(self) -> str:
        """Access Token密钥。"""
        return self._config_data.get("jwt", {}).get("access_token_secret", "")

    @property
    def refresh_token_secret(self) -> str:
        """Refresh Token密钥。"""
        return self._config_data.get("jwt", {}).get("refresh_token_secret", "")

    @property
    def jwt_algorithm(self) -> str:
        """JWT算法。"""
        return self._config_data.get("jwt", {}).get("algorithm", "HS256")

    @property
    def access_token_expire_minutes(self) -> int:
        """Access Token过期时间（分钟）。"""
        return self._config_data.get("jwt", {}).get("access_token_expire_minutes", 60)

    @property
    def refresh_token_expire_days(self) -> int:
        """Refresh Token过期时间（天）。"""
        return self._config_data.get("jwt", {}).get("refresh_token_expire_days", 7)

    # Redis配置
    @property
    def redis_host(self) -> str:
        """Redis服务器地址。"""
        return self._config_data.get("redis", {}).get("host", "localhost")

    @property
    def redis_port(self) -> int:
        """Redis端口。"""
        return self._config_data.get("redis", {}).get("port", 6379)

    @property
    def redis_password(self) -> Optional[str]:
        """Redis密码。"""
        return self._config_data.get("redis", {}).get("password")

    @property
    def redis_db(self) -> int:
        """Redis数据库编号。"""
        return self._config_data.get("redis", {}).get("db", 0)

    @property
    def redis_decode_responses(self) -> bool:
        """Redis是否自动解码响应。"""
        return self._config_data.get("redis", {}).get("decode_responses", True)

    # 邮件配置
    @property
    def email_host(self) -> str:
        """邮件服务器地址。"""
        return self._config_data.get("email", {}).get("host", "")

    @property
    def email_port(self) -> int:
        """邮件服务器端口。"""
        return self._config_data.get("email", {}).get("port", 465)

    @property
    def email_from(self) -> str:
        """发件人邮箱。"""
        return self._config_data.get("email", {}).get("from", "")

    @property
    def email_nickname(self) -> str:
        """发件人昵称。"""
        return self._config_data.get("email", {}).get("nickname", "")

    @property
    def email_secret(self) -> str:
        """邮件服务密钥/密码。"""
        return self._config_data.get("email", {}).get("secret", "")

    @property
    def email_is_ssl(self) -> bool:
        """是否使用SSL。"""
        return self._config_data.get("email", {}).get("is_ssl", True)

    # 前端配置
    @property
    def frontend_base_url(self) -> str:
        """前端基础URL。"""
        return self._config_data.get("frontend", {}).get("base_url", "http://localhost:3000")

    @property
    def frontend_verify_email_path(self) -> str:
        """前端邮箱验证页面路径。"""
        return self._config_data.get("frontend", {}).get("verify_email_path", "/verify-email")

    @property
    def frontend_reset_password_path(self) -> str:
        """前端密码重置页面路径。"""
        return self._config_data.get("frontend", {}).get("reset_password_path", "/reset-password")


# 创建全局设置对象
SETTINGS = Settings()
