import asyncio
import json
import os
import sys

sys.path.append(".")

from app.ai.tools.general import SearchTool


async def main():
    # 创建搜索工具实例
    search_tool = SearchTool()

    # 设置API密钥
    # 这里使用一个示例密钥，实际使用时需要替换为有效的API密钥
    os.environ["SERPER_API_KEY"] = "serper_api_key_here"

    try:
        # 执行普通搜索
        print("=== 普通搜索结果 ===")
        result = await search_tool.execute("Python programming", num_results=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n=== 新闻搜索结果 ===")
        result = await search_tool.execute(
            "Python programming", search_type="news", num_results=2
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n=== 图片搜索结果 ===")
        result = await search_tool.execute(
            "Python programming", search_type="images", num_results=2
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print("\n=== 地点搜索结果 ===")
        result = await search_tool.execute(
            "Python programming", search_type="places", num_results=2
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    finally:
        # 关闭客户端连接
        await search_tool.close()


if __name__ == "__main__":
    asyncio.run(main())
