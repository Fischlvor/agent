"""refactor_primary_keys_to_integer

Revision ID: c13982c3ae57
Revises: f7ccd960ff4d
Create Date: 2025-10-08 12:59:49.313052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c13982c3ae57'
down_revision: Union[str, None] = 'f7ccd960ff4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    重构主键为自增Integer

    策略：删除所有表，用正确的结构重建
    """
    # 删除所有表（按依赖顺序，使用原生SQL）
    connection = op.get_bind()
    connection.execute(sa.text('DROP TABLE IF EXISTS tool_invocations CASCADE'))
    connection.execute(sa.text('DROP TABLE IF EXISTS model_invocations CASCADE'))
    connection.execute(sa.text('DROP TABLE IF EXISTS chat_messages CASCADE'))
    connection.execute(sa.text('DROP TABLE IF EXISTS chat_sessions CASCADE'))
    connection.execute(sa.text('DROP TABLE IF EXISTS ai_models CASCADE'))
    connection.execute(sa.text('DROP TABLE IF EXISTS users CASCADE'))

    # 重建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='用户主键ID'),
        sa.Column('username', sa.String(50), nullable=False, comment='用户名'),
        sa.Column('email', sa.String(100), nullable=False, comment='邮箱'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='密码哈希'),
        sa.Column('full_name', sa.String(100), nullable=True, comment='全名'),
        sa.Column('avatar_url', sa.String(255), nullable=True, comment='头像URL'),
        sa.Column('bio', sa.Text(), nullable=True, comment='简介'),
        sa.Column('role', sa.String(20), nullable=True, comment='角色'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否激活'),
        sa.Column('is_verified', sa.Boolean(), default=False, comment='是否验证'),
        sa.Column('verification_token', sa.String(255), nullable=True, comment='验证令牌'),
        sa.Column('reset_password_token', sa.String(255), nullable=True, comment='重置密码令牌'),
        sa.Column('reset_password_expires', sa.DateTime(), nullable=True, comment='重置密码过期时间'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.Column('login_count', sa.Integer(), default=0, comment='登录次数'),
        sa.Column('preferences', sa.JSON(), default={}, comment='用户偏好'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])

    # 重建 chat_sessions 表
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='会话主键ID'),
        sa.Column('session_id', sa.String(36), unique=True, nullable=False, comment='会话业务ID(UUID字符串)'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('title', sa.String(200), nullable=True, comment='会话标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='会话描述'),
        sa.Column('status', sa.String(20), nullable=True, comment='会话状态'),
        sa.Column('is_pinned', sa.Boolean(), default=False, comment='是否置顶'),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True, comment='最后活动时间'),
        sa.Column('message_count', sa.Integer(), default=0, comment='消息数量'),
        sa.Column('total_tokens', sa.Integer(), default=0, comment='总令牌数'),
        sa.Column('current_context_tokens', sa.Integer(), default=0, comment='当前上下文令牌数'),
        sa.Column('ai_model', sa.String(50), nullable=True, comment='AI模型'),
        sa.Column('temperature', sa.Float(), default=0.7, comment='温度参数'),
        sa.Column('max_tokens', sa.Integer(), default=4000, comment='最大令牌数'),
        sa.Column('context_data', sa.JSON(), nullable=True, comment='上下文数据'),
        sa.Column('system_prompt', sa.Text(), nullable=True, comment='系统提示词'),
        sa.Column('session_metadata', sa.JSON(), nullable=True, comment='元数据'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_sessions_session_id', 'chat_sessions', ['session_id'])
    op.create_index('idx_sessions_user_id', 'chat_sessions', ['user_id'])

    # 重建 chat_messages 表
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='消息主键ID'),
        sa.Column('message_id', sa.String(36), unique=True, nullable=False, comment='消息业务ID(UUID字符串)'),
        sa.Column('session_id', sa.String(36), nullable=False, comment='会话业务ID'),
        sa.Column('parent_message_id', sa.String(36), nullable=True, comment='父消息业务ID'),
        sa.Column('role', sa.String(20), nullable=True, comment='角色'),
        sa.Column('content', sa.Text(), nullable=True, comment='内容'),
        sa.Column('message_type', sa.String(30), nullable=True, comment='消息类型'),
        sa.Column('status', sa.String(20), nullable=True, comment='状态'),
        sa.Column('is_edited', sa.Boolean(), default=False, comment='是否编辑'),
        sa.Column('is_deleted', sa.Boolean(), default=False, comment='是否删除'),
        sa.Column('is_pinned', sa.Boolean(), default=False, comment='是否置顶'),
        sa.Column('is_summarized', sa.Boolean(), default=False, comment='是否已摘要'),
        sa.Column('is_summary', sa.Boolean(), default=False, comment='是否为摘要'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='发送时间'),
        sa.Column('delivered_at', sa.DateTime(), nullable=True, comment='送达时间'),
        sa.Column('read_at', sa.DateTime(), nullable=True, comment='已读时间'),
        sa.Column('model_name', sa.String(50), nullable=True, comment='模型名称'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, comment='提示令牌数'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, comment='完成令牌数'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, comment='总令牌数'),
        sa.Column('generation_time', sa.Float(), nullable=True, comment='生成时间'),
        sa.Column('structured_content', sa.JSON(), nullable=True, comment='结构化内容'),
        sa.Column('attachments', sa.JSON(), nullable=True, comment='附件'),
        sa.Column('user_rating', sa.Integer(), nullable=True, comment='用户评分'),
        sa.Column('user_feedback', sa.Text(), nullable=True, comment='用户反馈'),
        sa.Column('message_metadata', sa.JSON(), nullable=True, comment='元数据'),
        sa.Column('error_info', sa.JSON(), nullable=True, comment='错误信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE')
    )
    op.create_index('idx_messages_message_id', 'chat_messages', ['message_id'])
    op.create_index('idx_messages_session_id', 'chat_messages', ['session_id'])

    # 重建 ai_models 表
    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='模型主键ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='模型名称'),
        sa.Column('model_id', sa.String(100), nullable=False, unique=True, comment='模型ID'),
        sa.Column('provider', sa.String(50), nullable=False, comment='提供商'),
        sa.Column('base_url', sa.String(255), nullable=False, comment='API地址'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('max_tokens', sa.Integer(), default=8192, comment='最大token数'),
        sa.Column('max_context_length', sa.Integer(), default=32768, comment='最大上下文长度'),
        sa.Column('supports_streaming', sa.Boolean(), default=True, comment='是否支持流式'),
        sa.Column('supports_tools', sa.Boolean(), default=True, comment='是否支持工具'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否激活'),
        sa.Column('icon_url', sa.String(500), nullable=True, comment='图标URL'),
        sa.Column('display_order', sa.Integer(), default=0, comment='显示顺序'),
        sa.Column('config', sa.JSON(), nullable=True, comment='额外配置'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_models_model_id', 'ai_models', ['model_id'])

    # 重建 model_invocations 表（修正外键类型）
    op.create_table(
        'model_invocations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='调用记录主键ID'),
        sa.Column('message_id', sa.String(36), nullable=False, comment='消息业务ID'),
        sa.Column('session_id', sa.String(36), nullable=False, comment='会话业务ID'),
        sa.Column('sequence_number', sa.Integer(), nullable=False, comment='第几次LLM调用'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, comment='输入token数'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, comment='输出token数'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, comment='总token数'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='调用耗时（毫秒）'),
        sa.Column('model_name', sa.String(100), nullable=True, comment='模型名称'),
        sa.Column('finish_reason', sa.String(50), nullable=True, comment='完成原因'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.message_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE')
    )
    op.create_index('idx_model_inv_message', 'model_invocations', ['message_id'])
    op.create_index('idx_model_inv_session', 'model_invocations', ['session_id'])
    op.create_index('idx_model_inv_created', 'model_invocations', ['created_at'])

    # 重建 tool_invocations 表（修正外键类型）
    op.create_table(
        'tool_invocations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='调用记录主键ID'),
        sa.Column('message_id', sa.String(36), nullable=False, comment='消息业务ID'),
        sa.Column('session_id', sa.String(36), nullable=False, comment='会话业务ID'),
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
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.message_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE')
    )
    op.create_index('idx_tool_inv_message', 'tool_invocations', ['message_id'])
    op.create_index('idx_tool_inv_session', 'tool_invocations', ['session_id'])
    op.create_index('idx_tool_inv_tool_name', 'tool_invocations', ['tool_name'])
    op.create_index('idx_tool_inv_created', 'tool_invocations', ['created_at'])


def downgrade() -> None:
    """降级：恢复为UUID主键"""
    # 这是破坏性更改，downgrade不实现
    raise NotImplementedError("此迁移不支持降级（破坏性更改）")

