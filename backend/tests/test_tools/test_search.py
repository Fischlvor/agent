import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.ai.tools.general.search import SearchTool


@pytest.fixture
def search_tool():
    """创建搜索工具实例"""
    return SearchTool()


@pytest.mark.asyncio
async def test_mock_search_results(search_tool):
    """测试模拟搜索结果生成"""
    # 测试默认搜索类型
    result = await search_tool.execute("Python programming")

    assert result["query"] == "Python programming"
    assert result["search_type"] == "search"
    assert "results" in result
    assert len(result["results"]) > 0
    assert "title" in result["results"][0]
    assert "link" in result["results"][0]
    assert "snippet" in result["results"][0]
    assert "note" in result  # 表明这是模拟数据

    # 测试新闻搜索类型
    result = await search_tool.execute("Python programming", search_type="news")

    assert result["search_type"] == "news"
    assert "title" in result["results"][0]
    assert "date" in result["results"][0]
    assert "source" in result["results"][0]

    # 测试图片搜索类型
    result = await search_tool.execute("Python programming", search_type="images")

    assert result["search_type"] == "images"
    assert "imageUrl" in result["results"][0]

    # 测试地点搜索类型
    result = await search_tool.execute("Python programming", search_type="places")

    assert result["search_type"] == "places"
    assert "address" in result["results"][0]
    assert "rating" in result["results"][0]


@pytest.mark.asyncio
async def test_num_results_parameter(search_tool):
    """测试结果数量参数"""
    # 测试默认数量
    result = await search_tool.execute("Python programming")
    assert len(result["results"]) == 5

    # 测试自定义数量
    result = await search_tool.execute("Python programming", num_results=3)
    assert len(result["results"]) == 3

    # 测试超出限制的数量
    result = await search_tool.execute("Python programming", num_results=10)
    assert len(result["results"]) == 5  # 应该被限制为5


@pytest.mark.asyncio
async def test_real_api_call(search_tool, monkeypatch):
    """测试真实API调用"""
    # 模拟API密钥存在
    monkeypatch.setattr(search_tool, "api_key", "fake_api_key")

    # 模拟httpx客户端响应
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "Python编程语言官网",
                "link": "https://www.python.org",
                "snippet": "Python是一种易于学习、功能强大的编程语言。",
                "position": 1,
            },
            {
                "title": "Python教程 - 菜鸟教程",
                "link": "https://www.runoob.com/python/python-tutorial.html",
                "snippet": "Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。",
                "position": 2,
            },
        ]
    }

    # 模拟httpx客户端的post方法
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(search_tool, "client", mock_client)

    # 执行测试
    result = await search_tool.execute("Python programming", num_results=2)

    # 验证API调用
    mock_client.post.assert_called_once()

    # 验证结果
    assert result["query"] == "Python programming"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Python编程语言官网"
    assert result["results"][0]["link"] == "https://www.python.org"
    assert result["results"][1]["title"] == "Python教程 - 菜鸟教程"


@pytest.mark.asyncio
async def test_news_api_call(search_tool, monkeypatch):
    """测试新闻API调用"""
    # 模拟API密钥存在
    monkeypatch.setattr(search_tool, "api_key", "fake_api_key")

    # 模拟httpx客户端响应
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "news": [
            {
                "title": "Python 3.11发布",
                "link": "https://news.example.com/python-3-11",
                "snippet": "Python 3.11版本发布，性能提升25%。",
                "date": "2025-10-01",
                "source": "Tech News",
            }
        ]
    }

    # 模拟httpx客户端的post方法
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(search_tool, "client", mock_client)

    # 执行测试
    result = await search_tool.execute("Python 3.11", search_type="news")

    # 验证结果
    assert result["search_type"] == "news"
    assert result["results"][0]["title"] == "Python 3.11发布"
    assert result["results"][0]["date"] == "2025-10-01"
    assert result["results"][0]["source"] == "Tech News"


@pytest.mark.asyncio
async def test_api_error_handling(search_tool, monkeypatch):
    """测试API错误处理"""
    # 模拟API密钥存在
    monkeypatch.setattr(search_tool, "api_key", "fake_api_key")

    # 模拟httpx客户端抛出异常
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("API连接失败")
    monkeypatch.setattr(search_tool, "client", mock_client)

    # 执行测试
    result = await search_tool.execute("Python programming")

    # 验证结果
    assert "error" in result
    assert "API连接失败" in result["error"]
    assert "mock_data" in result  # 应该返回模拟数据作为备用
    assert result["mock_data"]["query"] == "Python programming"


@pytest.mark.asyncio
async def test_close_method(search_tool):
    """测试close方法"""
    # 模拟httpx客户端
    mock_client = AsyncMock()
    search_tool.client = mock_client

    # 执行close方法
    await search_tool.close()

    # 验证客户端的aclose方法被调用
    mock_client.aclose.assert_called_once()
