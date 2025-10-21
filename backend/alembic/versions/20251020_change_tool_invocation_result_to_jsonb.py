"""change tool_invocation result to jsonb

Revision ID: 20251020_result_jsonb
Revises:
Create Date: 2025-10-20 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251020_result_jsonb'
down_revision = None  # 如果需要，填写前一个revision ID
branch_labels = None
depends_on = None


def upgrade():
    """
    将 tool_invocations.result 字段从 Text 改为 JSONB
    """
    # 1. 创建临时列
    op.add_column(
        'tool_invocations',
        sa.Column('result_jsonb', postgresql.JSONB(), nullable=True)
    )

    # 2. 迁移数据：处理现有的Python dict字符串格式
    # 现有格式: {'result': '{"success": true, ...}'}
    # 需要提取内部JSON并解析
    op.execute("""
        UPDATE tool_invocations
        SET result_jsonb =
            CASE
                -- 如果result是NULL，保持NULL
                WHEN result IS NULL THEN NULL
                -- 如果result包含 "{'result': "，提取内部JSON
                WHEN result LIKE '{''result'': %' THEN
                    -- 使用正则提取 'result': 后的JSON部分
                    (regexp_match(result, E'''result'':\\s*''(.*)''\\}'))[1]::jsonb
                -- 尝试直接转换为JSONB
                ELSE
                    CASE
                        WHEN result ~ '^\{.*\}$' THEN result::jsonb
                        ELSE NULL
                    END
            END
    """)

    # 3. 删除旧列
    op.drop_column('tool_invocations', 'result')

    # 4. 重命名新列
    op.alter_column('tool_invocations', 'result_jsonb', new_column_name='result')


def downgrade():
    """
    回滚：将 tool_invocations.result 字段从 JSONB 改回 Text
    """
    # 1. 创建临时列
    op.add_column(
        'tool_invocations',
        sa.Column('result_text', sa.Text(), nullable=True)
    )

    # 2. 迁移数据：将JSONB转换为Text
    op.execute("""
        UPDATE tool_invocations
        SET result_text =
            CASE
                WHEN result IS NULL THEN NULL
                ELSE result::text
            END
    """)

    # 3. 删除JSONB列
    op.drop_column('tool_invocations', 'result')

    # 4. 重命名回原来的名称
    op.alter_column('tool_invocations', 'result_text', new_column_name='result')

