#!/usr/bin/env python3
"""
数据迁移脚本：将 tool_invocations.result 从 Text 转换为 JSONB 格式

现有格式: {'result': '{"success": true, ...}'}  (Python dict的字符串表示)
目标格式: {"success": true, ...}  (标准JSONB)
"""
import sys
import json
import ast
import psycopg2
from psycopg2.extras import Json

def migrate_tool_results():
    """迁移工具调用结果数据"""

    # 连接数据库
    conn = psycopg2.connect(
        host='8.148.64.96',
        port=15432,
        database='agent_db',
        user='postgres',
        password='zJ0_jE6e,mSYLYYx'
    )

    cur = conn.cursor()

    try:
        # 1. 添加新的JSONB列
        print("步骤1: 添加result_jsonb列...")
        cur.execute("""
            ALTER TABLE tool_invocations
            ADD COLUMN IF NOT EXISTS result_jsonb JSONB
        """)
        conn.commit()
        print("✓ 完成")

        # 2. 查询所有需要迁移的记录
        print("\n步骤2: 查询现有记录...")
        cur.execute("""
            SELECT id, result
            FROM tool_invocations
            WHERE result IS NOT NULL
        """)
        records = cur.fetchall()
        print(f"✓ 找到 {len(records)} 条记录")

        # 3. 逐条转换
        print("\n步骤3: 转换数据...")
        success_count = 0
        error_count = 0

        for record_id, result_text in records:
            try:
                # 尝试解析Python dict字符串
                if result_text.startswith("{'result':") or result_text.startswith('{"result":'):
                    # 格式: {'result': '...'}
                    try:
                        # 使用ast.literal_eval解析Python dict
                        result_dict = ast.literal_eval(result_text)
                        if isinstance(result_dict, dict) and 'result' in result_dict:
                            # 提取内部的JSON字符串
                            inner_json_str = result_dict['result']
                            # 解析为JSON对象
                            json_obj = json.loads(inner_json_str)
                        else:
                            json_obj = result_dict
                    except (ValueError, SyntaxError):
                        # 如果ast失败，尝试直接JSON解析
                        json_obj = json.loads(result_text)
                else:
                    # 尝试直接解析为JSON
                    json_obj = json.loads(result_text)

                # 更新到JSONB列
                cur.execute("""
                    UPDATE tool_invocations
                    SET result_jsonb = %s
                    WHERE id = %s
                """, (Json(json_obj), record_id))

                success_count += 1
                if success_count % 10 == 0:
                    print(f"  已转换 {success_count}/{len(records)} 条记录...")

            except Exception as e:
                error_count += 1
                print(f"  ✗ ID={record_id} 转换失败: {e}")
                # 失败的记录设置为NULL
                cur.execute("""
                    UPDATE tool_invocations
                    SET result_jsonb = NULL
                    WHERE id = %s
                """, (record_id,))

        conn.commit()
        print(f"✓ 转换完成: 成功 {success_count} 条, 失败 {error_count} 条")

        # 4. 删除旧列，重命名新列
        print("\n步骤4: 替换旧列...")
        cur.execute("ALTER TABLE tool_invocations DROP COLUMN IF EXISTS result")
        cur.execute("ALTER TABLE tool_invocations RENAME COLUMN result_jsonb TO result")
        conn.commit()
        print("✓ 完成")

        print("\n✅ 数据迁移成功!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 80)
    print("开始迁移 tool_invocations.result: Text -> JSONB")
    print("=" * 80)

    response = input("\n⚠️  这将修改数据库结构，是否继续？ (yes/no): ")
    if response.lower() != 'yes':
        print("已取消")
        sys.exit(0)

    migrate_tool_results()

