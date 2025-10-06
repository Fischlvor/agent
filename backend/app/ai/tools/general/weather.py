import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

import httpx

from ..base import BaseTool

LOGGER = logging.getLogger(__name__)


class TemperatureUnit(str, Enum):
    """温度单位枚举"""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WeatherTool(BaseTool):
    """天气工具，用于获取城市天气信息"""

    def __init__(self):
        """初始化天气工具"""
        self.api_key = os.environ.get("WEATHER_API_KEY",
                                      "e8c77f35aedb3fd5e15a75dfade6ccc2")
        if not self.api_key:
            raise ValueError("必须设置WEATHER_API_KEY环境变量")

        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def execute(
        self,
        location: str,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS,
    ) -> Dict[str, Any]:
        """
        获取指定城市的天气信息

        :param location: 城市名称（英文），如 "Beijing" 或 "New York"
        :param unit: 温度单位，可选值为 "celsius" 或 "fahrenheit"
        :return: 包含天气信息的字典
        """
        LOGGER.info("获取天气信息: 城市=%s, 单位=%s", location, unit)

        try:
            # 构建请求参数
            params = {
                "q":
                location,
                "appid":
                self.api_key,
                "units":
                "metric" if unit == TemperatureUnit.CELSIUS else "imperial",
            }

            # 发送请求
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()

            # 解析响应
            data = response.json()

            # 提取天气信息
            weather_info = {
                "location": location,
                "temperature": {
                    "value": data["main"]["temp"],
                    "unit": unit,
                },
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind": {
                    "speed": data["wind"]["speed"],
                    "unit":
                    "m/s" if unit == TemperatureUnit.CELSIUS else "mph",
                },
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
            }

            return weather_info

        except Exception as e:
            error_message = f"获取天气信息失败: {str(e)}"
            LOGGER.error(error_message)
            raise RuntimeError(error_message)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
