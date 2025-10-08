"""add context management fields

Revision ID: d7e3f4a5b6c1
Revises: cfadc294894e
Create Date: 2025-10-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7e3f4a5b6c1'
down_revision: Union[str, None] = 'cfadc294894e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ChatMessage 表添加字段
    op.add_column('chat_messages', sa.Column('is_summarized', sa.Boolean(), nullable=False, server_default='0', comment='是否已被摘要覆盖'))
    op.add_column('chat_messages', sa.Column('is_summary', sa.Boolean(), nullable=False, server_default='0', comment='是否为摘要消息'))

    # ChatSession 表添加字段
    op.add_column('chat_sessions', sa.Column('current_context_tokens', sa.Integer(), nullable=False, server_default='0', comment='当前上下文令牌数'))

    # AIModel 表添加字段
    op.add_column('ai_models', sa.Column('max_context_length', sa.Integer(), nullable=False, server_default='32768', comment='最大上下文长度'))


def downgrade() -> None:
    # AIModel 表删除字段
    op.drop_column('ai_models', 'max_context_length')

    # ChatSession 表删除字段
    op.drop_column('chat_sessions', 'current_context_tokens')

    # ChatMessage 表删除字段
    op.drop_column('chat_messages', 'is_summary')
    op.drop_column('chat_messages', 'is_summarized')

