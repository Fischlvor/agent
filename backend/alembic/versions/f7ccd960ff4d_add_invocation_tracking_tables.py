"""add_invocation_tracking_tables

Revision ID: f7ccd960ff4d
Revises: d7e3f4a5b6c1
Create Date: 2025-10-08 10:25:09.878527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7ccd960ff4d'
down_revision: Union[str, None] = 'd7e3f4a5b6c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 model_invocations 表
    op.create_table(
        'model_invocations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False, comment='第几次LLM调用'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, comment='输入token数'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, comment='输出token数'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, comment='总token数'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='调用耗时（毫秒）'),
        sa.Column('model_name', sa.String(100), nullable=True, comment='模型名称'),
        sa.Column('finish_reason', sa.String(50), nullable=True, comment='完成原因'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='LLM调用记录表'
    )

    # 创建索引
    op.create_index('idx_model_inv_message', 'model_invocations', ['message_id'])
    op.create_index('idx_model_inv_session', 'model_invocations', ['session_id'])
    op.create_index('idx_model_inv_created', 'model_invocations', ['created_at'])

    # 创建 tool_invocations 表
    op.create_table(
        'tool_invocations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False, comment='第几次工具调用'),
        sa.Column('triggered_by_llm_sequence', sa.Integer(), nullable=True, comment='由第几次LLM调用触发'),
        sa.Column('tool_name', sa.String(100), nullable=False, comment='工具名称'),
        sa.Column('arguments', sa.dialects.postgresql.JSONB(), nullable=True, comment='输入参数'),
        sa.Column('result', sa.Text(), nullable=True, comment='执行结果'),
        sa.Column('status', sa.String(20), nullable=False, comment='执行状态'),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, server_default='false', comment='是否命中缓存'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='执行耗时（毫秒）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='工具调用记录表'
    )

    # 创建索引
    op.create_index('idx_tool_inv_message', 'tool_invocations', ['message_id'])
    op.create_index('idx_tool_inv_session', 'tool_invocations', ['session_id'])
    op.create_index('idx_tool_inv_tool_name', 'tool_invocations', ['tool_name'])
    op.create_index('idx_tool_inv_created', 'tool_invocations', ['created_at'])


def downgrade() -> None:
    # 删除表和索引
    op.drop_index('idx_tool_inv_created', 'tool_invocations')
    op.drop_index('idx_tool_inv_tool_name', 'tool_invocations')
    op.drop_index('idx_tool_inv_session', 'tool_invocations')
    op.drop_index('idx_tool_inv_message', 'tool_invocations')
    op.drop_table('tool_invocations')

    op.drop_index('idx_model_inv_created', 'model_invocations')
    op.drop_index('idx_model_inv_session', 'model_invocations')
    op.drop_index('idx_model_inv_message', 'model_invocations')
    op.drop_table('model_invocations')

