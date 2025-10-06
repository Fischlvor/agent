import asyncio
import json
import os
import sys

sys.path.append(".")

from app.ai.tools.general import WeatherTool
from app.ai.tools.general.weather import TemperatureUnit


async def main():
    # 创建天气工具实例
    weather_tool = WeatherTool()

    try:
        # 执行摄氏度查询
        print("=== 摄氏度天气查询结果 ===")
        result = await weather_tool.execute("Beijing", TemperatureUnit.CELSIUS)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n=== 华氏度天气查询结果 ===")
        result = await weather_tool.execute("New York", TemperatureUnit.FAHRENHEIT)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 展示不同城市的结果差异
        print("\n=== 不同城市的结果比较 ===")
        cities = ["Tokyo", "London", "Paris", "Sydney"]
        for city in cities:
            result = await weather_tool.execute(city, TemperatureUnit.CELSIUS)
            print(f"\n{city}:")
            print(f"  温度: {result['temperature']['value']}°C")
            print(f"  湿度: {result['humidity']}%")
            print(f"  天气: {result['description']}")

    finally:
        # 关闭客户端连接
        await weather_tool.close()


if __name__ == "__main__":
    asyncio.run(main())
