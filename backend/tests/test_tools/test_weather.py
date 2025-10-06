import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.ai.tools.general.weather import TemperatureUnit, WeatherTool


@pytest.fixture
def weather_tool():
    """创建天气工具实例"""
    return WeatherTool()


@pytest.mark.asyncio
async def test_mock_weather_data(weather_tool):
    """测试模拟天气数据生成"""
    # 测试摄氏度模式
    result = await weather_tool.execute("Beijing", TemperatureUnit.CELSIUS)

    assert result["location"] == "Beijing"
    assert "temperature" in result
    assert "value" in result["temperature"]
    assert "unit" in result["temperature"]
    assert result["temperature"]["unit"] == TemperatureUnit.CELSIUS
    assert "humidity" in result
    assert "pressure" in result
    assert "wind" in result
    assert "speed" in result["wind"]
    assert result["wind"]["unit"] == "m/s"
    assert "description" in result
    assert "icon" in result
    assert "note" in result  # 表明这是模拟数据

    # 测试华氏度模式
    result = await weather_tool.execute("New York", TemperatureUnit.FAHRENHEIT)

    assert result["location"] == "New York"
    assert result["temperature"]["unit"] == TemperatureUnit.FAHRENHEIT
    assert result["wind"]["unit"] == "mph"


@pytest.mark.asyncio
async def test_consistent_mock_data(weather_tool):
    """测试模拟数据的一致性"""
    # 同一城市应该返回相同的模拟数据
    result1 = await weather_tool.execute("Tokyo", TemperatureUnit.CELSIUS)
    result2 = await weather_tool.execute("Tokyo", TemperatureUnit.CELSIUS)

    assert result1["temperature"]["value"] == result2["temperature"]["value"]
    assert result1["humidity"] == result2["humidity"]
    assert result1["description"] == result2["description"]


@pytest.mark.asyncio
async def test_different_cities(weather_tool):
    """测试不同城市返回不同的模拟数据"""
    result1 = await weather_tool.execute("London", TemperatureUnit.CELSIUS)
    result2 = await weather_tool.execute("Paris", TemperatureUnit.CELSIUS)

    # 不同城市应该返回不同的数据
    assert (
        result1["temperature"]["value"] != result2["temperature"]["value"]
        or result1["humidity"] != result2["humidity"]
        or result1["description"] != result2["description"]
    )


@pytest.mark.asyncio
async def test_real_api_call(weather_tool, monkeypatch):
    """测试真实API调用"""
    # 模拟API密钥存在
    monkeypatch.setattr(weather_tool, "api_key", "fake_api_key")

    # 模拟httpx客户端响应
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "main": {"temp": 20.5, "humidity": 65, "pressure": 1012},
        "wind": {"speed": 5.2},
        "weather": [{"description": "晴朗", "icon": "01d"}],
    }

    # 模拟httpx客户端的get方法
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    monkeypatch.setattr(weather_tool, "client", mock_client)

    # 执行测试
    result = await weather_tool.execute("Shanghai", TemperatureUnit.CELSIUS)

    # 验证API调用
    mock_client.get.assert_called_once()

    # 验证结果
    assert result["location"] == "Shanghai"
    assert result["temperature"]["value"] == 20.5
    assert result["temperature"]["unit"] == TemperatureUnit.CELSIUS
    assert result["humidity"] == 65
    assert result["pressure"] == 1012
    assert result["wind"]["speed"] == 5.2
    assert result["wind"]["unit"] == "m/s"
    assert result["description"] == "晴朗"
    assert result["icon"] == "01d"


@pytest.mark.asyncio
async def test_api_error_handling(weather_tool, monkeypatch):
    """测试API错误处理"""
    # 模拟API密钥存在
    monkeypatch.setattr(weather_tool, "api_key", "fake_api_key")

    # 模拟httpx客户端抛出异常
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("API连接失败")
    monkeypatch.setattr(weather_tool, "client", mock_client)

    # 执行测试
    result = await weather_tool.execute("Shanghai", TemperatureUnit.CELSIUS)

    # 验证结果
    assert "error" in result
    assert "API连接失败" in result["error"]
    assert "mock_data" in result  # 应该返回模拟数据作为备用
    assert result["mock_data"]["location"] == "Shanghai"


@pytest.mark.asyncio
async def test_close_method(weather_tool):
    """测试close方法"""
    # 模拟httpx客户端
    mock_client = AsyncMock()
    weather_tool.client = mock_client

    # 执行close方法
    await weather_tool.close()

    # 验证客户端的aclose方法被调用
    mock_client.aclose.assert_called_once()
