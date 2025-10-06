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
        return self._config_data.get("database", {}).get("type", "postgresql")

    @property
    def postgres_server(self) -> str:
        """PostgreSQL服务器地址。"""
        return (self._config_data.get("database", {})
                .get("postgres", {}).get("server", "localhost"))

    @property
    def postgres_user(self) -> str:
        """PostgreSQL用户名。"""
        return (self._config_data.get("database", {})
                .get("postgres", {}).get("user", "postgres"))

    @property
    def postgres_password(self) -> str:
        """PostgreSQL密码。"""
        return (self._config_data.get("database", {})
                .get("postgres", {}).get("password", "postgres"))

    @property
    def postgres_db(self) -> str:
        """PostgreSQL数据库名。"""
        return (self._config_data.get("database", {})
                .get("postgres", {}).get("db", "agent_db"))

    @property
    def postgres_port(self) -> str:
        """PostgreSQL端口。"""
        return str(
            self._config_data.get("database", {})
            .get("postgres", {}).get("port", 5432))

    @property
    def database_uri(self) -> Optional[str]:
        """构建数据库URI。"""
        if self.database_type == "postgresql":
            return (f"postgresql://{self.postgres_user}:{self.postgres_password}"
                    f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}")
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
