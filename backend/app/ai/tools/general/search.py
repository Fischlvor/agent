import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from ..base import BaseTool

LOGGER = logging.getLogger(__name__)


class SearchTool(BaseTool):
    """搜索工具，用于执行网络搜索"""

    def __init__(self):
        """初始化搜索工具"""
        self.api_key = os.environ.get(
            "SERPER_API_KEY", "7a3fa888d859a1f575a29615f4b3088e57ba7f60")
        if not self.api_key:
            raise ValueError("必须设置SERPER_API_KEY环境变量")

        self.base_url = "https://google.serper.dev/search"
        self.client = httpx.AsyncClient(timeout=15.0)

        # 设置请求头
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "search",
    ) -> Dict[str, Any]:
        """
        执行网络搜索

        :param query: 搜索查询
        :param num_results: 返回结果数量，默认为5
        :param search_type: 搜索类型，可选值为 "search", "news", "images", "places"
        :return: 包含搜索结果的字典
        """
        LOGGER.info("执行搜索: 查询=%s, 类型=%s, 结果数量=%s", query, search_type, num_results)

        try:
            # 构建请求参数
            payload = {
                "q": query,
                "num": min(num_results, 10),  # 限制最大结果数
            }

            # 发送请求
            endpoint = f"/{search_type}" if search_type != "search" else ""
            response = await self.client.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()

            # 解析响应
            data = response.json()

            # 提取搜索结果
            search_results = {
                "query":
                query,
                "search_type":
                search_type,
                "results":
                self._parse_search_results(data, search_type, num_results),
            }

            return search_results

        except Exception as e:
            error_message = f"搜索失败: {str(e)}"
            LOGGER.error(error_message)
            raise RuntimeError(error_message)

    def _parse_search_results(
        self,
        data: Dict[str, Any],
        search_type: str,
        num_results: int,
    ) -> List[Dict[str, Any]]:
        """
        解析搜索结果

        :param data: API返回的原始数据
        :param search_type: 搜索类型
        :param num_results: 结果数量
        :return: 解析后的搜索结果列表
        """
        results = []

        if search_type == "search":
            # 提取普通搜索结果
            organic = data.get("organic", [])
            for item in organic[:num_results]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0),
                }
                results.append(result)

        elif search_type == "news":
            # 提取新闻搜索结果
            news = data.get("news", [])
            for item in news[:num_results]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "date": item.get("date", ""),
                    "source": item.get("source", ""),
                }
                results.append(result)

        elif search_type == "images":
            # 提取图片搜索结果
            images = data.get("images", [])
            for item in images[:num_results]:
                result = {
                    "title": item.get("title", ""),
                    "imageUrl": item.get("imageUrl", ""),
                    "link": item.get("link", ""),
                }
                results.append(result)

        elif search_type == "places":
            # 提取地点搜索结果
            places = data.get("places", [])
            for item in places[:num_results]:
                result = {
                    "title": item.get("title", ""),
                    "address": item.get("address", ""),
                    "rating": item.get("rating", 0),
                    "reviews": item.get("reviews", 0),
                }
                results.append(result)

        return results

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
